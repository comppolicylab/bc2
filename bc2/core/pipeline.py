import logging
from inspect import signature
from typing import Any, Union

from pydantic import BaseModel

from .common.context import Context
from .control import ControlConfig
from .extract import ExtractConfig
from .input import InputConfig
from .inspect import InspectConfig
from .output import OutputConfig
from .parse import ParseConfig
from .redact import RedactConfig
from .render import RenderConfig

logger = logging.getLogger(__name__)


AnyConfig = Union[
    InputConfig,
    ExtractConfig,
    RedactConfig,
    InspectConfig,
    ParseConfig,
    RenderConfig,
    OutputConfig,
    ControlConfig,
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
        ctx = Context()

        # Iteratively validate that the pipeline can be chained together
        for i, config in enumerate(self.pipeline):
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
            pipe_type = config.engine.split(":")[0]
            rt_param_set = {"context": ctx}
            rt_param_set.update(runtime_config.get(pipe_type, {}))
            for param in required_params:
                if rt_param_set.get(param, None) is None:
                    raise ValueError(
                        f"Step [{i}] `{config.engine}` is missing required "
                        f"runtime parameter `{param}`. "
                    )

            # Update the last_output
            last_output = sig.return_annotation

        # Validate that last step returns `None`
        if last_output is not None and last_output is not type(None):
            raise ValueError(
                f"Expected final step to return `None` but got {last_output}"
            )

    def run(self, runtime_config: dict[str, Any] | None = None) -> Context:
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

        # The final pipe value is validated as None via type-checking.
        # It's not an error if the final pipe is not None, but we should log it.
        # The value is not returned and cannot be used.
        if pipe is not None:
            logger.warning("Pipeline did not end with a `None` return value.")
        return ctx
