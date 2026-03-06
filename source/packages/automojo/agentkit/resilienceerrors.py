"""
    Exception classes for the Error Handling & Resilience feature.

    Provides CircuitBreakerOpenError for circuit breaker rejection and
    ResilienceError for general resilience operation failures.
"""

from typing import Optional

from automojo.agentkit.errors import AgentKitError


class ResilienceError(AgentKitError):
    """
        Raised when a resilience operation fails due to a configuration
        or execution error.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message, cause=cause)
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and message.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(message={!r})".format(self.__class__.__name__, self._message)
        return repr_str


class CircuitBreakerOpenError(AgentKitError):
    """
        Raised when a request is rejected because the CircuitBreaker is
        in the OPEN state.

        :param circuit_breaker_name: The name of the circuit breaker that rejected the request.
        :param service_name: The name of the service protected by the circuit breaker.
        :param time_remaining: The time remaining in seconds until the next half-open test.
    """

    def __init__(self, circuit_breaker_name: str, service_name: str,
                 time_remaining: float) -> None:
        self._circuit_breaker_name = circuit_breaker_name
        self._service_name = service_name
        self._time_remaining = time_remaining

        errmsg = (
            "Circuit breaker '{}' is OPEN for service '{}'. "
            "Time remaining until half-open: {:.1f}s."
        ).format(circuit_breaker_name, service_name, time_remaining)

        super().__init__(errmsg)
        return

    @property
    def circuit_breaker_name(self) -> str:
        """
            The name of the circuit breaker that rejected the request.

            :returns: The circuit breaker name string.
        """
        return self._circuit_breaker_name

    @property
    def service_name(self) -> str:
        """
            The name of the service protected by the circuit breaker.

            :returns: The service name string.
        """
        return self._service_name

    @property
    def time_remaining(self) -> float:
        """
            The time remaining in seconds until the next half-open test.

            :returns: The time remaining as a float.
        """
        return self._time_remaining

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            circuit breaker name, service name, and time remaining.

            :returns: A repr string for debugging.
        """
        repr_str = (
            "{}(circuit_breaker_name={!r}, service_name={!r}, time_remaining={:.1f})"
        ).format(
            self.__class__.__name__,
            self._circuit_breaker_name,
            self._service_name,
            self._time_remaining
        )
        return repr_str
