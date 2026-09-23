"""
    Defines the TraceEvent class representing an immutable timestamped
    annotation within a TraceSpan.

    TraceEvent objects record significant moments during a span's
    lifetime for debugging and analysis. Each event contains a name,
    a timestamp, and an attributes dictionary of key-value pairs.
    All fields are exposed as read-only properties to preserve
    immutability after construction.
"""

import json

from datetime import datetime


class TraceEvent:
    """
        An immutable object representing a timestamped annotation within
        a TraceSpan.

        Contains a name string, a timestamp, and an attributes dictionary
        of key-value pairs. The timestamp defaults to the current UTC time
        when not explicitly provided.

        :param name: The name string identifying this event.
        :param timestamp: Optional timestamp for the event. Defaults to
            the current UTC time if not provided.
        :param attributes: Optional dictionary of key-value attributes
            associated with this event.
    """

    def __init__(self, name: str, timestamp: datetime = None,
                 attributes: dict = None) -> None:

        self._name = name

        if timestamp is not None:
            self._timestamp = timestamp
        else:
            self._timestamp = datetime.utcnow()

        if attributes is not None:
            self._attributes = dict(attributes)
        else:
            self._attributes = {}

        return

    @property
    def name(self) -> str:
        """
            The name string identifying this event.

            :returns: The event name string.
        """
        return self._name

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp when this event occurred.

            :returns: The datetime timestamp.
        """
        return self._timestamp

    @property
    def attributes(self) -> dict:
        """
            A copy of the attributes dictionary of key-value pairs
            associated with this event. Returns a copy to preserve
            immutability.

            :returns: A dictionary copy of the event attributes.
        """
        result = dict(self._attributes)
        return result

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the event fields.

            The timestamp is serialized as an ISO format string for
            consistent representation.

            :returns: A dictionary containing all event fields.
        """
        result = {
            "name": self._name,
            "timestamp": self._timestamp.isoformat(),
            "attributes": dict(self._attributes)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the event fields.

            :returns: A JSON string containing all event fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "TraceEvent":
        """
            Constructs a TraceEvent from a dictionary.

            The timestamp field is expected to be an ISO format string
            and is parsed back into a datetime object.

            :param data: A dictionary containing event fields.

            :returns: A TraceEvent instance reconstructed from
                the dictionary.
        """
        name = data["name"]
        timestamp = datetime.fromisoformat(data["timestamp"])
        attributes = data.get("attributes", None)

        event = cls(
            name=name,
            timestamp=timestamp,
            attributes=attributes
        )
        return event

    @classmethod
    def from_json(cls, json_str: str) -> "TraceEvent":
        """
            Deserializes a JSON string into a TraceEvent instance.

            :param json_str: A JSON string containing event fields.

            :returns: A TraceEvent instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        event = cls.from_dict(data)
        return event

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            name, and timestamp.

            :returns: A repr string for debugging.
        """
        repr_str = "TraceEvent(name={!r}, timestamp={!r})".format(
            self._name, self._timestamp.isoformat()
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the name and
            timestamp.

            :returns: A human-readable string.
        """
        str_val = "TraceEvent: name={}, timestamp={}".format(
            self._name, self._timestamp.isoformat()
        )
        return str_val
