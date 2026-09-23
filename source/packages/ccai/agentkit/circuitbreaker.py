"""
    Defines the CircuitBreaker class for monitoring failure rates and
    preventing cascading failures in the Error Handling & Resilience feature.

    The CircuitBreaker transitions between CLOSED, OPEN, and HALF_OPEN states
    based on failure and success thresholds. Thread-safe via threading.Lock.
"""

import logging
import threading
import time

from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from ccai.agentkit.circuitbreakerevent import CircuitBreakerEvent
from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.resilienceerrors import CircuitBreakerOpenError


class CircuitBreaker:
    """
        Monitors the success and failure rate of operations directed at an
        external service and transitions between CLOSED, OPEN, and HALF_OPEN
        states.

        :param name: The circuit breaker name.
        :param configuration: The CircuitBreakerConfiguration.
    """

    def __init__(self, name: str, configuration: CircuitBreakerConfiguration) -> None:
        self._name = name
        self._configuration = configuration
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_attempt_count = 0
        self._open_timestamp = None
        self._events = []
        self._lock = threading.Lock()
        self._logger = logging.getLogger("ccai.agentkit.resilience")
        return

    @property
    def name(self) -> str:
        """
            The circuit breaker name.

            :returns: The name string.
        """
        return self._name

    @property
    def state(self) -> CircuitBreakerState:
        """
            The current CircuitBreakerState.

            :returns: The current state.
        """
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """
            The current failure count.

            :returns: The failure count as an integer.
        """
        with self._lock:
            return self._failure_count

    @property
    def success_count(self) -> int:
        """
            The current success count.

            :returns: The success count as an integer.
        """
        with self._lock:
            return self._success_count

    @property
    def events(self) -> list:
        """
            The list of recorded CircuitBreakerEvent objects.

            :returns: A list of CircuitBreakerEvent instances.
        """
        with self._lock:
            return list(self._events)

    def execute(self, callable_op, *args, **kwargs):
        """
            Evaluates the current state and either executes the callable or
            rejects the request.

            :param callable_op: The callable to execute.
            :param args: Positional arguments for the callable.
            :param kwargs: Keyword arguments for the callable.

            :returns: The callable result on success.
            :raises CircuitBreakerOpenError: If the circuit is OPEN.
        """
        with self._lock:
            current_state = self._state

            if current_state == CircuitBreakerState.OPEN:
                elapsed = time.monotonic() - self._open_timestamp
                timeout = self._configuration.open_state_timeout

                if elapsed >= timeout:
                    self._transition_to(CircuitBreakerState.HALF_OPEN, "open state timeout elapsed")
                    self._half_open_attempt_count = 0
                    self._success_count = 0
                    current_state = CircuitBreakerState.HALF_OPEN
                else:
                    time_remaining = timeout - elapsed
                    raise CircuitBreakerOpenError(self._name, self._name, time_remaining)

            if current_state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_attempt_count >= self._configuration.half_open_max_attempts:
                    time_remaining = self._configuration.open_state_timeout
                    raise CircuitBreakerOpenError(self._name, self._name, time_remaining)

                self._half_open_attempt_count += 1

        try:
            result = callable_op(*args, **kwargs)
        except Exception as exc:
            self._on_failure(current_state)
            raise
        else:
            self._on_success(current_state)
            return result

    def _on_success(self, state: CircuitBreakerState) -> None:
        """
            Handles a successful operation outcome.

            :param state: The state when the operation was executed.
        """
        with self._lock:
            if state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._configuration.success_threshold:
                    self._transition_to(CircuitBreakerState.CLOSED, "success threshold reached in half-open")
                    self._failure_count = 0
                    self._success_count = 0
            elif state == CircuitBreakerState.CLOSED:
                self._success_count += 1
        return

    def _on_failure(self, state: CircuitBreakerState) -> None:
        """
            Handles a failed operation outcome.

            :param state: The state when the operation was executed.
        """
        with self._lock:
            if state == CircuitBreakerState.HALF_OPEN:
                self._transition_to(CircuitBreakerState.OPEN, "failure in half-open state")
                self._open_timestamp = time.monotonic()
                self._success_count = 0
            elif state == CircuitBreakerState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self._configuration.failure_threshold:
                    self._transition_to(CircuitBreakerState.OPEN, "failure threshold reached")
                    self._open_timestamp = time.monotonic()
        return

    def _transition_to(self, new_state: CircuitBreakerState, reason: str) -> None:
        """
            Records a state transition event and updates the current state.
            Must be called while holding the lock.

            :param new_state: The new state.
            :param reason: The reason for the transition.
        """
        previous_state = self._state
        event = CircuitBreakerEvent(
            name=self._name,
            previous_state=previous_state,
            new_state=new_state,
            reason=reason
        )
        self._events.append(event)
        self._state = new_state

        self._logger.warning(
            "CircuitBreaker '%s' transitioned from %s to %s: %s",
            self._name, previous_state.value, new_state.value, reason
        )
        return

    def reset(self) -> None:
        """
            Transitions the CircuitBreaker to the CLOSED state and clears
            all counters and event history.
        """
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_attempt_count = 0
            self._open_timestamp = None
            self._events = []
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            circuit breaker name, and current state.

            :returns: A repr string for debugging.
        """
        repr_str = "CircuitBreaker(name={!r}, state={})".format(
            self._name, self._state.value
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the circuit breaker name,
            current state, failure count, and success count.

            :returns: A human-readable string.
        """
        str_val = "CircuitBreaker name='{}', state={}, failures={}, successes={}".format(
            self._name, self._state.value, self._failure_count, self._success_count
        )
        return str_val
