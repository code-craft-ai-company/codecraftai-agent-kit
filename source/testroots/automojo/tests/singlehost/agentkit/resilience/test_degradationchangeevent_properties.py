"""
    Property-based tests for the automojo.agentkit.degradationchangeevent module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 18: DegradationChangeEvent JSON round-trip

    **Validates: Requirements 10.7**
"""

from datetime import datetime

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.degradationchangeevent import DegradationChangeEvent
from automojo.agentkit.degradationlevel import DegradationLevel


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

_dependency_name = st.text(min_size=1, max_size=200)

_degradation_level = st.sampled_from([
    DegradationLevel.NORMAL,
    DegradationLevel.DEGRADED,
    DegradationLevel.CRITICAL,
])

_reason = st.text(min_size=0, max_size=200)

_timestamp = _datetimes()


# ---------------------------------------------------------------------------
# Property 18: DegradationChangeEvent JSON round-trip
# ---------------------------------------------------------------------------

@given(
    dependency_name=_dependency_name,
    previous_level=_degradation_level,
    new_level=_degradation_level,
    reason=_reason,
    timestamp=_timestamp,
    settings=settings(max_examples=50),
)
def test_degradationchangeevent_json_roundtrip(
    dependency_name: str,
    previous_level: DegradationLevel,
    new_level: DegradationLevel,
    reason: str,
    timestamp: datetime,
) -> None:
    """
        **Validates: Requirements 10.7**

        For all valid DegradationChangeEvent instances constructed with
        arbitrary dependency_name (non-empty string), previous_level
        (DegradationLevel), new_level (DegradationLevel), reason (string),
        and timestamp (datetime), calling to_json() and then from_json()
        shall produce a DegradationChangeEvent with equivalent
        dependency_name, previous_level, new_level, reason, and timestamp
        values.
    """
    original = DegradationChangeEvent(
        dependency_name=dependency_name,
        previous_level=previous_level,
        new_level=new_level,
        reason=reason,
        timestamp=timestamp,
    )

    json_str = original.to_json()
    restored = DegradationChangeEvent.from_json(json_str)

    assert restored.dependency_name == original.dependency_name, (
        "dependency_name mismatch: expected {!r}, got {!r}".format(
            original.dependency_name, restored.dependency_name
        )
    )

    assert restored.previous_level == original.previous_level, (
        "previous_level mismatch: expected {}, got {}".format(
            original.previous_level, restored.previous_level
        )
    )

    assert restored.new_level == original.new_level, (
        "new_level mismatch: expected {}, got {}".format(
            original.new_level, restored.new_level
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
