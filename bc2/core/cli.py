import json
import logging

import tomllib
import typer

from ..logo import bc2_logo
from .pipeline import Pipeline, PipelineConfig

logger = logging.getLogger(__name__)


cli = typer.Typer()


@cli.command()
def run(
    pipeline: str,
    params: str,
    validate: bool = False,
    debug: bool = False,
):
    """Run the pipeline."""
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

    print(bc2_logo)

    logger.debug("Running pipeline ...")

    cfg_obj = tomllib.loads(pipeline)
    config = PipelineConfig.model_validate(cfg_obj)

    runtime_cfg = json.loads(params)
    logger.debug("Pipeline configuration loaded.")
    if debug:
        runtime_cfg["debug"] = True

    pipe = Pipeline(config)
    if validate:
        # NOTE(jnu): the pipeline config will *always* be validated before running.
        # If the `validate` option is set on the CLI, we will *only* validated, and
        # not run the pipeline.
        pipe.validate(runtime_cfg)
        logger.info("Runtime configuration validated.")
        return

    pipe.run(runtime_cfg)

    logger.debug("Pipeline completed.")
