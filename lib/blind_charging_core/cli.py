import logging
from pathlib import Path
from typing import Optional

import tomllib
import typer

from .pipeline import Pipeline, PipelineConfig

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


cli = typer.Typer()


@cli.command()
def run(
    config_path: str,
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    validate: bool = False,
):
    """Run the pipeline."""
    logger.debug("Running pipeline ...")

    raw_cfg = Path(config_path).read_text()
    cfg_obj = tomllib.loads(raw_cfg)
    config = PipelineConfig.model_validate(cfg_obj)

    ctx = {
        "input_path": input_path,
        "output_path": output_path,
    }

    pipe = Pipeline(config)
    if validate:
        # NOTE(jnu): the pipeline config will *always* be validated before running.
        # If the `validate` option is set on the CLI, we will *only* validated, and
        # not run the pipeline.
        pipe.validate(ctx)
        logger.info("Runtime configuration validated.")
        return

    pipe.run(ctx)

    logger.debug("Pipeline completed.")
