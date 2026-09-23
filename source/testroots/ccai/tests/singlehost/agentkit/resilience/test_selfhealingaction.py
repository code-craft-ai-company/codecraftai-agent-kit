"""
    Unit tests for self-healing action implementations.
"""

from ccai.testbase.mocking import Mock

from ccai.agentkit.circuitbreaker import CircuitBreaker
from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.clearcacheaction import ClearCacheAction
from ccai.agentkit.healthstatus import HealthStatus
from ccai.agentkit.reconnecttransportaction import ReconnectTransportAction
from ccai.agentkit.resetcircuitbreakeraction import ResetCircuitBreakerAction


def test_reconnect_transport_action_success():
    """
        Verify ReconnectTransportAction returns success when transport reconnects.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    ctx = mock_transport.mock_context()
    ctx.mock_method("disconnect", return_value=None)
    ctx.mock_method("connect", return_value=None)

    action = ReconnectTransportAction(mock_transport)
    status = HealthStatus("transport-check", "unhealthy", detail="not connected")
    result = action.heal("transport-check", status)

    assert result.is_success is True, "should succeed when transport reconnects"
    assert result.action_name == "reconnect_transport", "action_name should match"
    assert result.check_name == "transport-check", "check_name should match"
    return


def test_reconnect_transport_action_failure():
    """
        Verify ReconnectTransportAction returns failure when disconnect raises.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    ctx = mock_transport.mock_context()

    def raise_disconnect():
        raise ConnectionError("cannot disconnect")

    ctx.mock_method("disconnect", side_effect=raise_disconnect)

    action = ReconnectTransportAction(mock_transport)
    status = HealthStatus("transport-check", "unhealthy")
    result = action.heal("transport-check", status)

    assert result.is_success is False, "should fail when disconnect raises"
    assert result.error_message == "cannot disconnect", "error_message should match"
    return


def test_reconnect_transport_action_connect_failure():
    """
        Verify ReconnectTransportAction returns failure when connect raises.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    ctx = mock_transport.mock_context()
    ctx.mock_method("disconnect", return_value=None)

    def raise_connect():
        raise ConnectionError("cannot connect")

    ctx.mock_method("connect", side_effect=raise_connect)

    action = ReconnectTransportAction(mock_transport)
    status = HealthStatus("transport-check", "unhealthy")
    result = action.heal("transport-check", status)

    assert result.is_success is False, "should fail when connect raises"
    assert result.error_message == "cannot connect", "error_message should match"
    return


def test_clear_cache_action_success():
    """
        Verify ClearCacheAction returns success when callable succeeds.
    """
    cleared = []

    def clear_fn():
        cleared.append(True)

    action = ClearCacheAction(clear_fn)
    status = HealthStatus("cache-check", "unhealthy")
    result = action.heal("cache-check", status)

    assert result.is_success is True, "should succeed when clear callable works"
    assert result.action_name == "clear_cache", "action_name should match"
    assert len(cleared) == 1, "clear callable should have been invoked"
    return


def test_clear_cache_action_failure():
    """
        Verify ClearCacheAction returns failure when callable raises.
    """
    def raise_clear():
        raise RuntimeError("cache locked")

    action = ClearCacheAction(raise_clear)
    status = HealthStatus("cache-check", "unhealthy")
    result = action.heal("cache-check", status)

    assert result.is_success is False, "should fail when clear callable raises"
    assert result.error_message == "cache locked", "error_message should match"
    return


def test_reset_circuit_breaker_action_success():
    """
        Verify ResetCircuitBreakerAction resets a circuit breaker to CLOSED.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=1, success_threshold=1,
        open_state_timeout=30.0, half_open_max_attempts=1
    )
    cb = CircuitBreaker("cb-test", config)

    # Trigger OPEN state
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        # Expected: the deliberately failing call is recorded by the circuit breaker;
        # the propagated exception itself is not what this test verifies.
        pass

    assert cb.state == CircuitBreakerState.OPEN, "should be OPEN before healing"

    action = ResetCircuitBreakerAction(cb)
    status = HealthStatus("cb-check", "degraded")
    result = action.heal("cb-check", status)

    assert result.is_success is True, "should succeed"
    assert cb.state == CircuitBreakerState.CLOSED, "should be CLOSED after healing"
    return


def test_reset_circuit_breaker_action_name():
    """
        Verify ResetCircuitBreakerAction has correct action_name.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=2,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    cb = CircuitBreaker("cb-test", config)
    action = ResetCircuitBreakerAction(cb)

    assert action.action_name == "reset_circuit_breaker", "action_name should match"
    return


def test_self_healing_action_repr():
    """
        Verify __repr__ for self-healing actions.
    """
    def noop():
        pass

    action = ClearCacheAction(noop)
    repr_str = repr(action)

    assert "ClearCacheAction" in repr_str, "repr should contain class name"
    assert "clear_cache" in repr_str, "repr should contain action_name"
    return


def test_self_healing_action_str():
    """
        Verify __str__ for self-healing actions.
    """
    def noop():
        pass

    action = ClearCacheAction(noop)
    str_val = str(action)

    assert "clear_cache" in str_val, "str should contain action_name"
    return
