"""
    Property-based tests for the automojo.agentkit.costestimate module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 15: CostEstimate construction validates total equals sum

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**
"""

from automojo.testbase.properties import given, settings, assume
from automojo.testbase.properties import strategies as st

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.costestimate import CostEstimate


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_non_negative_float = st.floats(
    min_value=0.0,
    max_value=1_000_000.0,
)


# ---------------------------------------------------------------------------
# Property 15: CostEstimate construction validates total equals sum
# ---------------------------------------------------------------------------

@given(
    prompt_cost=_non_negative_float,
    completion_cost=_non_negative_float,
    settings=settings(max_examples=50),
)
def test_costestimate_valid_construction_preserves_fields(
    prompt_cost: float,
    completion_cost: float,
) -> None:
    """
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

        For any two non-negative floats, constructing a CostEstimate
        with total_cost equal to prompt_cost + completion_cost shall
        succeed and all properties shall return the provided values.
    """
    total_cost = prompt_cost + completion_cost

    estimate = CostEstimate(
        prompt_cost=prompt_cost,
        completion_cost=completion_cost,
        total_cost=total_cost,
    )

    assert estimate.prompt_cost == prompt_cost, (
        "prompt_cost property should return {}, got {}".format(
            prompt_cost, estimate.prompt_cost
        )
    )
    assert estimate.completion_cost == completion_cost, (
        "completion_cost property should return {}, got {}".format(
            completion_cost, estimate.completion_cost
        )
    )
    assert estimate.total_cost == total_cost, (
        "total_cost property should return {}, got {}".format(
            total_cost, estimate.total_cost
        )
    )
    assert estimate.currency == "USD", (
        "currency should default to 'USD', got {!r}".format(
            estimate.currency
        )
    )

    return


@given(
    prompt_cost=_non_negative_float,
    completion_cost=_non_negative_float,
    total_cost=_non_negative_float,
    settings=settings(max_examples=50),
)
def test_costestimate_invalid_total_raises_semantic_error(
    prompt_cost: float,
    completion_cost: float,
    total_cost: float,
) -> None:
    """
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

        For any three non-negative floats where total_cost does not
        equal prompt_cost + completion_cost (within floating-point
        tolerance 1e-9), constructing a CostEstimate shall raise
        SemanticError.
    """
    expected_total = prompt_cost + completion_cost
    assume(abs(total_cost - expected_total) > 1e-9)

    raised = False
    try:
        CostEstimate(
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
        )
    except SemanticError:
        raised = True

    assert raised is True, (
        "CostEstimate should raise SemanticError when total_cost ({}) "
        "does not equal prompt_cost ({}) + completion_cost ({}) = {} "
        "(difference: {})".format(
            total_cost, prompt_cost, completion_cost, expected_total,
            abs(total_cost - expected_total)
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
