"""
    Unit tests for the automojo.agentkit.healthstatus module.
"""

from datetime import datetime

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.healthstatus import HealthStatus


def test_healthy_status():
    """
        Verify that a healthy HealthStatus is constructed correctly.
    """
    status = HealthStatus("db-check", "healthy", response_time=0.05)
    assert status.check_name == "db-check", "check_name should match"
    assert status.status == "healthy", "status should be healthy"
    assert status.is_healthy is True, "is_healthy should be True"
    return


def test_unhealthy_status():
    """
        Verify that an unhealthy HealthStatus is constructed correctly.
    """
    status = HealthStatus("db-check", "unhealthy", detail="connection refused")
    assert status.is_healthy is False, "is_healthy should be False"
    assert status.detail == "connection refused", "detail should match"
    return


def test_degraded_status():
    """
        Verify that a degraded HealthStatus is constructed correctly.
    """
    status = HealthStatus("cache-check", "degraded")
    assert status.is_healthy is False, "is_healthy should be False for degraded"
    return


def test_invalid_status_raises_semantic_error():
    """
        Verify that invalid status values raise SemanticError.
    """
    caught = False
    try:
        HealthStatus("check", "invalid")
    except SemanticError:
        caught = True
    assert caught is True, "should raise SemanticError for invalid status"
    return


def test_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    original = HealthStatus("db-check", "healthy", detail="ok", response_time=0.1, timestamp=ts)
    json_str = original.to_json()
    restored = HealthStatus.from_json(json_str)

    assert restored.check_name == original.check_name, "check_name should match"
    assert restored.status == original.status, "status should match"
    assert restored.detail == original.detail, "detail should match"
    return
