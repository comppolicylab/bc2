from __future__ import annotations
import logging
import json
import os
from abc import abstractmethod
from functools import cached_property
from typing import Any, Literal, Sequence

from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel, PositiveInt, NonNegativeInt

from .align import residual
from .datafile import DataType, load_data_file, load_data_file_from_path
from .image import ImageUrl
from .infer import remove_hanging_redactions
from .resolve import prepare_resolve_input
from .template import TemplateEngine, get_formatter
from .types import NameMap
from .validate import validate_json


logger = logging.getLogger(__name__)


class OpenAIClientConfig(BaseModel):
    """OpenAI API settings."""

    api_key: str
    organization: str | None = None
    project: str | None = None
    base_url: str | None = None
    azure_endpoint: str | None = None
    api_version: str | None = None

    def init(self) -> OpenAI:
        """Create an OpenAI client."""
        if self.azure_endpoint:
            return AzureOpenAI(
                api_key=self.api_key,
                organization=self.organization,
                project=self.project,
                base_url=self.base_url,
                azure_endpoint=self.azure_endpoint,
                api_version=self.api_version,
            )
        return OpenAI(
            api_key=self.api_key,
            organization=self.organization,
            project=self.project,
            base_url=self.base_url,
        )


class OpenAIChatInputText(BaseModel):
    """Text input for an OpenAI model."""

    type: Literal["text"] = "text"
    text: str


class OpenAIUrl(BaseModel):
    """A URL for an OpenAI model."""

    url: str


class OpenAIChatInputImageUrl(BaseModel):
    """Image input for an OpenAI model."""

    type: Literal["image_url"] = "image_url"
    image_url: OpenAIUrl


OpenAIChatInput = OpenAIChatInputText | OpenAIChatInputImageUrl


class OpenAIChatTurn(BaseModel):
    """A chat turn for an OpenAI model."""

    role: Literal["assistant", "user", "system"]
    content: str | list[OpenAIChatInput]


AnyChatInput = str | ImageUrl

class OpenAIChatOutput(BaseModel):
    """A chat output for an OpenAI model."""

    content: str
    completion_tokens: int
    aliases: NameMap | None = None


class ChatPrompt:
    engine: TemplateEngine = "string"

    @property
    @abstractmethod
    def prompt_value(self) -> str: ...

    @property
    @abstractmethod
    def examples_value(self) -> list[dict[str, str]] | None: ...

    def format(
        self, input: AnyChatInput | Sequence[AnyChatInput], **kwargs
    ) -> list[OpenAIChatTurn]:
        """Format the prompt."""
        ctx = kwargs.copy()
        fmt = get_formatter(self.engine)

        # Format system and example messages into the start of the thread
        base_messages: list[OpenAIChatTurn] = [
            OpenAIChatTurn(
                role="system",
                content=fmt(self.prompt_value, ctx),
            )
        ]
        for example in self.examples_value or []:
            turn = OpenAIChatTurn.model_validate(example)
            turn.content = fmt(turn.content, ctx)
            base_messages.append(turn)

        # TODO - we might get different results if the input image is
        # formatted into the pre-defined prompt instead of as a new message.
        inputs: list[AnyChatInput] = []
        if isinstance(input, str):
            inputs.append(input)
        elif isinstance(input, ImageUrl):
            inputs.append(input)
        else:
            for node in input:
                inputs.append(node)

        content: list[OpenAIChatInput] = []
        for node in inputs:
            if isinstance(node, ImageUrl):
                content.append(
                    OpenAIChatInputImageUrl(image_url=OpenAIUrl(url=node.url))
                )
            elif isinstance(node, str):
                content.append(OpenAIChatInputText(text=node))
            else:
                raise ValueError(f"Unsupported input type: {type(node)}")
        return base_messages + [OpenAIChatTurn(role="user", content=content)]
    

class OpenAIChatPromptInline(BaseModel, ChatPrompt):
    """An inline prompt for an OpenAI model."""

    prompt: str
    examples: list[dict[str, str]] | None = None

    @property
    def prompt_value(self) -> str:
        return self.prompt

    @property
    def examples_value(self) -> list[dict[str, str]] | None:
        return self.examples


class OpenAIChatPromptFile(BaseModel, ChatPrompt):
    """A prompt file for an OpenAI model."""

    prompt_file: str
    examples_file: str | None = None

    @cached_property
    def prompt_value(self) -> str:
        """Format the prompt file."""
        return load_data_file_from_path(DataType.prompt, self.prompt_file)

    @cached_property
    def examples_value(self) -> list[dict[str, str]]:
        """Load the examples file."""
        if self.examples_file is None:
            return []
        return load_data_file_from_path(DataType.example, self.examples_file)


class OpenAIChatPromptBuiltIn(BaseModel, ChatPrompt):
    """A built-in prompt for an OpenAI model."""

    prompt_id: str
    examples_id: str | None = None

    @cached_property
    def prompt_value(self) -> str:
        return load_data_file(DataType.prompt, self.prompt_id)

    @cached_property
    def examples_value(self) -> list[dict[str, str]]:
        if not self.examples_id:
            return []
        return load_data_file(DataType.example, self.examples_id)


class OpenAIChatPromptEnv(BaseModel, ChatPrompt):
    """A prompt file for an OpenAI model."""

    prompt_env: str
    examples_env: str | None = None

    @cached_property
    def prompt_value(self) -> str:
        """Load the prompt from the environment variable"""
        s = os.getenv(self.prompt_env)
        if s is None:
            raise ValueError(f"Environment variable {self.prompt_env} not set")
        return s

    @cached_property
    def examples_value(self) -> list[dict[str, str]]:
        """Load the examples from the environment variable"""
        messages: list[dict[str, str]] = []
        if self.examples_env is not None:
            s = os.getenv(self.examples_env)
            if s is None:
                raise ValueError(f"Environment variable {self.examples_env} not set")
            for example in s.split("\n"):
                new_turn = json.loads(example)
                messages.append(new_turn)
        return messages


OpenAIChatPrompt = (
    OpenAIChatPromptInline
    | OpenAIChatPromptFile
    | OpenAIChatPromptEnv
    | OpenAIChatPromptBuiltIn
)


class CompletionPrompt:
    engine: TemplateEngine = "string"

    @property
    @abstractmethod
    def prompt(self) -> str: ...

    def format(self, input: str, **kwargs) -> str:
        """Format the prompt."""
        ctx = {**kwargs, "input": input}
        fmt = get_formatter(self.engine)
        return fmt(self.prompt, ctx)


class OpenAICompletionPromptInline(BaseModel, CompletionPrompt):
    """A completion prompt for an OpenAI model."""

    prompt_text: str

    @property
    def prompt(self) -> str:
        """Echo the prompt text."""
        return self.prompt_text


class OpenAICompletionPromptFile(BaseModel, CompletionPrompt):
    """A prompt file for an OpenAI model."""

    prompt_file: str

    @cached_property
    def prompt(self) -> str:
        """Load the prompt file"""
        return load_data_file_from_path(DataType.prompt, self.prompt_file)


class OpenAICompletionPromptBuiltIn(BaseModel, CompletionPrompt):
    """A built-in prompt for an OpenAI model."""

    prompt_id: str

    @cached_property
    def prompt(self) -> str:
        return load_data_file(DataType.prompt, self.prompt_id)


class OpenAICompletionPromptEnv(BaseModel, CompletionPrompt):
    """A prompt file for an OpenAI model."""

    prompt_env: str

    @cached_property
    def prompt(self) -> str:
        """Load the prompt from the environment variable"""
        s = os.getenv(self.prompt_env)
        if s is None:
            raise ValueError(f"Environment variable {self.prompt_env} not set")
        return s


OpenAICompletionPrompt = (
    OpenAICompletionPromptInline
    | OpenAICompletionPromptFile
    | OpenAICompletionPromptEnv
    | OpenAICompletionPromptBuiltIn
)


class OpenAIExtenderConfig(BaseModel, ChatPrompt):
    """Allow outputs over the OpenAI output token limit."""

    max_extensions: NonNegativeInt
    api_completion_token_limit: PositiveInt
    

class OpenAIChatConfig(BaseModel):
    """OpenAI Chat config."""

    method: Literal["chat"]
    model: str
    system: OpenAIChatPrompt
    frequency_penalty: float | None = None
    max_tokens: PositiveInt | None = None
    n: int = 1
    presence_penalty: float | None = None
    seed: int | None = None
    temperature: float | None = None
    top_p: float | None = None

    extender: OpenAIExtenderConfig | None = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.extender and self.max_tokens:
            self.extender.api_completion_token_limit = min(self.max_tokens,
                                                           self.extender.api_completion_token_limit)

    def invoke(
        self, client: OpenAI, input: AnyChatInput | Sequence[AnyChatInput], 
        preset_aliases: NameMap | None = None
    ) -> OpenAIChatOutput:
        """Invoke the chat."""
        props = self.model_dump()
        openai_api_params = ["model", "frequency_penalty", "max_tokens", "n",
                             "presence_penalty", "seed", "temperature", "top_p"]
        # Only keep populated settings that are in the OpenAI API params list
        openai_api_settings = {k: v for k, v in props.items() 
                               if k in openai_api_params and v is not None}

        messages = [m.model_dump() for m in self.system.format(input, 
                                                               preset_aliases=preset_aliases)]
        completion = client.chat.completions.create(**openai_api_settings, 
                                                    messages=messages)
        content = completion.choices[0].message.content
        completion_tokens = completion.usage.completion_tokens
        return OpenAIChatOutput(content=content, 
                                completion_tokens=completion_tokens,
                                aliases=preset_aliases)
    
    def invoke_extend_resolve(
        self, client: OpenAI, input: AnyChatInput | Sequence[AnyChatInput], 
        resolver: OpenAIResolverConfig | None = None,
        raw_delimiters: Sequence[str] | None = None,
        preset_aliases: NameMap | None = None
    ) -> OpenAIChatOutput:
        """Invoke the chat with extensions and/or resolution,
        if either functions are configured."""
        if self.extender:
            token_limit = self.extender.api_completion_token_limit
            max_extensions = self.extender.max_extensions

            output = OpenAIChatOutput(content="", 
                                      completion_tokens=0,
                                      aliases=preset_aliases)
            tail = input
            num_extensions = 0
            while num_extensions <= max_extensions:
                logger.info(f"Running extension #{num_extensions + 1}")
                result = self.invoke(client, tail, output.aliases)

                if resolver:
                    output.aliases, result.content = \
                        resolver.resolve(client, input, result, raw_delimiters)
                output.content += result.content
                output.completion_tokens += result.completion_tokens

                if result.completion_tokens == token_limit:
                    num_extensions += 1
                    tail = residual(tail, result.content)
                    if not tail:
                        break
                    output.content += " "
                else:
                    break
        else:
            output = self.invoke(client, input)
            if resolver:
                output.aliases, _ = resolver.resolve(client, input, result, 
                                                     raw_delimiters)
        return output
        

class TooManyRetries(Exception): pass

class OpenAIResolverConfig(OpenAIChatConfig):
    """Resolve aliases using an OpenAI model."""
    retries: PositiveInt = 3

    def resolve(
        self, 
        client: OpenAI, 
        original: AnyChatInput | Sequence[AnyChatInput], 
        redacted: OpenAIChatOutput,
        raw_delimiters: Sequence[str]
    ) -> str:
        redacted.content = remove_hanging_redactions(redacted.content, 
                                                     raw_delimiters)
        input = prepare_resolve_input(original, 
                                      redacted.content, 
                                      redacted.aliases,
                                      raw_delimiters)

        last_e: Exception | None = None
        for i in range(self.retries):
            try:
                # Try calling the input and parsing the response
                response = self.invoke(client, input)
                aliases = validate_json(response.content)
                logger.debug(f"Resolved aliases: {aliases}")
                return (aliases, redacted.content)
            except Exception as e:
                last_e = e
                logger.warning(f"Error generating aliases (attempt {i + 1} of \
                               {self.retries}): {e}")
        else:
            raise TooManyRetries from last_e
    

class OpenAICompletionConfig(BaseModel):
    """OpenAI Completion config."""

    method: Literal["completion"]
    model: str
    prompt: OpenAICompletionPrompt
    best_of: int | None = None
    frequency_penalty: float | None = None
    logit_bias: dict[str, int] | None = None
    max_tokens: int | None = None
    n: int = 1
    presence_penalty: float | None = None
    seed: int | None = None
    stop: list[str] | None = None
    temperature: float | None = None
    top_p: float | None = None

    def __init__(self, **data: Any):
        super().__init__(**data)
        if self.best_of is not None and self.n is not None:
            if self.best_of <= self.n:
                raise ValueError("best_of must be greater than n")

    def invoke(self, client: OpenAI, input: str, **kwargs) -> str:
        """Invoke the completion."""
        settings = self.model_dump()
        settings.pop("method")
        settings.pop("prompt")
        prompt = self.prompt.format(input, **kwargs)
        # Remove any setting whose value is `None`
        settings = {k: v for k, v in settings.items() if v is not None}
        completion = client.completions.create(**settings, prompt=prompt)
        return completion.choices[0].text


OpenAIGeneratorConfig = OpenAIChatConfig | OpenAICompletionConfig


class OpenAIConfig(BaseModel):
    client: OpenAIClientConfig
