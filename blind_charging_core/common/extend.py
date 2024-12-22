from pydantic.types import PositiveInt
from openai import OpenAI

from .openai import OpenAIChatOutput, OpenAIChatConfig
from .infer import Delimiter

from rapidfuzz.fuzz import partial_ratio_alignment

def extend(client: OpenAI,
           input: str,
           generator: OpenAIChatConfig,
           token_limit: PositiveInt, 
           max_extensions: PositiveInt, 
           preset_aliases: dict | None = None,
           delimiters: list[Delimiter] | None = None, 
           debug: bool = False,
           ) -> str:
    """Extract up to the limit, left-truncate the input, try again until done."""

    output = OpenAIChatOutput(content="", completion_tokens= 0)
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
        if preset_aliases:
            result = generator.invoke(client, tail, preset_aliases=preset_aliases)
        else:
            result = generator.invoke(client, tail)

        if delimiters:
            # Look for, and remove, any incomplete redactions
            last_opening = result.content.rfind(delimiters[0])
            last_closing = result.content.rfind(delimiters[1])
            if last_closing < last_opening:
                result.content = result.content[:last_opening]

        if debug:
            result.content += "<suture>"
        output.content += result.content
        output.completion_tokens += result.completion_tokens
        output.aliases = preset_aliases

        if result.completion_tokens == token_limit:
            num_extensions += 1
            alignment = partial_ratio_alignment(tail, result.content)
            tail = tail[alignment.src_end:]
        else:
            break

    return output
