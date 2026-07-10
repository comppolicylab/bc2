from .usage import (
    create_usage_tracker,
    record_usage,
    usage_operation,
    usage_tracking,
)


def test_usage_reporting_is_disabled_by_default():
    assert create_usage_tracker({}) is None


def test_estimate_cost_enables_usage_reporting():
    created = create_usage_tracker({"estimate_cost": True})

    assert created is not None


def test_usage_call_and_totals_are_recorded():
    created = create_usage_tracker({"report_usage": True})
    assert created is not None
    report, tracker = created

    with usage_tracking(tracker), usage_operation("redact:openai"):
        record_usage(
            {
                "provider": "azure",
                "service": "responses",
                "model": "gpt-4.1",
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                },
            }
        )

    assert report["calls"][0]["operation"] == "redact:openai"
    assert report["totals"]["calls"] == 1
    assert report["totals"]["input_tokens"] == 100
    assert report["totals"]["output_tokens"] == 20


def test_pricing_failure_is_added_to_call_instead_of_raised():
    created = create_usage_tracker({"estimate_cost": True})
    assert created is not None
    report, tracker = created

    with usage_tracking(tracker):
        record_usage(
            {
                "provider": "azure",
                "service": "responses",
                "model": "gpt-4.1",
                "usage": {"input_tokens": 100},
            }
        )

    estimate = report["calls"][0]["cost_estimate"]
    assert estimate["estimated_cost"] is None
    assert "azure_region" in estimate["error"]
    assert report["totals"]["unpriced_calls"] == 1
