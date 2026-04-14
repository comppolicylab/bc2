import logging
from functools import cached_property
from io import BytesIO
from typing import Literal

from azure.ai.documentintelligence import AnalyzeResult, DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel, Field

from ..common.file import MemoryFile
from ..common.json import date_aware_json_dumps
from ..common.preprocess import register_preprocessor
from .base import BaseAnalyzeDriver

logger = logging.getLogger(__name__)


class AzureDIAnalyzeConfig(BaseModel):
    """Azure DI Analyze config."""

    engine: Literal["analyze:azuredi"]
    endpoint: str
    api_key: str
    # Todo: Add api_version, since we'll need to match what's on GovCloud,
    # which has more limited releases than commerical Azure.
    document_model: str = Field("prebuilt-read")
    locale: str = Field("en-US")

    @cached_property
    def driver(self) -> "AzureDIAnalyze":
        return AzureDIAnalyze(self)


class AzureDIAnalyze(BaseAnalyzeDriver):
    def __init__(self, config: AzureDIAnalyzeConfig):
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

    def analyze(self, doc: BytesIO) -> MemoryFile:
        analysis = self._analyze_document(doc)
        # Serialize the analysis result
        result = date_aware_json_dumps(analysis.to_dict())
        # Set an explicit mime type, so that subsequent steps will be able to load
        # it as a structured `AnalyzeResult` object.
        return MemoryFile(
            content=result.encode("utf-8"), mime_type="application/x-analyze-result"
        )

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
