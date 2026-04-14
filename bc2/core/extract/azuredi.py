import logging
from functools import cached_property
from typing import Literal, Tuple

from azure.ai.documentintelligence import AnalyzeResult
from pydantic import BaseModel, Field

from ..common.file import MemoryFile
from ..common.json import date_aware_json_load
from ..common.preprocess import register_preprocessor
from .base import BaseExtractDriver

logger = logging.getLogger(__name__)


class AzureDIExtractConfig(BaseModel):
    """Azure DI Extract config."""

    engine: Literal["extract:azuredi"]
    labels: list[str] | None = Field(None)
    min_confidence: float = Field(0.04)

    @cached_property
    def driver(self) -> "AzureDIExtract":
        return AzureDIExtract(self)


class AzureDIExtract(BaseExtractDriver[AnalyzeResult]):
    def __init__(self, config: AzureDIExtractConfig):
        self.config = config

    @register_preprocessor(r"^application/x-analyze-result")
    def load_analyze_result(self, file: MemoryFile) -> AnalyzeResult:
        file.buffer.seek(0)
        # Parse JSON and inflate the AnalyzeResult object.
        content = date_aware_json_load(file.buffer)
        return AnalyzeResult.from_dict(content)

    def extract(self, analysis: AnalyzeResult) -> Tuple[str, bool]:
        result = self._extract_text_from_analysis(analysis) or ""
        return result, False

    def _extract_document_content(
        self,
        analysis: AnalyzeResult,
        labels: list[str] | None = None,
    ) -> list[str]:
        """Extract text spans from the analysis results.

        Args:
            analysis (list[AnalyzeResult]): Results, one for each page
            labels (list[str], optional): Filter for specific fields. Defaults to None.
        """
        logger.info("Inspecting analysis result to find text ...")
        if labels:
            logger.debug(
                "Looking for text in fields (`%s`) with confidence >= %f ...",
                ", ".join(labels),
                self.config.min_confidence,
            )
        else:
            logger.debug(
                "No labels filter set, so extracting all text ...",
            )

        chunks = list[str]()
        labels_filter = set(labels) if labels else None
        # Look through each page of the analysis results and find any text.
        # If a labels filter was passed, use that to extract only labeled regions.
        if labels_filter:
            for doc in analysis.documents or []:
                for label, field in doc.fields.items():
                    if label in labels_filter:
                        confidence = getattr(field, "confidence", 0.0) or 0.0
                        if (
                            field
                            and field.content
                            and confidence >= self.config.min_confidence
                        ):
                            chunks.append(field.content)
        # When no filter was passed, get text from paragraphs in sequence instead.
        else:
            for para in analysis.paragraphs or []:
                if para.content:
                    chunks.append(para.content)
        return chunks

    def _extract_text_from_analysis(
        self, analysis: AnalyzeResult, chunk_separator: str = "\n\n"
    ) -> str | None:
        """Extract text from an analysis result.

        Args:
            analysis (AnalyzeResult): Analysis result from Azure DI

        Returns:
            str: The text, if text was found.
        """
        chunks = self._extract_document_content(analysis, self.config.labels)

        if not chunks:
            logger.warning("No text found in document!")
            return None

        return chunk_separator.join(chunks)
