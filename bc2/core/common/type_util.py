import inspect
import logging
from typing import Callable, Type, TypeVar, cast, get_args

logger = logging.getLogger(__name__)


T = TypeVar("T")


def inspect_return_type(f: Callable[..., T]) -> Type[T] | None:
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
            f"No return type annotation found, assuming None -- you should use an explicit annotation for {f}!"
        )
        return None

    if return_type is None:
        return None

    # If the return type is itself a TypeVar, we'll have to inspect it further.
    # Assume that the last generic argument is the return type.
    # TODO(jnu): this is a bit of a hack, but it works for now.
    # TODO(jnu): we could also look at the constraints/bounds of T.
    if isinstance(return_type, TypeVar):
        try:
            orig_cls = f.__orig_class__
            return_type = get_args(orig_cls)[-1]
        except AttributeError:
            raise TypeError(f"Unable to inspect return type of {f}")

    return cast(Type[T], return_type)
