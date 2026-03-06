"""
    Unit tests for the automojo.agentkit.retryattempt module.

    Tests RetryAttempt construction, properties, serialization, __repr__,
    and __str__.
"""

import json

from datetime import datetime

from automojo.agentkit.retryattempt import RetryAttempt


def test_retry_attempt_construction():
    """
        Verify that RetryAttempt stores all fields correctly.
    """
    ts = datetime(2026, 1, 15, 10, 30, 0)
    exc = ValueError("test error")
    attempt = RetryAttempt(attempt_number=2, delay=1.5, exception=exc, timestamp=ts)

    assert attempt.attempt_number == 2, "attempt_number should be 2"
    assert attempt.delay == 1.5, "delay should be 1.5"
    assert attempt.exception is exc, "exception should be the provided exception"
    assert attempt.timestamp == ts, "timestamp should match"
    return


def test_retry_attempt_default_timestamp():
    """
        Verify that RetryAttempt generates a timestamp when not provided.
    """
    exc = RuntimeError("fail")
    attempt = RetryAttempt(attempt_number=1, delay=0.5, exception=exc)

    assert attempt.timestamp is not None, "timestamp should be auto-generated"
    return


def test_retry_attempt_as_dict():
    """
        Verify that as_dict returns the expected dictionary.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    exc = ValueError("bad value")
    attempt = RetryAttempt(attempt_number=1, delay=2.0, exception=exc, timestamp=ts)

    data = attempt.as_dict()
    assert data["attempt_number"] == 1, "attempt_number should be 1"
    assert data["delay"] == 2.0, "delay should be 2.0"
    assert "ValueError" in data["exception"], "exception should contain type name"
    assert "bad value" in data["exception"], "exception should contain message"
    assert data["timestamp"] == ts.isoformat(), "timestamp should be ISO format"
    return


def test_retry_attempt_to_json():
    """
        Verify that to_json returns valid JSON.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    exc = RuntimeError("timeout")
    attempt = RetryAttempt(attempt_number=3, delay=4.0, exception=exc, timestamp=ts)

    json_str = attempt.to_json()
    data = json.loads(json_str)
    assert data["attempt_number"] == 3, "JSON should contain attempt_number"
    assert data["delay"] == 4.0, "JSON should contain delay"
    return


def test_retry_attempt_from_dict():
    """
        Verify that from_dict reconstructs a RetryAttempt.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    data = {
        "attempt_number": 2,
        "delay": 1.0,
        "exception": "ValueError(bad input)",
        "timestamp": ts.isoformat()
    }
    attempt = RetryAttempt.from_dict(data)

    assert attempt.attempt_number == 2, "attempt_number should be 2"
    assert attempt.delay == 1.0, "delay should be 1.0"
    assert attempt.timestamp == ts, "timestamp should match"
    return


def test_retry_attempt_from_json():
    """
        Verify that from_json reconstructs a RetryAttempt.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    data = {
        "attempt_number": 1,
        "delay": 0.5,
        "exception": "IOError(disk full)",
        "timestamp": ts.isoformat()
    }
    json_str = json.dumps(data)
    attempt = RetryAttempt.from_json(json_str)

    assert attempt.attempt_number == 1, "attempt_number should be 1"
    assert attempt.delay == 0.5, "delay should be 0.5"
    return


def test_retry_attempt_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    exc = ValueError("round trip test")
    original = RetryAttempt(attempt_number=2, delay=3.0, exception=exc, timestamp=ts)

    json_str = original.to_json()
    restored = RetryAttempt.from_json(json_str)

    assert restored.attempt_number == original.attempt_number, "attempt_number should match"
    assert restored.delay == original.delay, "delay should match"
    assert restored.timestamp == original.timestamp, "timestamp should match"
    return


def test_retry_attempt_repr():
    """
        Verify that __repr__ includes class name and attempt number.
    """
    exc = RuntimeError("fail")
    attempt = RetryAttempt(attempt_number=1, delay=0.5, exception=exc)
    repr_str = repr(attempt)

    assert "RetryAttempt" in repr_str, "repr should contain class name"
    assert "1" in repr_str, "repr should contain attempt number"
    assert "RuntimeError" in repr_str, "repr should contain exception type"
    return


def test_retry_attempt_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    exc = ValueError("bad")
    attempt = RetryAttempt(attempt_number=2, delay=1.5, exception=exc)
    str_val = str(attempt)

    assert "2" in str_val, "str should contain attempt number"
    assert "1.50" in str_val, "str should contain delay"
    return
