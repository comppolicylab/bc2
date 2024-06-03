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

    DISCLAIMER = """
The following passages have been automatically extracted from referral \
documents. These passages have been automatically redacted to hide \
race-related information. Please report any issues to 
<a href="mailto:issues@blindcharging.org">\
        issues@blindcharging.org</a>.
"""

    @abstractmethod
    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile: ...
