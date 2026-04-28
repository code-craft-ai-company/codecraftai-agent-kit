"""
    Property-based tests for the automojo.agentkit.retryattempt module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 1: RetryAttempt JSON round-trip

    **Validates: Requirements 2.7**
"""

from datetime import datetime

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.retryattempt import RetryAttempt


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_positive_int = st.integers(min_value=1, max_value=1_000_000)

_non_negative_float = st.floats(min_value=0.0, max_value=1_000_000.0)

_exception_message = st.text(min_size=0, max_size=200)


@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_timestamp = _datetimes()


# ---------------------------------------------------------------------------
# Property 1: RetryAttempt JSON round-trip
# ---------------------------------------------------------------------------

@given(
    attempt_number=_positive_int,
    delay=_non_negative_float,
    exception_message=_exception_message,
    timestamp=_timestamp,
    constraints={"max_examples": 50},
)
def test_retryattempt_json_roundtrip(
    attempt_number: int,
    delay: float,
    exception_message: str,
    timestamp: datetime,
) -> None:
    """
        **Validates: Requirements 2.7**

        For all valid RetryAttempt instances constructed with arbitrary
        attempt_number (positive int), delay (non-negative float),
        exception (Exception with arbitrary message), and timestamp
        (datetime), calling to_json() and then from_json() on the
        result shall produce a RetryAttempt with equivalent
        attempt_number, delay, exception string representation, and
        timestamp values.
    """
    exception = RuntimeError(exception_message)

    original = RetryAttempt(
        attempt_number=attempt_number,
        delay=delay,
        exception=exception,
        timestamp=timestamp,
    )

    json_str = original.to_json()
    restored = RetryAttempt.from_json(json_str)

    assert restored.attempt_number == original.attempt_number, (
        "attempt_number mismatch: expected {}, got {}".format(
            original.attempt_number, restored.attempt_number
        )
    )

    assert restored.delay == original.delay, (
        "delay mismatch: expected {}, got {}".format(
            original.delay, restored.delay
        )
    )

    original_exception_str = "{}({})".format(
        type(original.exception).__name__, str(original.exception)
    )
    restored_exception_str = str(restored.exception)
    assert original_exception_str in restored_exception_str, (
        "exception string mismatch: expected {!r} in {!r}".format(
            original_exception_str, restored_exception_str
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
