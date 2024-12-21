from pydantic.types import PositiveInt
from .infer import Delimiter

from rapidfuzz.fuzz import partial_ratio_alignment

def extend(generator,
           input: str,
           token_limit: PositiveInt, 
           max_extensions: PositiveInt, 
           existing_aliases: dict | None = None,
           delimiters: list[Delimiter] | None = None, 
           ) -> str:
    """Extract up to the limit, left-truncate the input, try again until done."""

    output = {"content": "", "completion_tokens": 0}
    tail = input
    num_extensions = 0
    while num_extensions <= max_extensions:

        # if alias_resolver:
        #     result = alias_resolver.execute_and_resolve(client, settings, system,
        #                                                 tail, 
        #                                                 preset_aliases=existing_aliases,
        #                                                 **kwargs)
        #     existing_aliases = result.aliases
        # else:
        result = generator.invoke(self.client, input)

        if delimiters:
            # Look for, and remove, any incomplete redactions
            last_opening = result.content.rfind(delimiters[0])
            last_closing = result.content.rfind(delimiters[1])
            if last_closing < last_opening:
                result.content = result.content[:last_opening]

        output.content += result.content + " <suture> "
        output.completion_tokens += result.completion_tokens
        output.aliases = existing_aliases

        if result.completion_tokens == token_limit:
            num_extensions += 1
            alignment = partial_ratio_alignment(tail, result.content)
            tail = tail[alignment.src_end:]
        else:
            break

    return output
