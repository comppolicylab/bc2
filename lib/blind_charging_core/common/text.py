from typing import Callable

from .infer import segment


class Text:
    """Wrapper for text content."""

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


Styler = Callable[[str, str], str]

Grafer = Callable[[str], str]

Escaper = Callable[[str], str]


class RedactedText:
    def __init__(self, redacted: str, original: str | None = None) -> None:
        self.redacted = redacted
        self.original = original

    def format(
        self,
        style: Styler,
        p: Grafer,
        escape: Escaper,
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
        if self.original:
            final = ""

            for seg in segment(self.original, self.redacted):
                original_txt = escape(seg.original.text)
                redacted_txt = escape(seg.redacted.text)
                if seg.is_edit:
                    type_ = "Redaction" if seg.is_valid else "RedactError"
                    final += style(redacted_txt, type_)
                else:
                    final += original_txt

        final = "".join(p(line) for line in final.splitlines())

        return final
