from io import BytesIO
from unittest.mock import MagicMock, patch

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

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


def test_document_intelligence_uses_api_key_credential():
    with patch("bc2.core.analyze.azuredi.DocumentIntelligenceClient") as client_cls:
        AzureDIAnalyze(
            AzureDIAnalyzeConfig(
                endpoint="https://example.cognitiveservices.azure.com",
                api_key="test-key",
            )
        )

    _, kwargs = client_cls.call_args
    assert isinstance(kwargs["credential"], AzureKeyCredential)


def test_document_intelligence_uses_identity_when_api_key_missing():
    with (
        patch("bc2.core.analyze.azuredi.DefaultAzureCredential") as cred_cls,
        patch("bc2.core.analyze.azuredi.DocumentIntelligenceClient") as client_cls,
    ):
        credential = MagicMock(spec=DefaultAzureCredential)
        cred_cls.return_value = credential
        AzureDIAnalyze(
            AzureDIAnalyzeConfig(
                endpoint="https://example.cognitiveservices.azure.com",
            )
        )

    cred_cls.assert_called_once_with()
    _, kwargs = client_cls.call_args
    assert kwargs["credential"] is credential
