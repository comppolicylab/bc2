import json
import logging
import math
import queue
import threading
from dataclasses import asdict, dataclass

from .example import ExampleDoc
from .io import FileIO
from .model import ModelRunner
from .train import ModelDetail

logger = logging.getLogger(__name__)


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


@dataclass
class EvaluationTask:
    model_id: str
    file: str
    fields: list[str]


@dataclass
class EvaluationTaskResult:
    model_id: str
    results: dict[str, ConfusionMatrix]


@dataclass
class ModelInfo:
    model_id: str
    fields: list[str]
    detail: ModelDetail
    test_samples: int


def validate(
    fr: FileIO,
    runner: ModelRunner,
    eval_dir: str,
    models: list[ModelDetail],
    threads: int = 1,
) -> CrossValidationResult:
    """Validate the given models.

    Args:
        fr: A FileIO instance.
        runner: A ModelRunner instance.
        eval_dir: The path to the evaluation directory.
        models: The list of models to evaluate.
        threads: The number of threads to use.

    Returns:
        The results of the evaluation.
    """
    results = list[ModelEvalResult]()

    task_q = queue.Queue[EvaluationTask]()
    results_q = queue.Queue[EvaluationTaskResult]()

    model_info = dict[str, ModelInfo]()

    # Generate tasks for every test file, for every model
    for m in models:
        model_id = m["model_id"]
        logger.info(f"Evaluating model {model_id} ...")
        test_dir = m["test_path"]
        test_files = [f for f in fr.list(test_dir) if f.endswith(".pdf")]
        fields = get_fields(fr, m["train_path"])
        model_info[model_id] = ModelInfo(model_id, fields, m, len(test_files))

        for f in test_files:
            task_q.put(EvaluationTask(model_id, f, fields))

    def worker():
        while True:
            try:
                task = task_q.get(timeout=1)
                if not task:
                    continue
                predicted_labels = runner.run(task.model_id, task.file)
                true_labels = ExampleDoc.load(fr, task.file, task.fields).labels
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

                results_q.put(EvaluationTaskResult(task.model_id, doc_score))
                task_q.task_done()
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error in worker: {e}")
                task_q.task_done()
                # TODO: retry

    # Start the workers
    tx = [threading.Thread(target=worker) for _ in range(threads)]
    for t in tx:
        t.start()

    # Wait for the tasks to complete
    task_q.join()

    # Stop the workers
    for _ in tx:
        t.join()

    # Aggregate the results
    agg_results = {m["model_id"]: dict[str, ConfusionMatrix]() for m in models}

    while not results_q.empty():
        score = results_q.get()
        for lbl, cm in score.results.items():
            if lbl not in agg_results[score.model_id]:
                agg_results[score.model_id][lbl] = cm
            else:
                agg_results[score.model_id][lbl] += cm

    # Compile results for each model
    for model_id, agg in agg_results.items():
        minfo = model_info[model_id]
        results.append(
            ModelEvalResult(
                model_id=model_id,
                model_detail=minfo.detail,
                labels=minfo.fields,
                n=minfo.test_samples,
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

    # Aggregate results over all models
    result = summarize_model_results(results)

    # Save results to the storage backend
    results_path = fr.join(eval_dir, "results.json")
    fr.write(results_path, json.dumps(asdict(result)), overwrite=True)
    return result
