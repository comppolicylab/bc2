import logging
import queue
import threading
from dataclasses import dataclass

from .io import FileIO

logger = logging.getLogger(__name__)


@dataclass
class Doc:
    name: str
    has_ocr: bool
    has_labels: bool


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

    def worker():
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

    logger.debug(f"Starting {threads} threads to copy data ...")
    tx = [threading.Thread(target=worker) for _ in range(threads)]
    for t in tx:
        t.start()
    q.join()
    for t in tx:
        t.join()
