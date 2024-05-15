import logging

from .common.config import PipelineConfig
from .common.pipeline import Pipeline

logger = logging.getLogger(__name__)


def run(config: PipelineConfig):
    """Run the pipeline."""
    logger.debug("Running pipeline ...")
    pipe = Pipeline(config)
    pipe.run()
    logger.debug("Pipeline completed.")
