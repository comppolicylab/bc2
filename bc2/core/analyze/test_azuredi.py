from io import BytesIO
from unittest.mock import MagicMock

from ..common.usage import (
    create_usage_tracker,
    usage_operation,
    usage_tracking,
)
from .azuredi import AzureDIAnalyze, AzureDIAnalyzeConfig


def test_document_intelligence_records_page_usage():
    driver = AzureDIAnalyze.__new__(AzureDIAnalyze)
    driver.config = AzureDIAnalyzeConfig(
        endpoint="https://example.cognitiveservices.azure.com",
        api_key="test",
    )
    result = MagicMock()
    result.pages = [MagicMock(), MagicMock(), MagicMock()]
    poller = MagicMock()
    poller.result.return_value = result
    driver.di_client = MagicMock()
    driver.di_client.begin_analyze_document.return_value = poller
    created = create_usage_tracker({"report_usage": True})
    assert created is not None
    report, tracker = created

    with usage_tracking(tracker), usage_operation("analyze:azuredi"):
        driver._analyze_document(BytesIO(b"document"))

    call = report["calls"][0]
    assert call["provider"] == "azure"
    assert call["service"] == "document_intelligence"
    assert call["operation"] == "analyze:azuredi"
    assert call["model"] == "prebuilt-read"
    assert call["usage"] == {"pages": 3}
