"""
    Defines the RetryPolicy class for configuring retry behavior
    in the codecraftai-agent-kit framework.

    RetryPolicy is the unified retry configuration used across all agent
    subsystems including LLM requests, tool execution, transport communication,
    and memory backend access.
"""

import json
import random

from ccai.agentkit.errors import SemanticError


class RetryPolicy:
    """
        Configuration for retry behavior on failed operations.

        Supports fixed, exponential, and exponential_with_jitter backoff
        strategies.

        :param max_retries: Maximum number of retry attempts.
        :param backoff_strategy: One of "fixed", "exponential", "exponential_with_jitter".
        :param base_delay: Base delay in seconds.
        :param max_delay: Maximum delay in seconds.
        :param retryable_exceptions: List of exception types that trigger retries.
    """

    VALID_STRATEGIES = {"fixed", "exponential", "exponential_with_jitter"}

    def __init__(self, max_retries: int, backoff_strategy: str,
                 base_delay: float, max_delay: float,
                 retryable_exceptions: list = None) -> None:
        if backoff_strategy not in self.VALID_STRATEGIES:
            errmsg = "Invalid backoff_strategy '{}'. Valid strategies are: {}.".format(
                backoff_strategy, ", ".join(sorted(self.VALID_STRATEGIES))
            )
            raise SemanticError(errmsg)

        self._max_retries = max_retries
        self._backoff_strategy = backoff_strategy
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._retryable_exceptions = list(retryable_exceptions) if retryable_exceptions is not None else []
        return

    @property
    def max_retries(self) -> int:
        """
            Maximum number of retry attempts.

            :returns: The max retries as an integer.
        """
        return self._max_retries

    @property
    def backoff_strategy(self) -> str:
        """
            The backoff strategy name.

            :returns: The strategy string.
        """
        return self._backoff_strategy

    @property
    def base_delay(self) -> float:
        """
            Base delay in seconds.

            :returns: The base delay as a float.
        """
        return self._base_delay

    @property
    def max_delay(self) -> float:
        """
            Maximum delay in seconds.

            :returns: The max delay as a float.
        """
        return self._max_delay

    @property
    def retryable_exceptions(self) -> list:
        """
            List of exception types that trigger retries.

            :returns: A list of exception types.
        """
        return list(self._retryable_exceptions)

    def get_delay(self, attempt: int) -> float:
        """
            Calculates the delay before the next retry attempt.

            :param attempt: The current retry attempt number (0-based).

            :returns: The delay in seconds.
        """
        if self._backoff_strategy == "fixed":
            rtnval = self._base_delay
        elif self._backoff_strategy == "exponential":
            computed = self._base_delay * (2 ** attempt)
            rtnval = min(computed, self._max_delay)
        elif self._backoff_strategy == "exponential_with_jitter":
            computed = self._base_delay * (2 ** attempt)
            capped = min(computed, self._max_delay)
            jitter = random.random()
            rtnval = capped * jitter
        else:
            rtnval = self._base_delay

        return rtnval

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
            Determines whether an operation should be retried.

            :param exception: The exception that occurred.
            :param attempt: The current attempt number.

            :returns: True if the operation should be retried.
        """
        if attempt >= self._max_retries:
            return False

        if len(self._retryable_exceptions) == 0:
            return True

        rtnval = any(isinstance(exception, exc_type) for exc_type in self._retryable_exceptions)
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the policy fields.

            :returns: A dictionary of policy fields.
        """
        rtnval = {
            "max_retries": self._max_retries,
            "backoff_strategy": self._backoff_strategy,
            "base_delay": self._base_delay,
            "max_delay": self._max_delay
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the policy fields.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "RetryPolicy":
        """
            Constructs a RetryPolicy from a dictionary.

            :param data: Dictionary containing policy fields.

            :returns: A RetryPolicy instance.
        """
        rtnval = cls(
            max_retries=data["max_retries"],
            backoff_strategy=data["backoff_strategy"],
            base_delay=data["base_delay"],
            max_delay=data["max_delay"]
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            max retries, and backoff strategy.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(max_retries={}, strategy={!r})".format(
            self.__class__.__name__, self._max_retries, self._backoff_strategy
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the retry configuration.

            :returns: A human-readable string.
        """
        rtnval = "RetryPolicy: max_retries={}, strategy={}, base_delay={}s, max_delay={}s".format(
            self._max_retries, self._backoff_strategy, self._base_delay, self._max_delay
        )
        return rtnval
