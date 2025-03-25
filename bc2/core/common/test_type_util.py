from collections import OrderedDict
from typing import Generic, TypeVar

from .type_util import (
    get_bindable_parameters,
    inspect_all_params,
    inspect_required_params,
    inspect_return_type,
)

T = TypeVar("T")


# Dummy functions for testing
def func_with_defaults(a: int, b: str = "default", c: float = 1.0) -> bool:
    return True


def func_no_annotation(a, b):
    return None


class GenericClass(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value

    def __call__(self) -> T:
        return self.value


def test_inspect_required_params_without_explicit():
    params = inspect_required_params(func_with_defaults)
    expected = OrderedDict([("a", int)])
    assert params == expected


def test_inspect_required_params_with_explicit():
    params = inspect_required_params(func_with_defaults, explicit=["b"])
    expected = OrderedDict([("a", int), ("b", str)])
    assert params == expected


def test_inspect_all_params():
    params = inspect_all_params(func_with_defaults)
    expected = OrderedDict([("a", int), ("b", str), ("c", float)])
    assert params == expected


def test_inspect_return_type_with_annotation(caplog):
    ret_type = inspect_return_type(func_with_defaults)
    assert ret_type is bool


def test_inspect_return_type_without_annotation(caplog):
    ret_type = inspect_return_type(func_no_annotation)
    # Since no return annotation was provided, it should warn and default to type(None)
    assert ret_type is type(None)
    # Verify that a warning was emitted
    assert "No return type annotation found" in caplog.text


def test_inspect_return_type_with_generic():
    ret_type = inspect_return_type(GenericClass[int](42))
    assert ret_type is int


def test_get_bindable_parameters():
    # Function with several parameters, including a 'context' parameter.
    def func_bind(a: int, b: str, context: dict, d: float = 0.0) -> None:
        pass

    kwargs = {
        "a": 10,
        "b": "test",
        "context": {"key": "value"},
        "d": 3.14,
        "extra": "should be removed",
    }
    result = get_bindable_parameters(func_bind, kwargs.copy())
    # First parameter ('a') and 'context' should be removed.
    # Only keys matching remaining parameters ('b' and 'd') are retained.
    expected = {"b": "test", "d": 3.14}
    assert result == expected
