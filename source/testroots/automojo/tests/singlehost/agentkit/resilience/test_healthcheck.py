"""
    Unit tests for health check implementations using mocks.
"""

from automojo.testbase.mocking import Mock

from automojo.agentkit.circuitbreaker import CircuitBreaker
from automojo.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from automojo.agentkit.circuitbreakerhealthcheck import CircuitBreakerHealthCheck
from automojo.agentkit.circuitbreakerstate import CircuitBreakerState
from automojo.agentkit.memorystorehealthcheck import MemoryStoreHealthCheck
from automojo.agentkit.transporthealthcheck import TransportHealthCheck


def test_transport_health_check_connected():
    """
        Verify that TransportHealthCheck returns healthy when connected.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    ctx = mock_transport.mock_context()
    ctx.mock_property("is_connected", return_value=True)

    check = TransportHealthCheck("transport-check", mock_transport)
    status = check.check()

    assert status.status == "healthy", "should be healthy when connected"
    return


def test_transport_health_check_disconnected():
    """
        Verify that TransportHealthCheck returns unhealthy when disconnected.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    ctx = mock_transport.mock_context()
    ctx.mock_property("is_connected", return_value=False)

    check = TransportHealthCheck("transport-check", mock_transport)
    status = check.check()

    assert status.status == "unhealthy", "should be unhealthy when disconnected"
    return


def test_memory_store_health_check_healthy():
    """
        Verify that MemoryStoreHealthCheck returns healthy when ping succeeds.
    """
    mock_store = Mock()
    mock_store.configure(recursive=True)
    ctx = mock_store.mock_context()
    ctx.mock_method("ping", return_value=None)

    check = MemoryStoreHealthCheck("memory-check", mock_store)
    status = check.check()

    assert status.status == "healthy", "should be healthy when ping succeeds"
    return


def test_memory_store_health_check_unhealthy():
    """
        Verify that MemoryStoreHealthCheck returns unhealthy when ping fails.
    """
    mock_store = Mock()
    mock_store.configure(recursive=True)
    ctx = mock_store.mock_context()

    def raise_error():
        raise RuntimeError("connection refused")

    ctx.mock_method("ping", side_effect=raise_error)

    check = MemoryStoreHealthCheck("memory-check", mock_store)
    status = check.check()

    assert status.status == "unhealthy", "should be unhealthy when ping fails"
    return


def test_circuit_breaker_health_check_closed():
    """
        Verify that CircuitBreakerHealthCheck returns healthy when CLOSED.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=2,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    cb = CircuitBreaker("cb-test", config)

    check = CircuitBreakerHealthCheck("cb-check", cb)
    status = check.check()

    assert status.status == "healthy", "should be healthy when CLOSED"
    return


def test_circuit_breaker_health_check_open():
    """
        Verify that CircuitBreakerHealthCheck returns degraded when OPEN.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=1, success_threshold=1,
        open_state_timeout=30.0, half_open_max_attempts=1
    )
    cb = CircuitBreaker("cb-test", config)

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    check = CircuitBreakerHealthCheck("cb-check", cb)
    status = check.check()

    assert status.status == "degraded", "should be degraded when OPEN"
    return


def test_health_check_name_and_interval():
    """
        Verify that HealthCheck exposes name and check_interval.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    check = TransportHealthCheck("my-check", mock_transport, check_interval=60.0)

    assert check.name == "my-check", "name should match"
    assert check.check_interval == 60.0, "check_interval should match"
    return
