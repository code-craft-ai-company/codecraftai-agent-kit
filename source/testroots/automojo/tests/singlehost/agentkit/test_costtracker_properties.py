"""
    Property-based tests for the automojo.agentkit.costtracker module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 16: CostTracker accumulation and per-provider breakdown

    **Validates: Requirements 5.8, 5.9, 5.10, 5.11, 5.12, 5.13**
"""

from collections import defaultdict

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.tokenusage import TokenUsage
from automojo.agentkit.costestimate import CostEstimate
from automojo.agentkit.costtracker import CostTracker


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_non_negative_int = st.integers(min_value=0, max_value=100_000)

_non_negative_float = st.floats(
    min_value=0.0,
    max_value=10_000.0,
)

_provider_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=10,
)


@composite
def _record_entry(draw):
    """
        Draws a single (provider_name, TokenUsage, CostEstimate) record.
    """
    pname = draw(_provider_name)

    prompt_tokens = draw(_non_negative_int)
    completion_tokens = draw(_non_negative_int)
    total_tokens = prompt_tokens + completion_tokens
    token_usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    prompt_cost = draw(_non_negative_float)
    completion_cost = draw(_non_negative_float)
    total_cost = prompt_cost + completion_cost
    cost_estimate = CostEstimate(
        prompt_cost=prompt_cost,
        completion_cost=completion_cost,
        total_cost=total_cost,
    )

    return (pname, token_usage, cost_estimate)


_record_list = st.lists(_record_entry(), min_size=0, max_size=20)


# ---------------------------------------------------------------------------
# Property 16: CostTracker accumulation and per-provider breakdown
# ---------------------------------------------------------------------------

@given(records=_record_list, constraints={"max_examples": 50})
def test_costtracker_request_count_equals_number_of_records(
    records: list,
) -> None:
    """
        **Validates: Requirements 5.8, 5.12**

        For any sequence of records added to a CostTracker,
        request_count shall equal the number of records.
    """
    tracker = CostTracker()

    for pname, token_usage, cost_estimate in records:
        tracker.record(pname, token_usage, cost_estimate)

    assert tracker.request_count == len(records), (
        "request_count should be {}, got {}".format(
            len(records), tracker.request_count
        )
    )

    return


@given(records=_record_list, constraints={"max_examples": 50})
def test_costtracker_total_token_usage_sums_all_records(
    records: list,
) -> None:
    """
        **Validates: Requirements 5.8, 5.9**

        For any sequence of records added to a CostTracker,
        total_token_usage shall equal the sum of all TokenUsage records.
    """
    tracker = CostTracker()

    for pname, token_usage, cost_estimate in records:
        tracker.record(pname, token_usage, cost_estimate)

    expected_prompt = sum(tu.prompt_tokens for _, tu, _ in records)
    expected_completion = sum(tu.completion_tokens for _, tu, _ in records)
    expected_total = expected_prompt + expected_completion

    total = tracker.total_token_usage

    assert total.prompt_tokens == expected_prompt, (
        "total prompt_tokens should be {}, got {}".format(
            expected_prompt, total.prompt_tokens
        )
    )
    assert total.completion_tokens == expected_completion, (
        "total completion_tokens should be {}, got {}".format(
            expected_completion, total.completion_tokens
        )
    )
    assert total.total_tokens == expected_total, (
        "total total_tokens should be {}, got {}".format(
            expected_total, total.total_tokens
        )
    )

    return


@given(records=_record_list, constraints={"max_examples": 50})
def test_costtracker_total_cost_estimate_sums_all_records(
    records: list,
) -> None:
    """
        **Validates: Requirements 5.8, 5.10**

        For any sequence of records added to a CostTracker,
        total_cost_estimate shall equal the sum of all CostEstimate records.
    """
    tracker = CostTracker()

    for pname, token_usage, cost_estimate in records:
        tracker.record(pname, token_usage, cost_estimate)

    expected_prompt_cost = sum(ce.prompt_cost for _, _, ce in records)
    expected_completion_cost = sum(ce.completion_cost for _, _, ce in records)
    expected_total_cost = expected_prompt_cost + expected_completion_cost

    total = tracker.total_cost_estimate

    assert abs(total.prompt_cost - expected_prompt_cost) < 1e-6, (
        "total prompt_cost should be ~{}, got {}".format(
            expected_prompt_cost, total.prompt_cost
        )
    )
    assert abs(total.completion_cost - expected_completion_cost) < 1e-6, (
        "total completion_cost should be ~{}, got {}".format(
            expected_completion_cost, total.completion_cost
        )
    )
    assert abs(total.total_cost - expected_total_cost) < 1e-6, (
        "total total_cost should be ~{}, got {}".format(
            expected_total_cost, total.total_cost
        )
    )

    return


@given(records=_record_list, constraints={"max_examples": 50})
def test_costtracker_per_provider_breakdown_groups_by_provider(
    records: list,
) -> None:
    """
        **Validates: Requirements 5.8, 5.11**

        For any sequence of records added to a CostTracker,
        per_provider_breakdown shall correctly group and sum records
        by provider name.
    """
    tracker = CostTracker()

    for pname, token_usage, cost_estimate in records:
        tracker.record(pname, token_usage, cost_estimate)

    breakdown = tracker.per_provider_breakdown()

    # Compute expected breakdown manually
    expected_providers = defaultdict(lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "prompt_cost": 0.0,
        "completion_cost": 0.0,
    })

    for pname, tu, ce in records:
        expected_providers[pname]["prompt_tokens"] += tu.prompt_tokens
        expected_providers[pname]["completion_tokens"] += tu.completion_tokens
        expected_providers[pname]["prompt_cost"] += ce.prompt_cost
        expected_providers[pname]["completion_cost"] += ce.completion_cost

    # Verify the breakdown keys match expected providers
    assert set(breakdown.keys()) == set(expected_providers.keys()), (
        "breakdown keys should be {}, got {}".format(
            set(expected_providers.keys()), set(breakdown.keys())
        )
    )

    for pname, expected in expected_providers.items():
        actual_tu = breakdown[pname]["token_usage"]
        actual_ce = breakdown[pname]["cost_estimate"]

        expected_total_tokens = expected["prompt_tokens"] + expected["completion_tokens"]

        assert actual_tu.prompt_tokens == expected["prompt_tokens"], (
            "provider {!r} prompt_tokens should be {}, got {}".format(
                pname, expected["prompt_tokens"], actual_tu.prompt_tokens
            )
        )
        assert actual_tu.completion_tokens == expected["completion_tokens"], (
            "provider {!r} completion_tokens should be {}, got {}".format(
                pname, expected["completion_tokens"], actual_tu.completion_tokens
            )
        )
        assert actual_tu.total_tokens == expected_total_tokens, (
            "provider {!r} total_tokens should be {}, got {}".format(
                pname, expected_total_tokens, actual_tu.total_tokens
            )
        )

        expected_total_cost = expected["prompt_cost"] + expected["completion_cost"]

        assert abs(actual_ce.prompt_cost - expected["prompt_cost"]) < 1e-6, (
            "provider {!r} prompt_cost should be ~{}, got {}".format(
                pname, expected["prompt_cost"], actual_ce.prompt_cost
            )
        )
        assert abs(actual_ce.completion_cost - expected["completion_cost"]) < 1e-6, (
            "provider {!r} completion_cost should be ~{}, got {}".format(
                pname, expected["completion_cost"], actual_ce.completion_cost
            )
        )
        assert abs(actual_ce.total_cost - expected_total_cost) < 1e-6, (
            "provider {!r} total_cost should be ~{}, got {}".format(
                pname, expected_total_cost, actual_ce.total_cost
            )
        )

    return


@given(records=_record_list, constraints={"max_examples": 50})
def test_costtracker_reset_clears_all_records(
    records: list,
) -> None:
    """
        **Validates: Requirements 5.8, 5.13**

        For any sequence of records added to a CostTracker,
        after reset(), request_count shall be 0.
    """
    tracker = CostTracker()

    for pname, token_usage, cost_estimate in records:
        tracker.record(pname, token_usage, cost_estimate)

    tracker.reset()

    assert tracker.request_count == 0, (
        "request_count should be 0 after reset, got {}".format(
            tracker.request_count
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
