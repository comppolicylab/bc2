import logging
import os

import click

from .evaluate import evaluate
from .io import AzureFileReader

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


@click.command()
@click.option("--account", prompt="Account", help="Account to use")
@click.option("--container", prompt="Container", help="Container to use")
@click.option("--path", prompt="Path", help="Path to use")
def main(account, container, path):
    fr = AzureFileReader(account, container)
    evaluate(fr, path)


if __name__ == "__main__":
    main()
