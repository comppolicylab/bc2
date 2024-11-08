from abc import ABC, abstractmethod

from pydantic import BaseModel

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.text import RedactedText


class BaseRenderConfig(BaseModel):
    """Common settings for all renderers."""

    ...


class BaseRenderer(ABC):
    TITLE = "Redacted Narrative for Race-Blind Charging"

    REDACT_ERROR_APPEARANCE = ""

    DISCLAIMER = f"""
-------------------------------------------------------------------------------\
-------------------------------------------------------------------------------\
The above passages have been automatically extracted from referral \
documents and automatically redacted to hide race-related information. \
In rare circumstances, words or punctuation may be automatically added to fix \
typos. {REDACT_ERROR_APPEARANCE}\
Please report any issues to <a href="mailto:blind_charging@hks.harvard.edu">\
blind_charging@hks.harvard.edu</a>.
"""

    @abstractmethod
    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile: ...
