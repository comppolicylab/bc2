import json

from .infer import infer_annotations
from .types import NameMap

INPUT_TEMPLATE = """\
[MAP#1]
{preset_aliases}

[MAP#2]
{inferred_annotations}

[NARRATIVE]
{original}
"""


def prepare_resolve_input(original: str, 
                          redacted: str, 
                          aliases: NameMap | None,
                          raw_delimiters: list[str]) -> str:
    """Prepare input for entity resolution.

    Args:
        original: The original text.
        redacted: The redacted OpenAIChatOutput object, 
            including content and aliases.
        raw_delimiters: The raw delimiters used for redaction

    Returns:
        Text ready for use as input on an entity resolution generator.
    """
    # Infer annotations from the original and redacted text
    inferred_annotations = infer_annotations(original, redacted,
                                             delimiters=raw_delimiters)
    inferred_annotations = {x["original"]: x["redacted"] 
                            for x in inferred_annotations}
    
    if not aliases:
        aliases = {}
    
    # Prepare the input for the resolver chat
    input = INPUT_TEMPLATE.format(
        preset_aliases=json.dumps(aliases, 
                                  indent=2, 
                                  sort_keys=True),
        inferred_annotations=json.dumps(inferred_annotations, 
                                        indent=2, 
                                        sort_keys=True),
        original=original
    )

    return input
