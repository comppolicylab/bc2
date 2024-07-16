import json
from abc import abstractmethod
from functools import cached_property
from typing import Any, Literal, Sequence

from openai import Client
from pydantic import BaseModel

from .image import ImageUrl
from .template import TemplateEngine, get_formatter


class OpenAIClientConfig(BaseModel):
    """OpenAI API settings."""

    api_key: str
    organization: str | None = None
    project: str | None = None
    base_url: str | None = None

    def init(self) -> Client:
        """Create an OpenAI client."""
        return Client(
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
        with open(self.prompt_file, "r") as f:
            return f.read()

    @cached_property
    def examples_value(self) -> list[dict[str, str]]:
        """Load the examples file."""
        messages: list[dict[str, str]] = []
        if self.examples_file is not None:
            # Examples should be specified as JSONL
            with open(self.examples_file, "r") as f:
                for example in f:
                    new_turn = json.loads(example)
                    messages.append(new_turn)
        return messages


OpenAIChatPrompt = OpenAIChatPromptInline | OpenAIChatPromptFile


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

    prompt: str


class OpenAICompletionPromptFile(BaseModel, CompletionPrompt):
    """A prompt file for an OpenAI model."""

    prompt_file: str

    @cached_property
    def prompt(self) -> str:
        """Load the prompt file"""
        with open(self.prompt_file, "r") as f:
            return f.read()


OpenAICompletionPrompt = OpenAICompletionPromptInline | OpenAICompletionPromptFile


class OpenAIChatConfig(BaseModel):
    """OpenAI Chat config."""

    method: Literal["chat"]
    model: str
    system: OpenAIChatPrompt
    frequency_penalty: float | None = None
    max_tokens: int | None = None
    n: int = 1
    presence_penalty: float | None = None
    seed: int | None = None
    temperature: float | None = None
    top_p: float | None = None

    def invoke(
        self, client: Client, input: AnyChatInput | Sequence[AnyChatInput], **kwargs
    ) -> str:
        """Invoke the chat."""
        settings = self.model_dump()
        settings.pop("method")
        settings.pop("system")
        messages = [m.model_dump() for m in self.system.format(input, **kwargs)]
        # Remove any setting whose value is `None`
        settings = {k: v for k, v in settings.items() if v is not None}
        completion = client.chat.completions.create(**settings, messages=messages)
        return completion.choices[0].message.content


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

    def invoke(self, client: Client, input: str, **kwargs) -> str:
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
