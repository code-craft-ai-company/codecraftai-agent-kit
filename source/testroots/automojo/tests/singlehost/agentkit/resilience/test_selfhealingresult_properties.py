"""
    Property-based tests for the automojo.agentkit.selfhealingresult module.

    Uses the hypothesis library to verify:
    - Property 33: SelfHealingResult JSON round-trip

    **Validates: Requirements 20.13**
"""

from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.selfhealingresult import SelfHealingResult


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_check_name = st.text(min_size=1, max_size=200)

_action_name = st.text(min_size=1, max_size=200)

_success = st.booleans()

_error_message = st.one_of(st.none(), st.text(min_size=0, max_size=200))

_attempt_number = st.integers(min_value=1, max_value=10000)

_timestamp = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
)


# ---------------------------------------------------------------------------
# Property 33: SelfHealingResult JSON round-trip
# ---------------------------------------------------------------------------

@given(
    check_name=_check_name,
    action_name=_action_name,
    success=_success,
    error_message=_error_message,
    attempt_number=_attempt_number,
    timestamp=_timestamp,
)
@settings(max_examples=100)
def test_selfhealingresult_json_roundtrip(
    check_name: str,
    action_name: str,
    success: bool,
    error_message: str,
    attempt_number: int,
    timestamp: datetime,
) -> None:
    """
        **Validates: Requirements 20.13**

        For all valid SelfHealingResult instances constructed with arbitrary
        check_name (non-empty string), action_name (non-empty string),
        success (bool), error_message (optional string), attempt_number
        (positive int), and timestamp (datetime), calling to_json() and
        then from_json() shall produce an equivalent SelfHealingResult
        object.
    """
    original = SelfHealingResult(
        check_name=check_name,
        action_name=action_name,
        success=success,
        error_message=error_message,
        attempt_number=attempt_number,
        timestamp=timestamp,
    )

    json_str = original.to_json()
    restored = SelfHealingResult.from_json(json_str)

    assert restored.check_name == original.check_name, (
        "check_name mismatch: expected {!r}, got {!r}".format(
            original.check_name, restored.check_name
        )
    )

    assert restored.action_name == original.action_name, (
        "action_name mismatch: expected {!r}, got {!r}".format(
            original.action_name, restored.action_name
        )
    )

    assert restored.success == original.success, (
        "success mismatch: expected {!r}, got {!r}".format(
            original.success, restored.success
        )
    )

    assert restored.error_message == original.error_message, (
        "error_message mismatch: expected {!r}, got {!r}".format(
            original.error_message, restored.error_message
        )
    )

    assert restored.attempt_number == original.attempt_number, (
        "attempt_number mismatch: expected {!r}, got {!r}".format(
            original.attempt_number, restored.attempt_number
        )
    )

    assert restored.timestamp == original.timestamp, (
        "timestamp mismatch: expected {}, got {}".format(
            original.timestamp, restored.timestamp
        )
    )

    return
