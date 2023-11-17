import json
import logging

from .fold import fold
from .io import FileIO
from .measure import CrossValidationResult, validate
from .model import ModelRunner, ModelTrainer
from .train import ModelDetail, train

logger = logging.getLogger(__name__)
logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
    logging.WARNING
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


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
    return validate(fr, runner, eval_dir, models, threads=threads)


def run_all(
    fr: FileIO,
    trainer: ModelTrainer,
    runner: ModelRunner,
    doc_base_path: str,
    eval_base_path: str,
    k: int = 5,
    seed: int = 0,
    threads: int = 10,
) -> CrossValidationResult:
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

    Returns:
        The results of the evaluation.
    """
    # The eval path can't be a subdirectory of the doc path.
    if is_subdir(fr, doc_base_path, eval_base_path):
        raise ValueError("eval_base_path must not be a subdirectory of doc_base_path")

    # Split documents into K folds
    eval_id = fold(fr, doc_base_path, eval_base_path, k, seed, threads=threads)

    # Train the K models corresponding to the folds
    train(fr, trainer, eval_base_path, eval_id, threads=threads)

    # Compute results
    return run_test(fr, runner, eval_base_path, eval_id, threads=threads)
