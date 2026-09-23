"""
    Unit tests for the ccai.agentkit.circuitbreakerregistry module.

    Tests register, deregister, lookup, list_all, count, has_circuit_breaker,
    reset_all, and duplicate name error.
"""

from ccai.agentkit.circuitbreaker import CircuitBreaker
from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from ccai.agentkit.circuitbreakerregistry import CircuitBreakerRegistry
from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.errors import SemanticError


def _make_cb(name):
    """
        Helper to create a CircuitBreaker with default config.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=3, success_threshold=2,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    return CircuitBreaker(name, config)


def test_register_and_lookup():
    """
        Verify that a registered CircuitBreaker can be looked up by name.
    """
    registry = CircuitBreakerRegistry()
    cb = _make_cb("cb-1")
    registry.register(cb)

    found = registry.lookup("cb-1")
    assert found is cb, "lookup should return the registered circuit breaker"
    return


def test_lookup_returns_none_for_unknown():
    """
        Verify that lookup returns None for unregistered names.
    """
    registry = CircuitBreakerRegistry()
    found = registry.lookup("nonexistent")
    assert found is None, "lookup should return None for unknown names"
    return


def test_deregister():
    """
        Verify that deregister removes a circuit breaker.
    """
    registry = CircuitBreakerRegistry()
    cb = _make_cb("cb-1")
    registry.register(cb)
    registry.deregister("cb-1")

    found = registry.lookup("cb-1")
    assert found is None, "should be None after deregister"
    assert registry.count == 0, "count should be 0 after deregister"
    return


def test_duplicate_name_raises_semantic_error():
    """
        Verify that registering a duplicate name raises SemanticError.
    """
    registry = CircuitBreakerRegistry()
    cb1 = _make_cb("cb-1")
    cb2 = _make_cb("cb-1")
    registry.register(cb1)

    caught = False
    try:
        registry.register(cb2)
    except SemanticError as err:
        caught = True
        assert "cb-1" in err.message, "error should contain the duplicate name"

    assert caught is True, "should raise SemanticError for duplicate name"
    return


def test_list_all():
    """
        Verify that list_all returns all registered circuit breakers.
    """
    registry = CircuitBreakerRegistry()
    cb1 = _make_cb("cb-1")
    cb2 = _make_cb("cb-2")
    registry.register(cb1)
    registry.register(cb2)

    all_cbs = registry.list_all()
    assert len(all_cbs) == 2, "should have 2 circuit breakers"
    return


def test_count():
    """
        Verify that count returns the number of registered circuit breakers.
    """
    registry = CircuitBreakerRegistry()
    assert registry.count == 0, "initial count should be 0"

    registry.register(_make_cb("cb-1"))
    assert registry.count == 1, "count should be 1"

    registry.register(_make_cb("cb-2"))
    assert registry.count == 2, "count should be 2"
    return


def test_has_circuit_breaker():
    """
        Verify that has_circuit_breaker returns correct boolean.
    """
    registry = CircuitBreakerRegistry()
    registry.register(_make_cb("cb-1"))

    assert registry.has_circuit_breaker("cb-1") is True, "should return True for registered"
    assert registry.has_circuit_breaker("cb-2") is False, "should return False for unregistered"
    return


def test_reset_all():
    """
        Verify that reset_all resets all registered circuit breakers.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=1, success_threshold=1,
        open_state_timeout=30.0, half_open_max_attempts=1
    )
    cb = CircuitBreaker("cb-1", config)

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        # Expected: the deliberately failing call is recorded by the circuit breaker;
        # the propagated exception itself is not what this test verifies.
        pass

    assert cb.state is CircuitBreakerState.OPEN, "should be OPEN"

    registry = CircuitBreakerRegistry()
    registry.register(cb)
    registry.reset_all()

    assert cb.state is CircuitBreakerState.CLOSED, "should be CLOSED after reset_all"
    return


def test_repr():
    """
        Verify that __repr__ includes class name and count.
    """
    registry = CircuitBreakerRegistry()
    repr_str = repr(registry)
    assert "CircuitBreakerRegistry" in repr_str, "repr should contain class name"
    assert "0" in repr_str, "repr should contain count"
    return


def test_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    registry = CircuitBreakerRegistry()
    registry.register(_make_cb("cb-1"))
    str_val = str(registry)
    assert "cb-1" in str_val, "str should contain circuit breaker name"
    return
