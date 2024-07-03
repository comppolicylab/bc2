import logging
from inspect import signature
from typing import Any, Tuple, Union

from pydantic import BaseModel

from .common.context import Context
from .extract.azuredi import AzureDIExtractConfig
from .extract.openai import OpenAIExtractConfig
from .extract.tesseract import TesseractExtractConfig
from .input.azureblob import AzureBlobInputConfig
from .input.file import FileInputConfig
from .input.memory import MemoryInputConfig
from .input.stdin import StdinInputConfig
from .output.azureblob import AzureBlobOutputConfig
from .output.file import FileOutputConfig
from .output.memory import MemoryOutputConfig
from .output.stdout import StdoutOutputConfig
from .parse.openai import OpenAIParseConfig
from .redact.noop import NoOpRedactConfig
from .redact.openai import OpenAIRedactConfig
from .render.html import HtmlRenderConfig
from .render.pdf import PdfRenderConfig
from .render.text import TextRenderConfig

logger = logging.getLogger(__name__)


InputConfig = Union[
    AzureBlobInputConfig, FileInputConfig, StdinInputConfig, MemoryInputConfig
]


ExtractConfig = Union[AzureDIExtractConfig, OpenAIExtractConfig, TesseractExtractConfig]


ParseConfig = Union[OpenAIParseConfig]


RedactConfig = Union[OpenAIRedactConfig, NoOpRedactConfig]


RenderConfig = Union[PdfRenderConfig, HtmlRenderConfig, TextRenderConfig]


OutputConfig = Union[
    AzureBlobOutputConfig, FileOutputConfig, StdoutOutputConfig, MemoryOutputConfig
]


AnyConfig = Union[
    InputConfig, ExtractConfig, RedactConfig, ParseConfig, RenderConfig, OutputConfig
]


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
            explicit_requires = set(getattr(config.driver, "required", []))
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
                        f"Expected {params[input_param].annotation}"
                        f"but got {last_output}"
                    )

            # Now check if we have all other required params from the runtime input
            for param in required_params:
                if runtime_config.get(param, None) is None:
                    raise ValueError(f"Missing required parameter {param}")

            # Update the last_output
            last_output = sig.return_annotation

        # TODO(jnu): Validate that last step returns the type `io.BytesIO | None`

    def run(self, runtime_config: dict[str, Any] | None = None) -> Tuple[Any, Context]:
        """Run the pipeline."""
        runtime_config = runtime_config or {}
        ctx = Context()
        runtime_config["context"] = ctx
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
                pipe_type = config.engine.split(":")[0]
                rt_param_set = runtime_config.get(pipe_type, {})
                for param in params:
                    if param == "context":
                        kwargs[param] = ctx
                    elif param in rt_param_set:
                        kwargs[param] = rt_param_set[param]

            # NOTE(jnu): mypy can't validate the kwarg types, but we've effectively
            # done this at runtime anyway so just hush the error.
            pipe = config.driver(*args, **kwargs)  # type: ignore[arg-type]

        return pipe, ctx
