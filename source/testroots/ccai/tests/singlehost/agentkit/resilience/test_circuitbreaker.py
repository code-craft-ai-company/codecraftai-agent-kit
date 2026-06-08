"""
    Unit tests for the ccai.agentkit.circuitbreaker module.

    Tests CircuitBreaker initial state, state transitions, reset,
    event recording, and error handling.
"""

from ccai.agentkit.circuitbreaker import CircuitBreaker
from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.resilienceerrors import CircuitBreakerOpenError


def _make_config(failure_threshold=3, success_threshold=2,
                 open_state_timeout=0.01, half_open_max_attempts=3):
    """
        Helper to create a CircuitBreakerConfiguration with short timeouts.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        open_state_timeout=open_state_timeout,
        half_open_max_attempts=half_open_max_attempts
    )
    return config


def test_initial_state_is_closed():
    """
        Verify that a new CircuitBreaker starts in the CLOSED state.
    """
    cb = CircuitBreaker("cb-test", _make_config())
    assert cb.state is CircuitBreakerState.CLOSED, "initial state should be CLOSED"
    assert cb.failure_count == 0, "initial failure count should be 0"
    assert cb.success_count == 0, "initial success count should be 0"
    return


def test_closed_state_passes_through():
    """
        Verify that requests pass through in CLOSED state.
    """
    cb = CircuitBreaker("cb-test", _make_config())
    result = cb.execute(lambda: "ok")
    assert result == "ok", "should return callable result"
    return


def test_closed_to_open_on_failure_threshold():
    """
        Verify that CircuitBreaker transitions from CLOSED to OPEN when
        failure threshold is reached.
    """
    cb = CircuitBreaker("cb-test", _make_config(failure_threshold=3))

    for i in range(3):
        caught = False
        try:
            cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
        except ValueError:
            caught = True
        assert caught is True, "exception should propagate"

    assert cb.state is CircuitBreakerState.OPEN, "state should be OPEN after threshold"
    assert cb.failure_count == 3, "failure count should be 3"
    return


def test_open_state_rejects_requests():
    """
        Verify that OPEN state rejects all requests with CircuitBreakerOpenError.
    """
    cb = CircuitBreaker("cb-test", _make_config(failure_threshold=1, open_state_timeout=10.0))

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    assert cb.state is CircuitBreakerState.OPEN, "state should be OPEN"

    caught = False
    try:
        cb.execute(lambda: "should not run")
    except CircuitBreakerOpenError as err:
        caught = True
        assert err.circuit_breaker_name == "cb-test", "should contain CB name"

    assert caught is True, "should raise CircuitBreakerOpenError"
    return


def test_open_to_half_open_after_timeout():
    """
        Verify that CircuitBreaker transitions from OPEN to HALF_OPEN
        after the timeout elapses.
    """
    import time

    cb = CircuitBreaker("cb-test", _make_config(failure_threshold=1, open_state_timeout=0.01))

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    time.sleep(0.02)

    # Next call should transition to HALF_OPEN and execute
    result = cb.execute(lambda: "recovered")
    assert result == "recovered", "should execute in HALF_OPEN"
    return


def test_half_open_to_closed_on_success_threshold():
    """
        Verify that CircuitBreaker transitions from HALF_OPEN to CLOSED
        when success threshold is reached.
    """
    import time

    cb = CircuitBreaker("cb-test", _make_config(
        failure_threshold=1, success_threshold=2, open_state_timeout=0.01,
        half_open_max_attempts=5
    ))

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    time.sleep(0.02)

    # Two successes in HALF_OPEN should close the circuit
    cb.execute(lambda: "ok1")
    cb.execute(lambda: "ok2")

    assert cb.state is CircuitBreakerState.CLOSED, "state should be CLOSED after recovery"
    return


def test_half_open_failure_returns_to_open():
    """
        Verify that a failure in HALF_OPEN transitions back to OPEN.
    """
    import time

    cb = CircuitBreaker("cb-test", _make_config(
        failure_threshold=1, open_state_timeout=0.01, half_open_max_attempts=5
    ))

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    time.sleep(0.02)

    # Fail in HALF_OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail again")))
    except ValueError:
        pass

    assert cb.state is CircuitBreakerState.OPEN, "should return to OPEN on half-open failure"
    return


def test_reset_returns_to_closed():
    """
        Verify that reset transitions to CLOSED and clears counters.
    """
    cb = CircuitBreaker("cb-test", _make_config(failure_threshold=1))

    # Trigger OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    assert cb.state is CircuitBreakerState.OPEN, "should be OPEN"

    cb.reset()

    assert cb.state is CircuitBreakerState.CLOSED, "should be CLOSED after reset"
    assert cb.failure_count == 0, "failure count should be 0 after reset"
    assert cb.success_count == 0, "success count should be 0 after reset"
    assert len(cb.events) == 0, "events should be cleared after reset"
    return


def test_events_recorded_on_transitions():
    """
        Verify that CircuitBreakerEvent objects are recorded for transitions.
    """
    cb = CircuitBreaker("cb-test", _make_config(failure_threshold=1))

    # Trigger CLOSED -> OPEN
    try:
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))
    except ValueError:
        pass

    events = cb.events
    assert len(events) == 1, "should have 1 event"
    assert events[0].previous_state is CircuitBreakerState.CLOSED, "previous should be CLOSED"
    assert events[0].new_state is CircuitBreakerState.OPEN, "new should be OPEN"
    return


def test_repr():
    """
        Verify that __repr__ includes class name and state.
    """
    cb = CircuitBreaker("cb-test", _make_config())
    repr_str = repr(cb)
    assert "CircuitBreaker" in repr_str, "repr should contain class name"
    assert "cb-test" in repr_str, "repr should contain name"
    assert "CLOSED" in repr_str, "repr should contain state"
    return


def test_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    cb = CircuitBreaker("cb-test", _make_config())
    str_val = str(cb)
    assert "cb-test" in str_val, "str should contain name"
    assert "CLOSED" in str_val, "str should contain state"
    return
