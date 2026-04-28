"""
    Property-based tests for the automojo.agentkit.circuitbreakerstate module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 14: CircuitBreakerState from_string round-trip

    **Validates: Requirements 4.2**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.circuitbreakerstate import CircuitBreakerState


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_circuit_breaker_state_strategy = st.sampled_from(list(CircuitBreakerState))


# ---------------------------------------------------------------------------
# Property 14: CircuitBreakerState from_string round-trip
# ---------------------------------------------------------------------------

@given(
    state=_circuit_breaker_state_strategy,
    constraints={"max_examples": 50},
)
def test_circuit_breaker_state_from_string_round_trip(
    state: CircuitBreakerState,
) -> None:
    """
        **Validates: Requirements 4.2**

        For all CircuitBreakerState members, calling
        CircuitBreakerState.from_string(state.value) shall return the
        same CircuitBreakerState member.
    """
    result = CircuitBreakerState.from_string(state.value)

    assert result is state, (
        "from_string({!r}) should return {!r}, got {!r}".format(
            state.value, state, result
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
