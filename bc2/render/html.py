from jinja2 import Template

from .common import Renderer, format_narrative, TITLE, DISCLAIMER, escape_for_xml


tpl = Template("""
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

    .Header {
        font-size: 16pt;
        font-weight: bold;
    }

    .Normal {
        font-size: 12pt;
        line-height: 1.5em;
    }

    .Italic {
        font-style: italic;
    }

    .Footer {
        font-size: 10pt;
    }

    .Redaction {
       font-family: monospace;
       color: #FFA500;
    }

    .RedactError {
        font-family: monospace;
        color: #FF0000;
    }
</style>
<body>
    <h1 class="Header">{{ title }}</h1>
    <p class="Italic">{{ disclaimer }}</p>
    <div class="Normal">
        {{ narrative }}
    </div>
</body>
</html>
""")


def apply_css_style(text: str, style: str) -> str:
    """Apply a CSS style to a text.

    Args:
        text: The text to apply the style to.
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
    return f'<p>{text}</p>'


def render_html(out: str, narrative: str, original: str | None = None) -> None:
    """Render a narrative to an HTML file.

    Args:
        out: The path to the output file.
        narrative: The narrative to render
        original: The original narrative, if available.
    """
    with open(out, "w") as f:
        f.write(tpl.render(
            title=TITLE,
            disclaimer=DISCLAIMER,
            narrative=format_narrative(apply_css_style,
                                       format_html_paragraph,
                                       escape_for_xml,
                                       narrative,
                                       original)
        ))


html = Renderer("html", "html", render_html)
