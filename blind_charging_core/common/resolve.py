import json

from .infer import Delimiter, infer_annotations

INPUT_TEMPLATE = """\
[MAP#1]
{preset_aliases}

[MAP#2]
{inferred_annotations}

[NARRATIVE]
{original}
"""


def prepare_resolve_input(original, redacted, raw_delimiters):
    # Infer annotations from the original and redacted text
    inferred_annotations = infer_annotations(original, redacted.content,
                                            delimiters=raw_delimiters)
    inferred_annotations = [{x["original"]: x["redacted"]} 
                            for x in inferred_annotations]
    
    # Prepare the input for the resolver chat
    input = INPUT_TEMPLATE.format(
        preset_aliases=json.dumps(redacted.aliases, 
                                  indent=2, 
                                  sort_keys=True),
        inferred_annotations=json.dumps(inferred_annotations, 
                                        indent=2, 
                                        sort_keys=True),
        original=original
    )

    return input
