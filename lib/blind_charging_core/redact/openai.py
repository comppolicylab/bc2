import json
import math
import os
import pathlib

import openai
from pydantic import BaseModel, Field, Literal

from ..common.openai import OpenAIApiConfig
from ..common.text import Text
from .base import BaseRedactDriver

ROOT_PATH = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

PROMPTS_DIR = ROOT_PATH / "common" / "prompts"

DEFAULT_PROMPT_PATH = PROMPTS_DIR / "redact.txt"
with open(DEFAULT_PROMPT_PATH, "r") as f:
    DEFAULT_PROMPT = f.read()

EXAMPLES_PATH = PROMPTS_DIR / "examples.jsonl"
with open(EXAMPLES_PATH, "r") as f:
    EXAMPLES = [json.loads(line) for line in f.readlines()]


class OpenAIRedactConfig(BaseModel):
    """OpenAI Redact config."""

    engine: Literal["openai"]
    api: OpenAIApiConfig
    model: str
    completion_type: Literal["chat", "completion"] = "completion"
    prompt_file: str = Field(DEFAULT_PROMPT_PATH)


class OpenAIRedactDriver(BaseRedactDriver):
    def __init__(self, config: OpenAIRedactConfig):
        self.config = config
        self.openai_client = openai.Client(
            api_key=config.api.key,
            api_type=config.api.type,
            api_base=config.api.base,
        )

    def __call__(self, narrative: Text) -> Text:
        return self.redact_with_completion(narrative.text, self.config.prompt_file)

    def get_model_slug(self) -> str:
        """Get a descriptive text name for the model specified in the config.

        Returns:
            str: The model name.
        """
        base = self.config.api.base
        # Extract the deployment name from the URL, which is specified in a URL
        # in the format: https://{deployment}.openai.azure.com/
        deployment = base.split(".")[0].split("//")[1]

        # Join the deployment name with the engine name
        return f"{deployment}_{self.config.engine}"

    def redact_with_chat(
        self, narrative: str, system_prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Redact a narrative using the OpenAI Chat API.

        Args:
            narrative: The narrative to redact.
            system_prompt: The prompt to use for the system.
            model: The model to use for the completion.
            **kwargs: Additional arguments to pass to the completion API.

        Returns:
            The redacted narrative.
        """
        self.openai_client.api_version = self.config.api.chat_version
        settings = dict(
            engine=self.config.engine,
            messages=[{"role": "system", "content": system_prompt}]
            + EXAMPLES
            + [
                {"role": "user", "content": narrative},
            ],
            temperature=0.0,
            top_p=0.95,
            max_tokens=int(math.ceil(len(narrative) * 1.1)),
            **kwargs,
        )
        # Create the completion
        completion = self.openai_client.ChatCompletion.create(**settings)

        # Get the returned message
        message = completion.choices[0].message
        return message["content"]

    def redact_with_completion(
        self, narrative: str, prompt: str = DEFAULT_PROMPT, **kwargs
    ) -> str:
        """Redact a narrative using the OpenAI Completion API.

        Args:
            narrative: The narrative to redact.
            prompt: The prompt to use for the completion.
            **kwargs: Additional arguments to pass to the completion API.

        Returns:
            The redacted narrative.
        """
        self.openai_client.api_version = self.config.api.version
        settings = dict(
            engine=self.config.api.engine,
            prompt=prompt,
            max_tokens=int(math.ceil(len(narrative) * 1.1)),
            top_p=0.5,
            temperature=0.0,
            **kwargs,
        )
        completion = self.openai_client.Completion.create(**settings)
        return completion.choices[0].text
