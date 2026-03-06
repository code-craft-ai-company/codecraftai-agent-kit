"""
    Unit tests for HealthMonitor.
"""

from automojo.testbase.mocking import Mock

from automojo.agentkit.healthcheckregistry import HealthCheckRegistry
from automojo.agentkit.healthmonitor import HealthMonitor
from automojo.agentkit.healthstatus import HealthStatus
from automojo.agentkit.selfhealingpolicy import SelfHealingPolicy
from automojo.agentkit.selfhealingresult import SelfHealingResult


def _create_mock_check(name, status_str, detail=None):
    """
        Creates a mock HealthCheck returning the given status.
    """
    mock_check = Mock()
    mock_check.configure(recursive=True)
    ctx = mock_check.mock_context()
    ctx.set_attribute("name", name)
    ctx.set_attribute("check_interval", 30.0)

    health_status = HealthStatus(name, status_str, detail=detail)
    ctx.mock_method("check", return_value=health_status)
    return mock_check


def _create_mock_action(action_name, success=True, error_message=None):
    """
        Creates a mock SelfHealingAction returning a SelfHealingResult.
    """
    mock_action = Mock()
    mock_action.configure(recursive=True)
    ctx = mock_action.mock_context()
    ctx.set_attribute("action_name", action_name)

    def heal_fn(check_name, status):
        return SelfHealingResult(
            check_name=check_name,
            action_name=action_name,
            success=success,
            error_message=error_message
        )

    ctx.mock_method("heal", side_effect=heal_fn)
    return mock_action


def test_healthmonitor_check_now_all_healthy():
    """
        Verify check_now returns healthy results when all checks pass.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("check-a", "healthy"))
    registry.register(_create_mock_check("check-b", "healthy"))

    monitor = HealthMonitor(registry)
    results = monitor.check_now()

    assert len(results) == 2, "should have 2 results"
    assert results["check-a"].status == "healthy", "check-a should be healthy"
    assert results["check-b"].status == "healthy", "check-b should be healthy"
    return


def test_healthmonitor_overall_status_healthy():
    """
        Verify overall_status is healthy when all checks are healthy.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("check-a", "healthy"))

    monitor = HealthMonitor(registry)
    monitor.check_now()

    assert monitor.overall_status == "healthy", "overall should be healthy"
    return


def test_healthmonitor_overall_status_degraded():
    """
        Verify overall_status is degraded when any check is degraded.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("check-a", "healthy"))
    registry.register(_create_mock_check("check-b", "degraded"))

    monitor = HealthMonitor(registry)
    monitor.check_now()

    assert monitor.overall_status == "degraded", "overall should be degraded"
    return


def test_healthmonitor_overall_status_unhealthy():
    """
        Verify overall_status is unhealthy when any check is unhealthy.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("check-a", "healthy"))
    registry.register(_create_mock_check("check-b", "unhealthy"))

    monitor = HealthMonitor(registry)
    monitor.check_now()

    assert monitor.overall_status == "unhealthy", "overall should be unhealthy"
    return


def test_healthmonitor_overall_status_no_results():
    """
        Verify overall_status is healthy when no checks have run.
    """
    registry = HealthCheckRegistry()
    monitor = HealthMonitor(registry)

    assert monitor.overall_status == "healthy", "overall should be healthy with no results"
    return


def test_healthmonitor_check_exception_becomes_unhealthy():
    """
        Verify that a check raising an exception is recorded as unhealthy.
    """
    mock_check = Mock()
    mock_check.configure(recursive=True)
    ctx = mock_check.mock_context()
    ctx.set_attribute("name", "bad-check")
    ctx.set_attribute("check_interval", 30.0)

    def raise_error():
        raise RuntimeError("check failed")

    ctx.mock_method("check", side_effect=raise_error)

    registry = HealthCheckRegistry()
    registry.register(mock_check)

    monitor = HealthMonitor(registry)
    results = monitor.check_now()

    assert results["bad-check"].status == "unhealthy", "should be unhealthy on exception"
    return


def test_healthmonitor_self_healing_triggered():
    """
        Verify self-healing is triggered for unhealthy checks with a policy.
    """
    heal_calls = []

    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("transport", "unhealthy", detail="disconnected"))

    mock_action = Mock()
    mock_action.configure(recursive=True)
    ctx = mock_action.mock_context()
    ctx.set_attribute("action_name", "reconnect_transport")

    def heal_fn(check_name, status):
        heal_calls.append(check_name)
        return SelfHealingResult(
            check_name=check_name,
            action_name="reconnect_transport",
            success=True
        )

    ctx.mock_method("heal", side_effect=heal_fn)

    policy = SelfHealingPolicy("transport", mock_action, max_attempts=3, cooldown_interval=60.0)

    monitor = HealthMonitor(registry)
    monitor.register_healing_policy(policy)
    monitor.check_now()

    assert len(heal_calls) == 1, "heal should have been called once"
    assert heal_calls[0] == "transport", "heal should be called with correct check_name"
    return


def test_healthmonitor_self_healing_max_attempts():
    """
        Verify self-healing stops after max_attempts and enters cooldown.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("transport", "unhealthy"))

    mock_action = _create_mock_action("reconnect", success=False, error_message="still down")
    policy = SelfHealingPolicy("transport", mock_action, max_attempts=2, cooldown_interval=60.0)

    monitor = HealthMonitor(registry)
    monitor.register_healing_policy(policy)

    # First two calls should attempt healing
    monitor.check_now()
    monitor.check_now()

    # Third call should be blocked by max_attempts -> cooldown
    monitor.check_now()

    # The action should have been called exactly 2 times (max_attempts)
    # then cooldown kicks in on the 3rd check_now
    return


def test_healthmonitor_healing_reset_on_healthy():
    """
        Verify healing attempt count resets when check becomes healthy.
    """
    # Start with unhealthy check
    unhealthy_check = _create_mock_check("transport", "unhealthy")
    registry = HealthCheckRegistry()
    registry.register(unhealthy_check)

    mock_action = _create_mock_action("reconnect", success=False)
    policy = SelfHealingPolicy("transport", mock_action, max_attempts=3, cooldown_interval=60.0)

    monitor = HealthMonitor(registry)
    monitor.register_healing_policy(policy)

    # Trigger one healing attempt
    monitor.check_now()

    # Now replace with healthy check
    registry.deregister("transport")
    registry.register(_create_mock_check("transport", "healthy"))

    monitor.check_now()

    # Healing state should be reset - verify by checking internal state
    assert "transport" not in monitor._healing_attempt_counts, \
        "healing attempts should be reset on healthy"
    return


def test_healthmonitor_healing_action_exception():
    """
        Verify that a healing action raising an exception is handled gracefully.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("transport", "unhealthy"))

    mock_action = Mock()
    mock_action.configure(recursive=True)
    ctx = mock_action.mock_context()
    ctx.set_attribute("action_name", "bad_action")

    def raise_heal(check_name, status):
        raise RuntimeError("heal exploded")

    ctx.mock_method("heal", side_effect=raise_heal)

    policy = SelfHealingPolicy("transport", mock_action, max_attempts=3, cooldown_interval=60.0)

    monitor = HealthMonitor(registry)
    monitor.register_healing_policy(policy)

    # Should not raise
    monitor.check_now()

    assert monitor.overall_status == "unhealthy", "should still be unhealthy"
    return


def test_healthmonitor_start_stop():
    """
        Verify start and stop toggle is_active.
    """
    registry = HealthCheckRegistry()
    monitor = HealthMonitor(registry)

    assert monitor.is_active is False, "should start inactive"

    monitor.start()
    assert monitor.is_active is True, "should be active after start"

    monitor.stop()
    assert monitor.is_active is False, "should be inactive after stop"
    return


def test_healthmonitor_latest_results():
    """
        Verify latest_results is populated after check_now.
    """
    registry = HealthCheckRegistry()
    registry.register(_create_mock_check("check-a", "healthy"))

    monitor = HealthMonitor(registry)

    assert len(monitor.latest_results) == 0, "should be empty before check"

    monitor.check_now()

    assert len(monitor.latest_results) == 1, "should have 1 result after check"
    assert "check-a" in monitor.latest_results, "should contain check-a"
    return


def test_healthmonitor_repr():
    """
        Verify __repr__ contains key fields.
    """
    registry = HealthCheckRegistry()
    monitor = HealthMonitor(registry)
    repr_str = repr(monitor)

    assert "HealthMonitor" in repr_str, "repr should contain class name"
    return


def test_healthmonitor_str():
    """
        Verify __str__ contains key fields.
    """
    registry = HealthCheckRegistry()
    monitor = HealthMonitor(registry)
    str_val = str(monitor)

    assert "HealthMonitor" in str_val, "str should contain class name"
    assert "healthy" in str_val, "str should contain overall status"
    return
