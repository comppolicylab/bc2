import openai
import math
import json

from config import config


DEFAULT_PROMPT_PATH = "prompts/redact.txt"
with open(DEFAULT_PROMPT_PATH, 'r') as f:
    DEFAULT_PROMPT = f.read()

EXAMPLES_PATH = "prompts/examples.jsonl"
with open(EXAMPLES_PATH, 'r') as f:
    EXAMPLES = [json.loads(line) for line in f.readlines()]


# Configure OpenAI with values from config
openai.api_type = config.openai_api_type
openai.api_base = config.openai_api_base
openai.api_key = config.openai_api_key


def redact_with_chat(narrative: str,
                     system_prompt: str = DEFAULT_PROMPT,
                     **kwargs) -> str:
    """Redact a narrative using the OpenAI Chat API.

    Args:
        narrative: The narrative to redact.
        system_prompt: The prompt to use for the system.
        model: The model to use for the completion.
        **kwargs: Additional arguments to pass to the completion API.

    Returns:
        The redacted narrative.
    """
    openai.api_version = config.openai_api_chat_version
    settings = dict(
            engine=config.openai_engine,
            messages=[
                {"role": "system", "content": system_prompt}] + EXAMPLES + [
                {"role": "user", "content": narrative},
                ],
            temperature=0.0,
            top_p=0.95,
            max_tokens=int(math.ceil(len(narrative) * 1.1)),
            **kwargs,
            )
    # Create the completion
    completion = openai.ChatCompletion.create(**settings)

    # Get the returned message
    message = completion.choices[0].message
    return message['content']


def redact_with_completion(narrative: str,
                           prompt: str = DEFAULT_PROMPT,
                           **kwargs) -> str:
    """Redact a narrative using the OpenAI Completion API.

    Args:
        narrative: The narrative to redact.
        prompt: The prompt to use for the completion.
        **kwargs: Additional arguments to pass to the completion API.

    Returns:
        The redacted narrative.
    """
    openai.api_version = config.openai_api_version
    settings = dict(
            engine=config.openai_engine,
            prompt=prompt,
            max_tokens=int(math.ceil(len(narrative) * 1.1)),
            top_p=0.5,
            temperature=0.0,
            **kwargs,
            )
    completion = openai.Completion.create(**settings)
    return completion.choices[0].text
