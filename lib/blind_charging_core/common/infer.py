import difflib
import re
from dataclasses import dataclass
from typing import Generator, Literal, NamedTuple, Sequence, Tuple

TextSpan = NamedTuple(
    "TextSpan",
    [
        ("start", int),
        ("end", int),
        ("text", str),
    ],
)


TextSegment = NamedTuple(
    "TextSegment",
    [
        ("original", TextSpan),
        ("redacted", TextSpan),
        ("is_edit", bool),
        ("is_valid", bool),
    ],
)


@dataclass
class Delimiter:
    pattern: re.Pattern[str]
    length: int

    @classmethod
    def parse(cls, delimiters: Sequence[str]) -> Tuple["Delimiter", "Delimiter"]:
        """Build regexes to match the delimiters.

        By default we use < and >, so the regex for the opener is `^(\\s*<)`
        and for the closer is `(>\\s*)$`.

        Args:
            delimiters: The delimiters to use (must be length of 2)

        Returns:
            A tuple of Delimiter instances.

        Raises:
            ValueError: If the delimiters are not of length 2.
        """
        if len(delimiters) != 2:
            raise ValueError(
                "Delimiters must be a sequence of two strings, such as ('<', '>')."
            )
        opener_re = re.compile(f"({re.escape(delimiters[0])})")
        opener_len = len(delimiters[0])
        closer_re = re.compile(f"({re.escape(delimiters[1])})")
        closer_len = len(delimiters[1])
        return cls(opener_re, opener_len), cls(closer_re, closer_len)


Op = Literal["replace", "insert", "delete", "equal"]
"""Diff segment operation type."""

Opcode = Tuple[Op, int, int, int, int]
"""Segment of a diff operation."""

_INSERT: Literal["insert"] = "insert"


def _split_opcode(
    mask: str,
    opcode: Op,
    i1: int,
    i2: int,
    j1: int,
    j2: int,
    opener: re.Match[str] | None,
    closer: re.Match[str] | None,
) -> list[Opcode]:
    """Split an opcode into multiple opcodes if needed.

    This is needed when the start/end tokens are not placed at
    the start / end of the mask.

    Returns:
        A list of opcodes.
    """
    if opener and opener.start() > 0:
        opening_op = (
            _INSERT,
            i1,
            i1,
            j1,
            j1 + opener.start(),
        )
        main_op = (
            opcode,
            i1,
            i2,
            j1 + opener.start(),
            j2,
        )
        return [opening_op, main_op]

    # If the closer is not at the end of the mask,
    # split the opcode into a new "insertion" and process
    # that after we process the current op.
    if closer and closer.end() < len(mask):
        main_op = (
            opcode,
            i1,
            i2,
            j1,
            j2 - (len(mask) - closer.end()),
        )
        closing_op = (
            _INSERT,
            i2,
            i2,
            j2 - (len(mask) - closer.end()),
            j2,
        )
        return [main_op, closing_op]

    return []


def segment(  # noqa: C901
    original: str,
    redacted: str,
    delimiters: Sequence[str] = ("<", ">"),
) -> Generator[TextSegment, None, None]:
    """Visit text segments in the redacted narrative.

    This function computes the delta between the original narrative text and
    the redacted narrative texts. It inspects the delta to generate a sequence
    of text segments. Some of these segments are masked annotations, some are
    spurious edits (e.g., noise from the LLM), and some are segments that are
    unmasked text shared between the original and redacted versions.

    Each segment yielded looks like this:
        - original: The text span in the original narrative (start, end, text).
        - label: The text span in the redacted narrative (start, end, text).
        - is_edit: Whether segment differs in the redacted from the original
        - is_valid: Whether segment appears to be a correct annotation.

    Note that the consuming code should check for the condition `is_edit` and
    not `is_valid`, which indicates a spurious edit rather than a redaction.

    Args:
        original: The original narrative text.
        redacted: The redacted narrative text.
        delimiters: The tokens that mark beginning and end of a redaction.
    """
    edit_stack = 0
    matcher = difflib.SequenceMatcher(None, original, redacted, autojunk=False)

    # Build regexes to match the delimiters
    opener_delim, closer_delim = Delimiter.parse(delimiters)

    op_seq_start = ("equal", 0, 0, 0, 0)
    opcodes = matcher.get_opcodes()
    while opcodes:
        opcode, i1, i2, j1, j2 = opcodes.pop(0)

        masked = original[i1:i2]
        mask = redacted[j1:j2]
        opener = opener_delim.pattern.search(mask)
        closer = closer_delim.pattern.search(mask)

        # Simplify the opcodes by splitting them if needed.
        new_ops = _split_opcode(mask, opcode, i1, i2, j1, j2, opener, closer)
        if new_ops:
            opcodes = new_ops + opcodes
            continue

        if opener:
            if edit_stack == 0:
                offset = opener.end() - opener_delim.length
                op_seq_start = (opcode, i1 + offset, i2, j1 + offset, j2)
            edit_stack += 1

        if opcode == "equal":
            if edit_stack == 0:
                yield TextSegment(
                    TextSpan(i1, i2, masked),
                    TextSpan(j1, j2, mask),
                    False,
                    True,
                )
        elif opcode in {"insert", "replace", "delete"}:
            if edit_stack == 0:
                yield TextSegment(
                    TextSpan(i1, i2, masked),
                    TextSpan(j1, j2, mask),
                    True,
                    False,
                )

        if closer:
            edit_stack = max(0, edit_stack - 1)
            # Yield the final segment
            if edit_stack == 0:
                offset = closer.end() - closer.start() - closer_delim.length
                i1 = op_seq_start[1]
                i2 = i2 - offset
                j1 = op_seq_start[3]
                j2 = j2 - offset

                masked = original[i1:i2]
                mask = redacted[j1:j2]
                yield TextSegment(
                    TextSpan(i1, i2, masked),
                    TextSpan(j1, j2, mask),
                    True,
                    True,
                )


def infer_annotations(
    original: str, redacted: str, **kwargs
) -> Generator[dict, None, None]:
    """Segment the narrative and return a sequence of redactions.

    Args:
        original: The original narrative text.
        redacted: The redacted narrative text.
        **kwargs: Additional arguments to pass to the `segment` function.

    Yields:
        A sequence of redaction annotations.
    """
    for seg in segment(original, redacted, **kwargs):
        if seg.is_edit and seg.is_valid:
            yield {
                "start": seg.original.start,
                "end": seg.original.end,
                "content": seg.redacted.text,
            }
