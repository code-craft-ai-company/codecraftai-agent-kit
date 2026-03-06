"""
    Property-based tests for the automojo.agentkit.retryresult module.

    Uses the hypothesis library to verify:
    - Property 2: RetryResult JSON round-trip

    **Validates: Requirements 2.17**
"""

from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.retryattempt import RetryAttempt
from automojo.agentkit.retryresult import RetryResult


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_positive_int = st.integers(min_value=1, max_value=1_000_000)

_non_negative_float = st.floats(
    min_value=0.0,
    max_value=1_000_000.0,
    allow_nan=False,
    allow_infinity=False,
)

_exception_message = st.text(min_size=0, max_size=200)

_timestamp = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
)

_json_serializable_result = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-1_000_000, max_value=1_000_000),
    st.floats(
        min_value=-1_000_000.0,
        max_value=1_000_000.0,
        allow_nan=False,
        allow_infinity=False,
    ),
    st.text(min_size=0, max_size=100),
)

_retry_attempt = st.builds(
    RetryAttempt,
    attempt_number=_positive_int,
    delay=_non_negative_float,
    exception=st.builds(RuntimeError, _exception_message),
    timestamp=_timestamp,
)

_retry_attempt_list = st.lists(
    _retry_attempt,
    min_size=0,
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 2: RetryResult JSON round-trip
# ---------------------------------------------------------------------------

@given(
    success=st.booleans(),
    result=_json_serializable_result,
    exception_message=_exception_message,
    attempts=_retry_attempt_list,
    elapsed_time=_non_negative_float,
)
@settings(max_examples=100)
def test_retryresult_json_roundtrip(
    success: bool,
    result,
    exception_message: str,
    attempts: list,
    elapsed_time: float,
) -> None:
    """
        **Validates: Requirements 2.17**

        For all valid RetryResult instances constructed with arbitrary
        success (bool), result (JSON-serializable value), exception
        (Exception with arbitrary message), attempts (list of
        RetryAttempt), and elapsed_time (non-negative float), calling
        to_json() and then from_json() on the result shall produce a
        RetryResult with equivalent success flag, attempt list, and
        elapsed time values.
    """
    exception = RuntimeError(exception_message) if not success else None

    original = RetryResult(
        success=success,
        result=result,
        exception=exception,
        attempts=attempts,
        elapsed_time=elapsed_time,
    )

    json_str = original.to_json()
    restored = RetryResult.from_json(json_str)

    assert restored.success == original.success, (
        "success mismatch: expected {}, got {}".format(
            original.success, restored.success
        )
    )

    assert len(restored.attempts) == len(original.attempts), (
        "attempts length mismatch: expected {}, got {}".format(
            len(original.attempts), len(restored.attempts)
        )
    )

    for idx in range(len(original.attempts)):
        orig_attempt = original.attempts[idx]
        rest_attempt = restored.attempts[idx]

        assert rest_attempt.attempt_number == orig_attempt.attempt_number, (
            "attempt[{}].attempt_number mismatch: expected {}, got {}".format(
                idx, orig_attempt.attempt_number, rest_attempt.attempt_number
            )
        )

        assert rest_attempt.delay == orig_attempt.delay, (
            "attempt[{}].delay mismatch: expected {}, got {}".format(
                idx, orig_attempt.delay, rest_attempt.delay
            )
        )

        assert rest_attempt.timestamp == orig_attempt.timestamp, (
            "attempt[{}].timestamp mismatch: expected {}, got {}".format(
                idx, orig_attempt.timestamp, rest_attempt.timestamp
            )
        )

    assert restored.elapsed_time == original.elapsed_time, (
        "elapsed_time mismatch: expected {}, got {}".format(
            original.elapsed_time, restored.elapsed_time
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 6: RetryResult attempt_count consistency
# ---------------------------------------------------------------------------

@given(
    success=st.booleans(),
    result=_json_serializable_result,
    exception_message=_exception_message,
    attempts=_retry_attempt_list,
    elapsed_time=_non_negative_float,
)
@settings(max_examples=100)
def test_retryresult_attempt_count_consistency(
    success: bool,
    result,
    exception_message: str,
    attempts: list,
    elapsed_time: float,
) -> None:
    """
        **Validates: Requirements 2.13**

        For all valid RetryResult instances, the attempt_count property
        shall equal len(attempts) + 1 (the initial attempt plus all
        retry attempts).
    """
    exception = RuntimeError(exception_message) if not success else None

    retry_result = RetryResult(
        success=success,
        result=result,
        exception=exception,
        attempts=attempts,
        elapsed_time=elapsed_time,
    )

    expected_count = len(attempts) + 1

    assert retry_result.attempt_count == expected_count, (
        "attempt_count mismatch: expected {} (len(attempts)={} + 1), got {}".format(
            expected_count, len(attempts), retry_result.attempt_count
        )
    )

    return
