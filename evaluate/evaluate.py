import json
import logging
import math
import queue
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TypedDict

from .example import ExampleDoc
from .io import FileIO
from .model import ModelRunner, ModelTrainer
from .sample import KFoldCrossValidationSampler

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


class FoldDetail(TypedDict):
    """Details for a fold."""

    id: str
    path: str
    train_path: str
    test_path: str
    train: list[str]
    test: list[str]


class ModelDetail(TypedDict):
    """Details for a model."""

    model_id: str
    eval_id: str
    test_path: str
    train_path: str


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


def train(
    fr: FileIO,
    trainer: ModelTrainer,
    eval_base_path: str,
    eval_id: str,
    threads: int = 1,
):
    """Train the model described at the given eval_id.

    Args:
        fr: A FileIO instance.
        trainer: The model trainer.
        eval_base_path: The base path to the evaluation data.
        eval_id: The evaluation id.
        threads: The number of threads to use.
    """
    # Load the metadata
    eval_dir = fr.join(eval_base_path, eval_id)
    md_path = fr.join(eval_dir, "metadata.json")
    if not fr.exists(md_path):
        raise ValueError(f"Metadata file {md_path} does not exist")
    metadata = Metadata(**json.loads(fr.read(md_path)))

    # Run training procedure on each fold
    q = queue.Queue[FoldDetail]()
    finished = queue.Queue[ModelDetail]()

    def worker():
        while True:
            try:
                d = q.get(timeout=1)
                train_dir = d["train_path"]
                test_dir = d["test_path"]
                model_name = d["id"]
                logger.info(f"Training model for {model_name} ...")
                model_id = trainer.train(model_name, train_dir)
                finished.put(
                    ModelDetail(
                        model_id=model_id,
                        eval_id=eval_id,
                        test_path=test_dir,
                        train_path=train_dir,
                    )
                )
                q.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error training model: {e}")
                q.task_done()

    for d in metadata.folds:
        q.put(d)

    tx = [threading.Thread(target=worker) for _ in range(threads)]
    for t in tx:
        t.start()

    q.join()

    # Collect the results
    models = list[ModelDetail]()
    while not finished.empty():
        models.append(finished.get())

    # Join the threads
    for t in tx:
        t.join()

    # Save models data
    fr.write(fr.join(eval_dir, "models.json"), json.dumps(models), overwrite=True)


@dataclass
class ConfusionMatrix:
    tp: int
    tn: int
    fp: int
    fn: int

    def precision(self) -> float:
        try:
            return self.tp / (self.tp + self.fp)
        except ZeroDivisionError:
            return math.nan

    def recall(self) -> float:
        try:
            return self.tp / (self.tp + self.fn)
        except ZeroDivisionError:
            return math.nan

    def __add__(self, other: "ConfusionMatrix") -> "ConfusionMatrix":
        return ConfusionMatrix(
            tp=self.tp + other.tp,
            tn=self.tn + other.tn,
            fp=self.fp + other.fp,
            fn=self.fn + other.fn,
        )

    def __iadd__(self, other: "ConfusionMatrix") -> "ConfusionMatrix":
        self.tp += other.tp
        self.tn += other.tn
        self.fp += other.fp
        self.fn += other.fn
        return self


def get_fields(fr: FileIO, path: str) -> list[str]:
    """Get the list of fields in the given path.

    Args:
        fr: A FileIO instance.
        path: The path to the directory containing the fields.

    Returns:
        The list of fields.
    """
    fields_json = fr.join(path, "fields.json")
    if not fr.exists(fields_json):
        raise ValueError(f"Fields data not found at {fields_json}")
    data = json.loads(fr.read(fields_json))
    return [d["fieldKey"] for d in data["fields"]]


@dataclass
class ClassResult:
    name: str
    confusion_matrix: ConfusionMatrix
    precision: float
    recall: float


@dataclass
class ModelEvalResult:
    model_id: str
    model_detail: ModelDetail
    labels: list[str]
    results: dict[str, ClassResult]
    n: int


@dataclass
class MeanClassResult:
    name: str
    precision: float
    recall: float
    n: int


@dataclass
class CrossValidationResult:
    mean_results: dict[str, MeanClassResult]
    model_results: list[ModelEvalResult]


def summarize_model_results(results: list[ModelEvalResult]) -> CrossValidationResult:
    """Summarize the results of a model evaluation.

    Args:
        results: The list of results.

    Returns:
        The summarized results.
    """
    all_classes = set[str]()
    for r in results:
        all_classes |= set(r.labels)

    mean_results = {c: MeanClassResult(c, math.nan, math.nan, 0) for c in all_classes}
    for c, mcr in mean_results.items():
        mcr.n = sum(m.n for m in results if c in m.results)
        if mcr.n > 0:
            mcr.precision = (
                sum(
                    m.results[c].precision * m.n
                    for m in results
                    if c in m.results and not math.isnan(m.results[c].precision)
                )
                / mcr.n
            )
            mcr.recall = (
                sum(
                    m.results[c].recall * m.n
                    for m in results
                    if c in m.results and not math.isnan(m.results[c].recall)
                )
                / mcr.n
            )

    return CrossValidationResult(
        model_results=results,
        mean_results=mean_results,
    )


def run_test(
    fr: FileIO, runner: ModelRunner, eval_base_path: str, eval_id: str, threads: int = 1
) -> CrossValidationResult:
    """Run the evaluation procedure.

    Args:
        fr: A FileIO instance.
        runner: A ModelRunner instance.
        eval_base_path: The base path to the evaluation data.
        eval_id: The ID of the evaluation run
        threads: The number of threads to use for backend calls

    Returns:
        The results of the evaluation.
    """
    # Load models data
    eval_dir = fr.join(eval_base_path, eval_id)
    models_path = fr.join(eval_dir, "models.json")
    if not fr.exists(models_path):
        raise ValueError(f"Models data not found at {models_path}")

    models = [ModelDetail(**d) for d in json.loads(fr.read(models_path))]  # type: ignore[typeddict-item]

    results = list[ModelEvalResult]()
    for m in models:
        model_id = m["model_id"]
        logger.info(f"Evaluating model {model_id} ...")
        test_dir = m["test_path"]
        test_files = [f for f in fr.list(test_dir) if f.endswith(".pdf")]
        fields = get_fields(fr, m["train_path"])

        scores = list[dict[str, ConfusionMatrix]]()

        n = len(test_files)
        logger.info(f"Running model {m['model_id']} on {n} file(s) ...")
        for i, f in enumerate(test_files):
            logger.info(f"Running model {m['model_id']} on {f} ({i + 1} / {n}) ...")
            predicted_labels = runner.run(model_id, f)
            true_labels = ExampleDoc.load(fr, f, fields).labels
            doc_score = dict[str, ConfusionMatrix]()
            for lbl in predicted_labels.keys() | true_labels.keys():
                doc_score[lbl] = ConfusionMatrix(
                    tp=0,
                    tn=0,
                    fp=0,
                    fn=0,
                )

                if true_labels.has(lbl):
                    # Either a true positive or a false negative
                    if true_labels.equal(lbl, predicted_labels):
                        doc_score[lbl].tp += 1
                    else:
                        doc_score[lbl].fn += 1
                else:
                    # Either a true negative or a false positive
                    if predicted_labels.has(lbl):
                        doc_score[lbl].fp += 1
                    else:
                        doc_score[lbl].tn += 1

            scores.append(doc_score)

        # Aggregate the matrices
        agg = dict[str, ConfusionMatrix]()
        for s in scores:
            for lbl, cm in s.items():
                if lbl not in agg:
                    agg[lbl] = cm
                else:
                    agg[lbl] += cm

        results.append(
            ModelEvalResult(
                model_id=model_id,
                model_detail=m,
                labels=fields,
                n=len(scores),
                results={
                    lbl: ClassResult(
                        name=lbl,
                        confusion_matrix=cm,
                        precision=cm.precision(),
                        recall=cm.recall(),
                    )
                    for lbl, cm in agg.items()
                },
            )
        )
        nar_cm = agg["narrative"]
        logger.info(
            f"Narrative result: precision={nar_cm.precision()}, recall={nar_cm.recall()}"
        )

    result = summarize_model_results(results)
    results_path = fr.join(eval_dir, "results.json")
    fr.write(results_path, json.dumps(asdict(result)), overwrite=True)
    return result


def run_all(
    fr: FileIO,
    trainer: ModelTrainer,
    runner: ModelRunner,
    doc_base_path: str,
    eval_base_path: str,
    k: int = 5,
    seed: int = 0,
    threads: int = 10,
):
    """Evaluate the model on the given data.

    Args:
        fr: A FileIO instance.
        trainer: The model trainer.
        runner: The model runner.
        doc_base_path: The base path to the data.
        eval_base_path: The base path to store the evaluation data.
        k: The number of folds to use for cross validation.
        seed: The random seed to use for cross validation.
        threads: The number of threads to use for parallelizing backend requests
    """
    # The eval path can't be a subdirectory of the doc path.
    if is_subdir(fr, doc_base_path, eval_base_path):
        raise ValueError("eval_base_path must not be a subdirectory of doc_base_path")

    # Split documents into K folds
    eval_id = fold(fr, doc_base_path, eval_base_path, k, seed, threads=threads)

    # Train the K models corresponding to the folds
    train(fr, trainer, eval_base_path, eval_id, threads=threads)

    # Compute results
    run_test(fr, runner, eval_base_path, eval_id, threads=threads)
