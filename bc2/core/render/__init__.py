from typing import Union

from .html import HtmlRenderConfig
from .json import JsonRenderConfig
from .pdf import PdfRenderConfig
from .text import TextRenderConfig

RenderConfig = Union[
    PdfRenderConfig, HtmlRenderConfig, TextRenderConfig, JsonRenderConfig
]
