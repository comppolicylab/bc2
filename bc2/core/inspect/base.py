from abc import ABC, abstractmethod

from ..common.context import Context
from ..common.name_map import IdToNameMap, NameToMaskMap
from ..common.text import RedactedText


class BaseInspectDriver(ABC):
    """An inspect driver takes in redacted text and outputs redacted text.

    Inspect can be used as a quality control mechanism to ensure that redaction
    has been applied correctly. It can also be used to extract information from
    redacted text, such as inferring the aliases used in redaction.

    Information extracted from the redacted text can be stored in the context
    object. The context can be referenced from other parts of the pipeline, and
    will be returned as part of the final output.
    """

    @abstractmethod
    def __call__(
        self,
        input: RedactedText,
        context: Context,
        subjects: IdToNameMap | None = None,
        placeholders: NameToMaskMap | None = None,
    ) -> RedactedText: ...
