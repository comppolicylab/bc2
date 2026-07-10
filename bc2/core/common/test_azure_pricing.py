import io
import json

import pytest

from .azure_pricing import AzurePricingUnavailable, AzureRetailPricing


def _meter(
    name: str,
    price: float,
    unit: str = "1M",
    tier: float = 0,
) -> dict:
    return {
        "skuName": name,
        "meterName": f"{name} Tokens",
        "retailPrice": price,
        "unitOfMeasure": unit,
        "tierMinimumUnits": tier,
        "type": "Consumption",
    }


def test_estimate_openai_response_cost(monkeypatch):
    pricing = AzureRetailPricing()
    meters = [
        _meter("5.5 ShortCo inp Gl", 5.0),
        _meter("5.5 ShortCo cd inp Gl", 0.5),
        _meter("5.5 ShortCo opt Gl", 30.0),
    ]
    monkeypatch.setattr(
        pricing, "_get_prices", lambda _: (meters, "2026-07-10T00:00:00+00:00")
    )

    estimate = pricing.estimate(
        {
            "service": "responses",
            "model": "gpt-5.5",
            "usage": {
                "input_tokens": 1_000_000,
                "cached_input_tokens": 100_000,
                "output_tokens": 10_000,
            },
        },
        {
            "azure_region": "eastus",
            "azure_deployment_type": "global",
            "azure_context_tier": "short",
        },
    )

    assert estimate["estimated_cost"] == pytest.approx(4.85)
    assert estimate["currency"] == "USD"
    assert len(estimate["components"]) == 3


def test_estimate_document_intelligence_read_cost(monkeypatch):
    pricing = AzureRetailPricing()
    meter = {
        "skuName": "S0",
        "meterName": "S0 Read Pages",
        "retailPrice": 1.5,
        "unitOfMeasure": "1K",
        "tierMinimumUnits": 0,
        "type": "Consumption",
    }
    monkeypatch.setattr(
        pricing, "_get_prices", lambda _: ([meter], "2026-07-10T00:00:00+00:00")
    )

    estimate = pricing.estimate(
        {
            "service": "document_intelligence",
            "model": "prebuilt-read",
            "features": [],
            "usage": {"pages": 25},
        },
        {"azure_region": "eastus"},
    )

    assert estimate["estimated_cost"] == pytest.approx(0.0375)


def test_estimate_embedding_cost(monkeypatch):
    pricing = AzureRetailPricing()
    meter = _meter("text-embedding-3-large-glbl", 0.00013, "1K")
    monkeypatch.setattr(
        pricing, "_get_prices", lambda _: ([meter], "2026-07-10T00:00:00+00:00")
    )

    estimate = pricing.estimate(
        {
            "service": "embeddings",
            "model": "text-embedding-3-large",
            "usage": {"input_tokens": 2_000},
        },
        {"azure_region": "eastus", "azure_deployment_type": "global"},
    )

    assert estimate["estimated_cost"] == pytest.approx(0.00026)


def test_missing_region_fails_without_fetching_prices():
    pricing = AzureRetailPricing()

    with pytest.raises(AzurePricingUnavailable, match="azure_region"):
        pricing.estimate(
            {
                "service": "responses",
                "model": "gpt-4.1",
                "usage": {"input_tokens": 10},
            },
            {},
        )


def test_region_falls_back_to_usage_call(monkeypatch):
    pricing = AzureRetailPricing()
    monkeypatch.setattr(
        pricing,
        "_estimate_openai_tokens",
        lambda call, runtime_config, region: {
            "estimated_cost": 0.0,
            "currency": "USD",
        },
    )

    estimate = pricing.estimate(
        {
            "service": "responses",
            "model": "gpt-4.1",
            "azure_region": "eastus",
            "usage": {"input_tokens": 10},
        },
        {},
    )

    assert estimate["region"] == "eastus"


def test_ambiguous_meter_fails_gracefully(monkeypatch):
    pricing = AzureRetailPricing()
    meters = [
        _meter("4.1 Inp glbl", 2.0, "1K"),
        _meter("4.1 Inp global", 3.0, "1K"),
    ]
    monkeypatch.setattr(
        pricing, "_get_prices", lambda _: (meters, "2026-07-10T00:00:00+00:00")
    )

    with pytest.raises(AzurePricingUnavailable, match="ambiguous"):
        pricing.estimate(
            {
                "service": "responses",
                "model": "gpt-4.1",
                "usage": {"input_tokens": 10},
            },
            {"azure_region": "eastus"},
        )


def test_retail_prices_are_cached(monkeypatch):
    pricing = AzureRetailPricing()
    requests = 0

    def fake_urlopen(url, timeout):
        nonlocal requests
        requests += 1
        return io.BytesIO(
            json.dumps({"Items": [{"meterName": "test"}]}).encode("utf-8")
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    first = pricing._get_prices("productName eq 'test'")
    second = pricing._get_prices("productName eq 'test'")

    assert first == second
    assert requests == 1
