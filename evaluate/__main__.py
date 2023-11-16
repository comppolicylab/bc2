import logging
import os

import click
from azure.ai.formrecognizer import DocumentModelAdministrationClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from .evaluate import evaluate
from .io import AzureFileIO
from .train import AzureModelTrainer

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


@click.command()
@click.option("--account", prompt="Account", help="Account to use")
@click.option("--container", prompt="Container", help="Container to use")
@click.option(
    "--formrecognizer", prompt="Form Recognizer", help="Form Recognizer endpoint"
)
@click.option(
    "--formrecognizer-key",
    default="",
    prompt="Form Recognizer key",
    help="Form Recognizer key",
)
@click.option("--docpath", prompt="Document path", help="Path to use")
@click.option(
    "--evalpath", prompt="Evaluation path", help="Path to store evaluation data"
)
@click.option("--k", default=5, help="Number of folds to use for cross validation")
@click.option("--seed", default=0, help="Random seed to use for cross validation")
@click.option("--threads", default=10, help="Number of threads to use for copying data")
def main(
    account,
    container,
    formrecognizer,
    formrecognizer_key,
    docpath,
    evalpath,
    k,
    seed,
    threads,
):
    fr = AzureFileIO(account, container)
    # Use default credential unless a specific API key was passed.
    cred = DefaultAzureCredential()
    if formrecognizer_key:
        cred = AzureKeyCredential(formrecognizer_key)
    dm = DocumentModelAdministrationClient(endpoint=formrecognizer, credential=cred)
    trainer = AzureModelTrainer(dm, fr)
    evaluate(fr, trainer, docpath, evalpath, k=k, seed=seed, threads=threads)


if __name__ == "__main__":
    main()
