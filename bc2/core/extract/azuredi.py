import logging
from functools import cached_property
from io import BytesIO
from typing import Literal, Tuple

from azure.ai.formrecognizer import AnalyzeResult, DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel, Field

from ..common.file import MemoryFile
from .base import BaseExtractDriver, register_preprocessor

logger = logging.getLogger(__name__)


class AzureDIExtractConfig(BaseModel):
    """Azure DI Extract config."""

    engine: Literal["extract:azuredi"]
    endpoint: str
    api_key: str
    # Todo: Add api_version, since we'll need to match what's on GovCloud,
    # which has more limited releases than commerical Azure.
    document_model: str = Field("prebuilt-read")
    labels: list[str] | None = Field(None)
    min_confidence: float = Field(0.04)
    locale: str = Field("en-US")

    @cached_property
    def driver(self) -> "AzureDIExtract":
        return AzureDIExtract(self)


class AzureDIExtract(BaseExtractDriver):
    def __init__(self, config: AzureDIExtractConfig):
        self.config = config
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=config.endpoint,
            credential=AzureKeyCredential(config.api_key),
        )

    @register_preprocessor(r"^application/pdf")
    def convert_pdf(self, file: MemoryFile) -> BytesIO:
        file.buffer.seek(0)
        return file.buffer

    @register_preprocessor(r"^image/tiff")
    def convert_tiff(self, file: MemoryFile) -> BytesIO:
        file.buffer.seek(0)
        return file.buffer

    def extract(self, doc: BytesIO) -> Tuple[str, bool]:
        result = self._extract_text_from_doc(doc) or ""
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

    def _extract_text_from_doc(
        self, doc: BytesIO, chunk_separator: str = "\n\n"
    ) -> str | None:
        """Extract text from a PDF.

        Args:
            doc (BytesIO): Stream containing the PDF.

        Returns:
            str: The text, if text was found.
        """
        analysis = self._analyze_document(doc)
        chunks = self._extract_document_content(analysis, self.config.labels)

        if not chunks:
            logger.warning("No text found in document!")
            return None

        return chunk_separator.join(chunks)

    def _analyze_document(
        self,
        doc: BytesIO,
    ) -> AnalyzeResult:
        """Run a PDF through Azure document analysis.

        Args:
            doc (BytesIO): The PDF to analyze.

        Returns:
            AnalyzeResult: Results from Azure document analysis.
        """
        logger.info(f"Running analysis with model {self.config.document_model} ...")

        # Run analysis on the document using the remote service.
        doc.seek(0)
        docbytes = doc.read()
        poller = self.document_analysis_client.begin_analyze_document(
            self.config.document_model,
            document=docbytes,
            locale=self.config.locale,
        )
        return poller.result()
