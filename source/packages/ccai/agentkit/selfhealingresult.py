"""
    Defines the SelfHealingResult class representing the outcome of a
    self-healing action.
"""

import json

from datetime import datetime
from typing import Optional


class SelfHealingResult:
    """
        Immutable object representing the outcome of a self-healing action.

        :param check_name: The health check name.
        :param action_name: The action name.
        :param success: Whether the action succeeded.
        :param error_message: Optional error message.
        :param attempt_number: The attempt number.
        :param timestamp: The datetime of the result. Defaults to UTC now.
    """

    def __init__(self, check_name: str, action_name: str, success: bool,
                 error_message: Optional[str] = None,
                 attempt_number: int = 1,
                 timestamp: Optional[datetime] = None) -> None:
        self._check_name = check_name
        self._action_name = action_name
        self._success = success
        self._error_message = error_message
        self._attempt_number = attempt_number
        self._timestamp = timestamp if timestamp is not None else datetime.utcnow()
        return

    @property
    def check_name(self) -> str:
        return self._check_name

    @property
    def action_name(self) -> str:
        return self._action_name

    @property
    def success(self) -> bool:
        return self._success

    @property
    def error_message(self) -> str:
        return self._error_message

    @property
    def attempt_number(self) -> int:
        return self._attempt_number

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def is_success(self) -> bool:
        return self._success

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the result fields.

            :returns: A dictionary of result fields.
        """
        result = {
            "check_name": self._check_name,
            "action_name": self._action_name,
            "success": self._success,
            "error_message": self._error_message,
            "attempt_number": self._attempt_number,
            "timestamp": self._timestamp.isoformat()
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
    def from_dict(cls, data: dict) -> "SelfHealingResult":
        """
            Constructs a SelfHealingResult from a dictionary.

            :param data: Dictionary containing result fields.

            :returns: A SelfHealingResult instance.
        """
        result = cls(
            check_name=data["check_name"],
            action_name=data["action_name"],
            success=data["success"],
            error_message=data.get("error_message"),
            attempt_number=data.get("attempt_number", 1),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None
        )
        return result

    @classmethod
    def from_json(cls, json_str: str) -> "SelfHealingResult":
        """
            Deserializes a JSON string into a SelfHealingResult instance.

            :param json_str: JSON string to deserialize.

            :returns: A SelfHealingResult instance.
        """
        data = json.loads(json_str)
        result = cls.from_dict(data)
        return result

    def __repr__(self) -> str:
        return "SelfHealingResult(check_name={!r}, action={!r}, success={})".format(
            self._check_name, self._action_name, self._success
        )

    def __str__(self) -> str:
        return "SelfHealingResult check='{}', action='{}', success={}, attempt={}".format(
            self._check_name, self._action_name, self._success, self._attempt_number
        )