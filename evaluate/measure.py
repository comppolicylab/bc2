import json
import logging
import math
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
