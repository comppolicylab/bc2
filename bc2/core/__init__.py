import typing

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

AnyConfig = typing._eval_type(  # type: ignore[attr-defined]
    _AnyConfig,
    globals(),
    locals(),
)

AnyProcessingConfig = typing._eval_type(  # type: ignore[attr-defined]
    _AnyProcessingConfig,
    globals(),
    locals(),
)

AnyIOConfig = typing._eval_type(  # type: ignore[attr-defined]
    _AnyIOConfig,
    globals(),
    locals(),
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
