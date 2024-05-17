import logging

from .common.config import PipelineConfig
from .pipeline import Pipeline

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


def run(config: PipelineConfig):
    """Run the pipeline."""
    logger.debug("Running pipeline ...")

    pipe = Pipeline(config)
    pipe.run()
    logger.debug("Pipeline completed.")


# TODO: Add a command line interface to run the pipeline
#  - Refactor configs to assemble the pipeline
#  - Accept the file path (anything else? potential overrides?) from the command line
#  - Run the pipeline
