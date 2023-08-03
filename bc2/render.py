from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.units import inch


def _escape_for_platypus(text: str) -> str:
    """Escape text for platypus.

    Args:
        text: The text to escape.

    Returns:
        The escaped text.
    """
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _format_for_platypus(text: str) -> str:
    """Format raw text using Platypus markup.

    Args:
        text: The text to format.

    Returns:
        The formatted text.
    """
    return '<font size=12>{}</font>'.format(text).replace('\n', '<br/><br/>')


def pdf(out: str, narrative: str) -> None:
    """Render a narrative to PDF.

    Args:
        out: The path to the output file.
        narrative: The narrative to render
    """
    doc = SimpleDocTemplate(out)

    story = [
            Spacer(1, 0.5*inch),
            Paragraph(_format_for_platypus(_escape_for_platypus(narrative))),
            ]
    doc.build(story)
