import json
import logging
import queue
import threading
from datetime import datetime

# from .example import ExampleDoc
from .io import FileIO
from .sample import KFoldCrossValidationSampler
from .train import ModelTrainer

logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_labeled_files(fr: FileIO, base_path: str) -> list[str]:
    """Get a list of files that have labels and OCR.

    Args:
        fr: A FileIO instance.
        base_path: The base path to the data.

    Returns:
        A list of file names.
    """
    all_files = list(fr.list(base_path))

    # Filter to files that have OCR and labels.
    pdfs = set[str]()
    has_labels = set[str]()
    has_ocr = set[str]()

    for name in all_files:
        if name.endswith(".pdf"):
            pdfs.add(name)
        elif name.endswith(".labels.json"):
            pdf_name = name[: -len(".labels.json")]
            has_labels.add(pdf_name)
        elif name.endswith(".ocr.json"):
            pdf_name = name[: -len(".ocr.json")]
            has_ocr.add(pdf_name)

    return list(pdfs.intersection(has_ocr))


def copy_labeled_data(fr: FileIO, name: str, dest_dir: str):
    """Copy the labeled data for the given file to the destination directory.

    Args:
        fr: A FileIO instance.
        name: The name of the file to copy.
        dest_dir: The destination directory.
    """
    basename = fr.basename(name)

    for sfx in ["", ".labels.json", ".ocr.json"]:
        src = name + sfx
        dst = fr.join(dest_dir, basename + sfx)
        if fr.exists(src):
            fr.copy(src, dst)


def multi_copy_labeled_data(
    fr: FileIO, files: list[str], dest_dir: str, threads: int = 1
):
    """Copy all labeled data for the given files to the destination directory.

    Args:
        fr: A FileIO instance.
        files: A list of file names.
        dest_dir: The destination directory.
        threads: The number of threads to use.
    """
    if threads < 1:
        raise ValueError("threads must be at least 1")

    q = queue.Queue[str]()
    for name in files:
        q.put_nowait(name)

    def worker():
        while True:
            try:
                name = q.get(timeout=1)
                if name is None:
                    continue
                logger.debug(f"Copying {name} to {dest_dir} ...")
                try:
                    copy_labeled_data(fr, name, dest_dir)
                except KeyboardInterrupt:
                    logger.warning("Keyboard interrupt, exiting thread ...")
                    break
                except Exception as e:
                    logger.warning(f"Failed to copy {name}: {e}, retrying ...")
                    # TODO: cap retries
                    q.put(name)
                finally:
                    q.task_done()
            except queue.Empty:
                break

    logger.debug(f"Starting {threads} threads to copy data ...")
    tx = [threading.Thread(target=worker) for _ in range(threads)]
    for t in tx:
        t.start()
    q.join()
    for t in tx:
        t.join()


def is_subdir(fr: FileIO, parent: str, child: str) -> bool:
    """Check if the child directory is a subdirectory of the parent directory.

    Args:
        fr: A FileIO instance.
        parent: The parent directory.
        child: The child directory.

    Returns:
        True if the child is a subdirectory of the parent.
    """
    parent_parts = fr.splitpath(parent)
    child_parts = fr.splitpath(child)
    return parent_parts == child_parts[: len(parent_parts)]


def evaluate(
    fr: FileIO,
    trainer: ModelTrainer,
    doc_base_path: str,
    eval_base_path: str,
    k: int = 5,
    seed: int = 0,
    threads: int = 4,
):
    """Evaluate the model on the given data.

    Args:
        fr: A FileIO instance.
        dm: A DocumentModelAdministrationClient instance.
        doc_base_path: The base path to the data.
        eval_base_path: The base path to store the evaluation data.
        k: The number of folds to use for cross validation.
        seed: The random seed to use for cross validation.
        threads: The number of threads to use for copying data.
    """
    # The eval path can't be a subdirectory of the doc path.
    if is_subdir(fr, doc_base_path, eval_base_path):
        raise ValueError("eval_base_path must not be a subdirectory of doc_base_path")

    files_to_process = get_labeled_files(fr, doc_base_path)

    logger.info(f"Found {len(files_to_process)} files in {doc_base_path}")
    kfold = KFoldCrossValidationSampler[str](k)

    # Generate a unique (but interprettable) name for this run.
    eval_name = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    eval_dir = fr.join(eval_base_path, eval_name)

    md_folds = list[dict[str, list[str]]]()
    metadata = {
        "eval_name": eval_name,
        "base_path": doc_base_path,
        "k": k,
        "seed": seed,
        "folds": md_folds,
        "timestamp": datetime.now().isoformat(),
        "files": files_to_process,
    }

    folds = list[str]()

    for i, (train, test) in enumerate(kfold(files_to_process, seed=seed)):
        logger.info(f"Setting up fold {i + 1} / {k} ...")
        # Save the training and testing sets in a new directory
        fold_dir = fr.join(eval_dir, f"fold-{i}")
        train_dir = fr.join(fold_dir, "train")
        test_dir = fr.join(fold_dir, "test")
        multi_copy_labeled_data(fr, train, train_dir, threads=threads)
        multi_copy_labeled_data(fr, test, test_dir, threads=threads)
        folds.append(fold_dir)
        md_folds.append({"train": train, "test": test})

    # Save the metadata
    fr.write(fr.join(eval_dir, "metadata.json"), json.dumps(metadata))

    # Train cross validation models
    validation = list[dict[str, str]]()
    for i, d in enumerate(folds):
        train_dir = fr.join(d, "train")
        test_dir = fr.join(d, "test")
        logger.info(f"Training model for fold {i + 1} / {k} ...")
        model_name = f"{eval_name}-fold-{i}"
        model_id = trainer.train(model_name, train_dir)
        validation.append(
            {
                "model_id": model_id,
                "test_dir": test_dir,
                "train_dir": train_dir,
            }
        )

    # Save models data
    fr.write(fr.join(eval_dir, "models.json"), json.dumps(validation))

    # Evaluate the models
    for spec in validation:
        model_id = spec["model_id"]
        test_dir = spec["test_dir"]
        logger.info(f"Evaluating model {model_id} ...")
        # doc = ExampleDoc.load(fr, name)
