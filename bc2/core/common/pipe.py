import logging
from typing import TYPE_CHECKING, Any, Tuple, Type

from .context import Context
from .type_util import inspect_all_params, inspect_required_params, inspect_return_type

if TYPE_CHECKING:
    from .all import AnyConfig


logger = logging.getLogger(__name__)


def validate_pipe(
    pipe: list[AnyConfig], runtime_config: dict[str, Any]
) -> Tuple[Type, Type]:
    """Validate the pipeline configuration.

    Args:
        pipe (list[AnyConfig]): The pipeline configuration.
        runtime_config (dict[str, Any]): The runtime configuration.

    Returns:
        Tuple[Type, Type]: The input and output types of the pipeline.
    """
    first_input_t: Type = type(None)
    last_output_t: Type = type(None)
    ctx = Context()

    # Iteratively validate that the pipeline can be chained together
    for i, config in enumerate(pipe):
        explicit_requires = getattr(config.driver, "required", [])
        required_params = inspect_required_params(
            config.driver, explicit=explicit_requires
        )

        # Check the output of the previous step with the next function
        if i > 0:
            input_t = list(required_params.values())[0]
            # Compare that last_output matches expected input type

        # Now check if we have all other required params from the runtime input
        pipe_type = config.engine.split(":")[0]
        rt_param_set = {"context": ctx, "runtime_config": runtime_config}
        rt_param_set.update(runtime_config.get(pipe_type, {}))

        for j, param in enumerate(required_params):
            input_t = required_params[param]

            if j == 0:
                # If this is the first argument of the first input
                # AND the parameter is not filled by the runtime config,
                # then record this as the pipe's input type.
                # When the first param is covered by the runtime config,
                # we will return that `input_t` is type(None).
                if i == 0:
                    if param not in rt_param_set:
                        first_input_t = input_t
                else:
                    # For the first argument of sub-commands, check that the output
                    # of the previous command matches the input of the next command.
                    if not issubclass(last_output_t, input_t):
                        raise ValueError(
                            f"Expected {input_t}" f"but got {last_output_t}"
                        )
                # Skip additional validation for the first param.
                continue

            if rt_param_set.get(param, None) is None:
                raise ValueError(
                    f"Step [{i}] `{config.engine}` is missing required "
                    f"runtime parameter `{param}`. "
                )

        # If the driver implements the `validate` protocol, call it.
        # This handles nested pipes, such as with the `Compose` module.
        if hasattr(config.driver, "validate"):
            config.driver.validate(runtime_config)

        # Update the pointer in the pipe to this function's return type.
        last_output_t = inspect_return_type(config.driver)

    return first_input_t, last_output_t


def run_pipe(pipe: list[AnyConfig], input: Any, runtime_config: dict[str, Any]) -> Any:
    # The calling function can optionally pass in their own Context, which is
    # useful if some values need to be primed before running the pipeline.
    # If the context exists already, use it. Otherwise create a new one.
    if "context" not in runtime_config:
        runtime_config["context"] = Context()

    ctx = runtime_config["context"]

    # Set the initial pipe value to the input
    output: Any = input

    for i, config in enumerate(pipe):
        logger.debug(f"Running {config.engine} ...")

        args = []
        kwargs = {}

        params = inspect_all_params(config.driver)

        # For everything but the first pipe value, pass the output
        # of the previous operation as the first argument.
        if i > 0:
            args.append(output)
            params.popitem(last=False)

        # Try to fill in additional parameters from the runtime config
        pipe_type = config.engine.split(":")[0]
        rt_param_set = runtime_config.get(pipe_type, {})
        for param in params:
            if param == "context":
                kwargs[param] = ctx
            elif param == "runtime_config":
                kwargs[param] = runtime_config
            elif param in rt_param_set:
                kwargs[param] = rt_param_set[param]

        # NOTE(jnu): mypy can't validate the kwarg types, but we've effectively
        # done this at runtime anyway so just hush the error.
        output = config.driver(*args, **kwargs)  # type: ignore[arg-type]

    return output
