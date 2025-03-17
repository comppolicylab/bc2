import time
from typing import Callable, Literal, Protocol, Tuple

from pydantic import BaseModel

from ..common.context import Context
from ..common.text import RedactedText, Text
from ..common.types import NameToReplacementMap

AnyRedactDriver = Callable[[Text, Context, NameToReplacementMap | None], RedactedText]


class AnyRedactConfig(Protocol):
    driver: AnyRedactDriver


class ChunkConfig(BaseModel):
    control: Literal["control:chunk"]
    processor: AnyRedactConfig
    chunk_size: int | None = None
    max_iterations: int | None = None
    timeout: int | None = None

    @property
    def driver(self) -> "ChunkDriver":
        return ChunkDriver(self)


class ChunkDriver:
    def __init__(self, config: ChunkConfig):
        self.config = config

    def __call__(
        self,
        input: Text,
        context: Context,
        placeholders: NameToReplacementMap | None = None,
    ) -> RedactedText:
        # Get the config for chunking
        timeout = self.config.timeout
        max_iterations = self.config.max_iterations
        chunk_size = self.config.chunk_size
        f = self.config.processor.driver

        # Set the initial state of the chunker
        iteration = 0
        t0 = time.monotonic()
        remainder = input
        output = RedactedText("", "", "[]")

        while remainder.text:
            iteration += 1

            next_chunk, remainder = self._chunk(remainder, chunk_size)

            new_output = f(next_chunk, context, placeholders)
            output = self._merge_output(output, new_output)

            # Enforce max iterations policy
            if max_iterations and iteration >= max_iterations:
                break

            # Enforce timeout policy
            if timeout and time.monotonic() - t0 >= timeout:
                break

        return output

    def _chunk(self, input: Text, size: int | None) -> Tuple[Text, Text]:
        if not size:
            return input, Text("")
        # TODO - smarter chunking so we don't split in a weird place
        return Text(input.text[:size]), Text(input.text[size:])

    def _merge_output(
        self, existing: RedactedText, addition: RedactedText
    ) -> RedactedText:
        # TODO - validate delimiters are consistent
        # TODO - smarter stitching together of redacted text?
        return RedactedText(
            existing.redacted + addition.redacted,
            existing.original + addition.original,
            addition.delimiters,
        )
