import functools
import logging
import os
from pprint import pprint
from typing import Callable

import click
from azure.ai.formrecognizer import (
    DocumentAnalysisClient,
    DocumentModelAdministrationClient,
)
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from .evaluate import DEFAULT_FILE_NAME_PATTERN, run_all, run_test
from .io import AzureFileIO
from .model import AzureModelRunner, AzureModelTrainer

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


@click.group()
@click.option("--account", prompt="Account", help="Account to use")
@click.option("--container", prompt="Container", help="Container to use")
@click.option(
    "--threads",
    default=10,
    help="Number of threads to use for running backend commands",
)
@click.option(
    "--evalpath", prompt="Evaluation path", help="Path to store evaluation data"
)
@click.pass_context
def cli(ctx: click.Context, account, container, threads, evalpath):
    ctx.ensure_object(dict)
    ctx.obj["file_io"] = AzureFileIO(account, container)
    ctx.obj["threads"] = threads
    ctx.obj["evalpath"] = evalpath


def form_recognizer(f: Callable) -> Callable:
    """Decorator for passing in Form Recognizer client based on CLI options."""

    @click.option(
        "--formrecognizer", prompt="Form Recognizer", help="Form Recognizer endpoint"
    )
    @click.option(
        "--formrecognizer-key",
        default="",
        prompt="Form Recognizer key",
        help="Form Recognizer key",
    )
    @functools.wraps(f)
    def inner(*args, **kwargs):
        """Take the formrecognizer args from CLI and instantiate client in context."""
        ctx = click.get_current_context()
        formrecognizer = kwargs.pop("formrecognizer")
        formrecognizer_key = kwargs.pop("formrecognizer_key")

        # Use default credential unless a specific API key was passed.
        cred = DefaultAzureCredential()
        if formrecognizer_key:
            cred = AzureKeyCredential(formrecognizer_key)
        dma_client = DocumentModelAdministrationClient(
            endpoint=formrecognizer, credential=cred
        )
        da_client = DocumentAnalysisClient(endpoint=formrecognizer, credential=cred)
        ctx.obj["dma_client"] = dma_client
        ctx.obj["da_client"] = da_client

        return f(*args, **kwargs)

    return inner


@cli.command()
@click.option("--eval-id", prompt="Evaluation ID", help="Evaluation ID to use")
@form_recognizer
@click.pass_context
def test(ctx: click.Context, eval_id):
    fr = ctx.obj["file_io"]
    evalpath = ctx.obj["evalpath"]
    threads = ctx.obj["threads"]
    runner = AzureModelRunner(ctx.obj["da_client"], fr)
    results = run_test(fr, runner, evalpath, eval_id, threads=threads)
    pprint(results)


@cli.command()
@click.option("--k", default=5, help="Number of folds to use for cross validation")
@click.option("--seed", default=0, help="Random seed to use for cross validation")
@click.option("--docpath", prompt="Document path", help="Path to use")
@click.option(
    "--file-name-pattern",
    default=DEFAULT_FILE_NAME_PATTERN,
    help="Regex pattern to use to extract case number",
)
@form_recognizer
@click.pass_context
def run(
    ctx: click.Context,
    k,
    seed,
    docpath,
    file_name_pattern,
):
    fr = ctx.obj["file_io"]
    dma_client = ctx.obj["dma_client"]
    evalpath = ctx.obj["evalpath"]
    threads = ctx.obj["threads"]
    trainer = AzureModelTrainer(dma_client, fr)
    runner = AzureModelRunner(ctx.obj["da_client"], fr)
    results = run_all(
        fr,
        trainer,
        runner,
        docpath,
        evalpath,
        k=k,
        seed=seed,
        threads=threads,
        file_name_pattern=file_name_pattern,
    )
    pprint(results)


if __name__ == "__main__":
    cli(obj={})
