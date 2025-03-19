import inspect
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, cast

from pydantic import BaseModel, Field

from ..common.context import Context

if TYPE_CHECKING:
    from ..pipeline import AnyConfig

T = TypeVar("T")
U = TypeVar("U")


class ComposeConfig(BaseModel):
    engine: Literal["$compose"] = "$compose"
    pipe: list[AnyConfig] = Field(..., min_length=1)

    # TODO - inspect types ... this is basically a sub-pipe

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

        # Set the input and output types for the driver based on the head and tail of the pipe.
        return ComposeDriver[head_arg, tail_return](self.pipe)  # type: ignore[valid-type]


class ComposeDriver(Generic[T, U]):
    def __init__(self, pipe: list[AnyConfig]):
        self.pipe = pipe

    def __call__(self, input: T, context: Context, **kwargs) -> U:
        value: Any = input
        for config in self.pipe:
            value = config.driver(value, context)
            # TODO - call each function in the body
            print(input, context, config)

        return cast(U, value)
