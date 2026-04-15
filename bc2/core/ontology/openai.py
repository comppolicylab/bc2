import logging
from functools import cached_property
from typing import Literal

from azure.ai.documentintelligence.models import AnalyzeResult
from openai import OpenAI

from ..common.file import MemoryFile
from ..common.json import date_aware_json_load
from ..common.ontology import (
    PoliceReport,
    PoliceReportParseResult,
    SourceChunk,
    SourceChunkBoundingRegion,
    SourceChunkSpan,
)
from ..common.openai import OpenAIChatConfig, OpenAIConfig
from ..common.preprocess import register_preprocessor
from .base import BaseOntologyDriver

logger = logging.getLogger(__name__)


class OpenAIOntologyConfig(OpenAIConfig):
    """OpenAI Ontology config."""

    engine: Literal["ontology:openai"] = "ontology:openai"
    generator: OpenAIChatConfig[PoliceReport]

    @cached_property
    def driver(self) -> "OpenAIOntologyDriver":
        return OpenAIOntologyDriver(self)


class OpenAIOntologyDriver(BaseOntologyDriver[AnalyzeResult]):
    def __init__(self, config: OpenAIOntologyConfig):
        self.config = config
        self.client: OpenAI = config.client.init()

    @register_preprocessor(r"^application/x-analyze-result")
    def load_analyze_result(self, file: MemoryFile) -> AnalyzeResult:
        file.buffer.seek(0)
        content = date_aware_json_load(file.buffer)
        return AnalyzeResult.from_dict(content)

    def extract(self, data: AnalyzeResult) -> PoliceReportParseResult:
        xml = _format_analyze_result(data)
        user_message = f"XML DOCUMENT\n===\n{xml}"

        result = self.config.generator.invoke(
            self.client, user_message, response_format=PoliceReport
        )

        report = result.parsed
        if report is None:
            raise ValueError(
                "OpenAI returned no structured output for ontology extraction."
            )

        source_chunks = _build_source_chunks(data)

        return PoliceReportParseResult(report=report, chunks=source_chunks)


def _format_analyze_result(analyze_result: AnalyzeResult) -> str:
    """Format an AnalyzeResult as XML for LLM consumption.

    Args:
        analyze_result: The analyze result to format.

    Returns:
        A string containing the XML.
    """
    chunks = list[str]()
    for idx, p in enumerate(analyze_result.paragraphs or []):
        chunks.append(f'<P id="{idx}">{p.content}</P>')
    return f"<CONTENT>{''.join(chunks)}</CONTENT>"


def _build_source_chunks(analyze_result: AnalyzeResult) -> list[SourceChunk]:
    """Build source chunks from an AnalyzeResult's paragraphs.

    Each paragraph becomes a SourceChunk with normalized bounding regions.

    Args:
        analyze_result: The analyze result to build chunks from.

    Returns:
        A list of SourceChunk objects.
    """
    source_chunks = list[SourceChunk]()
    for p in analyze_result.paragraphs or []:
        regions = list[SourceChunkBoundingRegion]()
        for region in p.bounding_regions or []:
            page_idx = next(
                (
                    i
                    for i, page in enumerate(analyze_result.pages)
                    if page.page_number == region.page_number
                ),
                None,
            )
            if page_idx is None:
                raise ValueError(
                    f"Page {region.page_number} not found in analyze result"
                )
            page_width = analyze_result.pages[page_idx].width or 1
            page_height = analyze_result.pages[page_idx].height or 1
            polygon = region.polygon
            points = [
                (polygon[i] / page_width, polygon[i + 1] / page_height)
                for i in range(0, len(polygon), 2)
            ]
            regions.append(SourceChunkBoundingRegion(page=page_idx, points=points))
        source_chunks.append(
            SourceChunk(
                spans=[
                    SourceChunkSpan(offset=span.offset, length=span.length)
                    for span in p.spans or []
                ],
                regions=regions,
                content=p.content,
            )
        )
    return source_chunks
