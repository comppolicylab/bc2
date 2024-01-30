import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import TypedDict

from .docs import list_docs, multi_copy_docs
from .io import FileIO
from .sample import KFoldCrossValidationSampler, RegExMatchGrouper

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


def fold(
    fr: FileIO,
    doc_base_path: str,
    eval_base_path: str,
    k: int,
    seed: int,
    threads: int = 1,
    file_name_pattern: str = r"(.*)",
) -> str:
    """Split the data into k folds for cross-validation.

    Args:
        fr: A FileIO instance.
        doc_base_path: The base path to the data.
        eval_base_path: The base path to the evaluation data.
        k: The number of folds.
        seed: The random seed.
        threads: The number of threads to use.
        file_name_pattern: A regex pattern to parse case number from file name.

    Returns:
        Name of the eval
    """
    # Generate a unique (but interprettable) name for this run.
    eval_name = f"eval-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    eval_dir = fr.join(eval_base_path, eval_name)
    logger.info(f"Creating evaluation directory {eval_dir} ...")

    files_to_process = [d.name for d in list_docs(fr, doc_base_path, ocr=True)]

    logger.info(f"Found {len(files_to_process)} files in {doc_base_path}")
    kfold = KFoldCrossValidationSampler[str](k)
    case_name_grouper = RegExMatchGrouper(file_name_pattern)

    metadata = Metadata(
        eval_name=eval_name,
        base_path=doc_base_path,
        k=k,
        seed=seed,
        folds=[],
        timestamp=datetime.now().isoformat(),
        files=files_to_process,
    )

    for i, (train, test) in enumerate(
        kfold(files_to_process, seed=seed, grouper=case_name_grouper)
    ):
        logger.info(f"Setting up fold {i + 1} / {k} ...")
        # Save the training and testing sets in a new directory
        fold_dir = fr.join(eval_dir, f"fold-{i}")
        train_dir = fr.join(fold_dir, "train")
        test_dir = fr.join(fold_dir, "test")
        multi_copy_docs(fr, train, train_dir, threads=threads)
        multi_copy_docs(fr, test, test_dir, threads=threads)
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
