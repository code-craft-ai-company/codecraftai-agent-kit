"""
    Defines the ConfigurationChangeEvent class representing a detected
    change in configuration within the automojo-agent-kit framework.

    A ConfigurationChangeEvent contains the field path that changed,
    the previous value, the new value, the ConfigurationLayerSource
    that caused the change, and a timestamp.
"""

import json

from datetime import datetime

from automojo.agentkit.configurationlayersource import ConfigurationLayerSource


class ConfigurationChangeEvent:
    """
        Immutable object representing a detected change in configuration.

        Contains the field path, previous value, new value, source, and timestamp.

        :param field_path: The dot-separated field path that changed.
        :param previous_value: The value before the change.
        :param new_value: The value after the change.
        :param source: The ConfigurationLayerSource that caused the change.
        :param timestamp: The datetime when the change was detected.
    """

    def __init__(self, field_path: str, previous_value, new_value,
                 source: ConfigurationLayerSource, timestamp: datetime) -> None:
        self._field_path = field_path
        self._previous_value = previous_value
        self._new_value = new_value
        self._source = source
        self._timestamp = timestamp
        return

    @property
    def field_path(self) -> str:
        """
            The dot-separated field path that changed.

            :returns: The field path string.
        """
        return self._field_path

    @property
    def previous_value(self):
        """
            The value before the change.

            :returns: The previous value.
        """
        return self._previous_value

    @property
    def new_value(self):
        """
            The value after the change.

            :returns: The new value.
        """
        return self._new_value

    @property
    def source(self) -> ConfigurationLayerSource:
        """
            The ConfigurationLayerSource that caused the change.

            :returns: The ConfigurationLayerSource value.
        """
        return self._source

    @property
    def timestamp(self) -> datetime:
        """
            The datetime when the change was detected.

            :returns: The timestamp as a datetime object.
        """
        return self._timestamp

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the event fields.

            The timestamp is serialized as an ISO format string and the
            source is serialized as its string value.

            :returns: A dictionary with field_path, previous_value, new_value,
                source, and timestamp.
        """
        result = {
            "field_path": self._field_path,
            "previous_value": self._previous_value,
            "new_value": self._new_value,
            "source": self._source.value,
            "timestamp": self._timestamp.isoformat()
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the event fields.

            :returns: A JSON string containing field_path, previous_value,
                new_value, source, and timestamp.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "ConfigurationChangeEvent":
        """
            Constructs a ConfigurationChangeEvent from a dictionary.

            Parses the timestamp from ISO format and the source from its
            string value.

            :param data: A dictionary containing field_path, previous_value,
                new_value, source, and timestamp.

            :returns: A ConfigurationChangeEvent instance reconstructed from
                the dictionary.
        """
        field_path = data["field_path"]
        previous_value = data["previous_value"]
        new_value = data["new_value"]
        source = ConfigurationLayerSource.from_string(data["source"])
        timestamp = datetime.fromisoformat(data["timestamp"])

        event = cls(
            field_path=field_path,
            previous_value=previous_value,
            new_value=new_value,
            source=source,
            timestamp=timestamp
        )
        return event

    @classmethod
    def from_json(cls, json_str: str) -> "ConfigurationChangeEvent":
        """
            Deserializes a JSON string into a ConfigurationChangeEvent instance.

            :param json_str: A JSON string containing event fields.

            :returns: A ConfigurationChangeEvent instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        event = cls.from_dict(data)
        return event

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            field path, and source.

            :returns: A repr string for debugging.
        """
        repr_str = "ConfigurationChangeEvent(field_path={!r}, source={!r})".format(
            self._field_path, self._source
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the field path,
            previous value, new value, and source.

            :returns: A human-readable string.
        """
        str_val = "ConfigurationChangeEvent field_path='{}', previous={!r}, new={!r}, source={}".format(
            self._field_path, self._previous_value, self._new_value, self._source
        )
        return str_val
