"""
    Unit tests for the ccai.agentkit.retryresult module.

    Tests RetryResult construction, properties, is_success, attempt_count,
    and serialization.
"""

import json

from datetime import datetime

from ccai.agentkit.retryattempt import RetryAttempt
from ccai.agentkit.retryresult import RetryResult


def test_retry_result_success_construction():
    """
        Verify that a successful RetryResult stores fields correctly.
    """
    result = RetryResult(success=True, result="ok", elapsed_time=0.5)

    assert result.success is True, "success should be True"
    assert result.result == "ok", "result should be 'ok'"
    assert result.exception is None, "exception should be None on success"
    assert result.elapsed_time == 0.5, "elapsed_time should be 0.5"
    return


def test_retry_result_failure_construction():
    """
        Verify that a failed RetryResult stores fields correctly.
    """
    exc = ValueError("failed")
    ts = datetime(2026, 3, 1, 12, 0, 0)
    attempt = RetryAttempt(attempt_number=1, delay=1.0, exception=exc, timestamp=ts)
    result = RetryResult(success=False, exception=exc, attempts=[attempt], elapsed_time=2.0)

    assert result.success is False, "success should be False"
    assert result.exception is exc, "exception should match"
    assert len(result.attempts) == 1, "should have 1 attempt"
    return


def test_retry_result_is_success():
    """
        Verify that is_success returns the success flag.
    """
    success_result = RetryResult(success=True, result=42)
    failure_result = RetryResult(success=False, exception=RuntimeError("fail"))

    assert success_result.is_success is True, "is_success should be True for success"
    assert failure_result.is_success is False, "is_success should be False for failure"
    return


def test_retry_result_attempt_count_no_retries():
    """
        Verify that attempt_count is 1 when there are no retry attempts.
    """
    result = RetryResult(success=True, result="ok")
    assert result.attempt_count == 1, "attempt_count should be 1 with no retries"
    return


def test_retry_result_attempt_count_with_retries():
    """
        Verify that attempt_count includes initial attempt plus retries.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    exc = RuntimeError("fail")
    attempts = [
        RetryAttempt(attempt_number=1, delay=1.0, exception=exc, timestamp=ts),
        RetryAttempt(attempt_number=2, delay=2.0, exception=exc, timestamp=ts),
    ]
    result = RetryResult(success=True, result="ok", attempts=attempts, elapsed_time=3.0)

    assert result.attempt_count == 3, "attempt_count should be 3 (1 initial + 2 retries)"
    return


def test_retry_result_as_dict():
    """
        Verify that as_dict returns the expected dictionary.
    """
    result = RetryResult(success=True, result="value", elapsed_time=1.0)
    data = result.as_dict()

    assert data["success"] is True, "success should be True"
    assert data["result"] == "value", "result should be 'value'"
    assert data["exception"] is None, "exception should be None"
    assert data["elapsed_time"] == 1.0, "elapsed_time should be 1.0"
    assert data["attempts"] == [], "attempts should be empty list"
    return


def test_retry_result_to_json():
    """
        Verify that to_json returns valid JSON.
    """
    result = RetryResult(success=True, result="ok", elapsed_time=0.5)
    json_str = result.to_json()
    data = json.loads(json_str)

    assert data["success"] is True, "JSON should contain success"
    return


def test_retry_result_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    exc = ValueError("test")
    attempts = [
        RetryAttempt(attempt_number=1, delay=1.0, exception=exc, timestamp=ts),
    ]
    original = RetryResult(success=False, exception=exc, attempts=attempts, elapsed_time=2.5)

    json_str = original.to_json()
    restored = RetryResult.from_json(json_str)

    assert restored.success == original.success, "success should match"
    assert restored.elapsed_time == original.elapsed_time, "elapsed_time should match"
    assert len(restored.attempts) == len(original.attempts), "attempt count should match"
    return


def test_retry_result_repr():
    """
        Verify that __repr__ includes class name and success flag.
    """
    result = RetryResult(success=True, result="ok")
    repr_str = repr(result)

    assert "RetryResult" in repr_str, "repr should contain class name"
    assert "True" in repr_str, "repr should contain success flag"
    return


def test_retry_result_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    result = RetryResult(success=False, exception=RuntimeError("fail"), elapsed_time=1.234)
    str_val = str(result)

    assert "False" in str_val, "str should contain success flag"
    assert "1.234" in str_val, "str should contain elapsed time"
    return
