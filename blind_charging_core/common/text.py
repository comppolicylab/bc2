from typing import Callable, Literal, Sequence, Tuple

from .infer import TextSegment, segment


class Text:
    """Wrapper for text content."""

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


Styler = Callable[[str, str], str]
"""A function that styles text based on its type.

Args:
    redacted_text: The replacement text for the segment.
    type_: The type of the text.
"""

Grafer = Callable[[str], str]
"""A function that formats a paragraph."""

EscapeType = Literal["original"] | Literal["redacted"]
Escaper = Callable[[TextSegment, EscapeType], str]
"""A function that escapes text for display.

Args:
    text: The text segment to escape.
    type_: The type of text to escape (original or redacted).
"""


def default_styler(text: str, type_: str) -> str:
    """Default styling function."""
    return text


def default_grafer(text: str) -> str:
    """Default paragraph formatting function."""
    return text + "\n\n"


def default_escaper(text: TextSegment, type_: EscapeType) -> str:
    """Default escape function."""
    if type_ == "redacted":
        return text.redacted.text
    elif type_ == "original":
        return text.original.text
    else:
        raise ValueError(f"Invalid escape type: {type_}")


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

    @property
    def annotations(self) -> list[TextSegment]:
        """Return the annotations for the redacted text."""
        return [
            s
            for s in segment(self.original, self.redacted, delimiters=self.delimiters)
            if s.is_edit
        ]

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
            original_txt = escape(seg, "original")
            redacted_txt = escape(seg, "redacted")
            if seg.is_edit:
                type_ = "Redaction" if seg.is_valid else "RedactError"
                final += style(redacted_txt, type_)
            else:
                final += original_txt

        final = "".join(p(line) for line in final.splitlines())

        return final

    def __repr__(self) -> str:
        return (
            f"RedactedText({self.redacted!r}, {self.original!r}, {self.delimiters!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RedactedText):
            return NotImplemented
        return (
            self.redacted == other.redacted
            and self.original == other.original
            and self.delimiters == other.delimiters
        )


def escape_for_xml(ts: TextSegment, type_: EscapeType, debug: bool = False) -> str:
    """Escape text for HTML-style markup languages (HTML, platypus, etc).

    Args:
        text: The text segment to escape.
        type_: The type of text to escape.
        debug (optional): Whether to include debug information.

    Returns:
        The escaped text.
    """
    replacements = [
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
    ]
    return escape_with_replacement(ts, type_, replacements, debug=debug)


def escape_for_txt(ts: TextSegment, type_: EscapeType, debug: bool = False) -> str:
    """Escape text for plain text.

    Args:
        text: The text segment to escape.
        type_: The type of text to escape
        debug (optional): Whether to include debug information.

    Returns:
        The escaped text.
    """
    return escape_with_replacement(ts, type_, [], debug=debug)


def escape_with_replacement(
    ts: TextSegment,
    type_: EscapeType,
    replacements: list[Tuple[str, str]],
    debug: bool = False,
) -> str:
    """Escape text with by replacing known characters with others.

    Args:
        ts: The text segment to escape.
        type_: The type of text to escape
        replacements: The replacements to make as (old, new) pairs.
        debug (optional): Whether to include debug information.
    """
    if type_ == "redacted":
        # Inject the original text into the redacted text for debugging.
        # We want to place it _inside_ the delimiter.
        if debug and ts.open_delim:
            open_delim_len = len(ts.open_delim)
            text = (
                ts.redacted.text[:open_delim_len]
                + ts.original.text
                + " -> "
                + ts.redacted.text[open_delim_len:]
            )
        else:
            text = ts.redacted.text
    elif type_ == "original":
        text = ts.original.text
    else:
        raise ValueError(f"Invalid escape type: {type_}")

    for old, new in replacements:
        text = text.replace(old, new)

    return text
