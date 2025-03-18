import time
from typing import Callable, Literal, Protocol

from pydantic import BaseModel, PositiveInt

from ..common.align import residual
from ..common.context import Context
from ..common.text import RedactedText, Text
from ..common.types import NameToReplacementMap

AnyRedactDriver = Callable[[Text, Context, NameToReplacementMap | None], RedactedText]
AnyTextDriver = Callable[[Text, Context], Text]

AnyChunkableDriver = AnyRedactDriver | AnyTextDriver


class AnyRedactConfig(Protocol):
    driver: AnyRedactDriver


class ChunkConfig(BaseModel):
    control: Literal["control:chunk"]
    processor: AnyRedactConfig
    max_iterations: PositiveInt | None = None
    timeout: PositiveInt | None = None

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
        f = self.config.processor.driver

        # Set the initial state of the chunker
        iteration = 0
        t0 = time.monotonic()
        remainder = input
        output = RedactedText("", "", "[]")

        while remainder.text:
            iteration += 1

            # Run the processor on the current chunk
            new_output = f(remainder, context, placeholders)
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
            remainder.text = residual(remainder.text, new_output.redacted)

            # It may be that even though we didn't catch the truncation earlier,
            # the remainder is empty. In that case, we're done.
            if not remainder.text:
                break
            output.redacted += " "

        return output

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
