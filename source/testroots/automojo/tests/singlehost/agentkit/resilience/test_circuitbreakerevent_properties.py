"""
    Property-based tests for the automojo.agentkit.circuitbreakerevent module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 8: CircuitBreakerEvent JSON round-trip

    **Validates: Requirements 5.7**
"""

from datetime import datetime

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.circuitbreakerevent import CircuitBreakerEvent
from automojo.agentkit.circuitbreakerstate import CircuitBreakerState


# ---------------------------------------------------------------------------
# Composite Strategies
# ---------------------------------------------------------------------------

@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_circuit_breaker_name = st.text(min_size=1, max_size=200)

_circuit_breaker_state = st.sampled_from([
    CircuitBreakerState.CLOSED,
    CircuitBreakerState.OPEN,
    CircuitBreakerState.HALF_OPEN,
])

_reason = st.text(min_size=0, max_size=200)

_timestamp = _datetimes()


# ---------------------------------------------------------------------------
# Property 8: CircuitBreakerEvent JSON round-trip
# ---------------------------------------------------------------------------

@given(
    name=_circuit_breaker_name,
    previous_state=_circuit_breaker_state,
    new_state=_circuit_breaker_state,
    reason=_reason,
    timestamp=_timestamp,
    constraints={"max_examples": 50},
)
def test_circuitbreakerevent_json_roundtrip(
    name: str,
    previous_state: CircuitBreakerState,
    new_state: CircuitBreakerState,
    reason: str,
    timestamp: datetime,
) -> None:
    """
        **Validates: Requirements 5.7**

        For all valid CircuitBreakerEvent instances constructed with
        arbitrary name (non-empty string), previous_state (CircuitBreakerState),
        new_state (CircuitBreakerState), reason (string), and timestamp
        (datetime), calling to_json() and then from_json() shall produce
        a CircuitBreakerEvent with equivalent name, previous_state,
        new_state, reason, and timestamp values.
    """
    original = CircuitBreakerEvent(
        name=name,
        previous_state=previous_state,
        new_state=new_state,
        reason=reason,
        timestamp=timestamp,
    )

    json_str = original.to_json()
    restored = CircuitBreakerEvent.from_json(json_str)

    assert restored.name == original.name, (
        "name mismatch: expected {!r}, got {!r}".format(
            original.name, restored.name
        )
    )

    assert restored.previous_state == original.previous_state, (
        "previous_state mismatch: expected {}, got {}".format(
            original.previous_state, restored.previous_state
        )
    )

    assert restored.new_state == original.new_state, (
        "new_state mismatch: expected {}, got {}".format(
            original.new_state, restored.new_state
        )
    )

    assert restored.reason == original.reason, (
        "reason mismatch: expected {!r}, got {!r}".format(
            original.reason, restored.reason
        )
    )

    assert restored.timestamp == original.timestamp, (
        "timestamp mismatch: expected {}, got {}".format(
            original.timestamp, restored.timestamp
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
