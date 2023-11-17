import json
import logging
import queue
import threading
from typing import TypedDict

from .fold import FoldDetail, Metadata
from .io import FileIO
from .model import ModelTrainer

logger = logging.getLogger(__name__)


class ModelDetail(TypedDict):
    """Details for a model."""

    model_id: str
    eval_id: str
    test_path: str
    train_path: str


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
