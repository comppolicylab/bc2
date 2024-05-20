import logging

from .common.config import PipelineConfig

logger = logging.getLogger(__name__)


class Pipeline:
    """Blind charging pipeline."""

    def __init__(self, config: PipelineConfig):
        """Initialize the pipeline."""
        self.configs = [
            config.input,
            config.extract,
            config.redact,
            config.render,
            config.output,
        ]

    def run(self):
        """Run the pipeline."""
        pipe = None
        for config in self.configs:
            logger.debug(f"Running {config.engine} ...")
            pipe = config.driver(pipe)
