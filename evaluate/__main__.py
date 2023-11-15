import logging
import os

import click
from azure.ai.formrecognizer import DocumentModelAdministrationClient
from azure.identity import DefaultAzureCredential

from .evaluate import evaluate
from .io import AzureFileIO

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


@click.command()
@click.option("--account", prompt="Account", help="Account to use")
@click.option("--container", prompt="Container", help="Container to use")
@click.option(
    "--formrecognizer", prompt="Form Recognizer", help="Form Recognizer endpoint"
)
@click.option("--docpath", prompt="Document path", help="Path to use")
@click.option(
    "--evalpath", prompt="Evaluation path", help="Path to store evaluation data"
)
@click.option("--k", default=5, help="Number of folds to use for cross validation")
@click.option("--seed", default=0, help="Random seed to use for cross validation")
@click.option("--threads", default=10, help="Number of threads to use for copying data")
def main(account, container, formrecognizer, docpath, evalpath, k, seed, threads):
    fr = AzureFileIO(account, container)
    dm = DocumentModelAdministrationClient(
        endpoint=formrecognizer, credential=DefaultAzureCredential()
    )
    evaluate(fr, dm, docpath, evalpath, k=k, seed=seed, threads=threads)


if __name__ == "__main__":
    main()
