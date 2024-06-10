from typing import Callable, Sequence

from .infer import segment


class Text:
    """Wrapper for text content."""

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


Styler = Callable[[str, str], str]
"""A function that styles text based on its type."""

Grafer = Callable[[str], str]
"""A function that formats a paragraph."""

Escaper = Callable[[str], str]
"""A function that escapes text for display."""


def default_styler(text: str, type_: str) -> str:
    """Default styling function."""
    return text


def default_grafer(text: str) -> str:
    """Default paragraph formatting function."""
    return text + "\n\n"


def default_escaper(text: str) -> str:
    """Default escape function."""
    return text


class RedactedText:
    """Container for redacted text.

    When the original text is available, the redacted text can be formatted
    into a rich diff.
    """

    def __init__(self, redacted: str, original: str, delimiters: Sequence[str]) -> None:
        """Initialize a redacted text.

        Args:
            redacted: The redacted text.
            original: The original text.
            delimiters: The open and close delimiters to use for marking
            redactions within the text.
        """
        self.redacted = redacted
        self.original = original
        self.delimiters = delimiters

    def format(
        self,
        style: Styler = default_styler,
        p: Grafer = default_grafer,
        escape: Escaper = default_escaper,
    ) -> str:
        """Format a narrative for display as an HTML-style document.

        Args:
            style: The style function to use.
            p: The paragraph formatting function to use.
            escape: The escape function to use.

        Returns:
            The formatted narrative.
        """
        final = self.redacted

        # Compute diff between original and redacted narrative
        final = ""

        for seg in segment(self.original, self.redacted, delimiters=self.delimiters):
            original_txt = escape(seg.original.text)
            redacted_txt = escape(seg.redacted.text)
            if seg.is_edit:
                type_ = "Redaction" if seg.is_valid else "RedactError"
                final += style(redacted_txt, type_)
            else:
                final += original_txt

        final = "".join(p(line) for line in final.splitlines())

        return final


def escape_for_xml(text: str) -> str:
    """Escape text for HTML-style markup languages (HTML, platypus, etc).

    Args:
        text: The text to escape.

    Returns:
        The escaped text.
    """
    replacements = [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text
