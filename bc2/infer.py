from typing import Generator, NamedTuple
import difflib
import re


TextSpan = NamedTuple("TextSpan", [
    ("start", int),
    ("end", int),
    ("text", str),
    ])


TextSegment = NamedTuple("TextSegment", [
    ("original", TextSpan),
    ("redacted", TextSpan),
    ("is_edit", bool),
    ("is_valid", bool),
    ])


def segment(
        original: str,
        redacted: str,
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
    """
    edit_stack = 0
    matcher = difflib.SequenceMatcher(None, original, redacted, autojunk=False)
    
    op_seq_start = ("equal", 0, 0, 0, 0)
    for op in matcher.get_opcodes():
        opcode, i1, i2, j1, j2 = op

        masked = original[i1:i2]
        mask = redacted[j1:j2]
        opener = re.search(r"^(\s*<)", mask)
        closer = re.search(r"(>\s*)$", mask)

        if opener:
            if edit_stack == 0:
                offset = opener.end() - 1
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
                offset = closer.end() - closer.start() - 1
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


def infer_annotations(original: str, redacted: str) -> Generator[dict, None, None]:
    """Segment the narrative and return a sequence of redactions.

    Args:
        original: The original narrative text.
        redacted: The redacted narrative text.

    Yields:
        A sequence of redaction annotations.
    """
    for seg in segment(original, redacted):
        if seg.is_edit and seg.is_valid:
            yield {
                "start": seg.original.start,
                "end": seg.original.end,
                "content": seg.redacted.text,
                }
