import functools
import json
import logging
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from .example import ExampleDoc
from .io import FileIO
from .label import Labels

logger = logging.getLogger(__name__)


@dataclass
class Doc:
    name: str
    has_ocr: bool
    has_labels: bool


@functools.lru_cache(maxsize=None)
def get_fields(fr: FileIO, fields_json: str) -> list[str]:
    """Get the list of fields in the given path.

    Args:
        fr: A FileIO instance.
        fields_json: The name of the fields JSON file.

    Returns:
        The list of fields.
    """
    if not fr.exists(fields_json):
        raise ValueError(f"Fields data not found at {fields_json}")
    data = json.loads(fr.read(fields_json))
    return [d["fieldKey"] for d in data["fields"]]


def get_true_labels(
    fr: FileIO, docs: list[str], fields_json: str = "fields.json", threads: int = 4
) -> dict[str, Labels]:
    """Get the true labels for the given path.

    Args:
        fr: A FileIO instance.
        docs: The list of documents to fetch labels for.
        fields_json: The name of the fields JSON file.
        threads: The number of threads to use.

    Returns:
        The true labels for each document.
    """
    fields = get_fields(fr, fields_json)

    result: dict[str, Labels] = {}

    def _run(path: str) -> Labels:
        return ExampleDoc.load(fr, path, fields).labels

    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(_run, path): path for path in docs}
        for future in as_completed(futures):
            path = futures[future]
            try:
                result[path] = future.result()
            except Exception as e:
                logger.warning(f"Failed to load labels for {path}: {e}")

    return result


def list_docs(
    fr: FileIO, base_path: str, ocr: bool = False, labels: bool = False
) -> list[Doc]:
    """Get a list of files, optionally filtering by OCR and labels.

    Careful with setting the `labels` feature to True, as it will ignore
    files that positively have no labels.

    Args:
        fr: A FileIO instance.
        base_path: The base path to the data.
        ocr: Filter to files that have OCR.
        labels: Filter to files that have labels.

    Returns:
        A list of file names.
    """
    all_files = list(fr.list(base_path))

    # Process all the files in the directory
    # (TODO - rewrite to simplify)
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

    # Apply filters
    if ocr:
        pdfs = pdfs.intersection(has_ocr)

    if labels:
        pdfs = pdfs.intersection(has_labels)

    # Return documents
    return [Doc(name, name in has_ocr, name in has_labels) for name in pdfs]


def copy_doc(fr: FileIO, name: str, dest_dir: str):
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


def _multi_copy_worker(fr: FileIO, q: queue.Queue[str], dest_dir: str):
    """Copy documents from queue (in a separate thread)."""
    while True:
        try:
            name = q.get(timeout=1)
            if name is None:
                continue
            logger.debug(f"Copying {name} to {dest_dir} ...")
            try:
                copy_doc(fr, name, dest_dir)
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


def multi_copy_docs(fr: FileIO, files: list[str], dest_dir: str, threads: int = 1):
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

    logger.debug(f"Starting {threads} threads to copy data ...")
    tx = [
        threading.Thread(target=_multi_copy_worker, args=(fr, q, dest_dir))
        for _ in range(threads)
    ]
    for t in tx:
        t.start()
    q.join()
    for t in tx:
        t.join()
