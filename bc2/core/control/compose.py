from typing import Any, Generic, Literal, TypeVar, cast

from pydantic import BaseModel

from ..common.context import Context

T = TypeVar("T")
U = TypeVar("U")


class ComposeConfig(BaseModel):
    control: Literal["control:compose"] = "control:compose"
    body: list[Any]

    # TODO - inspect types ... this is basically a sub-pipe

    @property
    def driver(self) -> "ComposeDriver":
        return ComposeDriver(self.body)


class ComposeDriver(Generic[T, U]):
    def __init__(self, body: list[Any]):
        self.body = body

    def __call__(self, input: T, context: Context) -> U:
        value: Any = input
        for config in self.body:
            value = config.driver(value, context)
            # TODO - call each function in the body
            print(input, context, config)

        return cast(U, value)
