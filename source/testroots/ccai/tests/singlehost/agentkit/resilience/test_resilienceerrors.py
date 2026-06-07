"""
    Unit tests for the ccai.agentkit.resilienceerrors module.

    Tests CircuitBreakerOpenError and ResilienceError construction,
    properties, and __repr__.
"""

from ccai.agentkit.errors import AgentKitError
from ccai.agentkit.resilienceerrors import CircuitBreakerOpenError
from ccai.agentkit.resilienceerrors import ResilienceError


def test_resilience_error_inherits_from_agentkit_error():
    """
        Verify that ResilienceError inherits from AgentKitError.
    """
    err = ResilienceError("resilience failure")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "ResilienceError should inherit from AgentKitError"
    return


def test_resilience_error_message_property():
    """
        Verify that ResilienceError stores and exposes the message.
    """
    err = ResilienceError("something failed")
    message = err.message
    assert message == "something failed", "Message property should return the provided message"
    return


def test_resilience_error_cause_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = ResilienceError("no cause")
    cause = err.cause
    assert cause is None, "Cause should be None when not provided"
    return


def test_resilience_error_cause_chaining():
    """
        Verify that ResilienceError supports cause chaining.
    """
    original = IOError("disk full")
    err = ResilienceError("write failed", cause=original)
    cause = err.cause
    assert cause is original, "Cause should be the original exception"
    return


def test_resilience_error_repr():
    """
        Verify that ResilienceError __repr__ includes class name and message.
    """
    err = ResilienceError("test repr")
    repr_str = repr(err)
    has_class_name = "ResilienceError" in repr_str
    has_message = "test repr" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    assert has_message is True, "repr should contain the message"
    return


def test_circuit_breaker_open_error_inherits_from_agentkit_error():
    """
        Verify that CircuitBreakerOpenError inherits from AgentKitError.
    """
    err = CircuitBreakerOpenError("cb-1", "service-a", 10.5)
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "CircuitBreakerOpenError should inherit from AgentKitError"
    return


def test_circuit_breaker_open_error_properties():
    """
        Verify that CircuitBreakerOpenError exposes all properties.
    """
    err = CircuitBreakerOpenError("cb-payments", "payment-service", 25.3)
    assert err.circuit_breaker_name == "cb-payments", "circuit_breaker_name should match"
    assert err.service_name == "payment-service", "service_name should match"
    assert err.time_remaining == 25.3, "time_remaining should match"
    return


def test_circuit_breaker_open_error_message():
    """
        Verify that CircuitBreakerOpenError formats a descriptive message.
    """
    err = CircuitBreakerOpenError("cb-1", "svc-1", 5.0)
    message = err.message
    has_cb_name = "cb-1" in message
    has_svc_name = "svc-1" in message
    has_open = "OPEN" in message
    assert has_cb_name is True, "Message should contain circuit breaker name"
    assert has_svc_name is True, "Message should contain service name"
    assert has_open is True, "Message should mention OPEN state"
    return


def test_circuit_breaker_open_error_repr():
    """
        Verify that CircuitBreakerOpenError __repr__ includes key fields.
    """
    err = CircuitBreakerOpenError("cb-2", "svc-2", 12.0)
    repr_str = repr(err)
    has_class_name = "CircuitBreakerOpenError" in repr_str
    has_cb_name = "cb-2" in repr_str
    has_svc_name = "svc-2" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    assert has_cb_name is True, "repr should contain circuit breaker name"
    assert has_svc_name is True, "repr should contain service name"
    return


def test_circuit_breaker_open_error_catchable_as_agentkit_error():
    """
        Verify that CircuitBreakerOpenError can be caught as AgentKitError.
    """
    caught = False
    try:
        raise CircuitBreakerOpenError("cb-test", "svc-test", 1.0)
    except AgentKitError:
        caught = True

    assert caught is True, "CircuitBreakerOpenError should be catchable as AgentKitError"
    return
