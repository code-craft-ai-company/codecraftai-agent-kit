"""
    Unit tests for SelfHealingResult.
"""

import json

from datetime import datetime

from automojo.agentkit.selfhealingresult import SelfHealingResult


def test_selfhealingresult_construction():
    """
        Verify SelfHealingResult stores all fields correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    result = SelfHealingResult(
        check_name="transport-check",
        action_name="reconnect_transport",
        success=True,
        error_message=None,
        attempt_number=1,
        timestamp=ts
    )

    assert result.check_name == "transport-check", "check_name should match"
    assert result.action_name == "reconnect_transport", "action_name should match"
    assert result.success is True, "success should be True"
    assert result.error_message is None, "error_message should be None"
    assert result.attempt_number == 1, "attempt_number should match"
    assert result.timestamp == ts, "timestamp should match"
    return


def test_selfhealingresult_is_success_true():
    """
        Verify is_success returns True when success is True.
    """
    result = SelfHealingResult("check", "action", True)

    assert result.is_success is True, "is_success should be True"
    return


def test_selfhealingresult_is_success_false():
    """
        Verify is_success returns False when success is False.
    """
    result = SelfHealingResult("check", "action", False, error_message="failed")

    assert result.is_success is False, "is_success should be False"
    return


def test_selfhealingresult_default_timestamp():
    """
        Verify SelfHealingResult auto-generates timestamp when not provided.
    """
    result = SelfHealingResult("check", "action", True)

    assert isinstance(result.timestamp, datetime), "timestamp should be a datetime"
    return


def test_selfhealingresult_default_attempt_number():
    """
        Verify SelfHealingResult defaults attempt_number to 1.
    """
    result = SelfHealingResult("check", "action", True)

    assert result.attempt_number == 1, "default attempt_number should be 1"
    return


def test_selfhealingresult_as_dict():
    """
        Verify as_dict returns correct dictionary.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    result = SelfHealingResult(
        check_name="transport-check",
        action_name="reconnect_transport",
        success=False,
        error_message="connection refused",
        attempt_number=2,
        timestamp=ts
    )

    data = result.as_dict()

    assert data["check_name"] == "transport-check", "check_name should match"
    assert data["action_name"] == "reconnect_transport", "action_name should match"
    assert data["success"] is False, "success should be False"
    assert data["error_message"] == "connection refused", "error_message should match"
    assert data["attempt_number"] == 2, "attempt_number should match"
    assert data["timestamp"] == ts.isoformat(), "timestamp should match"
    return


def test_selfhealingresult_to_json():
    """
        Verify to_json produces valid JSON.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    result = SelfHealingResult("check", "action", True, timestamp=ts)

    json_str = result.to_json()
    data = json.loads(json_str)

    assert data["check_name"] == "check", "check_name should match"
    assert data["success"] is True, "success should be True"
    return


def test_selfhealingresult_from_dict():
    """
        Verify from_dict constructs a SelfHealingResult correctly.
    """
    data = {
        "check_name": "transport-check",
        "action_name": "reconnect_transport",
        "success": True,
        "error_message": None,
        "attempt_number": 1,
        "timestamp": "2025-01-15T10:30:00"
    }

    result = SelfHealingResult.from_dict(data)

    assert result.check_name == "transport-check", "check_name should match"
    assert result.action_name == "reconnect_transport", "action_name should match"
    assert result.success is True, "success should be True"
    assert result.attempt_number == 1, "attempt_number should match"
    return


def test_selfhealingresult_from_json():
    """
        Verify from_json round-trip works correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    original = SelfHealingResult(
        check_name="cb-check",
        action_name="reset_circuit_breaker",
        success=False,
        error_message="reset failed",
        attempt_number=3,
        timestamp=ts
    )

    json_str = original.to_json()
    restored = SelfHealingResult.from_json(json_str)

    assert restored.check_name == original.check_name, "check_name should match"
    assert restored.action_name == original.action_name, "action_name should match"
    assert restored.success == original.success, "success should match"
    assert restored.error_message == original.error_message, "error_message should match"
    assert restored.attempt_number == original.attempt_number, "attempt_number should match"
    return


def test_selfhealingresult_repr():
    """
        Verify __repr__ contains key fields.
    """
    result = SelfHealingResult("check", "action", True)
    repr_str = repr(result)

    assert "SelfHealingResult" in repr_str, "repr should contain class name"
    assert "check" in repr_str, "repr should contain check_name"
    return


def test_selfhealingresult_str():
    """
        Verify __str__ contains key fields.
    """
    result = SelfHealingResult("check", "action", False, attempt_number=2)
    str_val = str(result)

    assert "check" in str_val, "str should contain check_name"
    assert "action" in str_val, "str should contain action_name"
    assert "2" in str_val, "str should contain attempt_number"
    return
