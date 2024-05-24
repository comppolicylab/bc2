import logging
from inspect import signature
from typing import Any, Union

from pydantic import BaseModel

from .extract.azuredi import AzureDIExtractConfig
from .extract.openai import OpenAIExtractConfig
from .input.azureblob import AzureBlobInputConfig
from .input.file import FileInputConfig
from .input.stdin import StdinInputConfig
from .output.azureblob import AzureBlobOutputConfig
from .output.file import FileOutputConfig
from .output.stdout import StdoutOutputConfig
from .redact.openai import OpenAIRedactConfig
from .render.html import HtmlRenderConfig
from .render.pdf import PdfRenderConfig
from .render.text import TextRenderConfig

logger = logging.getLogger(__name__)

InputConfig = Union[AzureBlobInputConfig, FileInputConfig, StdinInputConfig]


ExtractConfig = Union[AzureDIExtractConfig, OpenAIExtractConfig]


RedactConfig = Union[OpenAIRedactConfig]


RenderConfig = Union[PdfRenderConfig, HtmlRenderConfig, TextRenderConfig]


OutputConfig = Union[AzureBlobOutputConfig, FileOutputConfig, StdoutOutputConfig]

AnyConfig = Union[InputConfig, ExtractConfig, RedactConfig, RenderConfig, OutputConfig]


class PipelineConfig(BaseModel):
    pipe: list[AnyConfig]


class Pipeline:
    """Blind charging pipeline."""

    def __init__(self, config: PipelineConfig):
        """Initialize the pipeline."""
        self.pipeline = config.pipe

    def validate(self, runtime_config: dict[str, Any]):
        """Validate the pipeline configuration."""
        last_output: type | None = None

        # Iteratively validate that the pipeline can be chained together
        for config in self.pipeline:
            sig = signature(config.driver)
            params = sig.parameters
            explicit_requires = set(getattr(config, "required", []))
            required_params = [
                p
                for p in params
                if p != "self"
                and (p in explicit_requires or params[p].default is params[p].empty)
            ]

            # Check the output of the previous step with the next function
            if last_output is not None:
                input_param = required_params.pop(0)
                # Compare that last_output matches expected input type
                if not issubclass(last_output, params[input_param].annotation):
                    raise ValueError(
                        f"Expected {last_output} "
                        f"but got {params[input_param].annotation}"
                    )

            # Now check if we have all other required params from the runtime input
            for param in required_params:
                if param not in runtime_config:
                    raise ValueError(f"Missing required parameter {param}")

            # Update the last_output
            last_output = sig.return_annotation

        # Validate that the last step returns None.
        if last_output is not None:
            raise ValueError(
                f"Expected last step to have no return value, but got {last_output}"
            )

    def run(self, runtime_config: dict[str, Any] | None = None) -> None:
        """Run the pipeline."""
        runtime_config = runtime_config or {}
        self.validate(runtime_config)

        pipe: Any = None
        for config in self.pipeline:
            logger.debug(f"Running {config.engine} ...")

            args = []
            kwargs = {}

            sig = signature(config.driver)
            params = list(sig.parameters)
            if params:
                if params[0] == "self":
                    params = params[1:]

                if pipe is not None:
                    args.append(pipe)
                    params = params[1:]

                # Try to fill in additional parameters from the runtime config
                for param in params:
                    if param in runtime_config:
                        kwargs[param] = runtime_config[param]

            pipe = config.driver(*args, **kwargs)
