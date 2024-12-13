import logging
import json
import os
from abc import abstractmethod
from functools import cached_property
from typing import Any, Literal, Sequence

from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel, field_validator, FieldValidationInfo

from rapidfuzz.fuzz import partial_ratio_alignment

from .datafile import DataType, load_data_file, load_data_file_from_path
from .image import ImageUrl
from .infer import infer_annotations
from .template import TemplateEngine, get_formatter
from .types import NameMap


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

    class Config:
        allow_mutation = True


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

    def execute(
        self, client: OpenAI, settings: dict, 
        input: AnyChatInput | Sequence[AnyChatInput], **kwargs
    ) -> OpenAIChatOutput:
        """Execute the prompt."""
        messages = [m.model_dump() for m in self.format(input, **kwargs)]
        completion = client.chat.completions.create(**settings, messages=messages)
        content = completion.choices[0].message.content
        completion_tokens = completion.usage.completion_tokens
        return OpenAIChatOutput(content=content, completion_tokens=completion_tokens)
    

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


ALIASES_PROMPT_TPL = """\
[MAP#1]
{preset_aliases}

[MAP#2]
{inferred_annotations}

[NARRATIVE]
{narrative}"""

class OpenAIAliasResolverConfig(BaseModel, ChatPrompt):
    """Resolve aliases using an OpenAI model."""

    prompt: str
    examples: list[dict[str, str]] | None = None

    @property
    def prompt_value(self) -> str:
        return self.prompt

    @property
    def examples_value(self) -> list[dict[str, str]] | None:
        return self.examples
    
    def _generate_with_retry(self, client: OpenAI, settings: dict,
        original: str, preset_aliases: NameMap, inferred_annotations: NameMap, 
        retries: int = 3
    ) -> NameMap:
        """Resolve aliases from two alias sets and the original text, with retries.

        Args:
            original: The original text.
            preset_aliases: The preexisting aliases map.
            inferred_annotations: The aliases map inferred by the redaction process.
            retries: The number of retries to attempt.

        Returns:
            The new aliases map.
        """
        last_error: Exception | None = None
        for i in range(retries):
            try:
                return self._generate(client, settings, original, 
                                      preset_aliases, inferred_annotations)
            except Exception as e:
                logger.error(f"Error generating aliases (attempt {i + 1}): {e}")
                last_error = e

        raise ValueError("Error generating aliases.") from last_error

    def _generate(self, client: OpenAI, settings: dict,
        original: str, preset_aliases: NameMap, inferred_annotations: NameMap) -> NameMap:
        """Resolve aliases from two alias sets and the original text.

        Args:
            original: The original text.
            preset_aliases: The preexisting aliases map.
            inferred_annotations: The aliases map inferred by the redaction process.

        Returns:
            The new aliases map.
        """
        inferred_annotations = [{x["original"]: x["redacted"]} for x in inferred_annotations]
        input = ALIASES_PROMPT_TPL.format(
            preset_aliases = json.dumps(preset_aliases, indent=2, sort_keys=True),
            inferred_annotations = json.dumps(inferred_annotations, indent=2, sort_keys=True),
            narrative = original,
        )
        response = self.execute(client, settings, input)
        return self._parse(response.content)
    
    def _parse(self, response: str) -> NameMap:
        """Parse the response from the generator.

        The response should be a JSON object mapping IDs to aliases.

        Args:
            response: The response from the generator.
            preset_aliases: The preexisting aliases map (for validation).
            inferred_annotations: The aliases map inferred by the redaction process (for validation).

        Returns:
            The new aliases map.
        """
        try:
            data = json.loads(response)
            # TODO: Validate the JSON response matches the alias maps
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            raise ValueError("Error parsing JSON response.") from e

        return data

    def resolve_aliases(self, client: OpenAI, settings: dict,
                        original: str, redacted: str, 
                        preset_aliases: NameMap, delimiters: Sequence[str]
    ) -> NameMap:
        """Resolve aliases from the redacted text."""
        inferred_annotations = infer_annotations(original, redacted,
                                                 delimiters=delimiters)
        return self._generate_with_retry(client, settings, original, 
                                         preset_aliases, inferred_annotations)
    
    def execute_and_resolve(
        self, client: OpenAI, settings: dict, system: OpenAIChatPrompt,
        input: AnyChatInput | Sequence[AnyChatInput], 
        **kwargs            
    ) -> OpenAIChatOutput:
        """Execute the prompt and resolve aliases."""
        preset_aliases = kwargs.get("preset_aliases")
        delimiters = kwargs.get("delimiters")
        result = system.execute(client, settings, input, **kwargs)
        aliases = self.resolve_aliases(client, settings, input, result.content,
                                       preset_aliases, delimiters)
        logger.debug(f"\n\nResolved aliases: {aliases}\n\n")
        result.aliases = aliases
        return result


class OpenAIExtenderConfig(BaseModel, ChatPrompt):
    """Allow outputs over the OpenAI output token limit."""

    api_completion_token_limit: int
    max_extensions: int

    @field_validator("api_completion_token_limit", "max_extensions")
    @classmethod
    def must_be_positive(cls, value, info: FieldValidationInfo):
        if value <= 0:
            raise ValueError(f"{info.field_name} must be greater than zero")
        return value

    def extend(self, client: OpenAI, settings: dict, system: OpenAIChatPrompt,
               input: str, alias_resolver: OpenAIAliasResolverConfig, **kwargs
        ) -> str:
        """Extract up to the limit, left-truncate the input, try again until done."""

        delimiters = kwargs.get("delimiters")
        if settings.get("max_tokens"):
            self.api_completion_token_limit = min(self.api_completion_token_limit, 
                                                  settings["max_tokens"])
        output = OpenAIChatOutput(content="", completion_tokens=0)
        tail = input
        num_extensions = 0
        existing_aliases = kwargs.pop("preset_aliases")
        while num_extensions <= self.max_extensions:

            if alias_resolver:
                result = alias_resolver.execute_and_resolve(client, settings, system,
                                                            tail, 
                                                            preset_aliases=existing_aliases,
                                                            **kwargs)
                existing_aliases = result.aliases
            else:
                result = self.execute(client, settings, system, tail, 
                                      preset_aliases=existing_aliases, **kwargs)

            # If we're doing redactions here:
            if delimiters:
                # Remove any incomplete redactions
                last_opening = result.content.rfind(delimiters[0])
                last_closing = result.content.rfind(delimiters[1])
                if last_closing < last_opening:
                    result.content = result.content[:last_opening]

            output.content += result.content + " <suture> "
            output.completion_tokens += result.completion_tokens
            output.aliases = existing_aliases

            if result.completion_tokens == self.api_completion_token_limit:
                num_extensions += 1
                alignment = partial_ratio_alignment(tail, result.content)
                tail = tail[alignment.src_end:]
            else:
                break

        return output
    

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

    extender: OpenAIExtenderConfig | None = None

    def invoke(
        self, client: OpenAI, input: AnyChatInput | Sequence[AnyChatInput], **kwargs
    ) -> OpenAIChatOutput:

        """Invoke the chat."""
        settings = self.model_dump()
        settings.pop("method")
        settings.pop("system")
        settings.pop("extender")
        # Remove any setting whose value is `None`
        settings = {k: v for k, v in settings.items() if v is not None}

        resolver = kwargs.get("resolver")
        if self.extender:
            logger.debug("Starting extender")
            output = self.extender.extend(client, settings, self.system,
                                          input, resolver, **kwargs)
        elif resolver:
            logger.debug("Starting resolver")
            output = resolver.execute_and_resolve(client, settings, self.system,
                                                  input, **kwargs)
        else:
            logger.debug("Starting vanilla chat")
            output = self.system.execute(client, settings, input, **kwargs)

        logger.debug(f"\n\nChat output: {output}\n\n")

        # ACW: For now I'm just returning the content, we'll need to pass 
        # aliases somehow for other docs?
        return output.content
    

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
