"""
    Defines the RetryExecutor class for executing callables with retry logic
    in the Error Handling & Resilience feature.

    The RetryExecutor applies RetryPolicy-based retry logic to any callable
    operation, producing structured RetryAttempt and RetryResult objects.
"""

import logging
import time

from datetime import datetime

from ccai.agentkit.retryattempt import RetryAttempt
from ccai.agentkit.retrypolicy import RetryPolicy
from ccai.agentkit.retryresult import RetryResult


class RetryExecutor:
    """
        Executes a callable with retry logic governed by a RetryPolicy.

        Handles delay calculation, attempt tracking, and retryable exception
        filtering. This is the cross-cutting retry mechanism used by all
        agent subsystems.

        :param retry_policy: The RetryPolicy defining retry behavior.
    """

    def __init__(self, retry_policy: RetryPolicy) -> None:
        self._retry_policy = retry_policy
        self._logger = logging.getLogger("ccai.agentkit.resilience")
        return

    @property
    def retry_policy(self) -> RetryPolicy:
        """
            Returns the configured RetryPolicy instance.

            :returns: The RetryPolicy.
        """
        return self._retry_policy

    def execute(self, callable_op, *args, **kwargs) -> RetryResult:
        """
            Executes the callable with retry logic. Retries on retryable
            exceptions up to the maximum retry count. Non-retryable exceptions
            are raised immediately.

            :param callable_op: The callable to execute.
            :param args: Positional arguments for the callable.
            :param kwargs: Keyword arguments for the callable.

            :returns: A RetryResult containing the operation outcome.
            :raises: Non-retryable exceptions immediately.
        """
        attempts = []
        start_time = time.monotonic()
        attempt_number = 0

        while True:
            try:
                result_value = callable_op(*args, **kwargs)
                elapsed = time.monotonic() - start_time
                result = RetryResult(
                    success=True,
                    result=result_value,
                    attempts=attempts,
                    elapsed_time=elapsed
                )
                return result

            except Exception as exc:
                should_retry = self._retry_policy.should_retry(exc, attempt_number)

                if not should_retry:
                    # Check if retries exhausted vs non-retryable
                    is_retryable = self._is_retryable(exc)
                    if not is_retryable:
                        raise

                    # Retries exhausted
                    elapsed = time.monotonic() - start_time
                    result = RetryResult(
                        success=False,
                        exception=exc,
                        attempts=attempts,
                        elapsed_time=elapsed
                    )
                    return result

                delay = self._retry_policy.get_delay(attempt_number)
                timestamp = datetime.utcnow()

                attempt = RetryAttempt(
                    attempt_number=attempt_number + 1,
                    delay=delay,
                    exception=exc,
                    timestamp=timestamp
                )
                attempts.append(attempt)

                exception_type = type(exc).__name__
                self._logger.info(
                    "Retry attempt %d, delay=%.2fs, exception_type=%s, message=%s",
                    attempt_number + 1, delay, exception_type, str(exc)
                )

                time.sleep(delay)
                attempt_number += 1

    def _is_retryable(self, exception: Exception) -> bool:
        """
            Checks if the exception matches any retryable exception type.

            :param exception: The exception to check.

            :returns: True if the exception is retryable.
        """
        retryable_types = self._retry_policy.retryable_exceptions

        if len(retryable_types) == 0:
            return True

        rtnval = any(isinstance(exception, exc_type) for exc_type in retryable_types)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            maximum retry count, and backoff strategy.

            :returns: A repr string for debugging.
        """
        repr_str = "RetryExecutor(max_retries={}, strategy={!r})".format(
            self._retry_policy.max_retries, self._retry_policy.backoff_strategy
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the retry configuration.

            :returns: A human-readable string.
        """
        str_val = "RetryExecutor: max_retries={}, strategy={}, base_delay={}s".format(
            self._retry_policy.max_retries,
            self._retry_policy.backoff_strategy,
            self._retry_policy.base_delay
        )
        return str_val
