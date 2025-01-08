from abc import ABC, abstractmethod

from pydantic import BaseModel

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.text import RedactedText


class BaseRenderConfig(BaseModel):
    """Common settings for all renderers."""

    title: str = "Redacted Narrative for Race-Blind Charging"
    disclaimer: str = """\
The above passages were automatically extracted from referral documents and \
automatically redacted to hide race-related information. Occasionally, words \
or punctuation may be automatically added to fix typos. \
{REDACT_ERROR_APPEARANCE}\
Please report any issues at <a href="https://bit.ly/report-rbc-bug">https://bit.ly/report-rbc-bug</a>."""


class BaseRenderer(ABC):
    def __init__(self, config: BaseRenderConfig) -> None:
        self.config = config

    REDACT_ERROR_APPEARANCE = ""

    def disclaimer(self):
        return self.config.disclaimer.format(
            REDACT_ERROR_APPEARANCE=self.__class__.REDACT_ERROR_APPEARANCE
        )

    @abstractmethod
    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile: ...
