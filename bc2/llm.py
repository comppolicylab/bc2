import openai

from config import config


DEFAULT_PROMPT_PATH = "prompts/redact.txt"
with open(DEFAULT_PROMPT_PATH, 'r') as f:
    DEFAULT_PROMPT = f.read()


# Configure OpenAI with values from config
openai.api_type = config.openai_api_type
openai.api_base = config.openai_api_base
openai.api_version = config.openai_api_version
openai.api_key = config.openai_api_key


def redact(narrative,
           system_prompt=DEFAULT_PROMPT,
           **kwargs):
    settings = dict(
            engine=config.openai_engine,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": narrative},
                ],
            **kwargs,
            )
    # Create the completion
    completion = openai.ChatCompletion.create(**settings)

    # Get the returned message
    message = completion.choices[0].message
    return message['content']
