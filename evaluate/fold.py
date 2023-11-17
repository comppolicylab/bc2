import json
import logging
import queue
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TypedDict

from .io import FileIO
from .sample import KFoldCrossValidationSampler

logger = logging.getLogger(__name__)


class FoldDetail(TypedDict):
    """Details for a fold."""

    id: str
    path: str
    train_path: str
    test_path: str
    train: list[str]
    test: list[str]


@dataclass
class Metadata:
    """Metadata for an evaluation run."""

    eval_name: str
    base_path: str
    k: int
    seed: int
    folds: list[FoldDetail]
    timestamp: str
    files: list[str]


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


def fold(
    fr: FileIO,
    doc_base_path: str,
    eval_base_path: str,
    k: int,
    seed: int,
    threads: int = 1,
) -> str:
    """Split the data into k folds for cross-validation.

    Args:
        fr: A FileIO instance.
        doc_base_path: The base path to the data.
        eval_base_path: The base path to the evaluation data.
        k: The number of folds.
        seed: The random seed.
        threads: The number of threads to use.

    Returns:
        Name of the eval
    """
    # Generate a unique (but interprettable) name for this run.
    eval_name = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    eval_dir = fr.join(eval_base_path, eval_name)
    logger.info(f"Creating evaluation directory {eval_dir} ...")

    files_to_process = get_labeled_files(fr, doc_base_path)

    logger.info(f"Found {len(files_to_process)} files in {doc_base_path}")
    kfold = KFoldCrossValidationSampler[str](k)

    metadata = Metadata(
        eval_name=eval_name,
        base_path=doc_base_path,
        k=k,
        seed=seed,
        folds=[],
        timestamp=datetime.now().isoformat(),
        files=files_to_process,
    )

    for i, (train, test) in enumerate(kfold(files_to_process, seed=seed)):
        logger.info(f"Setting up fold {i + 1} / {k} ...")
        # Save the training and testing sets in a new directory
        fold_dir = fr.join(eval_dir, f"fold-{i}")
        train_dir = fr.join(fold_dir, "train")
        test_dir = fr.join(fold_dir, "test")
        multi_copy_labeled_data(fr, train, train_dir, threads=threads)
        multi_copy_labeled_data(fr, test, test_dir, threads=threads)
        metadata.folds.append(
            FoldDetail(
                id=f"{eval_name}-fold-{i}",
                path=fold_dir,
                train_path=train_dir,
                test_path=test_dir,
                train=train,
                test=test,
            )
        )

    # Save the metadata
    md_path = fr.join(eval_dir, "metadata.json")
    fr.write(md_path, json.dumps(asdict(metadata)), overwrite=True)

    return eval_name
