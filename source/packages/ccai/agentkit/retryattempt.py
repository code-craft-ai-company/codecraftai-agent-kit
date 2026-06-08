"""
    Defines the RetryAttempt class representing a single retry attempt
    in the Error Handling & Resilience feature.

    A RetryAttempt contains the attempt number, the delay before the attempt,
    the exception that triggered the retry, and a timestamp.
"""

import json

from datetime import datetime


class RetryAttempt:
    """
        Immutable object representing a single retry attempt.

        :param attempt_number: The attempt number as an integer.
        :param delay: The delay before the attempt in seconds.
        :param exception: The exception that triggered the retry.
        :param timestamp: The datetime of the attempt. Defaults to UTC now.
    """

    def __init__(self, attempt_number: int, delay: float, exception: Exception,
                 timestamp: datetime = None) -> None:
        self._attempt_number = attempt_number
        self._delay = delay
        self._exception = exception
        self._timestamp = timestamp if timestamp is not None else datetime.utcnow()
        return

    @property
    def attempt_number(self) -> int:
        """
            The attempt number.

            :returns: The attempt number as an integer.
        """
        return self._attempt_number

    @property
    def delay(self) -> float:
        """
            The delay before the attempt in seconds.

            :returns: The delay as a float.
        """
        return self._delay

    @property
    def exception(self) -> Exception:
        """
            The exception that triggered the retry.

            :returns: The exception instance.
        """
        return self._exception

    @property
    def timestamp(self) -> datetime:
        """
            The datetime of the attempt.

            :returns: The timestamp as a datetime object.
        """
        return self._timestamp

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the attempt fields.
            The exception is represented as a string containing the exception
            type and message.

            :returns: A dictionary of attempt fields.
        """
        exception_str = "{}({})".format(
            type(self._exception).__name__, str(self._exception)
        )
        result = {
            "attempt_number": self._attempt_number,
            "delay": self._delay,
            "exception": exception_str,
            "timestamp": self._timestamp.isoformat()
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the attempt fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "RetryAttempt":
        """
            Constructs a RetryAttempt from a dictionary.

            The exception field is stored as a RuntimeError wrapping the
            original exception string representation.

            :param data: Dictionary containing attempt fields.

            :returns: A RetryAttempt instance.
        """
        attempt_number = data["attempt_number"]
        delay = data["delay"]
        exception = RuntimeError(data["exception"])
        timestamp = datetime.fromisoformat(data["timestamp"])

        attempt = cls(
            attempt_number=attempt_number,
            delay=delay,
            exception=exception,
            timestamp=timestamp
        )
        return attempt

    @classmethod
    def from_json(cls, json_str: str) -> "RetryAttempt":
        """
            Deserializes a JSON string into a RetryAttempt instance.

            :param json_str: JSON string to deserialize.

            :returns: A RetryAttempt instance.
        """
        data = json.loads(json_str)
        attempt = cls.from_dict(data)
        return attempt

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            attempt number, and exception type.

            :returns: A repr string for debugging.
        """
        exception_type = type(self._exception).__name__
        repr_str = "RetryAttempt(attempt_number={}, exception_type={!r})".format(
            self._attempt_number, exception_type
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the attempt number,
            delay, and exception message.

            :returns: A human-readable string.
        """
        str_val = "RetryAttempt attempt={}, delay={:.2f}s, exception={}".format(
            self._attempt_number, self._delay, str(self._exception)
        )
        return str_val
