from functools import cached_property, partial
from typing import Literal

from jinja2 import Template

from ..common.context import Context
from ..common.file import MemoryFile
from ..common.text import RedactedText, escape_for_xml
from .base import BaseRenderConfig
from .rich_text import RichTextRenderer


class HtmlRenderConfig(BaseRenderConfig):
    """HTML Render config."""

    engine: Literal["render:html"]

    @cached_property
    def driver(self) -> "HTMLRenderer":
        return HTMLRenderer(self)


tpl = Template(
    """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{{ title }}</title>
</head>
<style type="text/css">
    body {
        font-family: sans-serif;
        font-size: 12pt;
        margin: 2rem 4rem;
    }

    a {
        color: #1E90FF;
        text-decoration: none;
    }

    .debug {
        color: #808080;
    }

    .Header {
        font-size: 16pt;
        font-weight: bold;
    }

    .Normal {
        font-size: 12pt;
        line-height: 1.5em;
    }

    .Disclaimer {
        font-size: 10pt;
        font-style: italic;
        color: dimgrey;
    }

    .Footer {
        font-size: 10pt;
    }

    .Redaction {
       font-family: monospace;
       color: tomato;
    }

    .RedactError {
        font-family: monospace;
        color: lightgrey;
    }
</style>
<body>
    <h1 class="Header">{{ title }}</h1>
    <div class="Normal">
        {{ narrative }}
    </div>
    <p class="Disclaimer">{{ disclaimer }}</p>
</body>
</html>
"""
)


def apply_css_style(text: str, style: str) -> str:
    """Apply a CSS style to a text.

    Args:
        redacted: The text to apply the style to.
        style: The CSS style to apply.

    Returns:
        The text with the style applied.
    """
    return f'<span class="{style}">{text}</span>'


def format_html_paragraph(text: str) -> str:
    """Format a paragraph of text for display as HTML.

    Args:
        text: The text to format.

    Returns:
        The formatted text.
    """
    return f"<p>{text}</p>"


class HTMLRenderer(RichTextRenderer):
    def __init__(self, config: HtmlRenderConfig) -> None:
        self.config = config

    def __call__(self, redaction: RedactedText, context: Context) -> MemoryFile:
        """Render a narrative to an HTML file.

        Args:
            redaction: The redaction to render

        Returns:
            The rendered narrative as an HTML file.
        """
        f = MemoryFile()
        f.write(
            tpl.render(
                title=self.TITLE,
                disclaimer=self.DISCLAIMER,
                narrative=redaction.format(
                    style=apply_css_style,
                    p=format_html_paragraph,
                    escape=partial(escape_for_xml, debug=context.debug),
                ),
            )
        )
        return f
