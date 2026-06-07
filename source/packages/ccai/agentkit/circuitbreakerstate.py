"""
    Defines the CircuitBreakerState enum representing the possible states
    of a circuit breaker in the Error Handling & Resilience feature.
"""

import enum

from ccai.agentkit.errors import SemanticError


class CircuitBreakerState(enum.Enum):
    """
        Enumeration defining the state of a CircuitBreaker.

        CLOSED: Normal operation, requests pass through.
        OPEN: Service is degraded, requests are rejected immediately.
        HALF_OPEN: Recovery testing, limited requests allowed through.
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    @classmethod
    def from_string(cls, value: str) -> "CircuitBreakerState":
        """
            Returns the CircuitBreakerState member matching the given string.

            :param value: The string value to match.

            :returns: The matching CircuitBreakerState member.
            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = [m.value for m in cls]
        errmsg = "Invalid CircuitBreakerState value '{}'. Valid values are: {}.".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)
