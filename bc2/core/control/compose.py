import inspect
from typing import Generic, Literal, Type, TypeVar, cast

from pydantic import BaseModel, Field

from ..common.all import AnyConfig
from ..common.context import Context
from ..common.pipe import run_pipe, validate_pipe
from ..common.runtime import RuntimeConfig

T = TypeVar("T")
U = TypeVar("U")


class ComposeConfig(BaseModel):
    engine: Literal["$compose"] = "$compose"
    pipe: list[AnyConfig] = Field(..., min_length=1)

    @property
    def driver(self) -> "ComposeDriver":
        head_f = self.pipe[0]
        tail_f = self.pipe[-1]

        head_sig = inspect.signature(head_f.driver)
        tail_sig = inspect.signature(tail_f.driver)

        # Get the type of the first argument of the head function
        first_head_arg = list(head_sig.parameters)[0]
        head_arg = cast(type, head_sig.parameters[first_head_arg].annotation)
        # Get the type of the return value of the tail function
        tail_return = cast(type, tail_sig.return_annotation)

        # Set the input and output types based on the head and tail of the pipe.
        return ComposeDriver[head_arg, tail_return](self.pipe, head_arg, tail_return)  # type: ignore[valid-type]


class ComposeDriver(Generic[T, U]):
    """Compose a sequence of modules into a single module."""

    def __init__(self, pipe: list[AnyConfig], input_t: Type[T], return_t: Type[U]):
        self.pipe = pipe
        self.input_t = input_t
        self.return_t = return_t

    def validate(self, runtime_config: RuntimeConfig):
        """Validate the composition configuration."""
        input_t, output_t = validate_pipe(self.pipe, runtime_config)

        if input_t is not self.input_t:
            raise ValueError(
                f"Expected first step to have `{self.input_t}` input type "
                f"but got {input_t}"
            )

        if output_t is not self.return_t:
            raise ValueError(
                f"Expected final step to return `{self.return_t}` but got {output_t}"
            )

    def __call__(
        self, input: T, context: Context, runtime_config: RuntimeConfig | None = None
    ) -> U:
        """Run the composition."""
        rt = runtime_config or {}
        rt["context"] = context

        output = run_pipe(self.pipe, input, rt, debug=context.debug)

        return cast(U, output)
