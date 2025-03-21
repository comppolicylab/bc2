import inspect
import logging
from collections import OrderedDict
from typing import Any, Callable, ParamSpec, Type, TypeVar, cast, get_args

logger = logging.getLogger(__name__)


T = TypeVar("T")
U = TypeVar("U")
P = ParamSpec("P")


def inspect_required_params(
    f: Callable[P, T],
    explicit: list[str] | None = None,
) -> OrderedDict[str, Type]:
    """Get the input type of a function.

    This will return the type of the first argument of the function.

    Args:
        f (Callable[P, T]): The function to inspect.
        explicit (list[str] | None): A list of known required arguments.

    Returns:
        OrderedDict[str, Type]: The input types of the function
    """
    explicit_set = set(explicit or [])
    sig = inspect.signature(f)
    params = sig.parameters

    rp = OrderedDict[str, Type]()
    for p in params:
        if p == "self":
            continue

        if p in explicit_set or params[p].default is params[p].empty:
            rp[p] = params[p].annotation

    return rp


def inspect_all_params(f: Callable[P, T]) -> OrderedDict[str, Type]:
    """Get the input type of a function.

    This will return the type of all arguments of the function.

    Args:
        f (Callable[P, T]): The function to inspect.

    Returns:
        OrderedDict[str, Type]: The input types of the function
    """
    sig = inspect.signature(f)
    params = sig.parameters

    rp = OrderedDict[str, Type]()
    for p in params:
        if p == "self":
            continue

        rp[p] = params[p].annotation

    return rp


def _resolve_generic_types(f: Any) -> tuple[Type]:
    """Try to resolve the types of a concrete instance of a generic class.

    Args:
        f (Any): The instance to inspect.

    Returns:
        tuple[Type]: The types of the instance.

    Raises:
        TypeError: If we are unable to resolve the types.
    """
    try:
        orig_cls = f.__orig_class__
        return cast(tuple[Type], get_args(orig_cls))
    except AttributeError as e:
        raise TypeError(f"Unable to find concrete type of {f}") from e


def inspect_return_type(f: Callable[..., T]) -> Type[T]:
    """Get the return type of a function.

    This will return either the return type or, in the case of a generic
    return type, the last generic argument that instantiates the callable.

    (NOTE that the assumption about the type arg is a convention used narrowly
    within this application, and is not explicitly enforced!)

    Args:
        f (Callable[..., T]): The function to inspect.

    Returns:
        Type[T]: The return type of the function.

    Raises:
        TypeError: If we are unable to inspect the return type
    """
    sig = inspect.signature(f)
    return_type = sig.return_annotation

    if return_type is sig.empty:
        logger.warning(
            "No return type annotation found, assuming None -- "
            f"you should use an explicit annotation for {f}!"
        )
        return cast(Type[T], type(None))

    if return_type is None or return_type is type(None):
        return cast(Type[T], type(None))

    # If the return type is itself a TypeVar, we'll have to inspect it further.
    # Assume that the last generic argument is the return type.
    # TODO(jnu): this is a bit of a hack, but it works for now.
    # TODO(jnu): we could also look at the constraints/bounds of T.
    if isinstance(return_type, TypeVar):
        return_type = _resolve_generic_types(f)[-1]

    return cast(Type[T], return_type)


def get_bindable_parameters(
    f: Callable[P, T], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Get a subset of parameters needed for binding to a function.

    This will exclude the first parameter and the Context parameter.

    Args:
        f (Callable[P, T]): The function to inspect.
        kwargs (dict[str, Any]): The keyword arguments to filter.

    Returns:
        dict[str, Any]: The filtered keyword arguments.
    """
    params = inspect_all_params(f)
    params.popitem(last=False)
    params.pop("context", None)
    kwargs["runtime_config"] = kwargs
    return {k: v for k, v in kwargs.items() if k in params}
