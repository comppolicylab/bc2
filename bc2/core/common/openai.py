from __future__ import annotations

import json
import logging
import os
from abc import abstractmethod
from functools import cached_property
from typing import Literal, Sequence, cast

import openai.types.chat as oai_chat_types
from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel, Field, PositiveInt

from .datafile import DataType, load_data_file, load_data_file_from_path
from .image import ImageUrl
from .infer import remove_hanging_redactions
from .openai_metadata import ModelNotFound, get_model_meta
from .resolve import prepare_resolve_input
from .template import TemplateEngine, get_formatter
from .types import NameToReplacementMap
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
            if not self.api_version:
                raise ValueError("Azure endpoint requires an API version.")
            if not self.api_key:
                raise ValueError("Azure endpoint requires an API key.")
            return AzureOpenAI(
                api_key=self.api_key,
                organization=self.organization,
                azure_endpoint=self.azure_endpoint,
                api_version=self.api_version,
            )
        return OpenAI(
            api_key=self.api_key,
            organization=self.organization,
            project=self.project,
            base_url=self.base_url,
        )


_OpenAIChatTextMessagePart = oai_chat_types.ChatCompletionContentPartTextParam
_OpenAIChatImageMessagePart = oai_chat_types.ChatCompletionContentPartImageParam
_OpenAIChatMessagePart = _OpenAIChatTextMessagePart | _OpenAIChatImageMessagePart


class OpenAIChatInputText(BaseModel):
    """Text input for an OpenAI model."""

    type: Literal["text"] = "text"
    text: str

    def as_chat_message_part(self) -> _OpenAIChatTextMessagePart:
        """Convert the input to a chat message."""
        return _OpenAIChatTextMessagePart(type=self.type, text=self.text)


class OpenAIUrl(BaseModel):
    """A URL for an OpenAI model."""

    url: str


class OpenAIChatInputImageUrl(BaseModel):
    """Image input for an OpenAI model."""

    type: Literal["image_url"] = "image_url"
    image_url: OpenAIUrl

    def as_chat_message_part(self) -> _OpenAIChatImageMessagePart:
        """Convert the input to a chat message."""
        return _OpenAIChatImageMessagePart(
            type=self.type,
            image_url=oai_chat_types.chat_completion_content_part_image_param.ImageURL(
                url=self.image_url.url,
                detail="high",
            ),
        )


OpenAIChatInput = OpenAIChatInputText | OpenAIChatInputImageUrl


class OpenAIChatTurn(BaseModel):
    """A chat turn for an OpenAI model."""

    role: Literal["assistant", "user", "system"]
    content: str | list[OpenAIChatInput]

    def as_chat_message(self) -> oai_chat_types.ChatCompletionMessageParam:
        """Convert the turn to a chat message."""
        match self.role:
            case "assistant":
                return oai_chat_types.ChatCompletionAssistantMessageParam(
                    role=self.role,
                    content=self._format_content_no_images(),
                )
            case "user":
                return oai_chat_types.ChatCompletionUserMessageParam(
                    role=self.role,
                    content=self._format_content(),
                )
            case "system":
                return oai_chat_types.ChatCompletionSystemMessageParam(
                    role=self.role,
                    content=self._format_content_no_images(),
                )

    def _format_content(self) -> str | list[_OpenAIChatMessagePart]:
        if isinstance(self.content, str):
            return self.content
        return [
            c if isinstance(c, str) else c.as_chat_message_part() for c in self.content
        ]

    def _format_content_no_images(self) -> str | list[_OpenAIChatTextMessagePart]:
        if isinstance(self.content, str):
            return self.content
        return [
            c if isinstance(c, str) else c.as_chat_message_part()
            for c in self.content
            if not isinstance(c, OpenAIChatInputImageUrl)
        ]


AnyChatInput = str | ImageUrl


class OpenAIChatOutput(BaseModel):
    """A chat output for an OpenAI model."""

    content: str
    completion_tokens: int
    placeholders: NameToReplacementMap | None = None
    max_tokens: int | None = None

    @property
    def is_truncated(self) -> bool:
        """Check if the output is truncated.

        This checks if the completion tokens are equal to the max tokens.
        Thus there is an edge case where the expected token output is exactly
        equal to the max tokens. In this case no truncation happened. Since
        this is a very uncommon case and impossible to see from the information
        we have in this class, we ignore it.
        """
        return self.completion_tokens == self.max_tokens


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
            # For examples, turns can only be strings. Throw an error if not.
            if not isinstance(turn.content, str):
                raise ValueError(f"Unsupported example type: {type(turn.content)}")
            turn.content = fmt(cast(str, turn.content), ctx)
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


class OpenAIChatConfig(BaseModel):
    """OpenAI Chat config."""

    method: Literal["chat"] = "chat"
    model: str
    openai_model: str | None = Field(
        None,
        description="When using Azure, the `model` refers to a model *deployment*. Set the `openai_model` parameter to indicate which underlying OpenAI model is used.",
    )
    system: OpenAIChatPrompt
    frequency_penalty: float | None = None
    max_tokens: PositiveInt | None = None
    n: int = 1
    presence_penalty: float | None = None
    seed: int | None = None
    temperature: float | None = None
    top_p: float | None = None

    extender: None = Field(
        None,
        deprecated=True,
        description="Use `control:chunk` instead.",
    )

    @property
    def model_completion_tokens(self) -> int | None:
        """Get the completion tokens for the model."""
        model_name = self.openai_model or self.model
        try:
            return get_model_meta(model_name).output
        except ModelNotFound:
            logger.warning(f"Model '{model_name}' not found in metadata.")
            return None

    @property
    def token_cap(self) -> int | None:
        """Get the token cap for the model."""
        custom_max_tokens = self.max_tokens
        model_max_tokens = self.model_completion_tokens

        if custom_max_tokens is None and model_max_tokens is None:
            logger.warning(
                "Unable to determine token limit for model output. There almost certainly *is* a limit, but since we do not know what it is, document chunking will not work."
            )
            return None

        if custom_max_tokens is None:
            logger.debug(f"Using model output token limit as cap ({model_max_tokens})")
            return model_max_tokens

        if model_max_tokens is None:
            logger.debug(f"Using custom token limit as cap ({custom_max_tokens})")
            return custom_max_tokens

        if custom_max_tokens == model_max_tokens:
            logger.debug(
                f"Custom token limit is set to model output size, using it is token cap ({custom_max_tokens})"
            )
            return custom_max_tokens

        if custom_max_tokens > model_max_tokens:
            logger.warning(
                f"Custom token limit ({custom_max_tokens}) is greater than model output size ({model_max_tokens}). This looks like a config error! Using model output size as token cap."
            )
            return model_max_tokens

        logger.debug(
            f"Custom token limit ({custom_max_tokens}) is smaller than model output size ({model_max_tokens}). Using custom token limit as token cap."
        )
        return custom_max_tokens

    def invoke(
        self,
        client: OpenAI,
        input: AnyChatInput | Sequence[AnyChatInput],
        placeholders: NameToReplacementMap | None = None,
    ) -> OpenAIChatOutput:
        """Invoke the chat."""
        props = self.model_dump()
        openai_api_params = {
            "model",
            "frequency_penalty",
            "n",
            "presence_penalty",
            "seed",
            "temperature",
            "top_p",
        }

        # Only keep populated settings that are in the OpenAI API params list.
        # Note that `max_tokens` is determined and applied separate from these params.
        openai_api_settings = {
            k: v for k, v in props.items() if k in openai_api_params and v is not None
        }

        # Format chat message
        placeholder_txt = placeholders.to_xml() if placeholders else ""
        messages = [
            m.as_chat_message()
            for m in self.system.format(input, placeholders=placeholder_txt)
        ]

        # Configure max tokens and submit the query.
        max_tokens = self.token_cap
        completion = client.chat.completions.create(
            **openai_api_settings, max_tokens=max_tokens, messages=messages
        )

        # Interpret completion response.
        content = completion.choices[0].message.content

        if not completion.usage:
            raise ValueError("Completion usage not found in response.")

        completion_tokens = completion.usage.completion_tokens
        return OpenAIChatOutput(
            max_tokens=max_tokens,
            content=content or "",
            completion_tokens=completion_tokens,
            placeholders=placeholders,
        )


class TooManyRetries(Exception):
    pass


class OpenAIResolverConfig(OpenAIChatConfig):
    """Resolve placeholders using an OpenAI model."""

    retries: PositiveInt = 3
    delimiters: Sequence[str] = ""

    def resolve(
        self,
        client: OpenAI,
        original: str,
        redacted: OpenAIChatOutput,
    ) -> tuple[dict, str]:
        redacted.content = remove_hanging_redactions(redacted.content, self.delimiters)
        input = prepare_resolve_input(
            original, redacted.content, redacted.placeholders, self.delimiters
        )

        last_e: Exception | None = None
        for i in range(self.retries):
            try:
                # Try calling the input and parsing the response
                response = self.invoke(client, input)
                placeholders = validate_json(response.content)
                logger.debug(f"Resolved placeholders: {placeholders}")
                return (placeholders, redacted.content)
            except Exception as e:
                last_e = e
                logger.warning(f"Error generating placeholders (attempt {i + 1} of \
                               {self.retries}): {e}")
        else:
            raise TooManyRetries from last_e


class OpenAIConfig(BaseModel):
    client: OpenAIClientConfig
