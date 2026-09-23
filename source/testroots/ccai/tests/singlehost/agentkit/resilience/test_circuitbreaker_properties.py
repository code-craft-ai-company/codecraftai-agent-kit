"""
    Property-based tests for the ccai.agentkit.circuitbreaker module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 9: CircuitBreaker initial state is CLOSED
    - Property 10: CircuitBreaker CLOSED-to-OPEN transition on failure threshold
    - Property 11: CircuitBreaker OPEN state rejects all requests
    - Property 12: CircuitBreaker reset returns to CLOSED
    - Property 13: CircuitBreaker event count matches transition count

    **Validates: Requirements 3.2, 3.5, 3.6, 3.16, 3.11**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.circuitbreaker import CircuitBreaker
from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.resilienceerrors import CircuitBreakerOpenError


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_circuit_breaker_name = st.text(min_size=1, max_size=200)

_failure_threshold = st.integers(min_value=1, max_value=1000)

_success_threshold = st.integers(min_value=1, max_value=1000)

_open_state_timeout = st.floats(min_value=0.1, max_value=3600.0)

_half_open_max_attempts = st.integers(min_value=1, max_value=1000)

_circuit_breaker_configuration = st.builds(
    CircuitBreakerConfiguration,
    failure_threshold=_failure_threshold,
    success_threshold=_success_threshold,
    open_state_timeout=_open_state_timeout,
    half_open_max_attempts=_half_open_max_attempts,
)


# ---------------------------------------------------------------------------
# Property 9: CircuitBreaker initial state is CLOSED
# ---------------------------------------------------------------------------

@given(
    name=_circuit_breaker_name,
    configuration=_circuit_breaker_configuration,
    constraints={"max_examples": 50},
)
def test_circuitbreaker_initial_state_is_closed(
    name: str,
    configuration: CircuitBreakerConfiguration,
) -> None:
    """
        **Validates: Requirements 3.2**

        For all CircuitBreaker instances constructed with any valid name
        (non-empty string) and CircuitBreakerConfiguration (with positive
        failure_threshold, success_threshold, half_open_max_attempts, and
        positive open_state_timeout), the initial state property shall be
        CircuitBreakerState.CLOSED.
    """
    cb = CircuitBreaker(name=name, configuration=configuration)

    assert cb.state == CircuitBreakerState.CLOSED, (
        "Expected initial state CLOSED, got {}".format(cb.state)
    )

    assert cb.failure_count == 0, (
        "Expected initial failure_count 0, got {}".format(cb.failure_count)
    )

    assert cb.success_count == 0, (
        "Expected initial success_count 0, got {}".format(cb.success_count)
    )

    assert cb.events == [], (
        "Expected initial events to be empty, got {}".format(cb.events)
    )

    return


# ---------------------------------------------------------------------------
# Strategies for Property 10 and 11 (small thresholds for fast tests)
# ---------------------------------------------------------------------------

_small_failure_threshold = st.integers(min_value=1, max_value=10)

_small_circuit_breaker_configuration = st.builds(
    CircuitBreakerConfiguration,
    failure_threshold=_small_failure_threshold,
    success_threshold=_success_threshold,
    open_state_timeout=_open_state_timeout,
    half_open_max_attempts=_half_open_max_attempts,
)


# ---------------------------------------------------------------------------
# Property 10: CircuitBreaker CLOSED-to-OPEN transition on failure threshold
# ---------------------------------------------------------------------------

@given(
    name=_circuit_breaker_name,
    configuration=_small_circuit_breaker_configuration,
    constraints={"max_examples": 50},
)
def test_circuitbreaker_closed_to_open_on_failure_threshold(
    name: str,
    configuration: CircuitBreakerConfiguration,
) -> None:
    """
        **Validates: Requirements 3.5**

        For all CircuitBreaker instances with failure_threshold N (1-10),
        after exactly N consecutive failures from executed callables in the
        CLOSED state, the CircuitBreaker state shall be
        CircuitBreakerState.OPEN.
    """
    cb = CircuitBreaker(name=name, configuration=configuration)
    threshold = configuration.failure_threshold

    def failing_callable():
        raise RuntimeError("simulated failure")

    # Execute exactly failure_threshold failures
    for i in range(threshold):
        # Before the last failure, state should still be CLOSED
        if i < threshold - 1:
            assert cb.state == CircuitBreakerState.CLOSED, (
                "Expected CLOSED before reaching threshold, got {} at failure {}".format(
                    cb.state, i + 1
                )
            )

        try:
            cb.execute(failing_callable)
        except RuntimeError:
            # Expected: the deliberately failing call is recorded by the circuit breaker;
            # the propagated exception itself is not what this test verifies.
            pass

    # After exactly failure_threshold failures, state must be OPEN
    assert cb.state == CircuitBreakerState.OPEN, (
        "Expected OPEN after {} failures, got {}".format(threshold, cb.state)
    )

    return


# ---------------------------------------------------------------------------
# Strategies for Property 11 (large timeout so CB stays OPEN)
# ---------------------------------------------------------------------------

_open_reject_configuration = st.builds(
    CircuitBreakerConfiguration,
    failure_threshold=_small_failure_threshold,
    success_threshold=_success_threshold,
    open_state_timeout=st.just(3600.0),
    half_open_max_attempts=_half_open_max_attempts,
)

_additional_requests = st.integers(min_value=1, max_value=20)


# ---------------------------------------------------------------------------
# Property 11: CircuitBreaker OPEN state rejects all requests
# ---------------------------------------------------------------------------

@given(
    name=_circuit_breaker_name,
    configuration=_open_reject_configuration,
    num_requests=_additional_requests,
    constraints={"max_examples": 50},
)
def test_circuitbreaker_open_state_rejects_all_requests(
    name: str,
    configuration: CircuitBreakerConfiguration,
    num_requests: int,
) -> None:
    """
        **Validates: Requirements 3.6**

        For all CircuitBreaker instances in the OPEN state, calling execute
        with any callable shall raise CircuitBreakerOpenError without
        invoking the callable.
    """
    cb = CircuitBreaker(name=name, configuration=configuration)
    threshold = configuration.failure_threshold

    def failing_callable():
        raise RuntimeError("simulated failure")

    # Force the circuit breaker to OPEN by causing failure_threshold failures
    for _ in range(threshold):
        try:
            cb.execute(failing_callable)
        except RuntimeError:
            # Expected: the deliberately failing call is recorded by the circuit breaker;
            # the propagated exception itself is not what this test verifies.
            pass

    assert cb.state == CircuitBreakerState.OPEN, (
        "Expected OPEN after {} failures, got {}".format(threshold, cb.state)
    )

    # Track whether the callable is invoked while OPEN
    invocation_count = [0]

    def guarded_callable():
        invocation_count[0] += 1
        return "should not be reached"

    # All subsequent requests must raise CircuitBreakerOpenError
    for i in range(num_requests):
        raised = False
        try:
            cb.execute(guarded_callable)
        except CircuitBreakerOpenError:
            raised = True
        except Exception as exc:
            assert False, (
                "Expected CircuitBreakerOpenError on request {}, got {}: {}".format(
                    i + 1, type(exc).__name__, exc
                )
            )

        assert raised, (
            "Expected CircuitBreakerOpenError on request {}, but no exception was raised".format(
                i + 1
            )
        )

    # The callable must never have been invoked
    assert invocation_count[0] == 0, (
        "Expected callable to never be invoked while OPEN, but it was called {} times".format(
            invocation_count[0]
        )
    )

    return


# ---------------------------------------------------------------------------
# Strategies for Property 12 (force to any state, then reset)
# ---------------------------------------------------------------------------

_pre_reset_state = st.sampled_from([
    CircuitBreakerState.CLOSED,
    CircuitBreakerState.OPEN,
    CircuitBreakerState.HALF_OPEN,
])


# ---------------------------------------------------------------------------
# Property 12: CircuitBreaker reset returns to CLOSED
# ---------------------------------------------------------------------------

@given(
    name=_circuit_breaker_name,
    configuration=_open_reject_configuration,
    target_state=_pre_reset_state,
    constraints={"max_examples": 50},
)
def test_circuitbreaker_reset_returns_to_closed(
    name: str,
    configuration: CircuitBreakerConfiguration,
    target_state: CircuitBreakerState,
) -> None:
    """
        **Validates: Requirements 3.16**

        For all CircuitBreaker instances in any state (CLOSED, OPEN, or
        HALF_OPEN), calling reset() shall transition the state to
        CircuitBreakerState.CLOSED and set both failure_count and
        success_count to 0 with an empty events list.
    """
    cb = CircuitBreaker(name=name, configuration=configuration)
    threshold = configuration.failure_threshold

    def failing_callable():
        raise RuntimeError("simulated failure")

    if target_state == CircuitBreakerState.CLOSED:
        # Already in CLOSED; optionally accumulate some failures below threshold
        if threshold > 1:
            try:
                cb.execute(failing_callable)
            except RuntimeError:
                # Expected: the deliberately failing call is recorded by the circuit breaker;
                # the propagated exception itself is not what this test verifies.
                pass

    elif target_state == CircuitBreakerState.OPEN:
        # Force to OPEN by causing failure_threshold failures
        for _ in range(threshold):
            try:
                cb.execute(failing_callable)
            except RuntimeError:
                # Expected: the deliberately failing call is recorded by the circuit breaker;
                # the propagated exception itself is not what this test verifies.
                pass
        assert cb.state == CircuitBreakerState.OPEN, (
            "Expected OPEN before reset, got {}".format(cb.state)
        )

    elif target_state == CircuitBreakerState.HALF_OPEN:
        # Force to OPEN first, then manually transition to HALF_OPEN
        for _ in range(threshold):
            try:
                cb.execute(failing_callable)
            except RuntimeError:
                # Expected: the deliberately failing call is recorded by the circuit breaker;
                # the propagated exception itself is not what this test verifies.
                pass
        assert cb.state == CircuitBreakerState.OPEN, (
            "Expected OPEN before HALF_OPEN transition, got {}".format(cb.state)
        )
        # Manually set state to HALF_OPEN to avoid waiting for timeout
        with cb._lock:
            cb._state = CircuitBreakerState.HALF_OPEN
            cb._half_open_attempt_count = 0
            cb._success_count = 0
        assert cb.state == CircuitBreakerState.HALF_OPEN, (
            "Expected HALF_OPEN before reset, got {}".format(cb.state)
        )

    # Call reset
    cb.reset()

    # Verify state is CLOSED
    assert cb.state == CircuitBreakerState.CLOSED, (
        "Expected CLOSED after reset, got {}".format(cb.state)
    )

    # Verify counters are zeroed
    assert cb.failure_count == 0, (
        "Expected failure_count 0 after reset, got {}".format(cb.failure_count)
    )

    assert cb.success_count == 0, (
        "Expected success_count 0 after reset, got {}".format(cb.success_count)
    )

    # Verify events are cleared
    assert cb.events == [], (
        "Expected events to be empty after reset, got {}".format(cb.events)
    )

    return


# ---------------------------------------------------------------------------
# Strategies for Property 13 (small thresholds for fast tests)
# ---------------------------------------------------------------------------

_small_event_count_configuration = st.builds(
    CircuitBreakerConfiguration,
    failure_threshold=st.integers(min_value=1, max_value=10),
    success_threshold=st.integers(min_value=1, max_value=10),
    open_state_timeout=st.just(3600.0),
    half_open_max_attempts=st.integers(min_value=1, max_value=10),
)


# ---------------------------------------------------------------------------
# Property 13: CircuitBreaker event count matches transition count
# ---------------------------------------------------------------------------

@given(
    name=_circuit_breaker_name,
    configuration=_small_event_count_configuration,
    constraints={"max_examples": 50},
)
def test_circuitbreaker_event_count_matches_transition_count(
    name: str,
    configuration: CircuitBreakerConfiguration,
) -> None:
    """
        **Validates: Requirements 3.11**

        For all sequences of operations on a CircuitBreaker that cause N
        state transitions, the events list shall contain exactly N
        CircuitBreakerEvent objects.

        # Feature: error-handling-resilience, Property 13: CircuitBreaker event count matches transition count
    """
    cb = CircuitBreaker(name=name, configuration=configuration)
    threshold = configuration.failure_threshold

    # Initially there are no events
    assert len(cb.events) == 0, (
        "Expected 0 events initially, got {}".format(len(cb.events))
    )

    def failing_callable():
        raise RuntimeError("simulated failure")

    # Force failure_threshold failures to trigger CLOSED -> OPEN (1 transition)
    for _ in range(threshold):
        try:
            cb.execute(failing_callable)
        except RuntimeError:
            # Expected: the deliberately failing call is recorded by the circuit breaker;
            # the propagated exception itself is not what this test verifies.
            pass

    assert cb.state == CircuitBreakerState.OPEN, (
        "Expected OPEN after {} failures, got {}".format(threshold, cb.state)
    )

    # Exactly 1 state transition occurred: CLOSED -> OPEN
    events = cb.events
    assert len(events) == 1, (
        "Expected 1 event after CLOSED->OPEN transition, got {}".format(len(events))
    )

    event = events[0]
    assert event.previous_state == CircuitBreakerState.CLOSED, (
        "Expected previous_state CLOSED, got {}".format(event.previous_state)
    )
    assert event.new_state == CircuitBreakerState.OPEN, (
        "Expected new_state OPEN, got {}".format(event.new_state)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
