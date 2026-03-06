"""
    Defines the CircuitBreakerConfiguration class for configuring circuit
    breaker thresholds and timing in the Error Handling & Resilience feature.
"""

import json

from typing import List
from typing import Optional


class CircuitBreakerConfiguration:
    """
        Immutable configuration object defining the thresholds and timing
        for a CircuitBreaker.

        :param failure_threshold: Number of failures before opening the circuit.
        :param success_threshold: Number of successes in half-open before closing.
        :param open_state_timeout: Seconds to wait in open state before half-open.
        :param half_open_max_attempts: Max attempts allowed in half-open state.
        :param monitored_exception_types: Optional list of exception types to monitor.
    """

    def __init__(self, failure_threshold: int, success_threshold: int,
                 open_state_timeout: float, half_open_max_attempts: int,
                 monitored_exception_types: Optional[List[type]] = None) -> None:
        self._failure_threshold = failure_threshold
        self._success_threshold = success_threshold
        self._open_state_timeout = open_state_timeout
        self._half_open_max_attempts = half_open_max_attempts
        self._monitored_exception_types = list(monitored_exception_types) if monitored_exception_types is not None else []
        return

    @property
    def failure_threshold(self) -> int:
        """
            Number of failures before opening the circuit.

            :returns: The failure threshold as an integer.
        """
        return self._failure_threshold

    @property
    def success_threshold(self) -> int:
        """
            Number of successes in half-open before closing.

            :returns: The success threshold as an integer.
        """
        return self._success_threshold

    @property
    def open_state_timeout(self) -> float:
        """
            Seconds to wait in open state before transitioning to half-open.

            :returns: The timeout as a float.
        """
        return self._open_state_timeout

    @property
    def half_open_max_attempts(self) -> int:
        """
            Maximum attempts allowed in half-open state.

            :returns: The max attempts as an integer.
        """
        return self._half_open_max_attempts

    @property
    def monitored_exception_types(self) -> list:
        """
            List of exception types to monitor.

            :returns: A list of exception types.
        """
        return list(self._monitored_exception_types)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration fields.

            :returns: A dictionary of configuration fields.
        """
        result = {
            "failure_threshold": self._failure_threshold,
            "success_threshold": self._success_threshold,
            "open_state_timeout": self._open_state_timeout,
            "half_open_max_attempts": self._half_open_max_attempts
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "CircuitBreakerConfiguration":
        """
            Constructs a CircuitBreakerConfiguration from a dictionary.

            :param data: Dictionary containing configuration fields.

            :returns: A CircuitBreakerConfiguration instance.
        """
        config = cls(
            failure_threshold=data["failure_threshold"],
            success_threshold=data["success_threshold"],
            open_state_timeout=data["open_state_timeout"],
            half_open_max_attempts=data["half_open_max_attempts"]
        )
        return config

    @classmethod
    def from_json(cls, json_str: str) -> "CircuitBreakerConfiguration":
        """
            Deserializes a JSON string into a CircuitBreakerConfiguration.

            :param json_str: JSON string to deserialize.

            :returns: A CircuitBreakerConfiguration instance.
        """
        data = json.loads(json_str)
        config = cls.from_dict(data)
        return config

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            failure threshold, and open state timeout.

            :returns: A repr string for debugging.
        """
        repr_str = "CircuitBreakerConfiguration(failure_threshold={}, open_state_timeout={})".format(
            self._failure_threshold, self._open_state_timeout
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the circuit breaker configuration.

            :returns: A human-readable string.
        """
        str_val = (
            "CircuitBreakerConfiguration: failure_threshold={}, success_threshold={}, "
            "open_state_timeout={}s, half_open_max_attempts={}"
        ).format(
            self._failure_threshold, self._success_threshold,
            self._open_state_timeout, self._half_open_max_attempts
        )
        return str_val
