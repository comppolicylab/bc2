import typing

from . import common as _common
from .common.all import AnyConfig as _AnyConfig
from .common.all import AnyIOConfig as _AnyIOConfig
from .common.all import AnyProcessingConfig as _AnyProcessingConfig
from .common.name_map import IdToMaskMap, IdToNameMap, NameToMaskMap
from .pipeline import Pipeline, PipelineConfig

# MyPy doesn't like using `typing._eval_type` to evaluate the forward references.
# We silence the error here.
#
# The reason we do this is to allow library users to import these types for use as
# Pydantic models. Since our types are recursive and use forward references, we need
# to resolve them before Pydantic can use them.
#
# We further define these with `typing.TypeAlias` to silence warnings about using
# a variable as a type.
#
# The forward references (e.g. "ChunkConfig", "ComposeConfig") are declared inside
# `bc2.core.common.all` and only become resolvable after that module's bottom-of-file
# circular-import imports complete. We therefore evaluate them against that module's
# globals rather than the globals of this module. Prior to Python 3.14 the standard
# library was more lenient about looking up forward refs (in particular it consulted
# `ForwardRef.__forward_module__` more aggressively), which is why passing this
# module's `globals()` happened to work on 3.12 but raises `NameError` on 3.14+.
_fwd_globals = vars(_common.all)

AnyConfig: typing.TypeAlias = typing.cast(
    typing.Type[_AnyConfig],
    typing._eval_type(  # type: ignore[attr-defined]
        _AnyConfig,
        _fwd_globals,
        None,
    ),
)

AnyProcessingConfig: typing.TypeAlias = typing.cast(
    typing.Type[_AnyProcessingConfig],
    typing._eval_type(  # type: ignore[attr-defined]
        _AnyProcessingConfig,
        _fwd_globals,
        None,
    ),
)

AnyIOConfig: typing.TypeAlias = typing.cast(
    typing.Type[_AnyIOConfig],
    typing._eval_type(  # type: ignore[attr-defined]
        _AnyIOConfig,
        _fwd_globals,
        None,
    ),
)

__all__ = [
    "Pipeline",
    "PipelineConfig",
    "NameToMaskMap",
    "IdToNameMap",
    "IdToMaskMap",
    "AnyConfig",
    "AnyProcessingConfig",
    "AnyIOConfig",
]
