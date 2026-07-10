from __future__ import annotations

import json
import re
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

AZURE_RETAIL_PRICES_URL = "https://prices.azure.com/api/retail/prices"
DEFAULT_CACHE_TTL_SECONDS = 24 * 60 * 60


class AzurePricingUnavailable(Exception):
    """Raised when an Azure retail price cannot be determined unambiguously."""


@dataclass
class _CacheEntry:
    expires_at: float
    fetched_at: str
    items: list[dict[str, Any]]


class AzureRetailPricing:
    """Fetch and cache public Azure retail prices."""

    def __init__(self, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS):
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    def estimate(
        self, call: dict[str, Any], runtime_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Estimate the cost of one Azure service call."""
        region = runtime_config.get("azure_region")
        if not region:
            raise AzurePricingUnavailable(
                "azure_region is required to look up Azure retail pricing"
            )

        service = call.get("service")
        if service == "responses":
            result = self._estimate_openai_tokens(call, runtime_config, region)
        elif service == "embeddings":
            result = self._estimate_openai_tokens(call, runtime_config, region)
        elif service == "document_intelligence":
            result = self._estimate_document_intelligence(call, region)
            result["sku"] = "S0"
        else:
            raise AzurePricingUnavailable(f"unsupported Azure service: {service}")

        result["region"] = region
        if service in {"responses", "embeddings"}:
            result["deployment_type"] = runtime_config.get(
                "azure_deployment_type", "global"
            )
            result["context_tier"] = runtime_config.get("azure_context_tier", "short")
        return result

    def _estimate_openai_tokens(
        self,
        call: dict[str, Any],
        runtime_config: dict[str, Any],
        region: str,
    ) -> dict[str, Any]:
        model = call.get("model")
        if not model:
            raise AzurePricingUnavailable("OpenAI model was not reported")

        is_embedding = call.get("service") == "embeddings"
        search_term = "embedding" if is_embedding else _model_search_term(model)
        odata_filter = (
            "contains(productName, 'OpenAI') "
            f"and armRegionName eq '{_odata_escape(region)}' "
            f"and contains(skuName, '{_odata_escape(search_term)}')"
        )
        items, fetched_at = self._get_prices(odata_filter)
        deployment_type = runtime_config.get("azure_deployment_type", "global")
        context_tier = runtime_config.get("azure_context_tier", "short")
        usage = call.get("usage", {})

        components: list[dict[str, Any]] = []
        input_tokens = int(usage.get("input_tokens") or 0)
        cached_tokens = int(usage.get("cached_input_tokens") or 0)
        regular_input_tokens = max(0, input_tokens - cached_tokens)
        output_tokens = int(usage.get("output_tokens") or 0)

        if is_embedding and input_tokens:
            meter = _select_embedding_meter(
                items,
                model=model,
                deployment_type=deployment_type,
            )
            components.append(_price_tokens(input_tokens, meter, "input"))
            return _cost_result(components, fetched_at)

        if regular_input_tokens:
            meter = _select_openai_meter(
                items,
                model=model,
                kind="input",
                deployment_type=deployment_type,
                context_tier=context_tier,
            )
            components.append(_price_tokens(regular_input_tokens, meter, "input"))
        if cached_tokens:
            meter = _select_openai_meter(
                items,
                model=model,
                kind="cached_input",
                deployment_type=deployment_type,
                context_tier=context_tier,
            )
            components.append(_price_tokens(cached_tokens, meter, "cached_input"))
        if output_tokens:
            meter = _select_openai_meter(
                items,
                model=model,
                kind="output",
                deployment_type=deployment_type,
                context_tier=context_tier,
            )
            components.append(_price_tokens(output_tokens, meter, "output"))

        if not components:
            raise AzurePricingUnavailable("no billable token usage was reported")
        return _cost_result(components, fetched_at)

    def _estimate_document_intelligence(
        self, call: dict[str, Any], region: str
    ) -> dict[str, Any]:
        model = str(call.get("model") or "")
        features = call.get("features") or []
        if model != "prebuilt-read":
            raise AzurePricingUnavailable(
                f"unsupported Document Intelligence model: {model or '<unknown>'}"
            )
        if features:
            raise AzurePricingUnavailable(
                "Document Intelligence feature add-on pricing is not supported"
            )

        pages = int((call.get("usage") or {}).get("pages") or 0)
        if pages <= 0:
            raise AzurePricingUnavailable("no analyzed pages were reported")

        odata_filter = (
            "productName eq 'Azure Document Intelligence' "
            f"and armRegionName eq '{_odata_escape(region)}' "
            "and skuName eq 'S0'"
        )
        items, fetched_at = self._get_prices(odata_filter)
        matches = [
            item
            for item in items
            if item.get("meterName") == "S0 Read Pages"
            and item.get("type") == "Consumption"
            and float(item.get("tierMinimumUnits") or 0) == 0
        ]
        meter = _select_unique_price(matches, "S0 Read Pages")
        component = _price_quantity(pages, meter, "pages")
        return _cost_result([component], fetched_at)

    def _get_prices(self, odata_filter: str) -> tuple[list[dict[str, Any]], str]:
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(odata_filter)
            if cached and cached.expires_at > now:
                return cached.items, cached.fetched_at

        params = urllib.parse.urlencode(
            {
                "api-version": "2023-01-01-preview",
                "$filter": odata_filter,
                "currencyCode": "USD",
            }
        )
        url: str | None = f"{AZURE_RETAIL_PRICES_URL}?{params}"
        items: list[dict[str, Any]] = []
        while url:
            with urllib.request.urlopen(url, timeout=10) as response:
                payload = json.load(response)
            items.extend(payload.get("Items") or [])
            url = payload.get("NextPageLink")

        fetched_at = datetime.now(timezone.utc).isoformat()
        entry = _CacheEntry(
            expires_at=now + self.cache_ttl_seconds,
            fetched_at=fetched_at,
            items=items,
        )
        with self._lock:
            self._cache[odata_filter] = entry
        return items, fetched_at


def _model_search_term(model: str) -> str:
    normalized = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model.lower())
    if normalized.startswith("gpt-"):
        return normalized.removeprefix("gpt-")
    return normalized


def _odata_escape(value: str) -> str:
    return value.replace("'", "''")


def _select_openai_meter(
    items: list[dict[str, Any]],
    *,
    model: str,
    kind: str,
    deployment_type: str,
    context_tier: str,
) -> dict[str, Any]:
    matches = []
    for item in items:
        if item.get("type") != "Consumption":
            continue
        name = f"{item.get('skuName', '')} {item.get('meterName', '')}".lower()
        if "batch" in name or re.search(r"\bpp\b", name):
            continue
        if not _matches_model_variant(name, model):
            continue
        if not _matches_deployment_type(name, deployment_type):
            continue
        if not _matches_context_tier(name, context_tier):
            continue

        is_cached = bool(re.search(r"\b(cached|cchd|cd)\b", name))
        is_input = bool(re.search(r"\b(input|inpt|inp)\b", name))
        is_output = bool(re.search(r"\b(output|outp|opt)\b", name))
        if kind == "input" and is_input and not is_cached:
            matches.append(item)
        elif kind == "cached_input" and is_input and is_cached:
            matches.append(item)
        elif kind == "output" and is_output and not is_cached:
            matches.append(item)

    return _select_unique_price(matches, f"OpenAI {kind}")


def _matches_model_variant(name: str, model: str) -> bool:
    normalized_model = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", model.lower())
    qualifiers = ("mini", "nano", "ft", "dev", "audio", "realtime", "codex", "pro")
    for qualifier in qualifiers:
        model_has_qualifier = bool(
            re.search(rf"(^|[-_. ]){qualifier}($|[-_. ])", normalized_model)
        )
        name_has_qualifier = bool(re.search(rf"(^|[-_. ]){qualifier}($|[-_. ])", name))
        if model_has_qualifier != name_has_qualifier:
            return False
    return "grader" not in name


def _select_embedding_meter(
    items: list[dict[str, Any]],
    *,
    model: str,
    deployment_type: str,
) -> dict[str, Any]:
    target = re.sub(r"[^a-z0-9]", "", model.lower())
    matches = []
    for item in items:
        if item.get("type") != "Consumption":
            continue
        name = f"{item.get('skuName', '')} {item.get('meterName', '')}".lower()
        compact_name = re.sub(r"[^a-z0-9]", "", name)
        if target not in compact_name:
            continue
        if "grader" in name or not _matches_deployment_type(name, deployment_type):
            continue
        matches.append(item)
    return _select_unique_price(matches, "OpenAI embedding input")


def _matches_deployment_type(name: str, deployment_type: str) -> bool:
    is_global = bool(re.search(r"\b(global|glbl|gl)\b", name))
    is_data_zone = bool(re.search(r"\b(data zone|dzn|dz)\b", name))
    is_regional = bool(re.search(r"\b(regional|regnl)\b", name))
    if deployment_type == "global":
        return is_global
    if deployment_type == "data_zone":
        return is_data_zone
    if deployment_type == "regional":
        return is_regional or (not is_global and not is_data_zone)
    raise AzurePricingUnavailable(
        "azure_deployment_type must be global, data_zone, or regional"
    )


def _matches_context_tier(name: str, context_tier: str) -> bool:
    is_short = "shortco" in name
    is_long = "longco" in name
    if not is_short and not is_long:
        return True
    if context_tier == "short":
        return is_short
    if context_tier == "long":
        return is_long
    raise AzurePricingUnavailable("azure_context_tier must be short or long")


def _select_unique_price(
    matches: list[dict[str, Any]], description: str
) -> dict[str, Any]:
    prices = {
        (float(item["retailPrice"]), str(item["unitOfMeasure"])) for item in matches
    }
    if not prices:
        raise AzurePricingUnavailable(f"no retail meter found for {description}")
    if len(prices) > 1:
        raise AzurePricingUnavailable(
            f"multiple retail meters matched {description}; pricing is ambiguous"
        )
    return matches[0]


def _price_tokens(tokens: int, meter: dict[str, Any], category: str) -> dict[str, Any]:
    return _price_quantity(tokens, meter, category)


def _price_quantity(
    quantity: int, meter: dict[str, Any], category: str
) -> dict[str, Any]:
    unit = str(meter["unitOfMeasure"])
    divisor = _unit_divisor(unit)
    unit_price = float(meter["retailPrice"])
    return {
        "category": category,
        "quantity": quantity,
        "meter_name": meter["meterName"],
        "unit_of_measure": unit,
        "unit_price": unit_price,
        "estimated_cost": quantity / divisor * unit_price,
    }


def _unit_divisor(unit: str) -> int:
    normalized = unit.upper()
    if normalized == "1K":
        return 1_000
    if normalized == "1M":
        return 1_000_000
    if normalized == "1":
        return 1
    raise AzurePricingUnavailable(f"unsupported Azure pricing unit: {unit}")


def _cost_result(components: list[dict[str, Any]], fetched_at: str) -> dict[str, Any]:
    return {
        "estimated_cost": sum(c["estimated_cost"] for c in components),
        "currency": "USD",
        "source": "azure-retail-prices",
        "pricing_fetched_at": fetched_at,
        "components": components,
    }
