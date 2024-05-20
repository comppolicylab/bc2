import logging
from io import BytesIO
from typing import Literal

from azure.ai.formrecognizer import AnalyzeResult, DocumentAnalysisClient
from azure.ai.formrecognizer._models import DocumentField
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel, Field
from pypdf import PdfReader

from ..common.file import MemoryFile
from ..common.text import Text
from .base import BaseExtractDriver, EmptyExtractionError

logger = logging.getLogger(__name__)


class AzureDIExtractConfig(BaseModel):
    """Azure DI Extract config."""

    engine: Literal["azuredi"]
    endpoint: str
    key: str
    document_model: str = Field("prebuilt-read")
    min_confidence: float = Field(0.04)
    narrative_field: str = Field("narrative")
    locale: str = Field("en-US")


class AzureDIExtract(BaseExtractDriver):
    def __init__(self, config: AzureDIExtractConfig):
        self.config = config
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=config.endpoint,
            credential=AzureKeyCredential(config.key),
        )

    def __call__(self, file: MemoryFile) -> Text:
        txt = self.extract_narrative_from_pdf(file.buffer)
        if not txt:
            raise EmptyExtractionError("No narrative found in document!")
        return Text(txt)

    def extract_narrative_fields(
        self,
        analysis: list[AnalyzeResult],
    ) -> list[DocumentField]:
        """Extract the narrative from the analysis results.

        Args:
            analysis (list[AnalyzeResult]): Results, one for each page
        """
        logger.info("Inspecting analysis result to find narrative(s) ...")
        logger.debug(
            "Looking for narrative field `%s` with confidence >= %f ...",
            self.config.narrative_field,
            self.config.min_confidence,
        )

        narratives = list[str]()
        # Look through each page of the analysis results and find any narratives.
        for page in analysis:
            for doc in page.documents:
                narrative = doc.fields.get(self.config.narrative_field)
                confidence = getattr(narrative, "confidence", 0.0) or 0.0
                if narrative and confidence >= self.config.min_confidence:
                    narratives.append(narrative)
        return narratives

    def concat_fields(self, fields: list[DocumentField], sep: str = "\n\n") -> str:
        """Join the text content from a set of text fields.

        Args:
            fields (list[DocumentField]): List of document fields.

        Returns:
            str: The joined text
        """
        txt = ""
        for field in fields:
            if field.content:
                if txt:
                    txt += sep
                txt += field.content
        return txt

    def extract_narrative_from_pdf(self, doc: BytesIO) -> str | None:
        """Extract the narrative from a PDF.

        Args:
            doc (BytesIO): Stream containing the PDF.

        Returns:
            str: The narrative, if one was found.
        """
        analysis = self.analyze_document(doc)
        fields = self.extract_narrative_fields(analysis)

        if not fields:
            logger.warning("No narrative found in document!")
            return None

        return self.concat_fields(fields)

    def analyze_document(
        self,
        doc: BytesIO,
    ) -> list[AnalyzeResult]:
        """Run a PDF through Azure document analysis.

        Args:
            doc (BytesIO): The PDF to analyze.

        Returns:
            list[AnalyzeResult]: Results from Azure document analysis.
        """
        logger.info(f"Running analysis with model {self.config.document_model} ...")
        # We analyze each page separately because the FormRecognizer API doesn't
        # currently fully support entire document analysis. It just analyzes two
        # pages at a time, even if you request more.
        pages = len(PdfReader(doc).pages)
        results: list[AnalyzeResult] = [None] * pages

        # Run analysis on the document using the remote service.
        for i in range(pages):
            if results[i] is None:
                poller = self.document_analysis_client.begin_analyze_document(
                    self.config.document_model,
                    document=doc,
                    locale=self.config.locale,
                    pages=f"{i + 1}",
                )
                results[i] = poller.result()

        return results
