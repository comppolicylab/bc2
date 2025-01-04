from rapidfuzz.fuzz import partial_ratio_alignment

def residual(original: str, extract: str, needle_size = 10000) -> str | None:
    """Try to align an extracted string output with its source string. 

    If a match is found, return everything after the match in the source string.

    Args:
        original: The full source string.
        extract: A string extracted from the source string, which may contain
            small modifications (e.g., as a result of passing through GPT-4o.)

    Returns:
        The original string trimmed to after the best match, 
        or None if no match is found.
    """
    alignment = partial_ratio_alignment(original, extract[-needle_size:])
    if not alignment:
        return None

    return original[alignment.src_end:]
