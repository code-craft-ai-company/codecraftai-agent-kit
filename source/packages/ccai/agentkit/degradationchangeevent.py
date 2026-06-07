"""
    Defines the DegradationChangeEvent class representing a change in
    degradation level in the Error Handling & Resilience feature.
"""

import json

from datetime import datetime

from ccai.agentkit.degradationlevel import DegradationLevel


class DegradationChangeEvent:
    """
        Immutable object representing a change in degradation level.

        :param dependency_name: The name of the dependency.
        :param previous_level: The previous DegradationLevel.
        :param new_level: The new DegradationLevel.
        :param reason: The reason for the change.
        :param timestamp: The datetime of the event. Defaults to UTC now.
    """

    def __init__(self, dependency_name: str, previous_level: DegradationLevel,
                 new_level: DegradationLevel, reason: str,
                 timestamp: datetime = None) -> None:
        self._dependency_name = dependency_name
        self._previous_level = previous_level
        self._new_level = new_level
        self._reason = reason
        self._timestamp = timestamp if timestamp is not None else datetime.utcnow()
        return

    @property
    def dependency_name(self) -> str:
        return self._dependency_name

    @property
    def previous_level(self) -> DegradationLevel:
        return self._previous_level

    @property
    def new_level(self) -> DegradationLevel:
        return self._new_level

    @property
    def reason(self) -> str:
        return self._reason

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the event fields.

            :returns: A dictionary of event fields.
        """
        result = {
            "dependency_name": self._dependency_name,
            "previous_level": self._previous_level.value,
            "new_level": self._new_level.value,
            "reason": self._reason,
            "timestamp": self._timestamp.isoformat()
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the event fields.

            :returns: A JSON string.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "DegradationChangeEvent":
        """
            Constructs a DegradationChangeEvent from a dictionary.

            :param data: Dictionary containing event fields.

            :returns: A DegradationChangeEvent instance.
        """
        event = cls(
            dependency_name=data["dependency_name"],
            previous_level=DegradationLevel.from_string(data["previous_level"]),
            new_level=DegradationLevel.from_string(data["new_level"]),
            reason=data["reason"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
        return event

    @classmethod
    def from_json(cls, json_str: str) -> "DegradationChangeEvent":
        """
            Deserializes a JSON string into a DegradationChangeEvent instance.

            :param json_str: JSON string to deserialize.

            :returns: A DegradationChangeEvent instance.
        """
        data = json.loads(json_str)
        event = cls.from_dict(data)
        return event

    def __repr__(self) -> str:
        repr_str = "DegradationChangeEvent(dependency={!r}, {} -> {})".format(
            self._dependency_name, self._previous_level.value, self._new_level.value
        )
        return repr_str

    def __str__(self) -> str:
        str_val = "DegradationChangeEvent dependency='{}', {} -> {}, reason='{}'".format(
            self._dependency_name, self._previous_level.value, self._new_level.value, self._reason
        )
        return str_val
