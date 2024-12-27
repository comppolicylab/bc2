import logging

from pydantic.types import PositiveInt
from openai import OpenAI

from .openai import OpenAIChatOutput, OpenAIChatConfig, OpenAIResolverConfig
from .infer import Delimiter
from .types import NameMap

from rapidfuzz.fuzz import partial_ratio_alignment

logger = logging.getLogger(__name__)

def extend(client: OpenAI,
           input: str,
           generator: OpenAIChatConfig,
           preset_aliases: NameMap | None = None,
           delimiters: list[Delimiter] | None = None, 
           resolver: OpenAIResolverConfig | None = None,
           debug: bool = False,
           ) -> str:
    """Extract up to the limit, left-truncate the input, try again until done."""

    token_limit = generator.extender.api_completion_token_limit
    max_extensions = generator.extender.max_extensions

    output = OpenAIChatOutput(content="", completion_tokens= 0)
    tail = input
    num_extensions = 0
    while num_extensions <= max_extensions:
        logger.debug(f"Running extension #{num_extensions}")

        # ACW to do: check what happens when preset_aliases is None
        result = generator.invoke(client, tail, 
                                  preset_aliases=preset_aliases)

        # Redact only
        if delimiters:
            # Look for, and remove, any incomplete redactions
            last_opening = result.content.rfind(delimiters[0])
            last_closing = result.content.rfind(delimiters[1])
            if last_closing < last_opening:
                result.content = result.content[:last_opening]

        # Redact only
        if resolver:
            preset_aliases = resolver.resolve(client,
                                              input,
                                              result.content,
                                              preset_aliases,
                                              delimiters)
        # Redact only
        if preset_aliases:
            output.aliases = preset_aliases

        output.content += result.content
        output.completion_tokens += result.completion_tokens

        if result.completion_tokens == token_limit:
            num_extensions += 1
            alignment = partial_ratio_alignment(tail, result.content)
            tail = tail[alignment.src_end:]
        else:
            break

    return output
