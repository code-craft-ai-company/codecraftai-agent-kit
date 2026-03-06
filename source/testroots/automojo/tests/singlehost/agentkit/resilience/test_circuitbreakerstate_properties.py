"""
    Property-based tests for the automojo.agentkit.circuitbreakerstate module.

    Uses the hypothesis library to verify:
    - Property 14: CircuitBreakerState from_string round-trip

    **Validates: Requirements 4.2**
"""

from hypothesis import given, settings
from hypothesis.strategies import sampled_from

from automojo.agentkit.circuitbreakerstate import CircuitBreakerState


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_circuit_breaker_state_strategy = sampled_from(list(CircuitBreakerState))


# ---------------------------------------------------------------------------
# Property 14: CircuitBreakerState from_string round-trip
# ---------------------------------------------------------------------------

@given(state=_circuit_breaker_state_strategy)
@settings(max_examples=100)
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
