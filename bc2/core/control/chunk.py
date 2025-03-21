import time
from typing import Generic, Literal, Type, TypeVar, Union, cast

from pydantic import BaseModel, PositiveInt

from ..common.align import residual
from ..common.context import Context
from ..common.runtime import RuntimeConfig
from ..common.text import RedactedText, Text
from ..common.type_util import (
    get_bindable_parameters,
    inspect_all_params,
    inspect_required_params,
    inspect_return_type,
)
from ..common.types import NameToReplacementMap
from ..parse import ParseConfig
from ..redact import RedactConfig
from .compose import ComposeConfig

AnyChunkableConfig = Union[
    ParseConfig,
    RedactConfig,
    ComposeConfig,
]


T = TypeVar("T", bound=RedactedText | Text)


class ChunkConfig(BaseModel):
    engine: Literal["$chunk"] = "$chunk"
    processor: AnyChunkableConfig
    max_iterations: PositiveInt | None = None
    timeout: PositiveInt | None = None

    @property
    def driver(self) -> "ChunkDriver":
        return_t = inspect_return_type(self.processor.driver)
        return ChunkDriver[return_t](self, return_t)  # type: ignore[valid-type]


class ChunkDriver(Generic[T]):
    def __init__(
        self,
        config: ChunkConfig,
        return_t: Type[T],
    ):
        self.config = config
        self.return_type = return_t

    def validate(self, runtime_config: RuntimeConfig):
        """Validate the chunk configuration."""
        return_t = inspect_return_type(self.config.processor.driver)
        if return_t != Text and return_t != RedactedText:
            raise TypeError(f"Unsupported processor return type: {return_t}")

        all_params = inspect_all_params(self.config.processor.driver)
        # Ensure first argument is a Text object
        first_input_t = list(all_params.values())[0]
        if first_input_t != Text:
            raise TypeError(f"Unsupported processor input type: {first_input_t}")

        # Ensure we have all required parameters for the input
        required_p = inspect_required_params(self.config.processor.driver)
        bindable = get_bindable_parameters(self.config.processor.driver, runtime_config)
        missing = set(required_p.keys()) - set(bindable.keys())
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")

    def _get_initial_state(self, initial: str) -> T:
        """Get the empty value for the return type of the pipe.

        Returns:
            T: The empty value for the return type (Text, or RedactedText)

        Raises:
            ValueError: If the return type is not supported
        """
        if self.return_type == RedactedText:
            # Set the initial delimiters to empty, they will be updated
            # when the first chunk is processed.
            return cast(T, RedactedText("", initial, delimiters=""))
        elif self.return_type == Text:
            return cast(T, Text(""))
        else:
            raise ValueError(f"Unsupported return type: {self.return_type}")

    def __call__(
        self,
        input: Text,
        context: Context,
        runtime_config: RuntimeConfig | None = None,
    ) -> T:
        """Run the processor on the given input in a loop.

        The loop will terminate under any of the following conditions:
            1. The processor produces untruncated output;
            2. There's no more input (probably happens at the same time as 1);
            3. The maximum number of iterations is reached;
            4. The timeout is reached.

        Args:
            input (Text): The input text to process
            context (Context): The context object
            **kwargs: Additional keyword arguments to pass to the processor

        Returns:
            T: The result of processing the input text
        """
        # Get the basic chunking configuration
        timeout = self.config.timeout
        max_iterations = self.config.max_iterations
        f = self.config.processor.driver

        # Set the initial state of the chunker
        iteration = 0
        t0 = time.monotonic()
        remainder = input
        output = self._get_initial_state(input.text)

        while remainder.text:
            iteration += 1

            # Run the processor on the current chunk
            filtered_kwargs = get_bindable_parameters(f, runtime_config or {})
            new_output = cast(T, f(remainder, context, **filtered_kwargs))
            output = self._merge_output(output, new_output)

            # If the output is not truncated, we're done!
            if not output.truncated:
                break

            # Enforce max iterations policy
            if max_iterations and iteration >= max_iterations:
                break

            # Enforce timeout policy
            if timeout and time.monotonic() - t0 >= timeout:
                break

            # No other policies apply, so we will prepare a new
            # chunk and continue.
            remainder.text = self._compute_residual(remainder, new_output)

            # It may be that even though we didn't catch the truncation earlier,
            # the remainder is empty. In that case, we're done.
            if not remainder.text:
                break

        return output

    def _merge_output(self, existing: T, addition: T, separator: str = " ") -> T:
        """Merge two textual objects together.

        Works for both Text and RedactedText.

        Args:
            existing (T): The existing text object
            addition (T): The additional text object
            separator (str, optional): The separator to use when merging text.

        Returns:
            T: A new text object that is the result of merging the two inputs
        """
        if self.return_type == Text:
            return cast(
                T,
                Text(
                    self._merge_strings(
                        cast(Text, existing).text,
                        cast(Text, addition).text,
                        separator=separator,
                    ),
                    truncated=addition.truncated,
                ),
            )
        elif self.return_type == RedactedText:
            existing_t = cast(RedactedText, existing)
            addition_t = cast(RedactedText, addition)
            return cast(
                T,
                RedactedText(
                    # 1. Stitch the redacted text together.
                    self._merge_strings(
                        existing_t.redacted,
                        addition_t.redacted,
                        separator=separator,
                    ),
                    # 2. The initial text should be *complete*, the addition isn't!
                    existing_t.original,
                    # 3. The delimiters are initially empty; fill in from first chunk.
                    delimiters=existing_t.delimiters or addition_t.delimiters,
                    # 4. Merge the placeholder maps.
                    aliases=NameToReplacementMap.merge(
                        existing_t.aliases, addition_t.aliases
                    ),
                    # 4. Set truncation according to latest data.
                    truncated=addition_t.truncated,
                ),
            )
        else:
            raise ValueError(f"Unsupported return type: {self.return_type}")

    def _merge_strings(self, existing: str, addition: str, separator: str = " ") -> str:
        """Merge two strings together.

        Args:
            existing (str): The existing string
            addition (str): The additional string
            separator (str, optional): The separator to use when merging text.

        Returns:
            str: A new string that is the result of merging the two inputs
        """
        if existing:
            existing += separator
        return existing + addition

    def _compute_residual(self, old: Text, new: T, window_size: int = 10_000) -> str:
        """Compute the remainder text after processing a chunk.

        Args:
            old (Text): The original text
            new (T): The new text object
            window_size (int, optional): The window to use for aligning segments.

        Returns:
            str: The remaining text to segment.
        """
        old_text = old.text
        new_text = ""
        if self.return_type == Text:
            new_text = cast(Text, new).text
        elif self.return_type == RedactedText:
            new_text = cast(RedactedText, new).redacted
        else:
            raise ValueError(f"Unsupported return type: {self.return_type}")
        return residual(old_text, new_text, needle_size=window_size)
