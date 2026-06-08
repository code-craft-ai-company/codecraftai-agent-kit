"""
    Defines the InvocationResult class representing an immutable result of
    a compute invocation with status, response payload, optional error
    message, execution duration, and request identifier. Supports
    serialization to and from dictionary and JSON representations.

    .. module:: ccai.agentkit.platform.services.invocationresult
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable compute invocation result for platform compute services.
"""

import json

from typing import Optional


class InvocationResult:
    """
        Immutable object representing the result of a compute invocation.
        Contains a status string (one of "success", "error", "timeout"),
        a response payload as a Python object, an optional error message,
        the execution duration in seconds, and a request identifier.

        All fields are exposed as read-only properties.

        :param status: The invocation status ("success", "error", or "timeout").
        :param response: The response payload as a Python object.
        :param error_message: An optional error message string.
        :param duration: The execution duration in seconds.
        :param request_id: A request identifier string.
    """

    VALID_STATUSES = ("success", "error", "timeout")

    def __init__(self, status: str, response: object = None,
                 error_message: Optional[str] = None,
                 duration: float = 0.0, request_id: str = "") -> None:
        self._status = status
        self._response = response
        self._error_message = error_message
        self._duration = duration
        self._request_id = request_id
        return

    @property
    def status(self) -> str:
        """
            The invocation status string.

            :returns: One of "success", "error", or "timeout".
        """
        rtnval = self._status
        return rtnval

    @property
    def response(self) -> object:
        """
            The response payload as a Python object.

            :returns: The response object.
        """
        rtnval = self._response
        return rtnval

    @property
    def error_message(self) -> str:
        """
            The optional error message string.

            :returns: The error message string or None.
        """
        rtnval = self._error_message
        return rtnval

    @property
    def duration(self) -> float:
        """
            The execution duration in seconds.

            :returns: The duration float.
        """
        rtnval = self._duration
        return rtnval

    @property
    def request_id(self) -> str:
        """
            The request identifier string.

            :returns: The request identifier string.
        """
        rtnval = self._request_id
        return rtnval

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the result fields.

            :returns: A dictionary with all result fields.
        """
        rtnval = {
            "status": self._status,
            "response": self._response,
            "error_message": self._error_message,
            "duration": self._duration,
            "request_id": self._request_id
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the result fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "InvocationResult":
        """
            Constructs an InvocationResult from a dictionary.

            :param data: Dictionary containing result fields.

            :returns: An InvocationResult instance.
        """
        rtnval = cls(
            status=data["status"],
            response=data.get("response"),
            error_message=data.get("error_message"),
            duration=data.get("duration", 0.0),
            request_id=data.get("request_id", "")
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "InvocationResult":
        """
            Deserializes a JSON string into an InvocationResult instance.

            :param json_str: A JSON string containing result fields.

            :returns: An InvocationResult instance.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            status, and request identifier.

            :returns: A repr string for debugging.
        """
        rtnval = "InvocationResult(status={}, request_id={})".format(
            self._status, self._request_id
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the status,
            request identifier, and execution duration.

            :returns: A human-readable string.
        """
        rtnval = "InvocationResult: status={}, request_id={}, duration={:.3f}s".format(
            self._status, self._request_id, self._duration
        )
        return rtnval
