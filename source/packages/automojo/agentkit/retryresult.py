"""
    Defines the RetryResult class encapsulating the outcome of a retried
    operation in the Error Handling & Resilience feature.

    A RetryResult contains the result value on success, the final exception
    on failure, the list of RetryAttempt objects, the total elapsed time,
    and a success flag.
"""

import json

from typing import List
from typing import Optional

from automojo.agentkit.retryattempt import RetryAttempt


class RetryResult:
    """
        Immutable object encapsulating the outcome of a retried operation.

        :param success: Whether the operation succeeded.
        :param result: The operation result value on success.
        :param exception: The final exception on failure.
        :param attempts: The list of RetryAttempt objects from failed attempts.
        :param elapsed_time: The total elapsed time in seconds.
    """

    def __init__(self, success: bool, result=None, exception: Optional[Exception] = None,
                 attempts: Optional[List[RetryAttempt]] = None,
                 elapsed_time: float = 0.0) -> None:
        self._success = success
        self._result = result
        self._exception = exception
        self._attempts = list(attempts) if attempts is not None else []
        self._elapsed_time = elapsed_time
        return

    @property
    def success(self) -> bool:
        """
            Whether the operation succeeded.

            :returns: True if the operation succeeded.
        """
        return self._success

    @property
    def result(self):
        """
            The operation result value on success.

            :returns: The result value or None.
        """
        return self._result

    @property
    def exception(self) -> Optional[Exception]:
        """
            The final exception on failure.

            :returns: The exception or None.
        """
        return self._exception

    @property
    def attempts(self) -> List[RetryAttempt]:
        """
            The list of RetryAttempt objects from failed attempts.

            :returns: A list of RetryAttempt instances.
        """
        return list(self._attempts)

    @property
    def elapsed_time(self) -> float:
        """
            The total elapsed time in seconds.

            :returns: The elapsed time as a float.
        """
        return self._elapsed_time

    @property
    def is_success(self) -> bool:
        """
            Returns True when the success flag is True.

            :returns: Boolean indicating success.
        """
        return self._success

    @property
    def attempt_count(self) -> int:
        """
            Returns the total number of attempts including the initial attempt
            and all retries.

            :returns: Integer count of attempts.
        """
        count = len(self._attempts) + 1
        return count

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the result fields.

            :returns: A dictionary of result fields.
        """
        exception_str = None
        if self._exception is not None:
            exception_str = "{}({})".format(
                type(self._exception).__name__, str(self._exception)
            )

        result = {
            "success": self._success,
            "result": self._result,
            "exception": exception_str,
            "attempts": [a.as_dict() for a in self._attempts],
            "elapsed_time": self._elapsed_time
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the result fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_json(cls, json_str: str) -> "RetryResult":
        """
            Deserializes a JSON string into a RetryResult instance.

            :param json_str: JSON string to deserialize.

            :returns: A RetryResult instance.
        """
        data = json.loads(json_str)

        attempts = []
        for attempt_data in data.get("attempts", []):
            attempt = RetryAttempt.from_dict(attempt_data)
            attempts.append(attempt)

        exception = None
        if data.get("exception") is not None:
            exception = RuntimeError(data["exception"])

        result = cls(
            success=data["success"],
            result=data.get("result"),
            exception=exception,
            attempts=attempts,
            elapsed_time=data.get("elapsed_time", 0.0)
        )
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            success flag, and attempt count.

            :returns: A repr string for debugging.
        """
        repr_str = "RetryResult(success={}, attempt_count={})".format(
            self._success, self.attempt_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the success flag,
            attempt count, and elapsed time.

            :returns: A human-readable string.
        """
        str_val = "RetryResult success={}, attempts={}, elapsed={:.3f}s".format(
            self._success, self.attempt_count, self._elapsed_time
        )
        return str_val
