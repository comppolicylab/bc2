import logging

from pydantic import BaseModel

from .common.all import AnyConfig
from .common.context import Context
from .common.runtime import RuntimeConfig
from .control.compose import ComposeDriver

logger = logging.getLogger(__name__)


class PipelineConfig(BaseModel):
    pipe: list[AnyConfig]


class Pipeline:
    """Compose a sequence of processing operations into a single pipeline.

    The pipeline is a special case of the `Compose` control module with
    null input and output types. See `control/compose.py` for more details.
    """

    def __init__(self, config: PipelineConfig):
        """Initialize the pipeline."""
        none_t = type(None)
        self.pipeline = ComposeDriver[none_t, none_t](config.pipe, none_t, none_t)

    def validate(self, runtime_config: RuntimeConfig):
        """Validate the pipeline configuration."""
        self.pipeline.validate(runtime_config)

    def run(self, runtime_config: RuntimeConfig | None = None) -> Context:
        """Run the pipeline.

        Args:
            runtime_config: The runtime configuration.
            Most values in the runtime config are dependent on the pipeline.
            The `debug` flag is interpretted globally.

        Returns:
            The context object created during the pipeline run.
        """
        runtime_config = runtime_config or {}
        ctx = Context()
        ctx.debug = runtime_config.get("debug", False)
        runtime_config["context"] = ctx

        output = self.pipeline(None, ctx, runtime_config)

        # The final pipe value is validated as None via type-checking.
        # It's not an error if the final pipe is not None, but we should log it.
        # The value is not returned and cannot be used.
        if output is not None:
            logger.warning("Pipeline did not end with a `None` return value.")

        return ctx
