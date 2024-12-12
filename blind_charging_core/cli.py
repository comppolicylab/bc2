import json
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
    aliases: Optional[str] = None,
    debug: bool = False,
):
    """Run the pipeline."""
    logger.debug("Running pipeline ...")

    raw_cfg = Path(config_path).read_text()
    cfg_obj = tomllib.loads(raw_cfg)
    config = PipelineConfig.model_validate(cfg_obj)

    # Map of arguments passed at runtime to the pipeline.
    runtime_cfg = {
        "debug": debug,
        "in": {
            "path": input_path,
        },
        "out": {
            "path": output_path,
        },
        "redact": {
            "preset_aliases": json.loads(aliases) if aliases else None,
        },
        "inspect": {
            "preset_aliases": json.loads(aliases) if aliases else None,
        },    }

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
