import difflib


def infer_annotations(original_narrative, redacted_narrative):
    """Generate a list of annotations that the LLM applied.

    This function computes the delta between the original narrative text and
    the redacted narrative texts. It inspects the delta to generate a list
    of annotations that the LLM applied to the original narrative text.
    Each annotation contains the following fields:
      - start: The start index of the annotation in the original narrative text.
      - end: The end index of the annotation in the original narrative text.
      - content: The content of the annotation.
    """
    annotations = []
    # Compute the delta between the original and redacted narrative.
    delta = list(difflib.ndiff(original_narrative, redacted_narrative))
    # Iterate over the delta to generate annotations.
    ptr = -1
    start = -1
    content = ""
    for i, diff in enumerate(delta):
        type_, _, char = diff

        # Increment pointer for same / subtractions
        if type_ in ("-", " "):
            ptr += 1

        # Accumulate content when inside annotation
        if start > -1 and type_ in ("+", " "):
            content += char

        # Handle additions
        if type_ == "+":
            # If we are not currently in an annotation, start a new one.
            if char == "<":
                content = char
                start = ptr + 1

                # Look behind to cover preceding adjacent subtractions
                lookbehind = i
                while lookbehind > 0:
                    lookbehind -= 1
                    if delta[lookbehind][0] == "-":
                        start -= 1
                    else:
                        break
            elif char == ">":
                end = ptr + 1

                # Look-ahead to cover subsequent adjacent subtractions
                lookahead = i
                while lookahead < len(delta) - 1:
                    lookahead += 1
                    if delta[lookahead][0] == "-":
                        end += 1
                    else:
                        break

                annotations.append({
                    "start": start,
                    "end": end,
                    "content": content,
                    })
                start = -1
                content = ""
    return annotations
