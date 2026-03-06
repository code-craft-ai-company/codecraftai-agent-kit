"""
    Unit tests for the automojo.agentkit.costtracker module.

    Tests CostTracker construction, record accumulation, total properties,
    per-provider breakdown, request count, and reset.

    Feature: llm-integration, Task 7.3
    **Validates: Requirements 5.8, 5.9, 5.10, 5.11, 5.12, 5.13**
"""

from automojo.agentkit.costtracker import CostTracker
from automojo.agentkit.tokenusage import TokenUsage
from automojo.agentkit.costestimate import CostEstimate


# ---------------------------------------------------------------------------
# Empty tracker
# ---------------------------------------------------------------------------


def test_empty_tracker_request_count():
    """
        A new CostTracker has zero request count.

        **Validates: Requirements 5.12**
    """
    tracker = CostTracker()

    assert tracker.request_count == 0, (
        "Empty tracker request_count should be 0, got: {}".format(tracker.request_count)
    )

    return


def test_empty_tracker_total_token_usage():
    """
        A new CostTracker returns zero-valued total TokenUsage.

        **Validates: Requirements 5.9**
    """
    tracker = CostTracker()
    total = tracker.total_token_usage

    assert total.prompt_tokens == 0, (
        "Empty tracker prompt_tokens should be 0, got: {}".format(total.prompt_tokens)
    )
    assert total.completion_tokens == 0, (
        "Empty tracker completion_tokens should be 0, got: {}".format(total.completion_tokens)
    )
    assert total.total_tokens == 0, (
        "Empty tracker total_tokens should be 0, got: {}".format(total.total_tokens)
    )

    return


def test_empty_tracker_total_cost_estimate():
    """
        A new CostTracker returns zero-valued total CostEstimate.

        **Validates: Requirements 5.10**
    """
    tracker = CostTracker()
    total = tracker.total_cost_estimate

    assert abs(total.prompt_cost) < 1e-9, (
        "Empty tracker prompt_cost should be 0.0, got: {}".format(total.prompt_cost)
    )
    assert abs(total.completion_cost) < 1e-9, (
        "Empty tracker completion_cost should be 0.0, got: {}".format(total.completion_cost)
    )
    assert abs(total.total_cost) < 1e-9, (
        "Empty tracker total_cost should be 0.0, got: {}".format(total.total_cost)
    )

    return


# ---------------------------------------------------------------------------
# Single record
# ---------------------------------------------------------------------------


def test_single_record_request_count():
    """
        Recording one entry increments request_count to 1.

        **Validates: Requirements 5.8, 5.12**
    """
    tracker = CostTracker()
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    cost = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)

    tracker.record("openai", usage, cost)

    assert tracker.request_count == 1, (
        "request_count should be 1 after one record, got: {}".format(tracker.request_count)
    )

    return


def test_single_record_total_token_usage():
    """
        After one record, total_token_usage matches the recorded TokenUsage.

        **Validates: Requirements 5.8, 5.9**
    """
    tracker = CostTracker()
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    cost = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)

    tracker.record("openai", usage, cost)
    total = tracker.total_token_usage

    assert total.prompt_tokens == 10, (
        "prompt_tokens mismatch: {}".format(total.prompt_tokens)
    )
    assert total.completion_tokens == 20, (
        "completion_tokens mismatch: {}".format(total.completion_tokens)
    )
    assert total.total_tokens == 30, (
        "total_tokens mismatch: {}".format(total.total_tokens)
    )

    return


def test_single_record_total_cost_estimate():
    """
        After one record, total_cost_estimate matches the recorded CostEstimate.

        **Validates: Requirements 5.8, 5.10**
    """
    tracker = CostTracker()
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    cost = CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)

    tracker.record("openai", usage, cost)
    total = tracker.total_cost_estimate

    assert abs(total.prompt_cost - 0.01) < 1e-9, (
        "prompt_cost mismatch: {}".format(total.prompt_cost)
    )
    assert abs(total.completion_cost - 0.02) < 1e-9, (
        "completion_cost mismatch: {}".format(total.completion_cost)
    )
    assert abs(total.total_cost - 0.03) < 1e-9, (
        "total_cost mismatch: {}".format(total.total_cost)
    )

    return


# ---------------------------------------------------------------------------
# Multiple records (same provider)
# ---------------------------------------------------------------------------


def test_multiple_records_same_provider_totals():
    """
        Multiple records from the same provider accumulate correctly.

        **Validates: Requirements 5.8, 5.9, 5.10**
    """
    tracker = CostTracker()

    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    )
    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20),
        CostEstimate(prompt_cost=0.005, completion_cost=0.015, total_cost=0.02)
    )

    assert tracker.request_count == 2, (
        "request_count should be 2, got: {}".format(tracker.request_count)
    )

    total_usage = tracker.total_token_usage
    assert total_usage.prompt_tokens == 15, (
        "total prompt_tokens mismatch: {}".format(total_usage.prompt_tokens)
    )
    assert total_usage.completion_tokens == 35, (
        "total completion_tokens mismatch: {}".format(total_usage.completion_tokens)
    )
    assert total_usage.total_tokens == 50, (
        "total total_tokens mismatch: {}".format(total_usage.total_tokens)
    )

    total_cost = tracker.total_cost_estimate
    assert abs(total_cost.prompt_cost - 0.015) < 1e-9, (
        "total prompt_cost mismatch: {}".format(total_cost.prompt_cost)
    )
    assert abs(total_cost.completion_cost - 0.035) < 1e-9, (
        "total completion_cost mismatch: {}".format(total_cost.completion_cost)
    )
    assert abs(total_cost.total_cost - 0.05) < 1e-9, (
        "total total_cost mismatch: {}".format(total_cost.total_cost)
    )

    return


# ---------------------------------------------------------------------------
# Multiple providers
# ---------------------------------------------------------------------------


def test_multiple_providers_totals():
    """
        Records from different providers accumulate into correct totals.

        **Validates: Requirements 5.8, 5.9, 5.10**
    """
    tracker = CostTracker()

    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    )
    tracker.record(
        "anthropic",
        TokenUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300),
        CostEstimate(prompt_cost=0.10, completion_cost=0.20, total_cost=0.30)
    )

    total_usage = tracker.total_token_usage
    assert total_usage.prompt_tokens == 110, (
        "total prompt_tokens mismatch: {}".format(total_usage.prompt_tokens)
    )
    assert total_usage.total_tokens == 330, (
        "total total_tokens mismatch: {}".format(total_usage.total_tokens)
    )

    total_cost = tracker.total_cost_estimate
    assert abs(total_cost.total_cost - 0.33) < 1e-9, (
        "total total_cost mismatch: {}".format(total_cost.total_cost)
    )

    return


# ---------------------------------------------------------------------------
# Per-provider breakdown
# ---------------------------------------------------------------------------


def test_per_provider_breakdown_empty():
    """
        An empty tracker returns an empty breakdown dictionary.

        **Validates: Requirements 5.11**
    """
    tracker = CostTracker()
    breakdown = tracker.per_provider_breakdown()

    assert len(breakdown) == 0, (
        "Empty tracker breakdown should be empty, got: {}".format(breakdown)
    )

    return


def test_per_provider_breakdown_single_provider():
    """
        Breakdown with a single provider contains one key with correct totals.

        **Validates: Requirements 5.11**
    """
    tracker = CostTracker()

    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    )
    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20),
        CostEstimate(prompt_cost=0.005, completion_cost=0.015, total_cost=0.02)
    )

    breakdown = tracker.per_provider_breakdown()

    assert "openai" in breakdown, "Breakdown should contain 'openai' key"
    assert len(breakdown) == 1, (
        "Breakdown should have 1 provider, got: {}".format(len(breakdown))
    )

    openai_usage = breakdown["openai"]["token_usage"]
    assert openai_usage.prompt_tokens == 15, (
        "openai prompt_tokens mismatch: {}".format(openai_usage.prompt_tokens)
    )
    assert openai_usage.total_tokens == 50, (
        "openai total_tokens mismatch: {}".format(openai_usage.total_tokens)
    )

    openai_cost = breakdown["openai"]["cost_estimate"]
    assert abs(openai_cost.prompt_cost - 0.015) < 1e-9, (
        "openai prompt_cost mismatch: {}".format(openai_cost.prompt_cost)
    )
    assert abs(openai_cost.total_cost - 0.05) < 1e-9, (
        "openai total_cost mismatch: {}".format(openai_cost.total_cost)
    )

    return


def test_per_provider_breakdown_multiple_providers():
    """
        Breakdown groups records by provider name with correct per-provider totals.

        **Validates: Requirements 5.11**
    """
    tracker = CostTracker()

    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    )
    tracker.record(
        "anthropic",
        TokenUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300),
        CostEstimate(prompt_cost=0.10, completion_cost=0.20, total_cost=0.30)
    )
    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=5, completion_tokens=15, total_tokens=20),
        CostEstimate(prompt_cost=0.005, completion_cost=0.015, total_cost=0.02)
    )

    breakdown = tracker.per_provider_breakdown()

    assert len(breakdown) == 2, (
        "Breakdown should have 2 providers, got: {}".format(len(breakdown))
    )
    assert "openai" in breakdown, "Breakdown should contain 'openai'"
    assert "anthropic" in breakdown, "Breakdown should contain 'anthropic'"

    openai_usage = breakdown["openai"]["token_usage"]
    assert openai_usage.prompt_tokens == 15, (
        "openai prompt_tokens mismatch: {}".format(openai_usage.prompt_tokens)
    )
    assert openai_usage.total_tokens == 50, (
        "openai total_tokens mismatch: {}".format(openai_usage.total_tokens)
    )

    anthropic_usage = breakdown["anthropic"]["token_usage"]
    assert anthropic_usage.prompt_tokens == 100, (
        "anthropic prompt_tokens mismatch: {}".format(anthropic_usage.prompt_tokens)
    )
    assert anthropic_usage.total_tokens == 300, (
        "anthropic total_tokens mismatch: {}".format(anthropic_usage.total_tokens)
    )

    anthropic_cost = breakdown["anthropic"]["cost_estimate"]
    assert abs(anthropic_cost.total_cost - 0.30) < 1e-9, (
        "anthropic total_cost mismatch: {}".format(anthropic_cost.total_cost)
    )

    return


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_reset_clears_all_records():
    """
        Calling reset clears all accumulated records.

        **Validates: Requirements 5.13**
    """
    tracker = CostTracker()

    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    )
    tracker.record(
        "anthropic",
        TokenUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300),
        CostEstimate(prompt_cost=0.10, completion_cost=0.20, total_cost=0.30)
    )

    tracker.reset()

    assert tracker.request_count == 0, (
        "request_count should be 0 after reset, got: {}".format(tracker.request_count)
    )

    total_usage = tracker.total_token_usage
    assert total_usage.prompt_tokens == 0, (
        "prompt_tokens should be 0 after reset, got: {}".format(total_usage.prompt_tokens)
    )
    assert total_usage.total_tokens == 0, (
        "total_tokens should be 0 after reset, got: {}".format(total_usage.total_tokens)
    )

    total_cost = tracker.total_cost_estimate
    assert abs(total_cost.total_cost) < 1e-9, (
        "total_cost should be 0.0 after reset, got: {}".format(total_cost.total_cost)
    )

    breakdown = tracker.per_provider_breakdown()
    assert len(breakdown) == 0, (
        "Breakdown should be empty after reset, got: {}".format(breakdown)
    )

    return


def test_reset_allows_new_records():
    """
        After reset, new records accumulate from scratch.

        **Validates: Requirements 5.8, 5.13**
    """
    tracker = CostTracker()

    tracker.record(
        "openai",
        TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        CostEstimate(prompt_cost=0.01, completion_cost=0.02, total_cost=0.03)
    )

    tracker.reset()

    tracker.record(
        "anthropic",
        TokenUsage(prompt_tokens=50, completion_tokens=50, total_tokens=100),
        CostEstimate(prompt_cost=0.05, completion_cost=0.05, total_cost=0.10)
    )

    assert tracker.request_count == 1, (
        "request_count should be 1 after reset and new record, got: {}".format(
            tracker.request_count
        )
    )

    total_usage = tracker.total_token_usage
    assert total_usage.prompt_tokens == 50, (
        "prompt_tokens should reflect only new record, got: {}".format(
            total_usage.prompt_tokens
        )
    )

    breakdown = tracker.per_provider_breakdown()
    assert "openai" not in breakdown, (
        "Old provider should not appear after reset"
    )
    assert "anthropic" in breakdown, (
        "New provider should appear in breakdown"
    )

    return
