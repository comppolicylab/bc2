from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from threading import Lock
from typing import Any, Iterator

from .azure_pricing import AzurePricingUnavailable, AzureRetailPricing

logger = logging.getLogger(__name__)

_current_tracker: ContextVar[UsageTracker | None] = ContextVar(
    "bc2_usage_tracker", default=None
)
_current_operation: ContextVar[str | None] = ContextVar(
    "bc2_usage_operation", default=None
)
_azure_pricing = AzureRetailPricing()


class UsageTracker:
    """Collect per-call service usage for a single pipeline run."""

    def __init__(
        self,
        report: dict[str, Any],
        runtime_config: dict[str, Any],
    ):
        self.report = report
        self.runtime_config = runtime_config
        self.estimate_cost = bool(runtime_config.get("estimate_cost", False))
        self._lock = Lock()

    def record(self, call: dict[str, Any]) -> None:
        """Record one service call without disrupting the pipeline."""
        call["operation"] = call.get("operation") or _current_operation.get()
        if self.estimate_cost:
            call["cost_estimate"] = self._estimate(call)

        with self._lock:
            self.report["calls"].append(call)
            totals = self.report["totals"]
            totals["calls"] += 1
            for name, value in (call.get("usage") or {}).items():
                if isinstance(value, int):
                    totals[name] = totals.get(name, 0) + value

            estimate = call.get("cost_estimate") or {}
            cost = estimate.get("estimated_cost")
            if isinstance(cost, int | float):
                totals["estimated_cost"] += cost
                totals["estimated_calls"] += 1
            elif self.estimate_cost:
                totals["unpriced_calls"] += 1

    def _estimate(self, call: dict[str, Any]) -> dict[str, Any]:
        if call.get("provider") != "azure":
            return {
                "estimated_cost": None,
                "currency": "USD",
                "error": "cost estimation is currently supported only for Azure",
            }
        try:
            return _azure_pricing.estimate(call, self.runtime_config)
        except AzurePricingUnavailable as exc:
            return {
                "estimated_cost": None,
                "currency": "USD",
                "error": str(exc),
            }
        except Exception as exc:
            logger.warning("Unable to fetch Azure pricing: %s", exc)
            return {
                "estimated_cost": None,
                "currency": "USD",
                "error": f"Azure pricing lookup failed: {exc}",
            }


def create_usage_tracker(
    runtime_config: dict[str, Any],
) -> tuple[dict[str, Any], UsageTracker] | None:
    """Create a usage report when runtime reporting is enabled."""
    if not (
        runtime_config.get("report_usage", False)
        or runtime_config.get("estimate_cost", False)
    ):
        return None
    report: dict[str, Any] = {
        "calls": [],
        "totals": {
            "calls": 0,
            "estimated_cost": 0.0,
            "estimated_calls": 0,
            "unpriced_calls": 0,
        },
    }
    return report, UsageTracker(report, runtime_config)


@contextmanager
def usage_tracking(tracker: UsageTracker | None) -> Iterator[None]:
    """Make a pipeline's usage tracker available to service wrappers."""
    token = _current_tracker.set(tracker)
    try:
        yield
    finally:
        _current_tracker.reset(token)


@contextmanager
def usage_operation(operation: str) -> Iterator[None]:
    """Attribute service calls to a pipeline operation."""
    token = _current_operation.set(operation)
    try:
        yield
    finally:
        _current_operation.reset(token)


def record_usage(call: dict[str, Any]) -> None:
    """Record usage on the active pipeline tracker, if any."""
    tracker = _current_tracker.get()
    if tracker is not None:
        tracker.record(call)
