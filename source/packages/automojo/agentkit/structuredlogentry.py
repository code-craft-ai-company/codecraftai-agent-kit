"""
    Defines the StructuredLogEntry class representing an immutable
    structured log record containing a timestamp, log level, message,
    logger name, correlation identifier, agent identifier, and a
    metadata dictionary of additional key-value fields.

    StructuredLogEntry objects are created by the StructuredLogger
    and consumed by LogFormatter and LogExporter implementations.
    All fields are exposed as read-only properties to preserve
    immutability after construction.
"""

import json

from datetime import datetime


class StructuredLogEntry:
    """
        An immutable object representing a single structured log record.

        Contains a timestamp, log level, message, logger name, correlation
        identifier, agent identifier, and a metadata dictionary. All fields
        are read-only after construction.

        :param timestamp: The timestamp when the log entry was created.
        :param level: The log level string (e.g. "debug", "info", "warning",
            "error", "critical").
        :param message: The log message string.
        :param logger_name: The name of the logger that produced this entry.
        :param correlation_id: The correlation identifier string linking
            this entry to a logical operation.
        :param agent_id: The agent identifier string for the agent that
            produced this entry.
        :param metadata: Optional dictionary of additional key-value fields.
    """

    def __init__(self, timestamp: datetime, level: str, message: str,
                 logger_name: str, correlation_id: str, agent_id: str,
                 metadata: dict = None) -> None:

        self._timestamp = timestamp
        self._level = level
        self._message = message
        self._logger_name = logger_name
        self._correlation_id = correlation_id
        self._agent_id = agent_id

        if metadata is not None:
            self._metadata = dict(metadata)
        else:
            self._metadata = {}

        return

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp when the log entry was created.

            :returns: The datetime timestamp.
        """
        return self._timestamp

    @property
    def level(self) -> str:
        """
            The log level string for this entry.

            :returns: The log level string.
        """
        return self._level

    @property
    def message(self) -> str:
        """
            The log message string.

            :returns: The message string.
        """
        return self._message

    @property
    def logger_name(self) -> str:
        """
            The name of the logger that produced this entry.

            :returns: The logger name string.
        """
        return self._logger_name

    @property
    def correlation_id(self) -> str:
        """
            The correlation identifier string linking this entry to a
            logical operation.

            :returns: The correlation identifier string.
        """
        return self._correlation_id

    @property
    def agent_id(self) -> str:
        """
            The agent identifier string for the agent that produced
            this entry.

            :returns: The agent identifier string.
        """
        return self._agent_id

    @property
    def metadata(self) -> dict:
        """
            A copy of the metadata dictionary of additional key-value
            fields. Returns a copy to preserve immutability.

            :returns: A dictionary copy of the metadata fields.
        """
        result = dict(self._metadata)
        return result

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the log entry fields.

            The timestamp is serialized as an ISO format string for
            consistent representation.

            :returns: A dictionary containing all log entry fields.
        """
        result = {
            "timestamp": self._timestamp.isoformat(),
            "level": self._level,
            "message": self._message,
            "logger_name": self._logger_name,
            "correlation_id": self._correlation_id,
            "agent_id": self._agent_id,
            "metadata": dict(self._metadata)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the log entry fields.

            :returns: A JSON string containing all log entry fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "StructuredLogEntry":
        """
            Constructs a StructuredLogEntry from a dictionary.

            The timestamp field is expected to be an ISO format string
            and is parsed back into a datetime object.

            :param data: A dictionary containing log entry fields.

            :returns: A StructuredLogEntry instance reconstructed from
                the dictionary.
        """
        timestamp = datetime.fromisoformat(data["timestamp"])
        level = data["level"]
        message = data["message"]
        logger_name = data["logger_name"]
        correlation_id = data["correlation_id"]
        agent_id = data["agent_id"]
        metadata = data.get("metadata", None)

        entry = cls(
            timestamp=timestamp,
            level=level,
            message=message,
            logger_name=logger_name,
            correlation_id=correlation_id,
            agent_id=agent_id,
            metadata=metadata
        )
        return entry

    @classmethod
    def from_json(cls, json_str: str) -> "StructuredLogEntry":
        """
            Deserializes a JSON string into a StructuredLogEntry instance.

            :param json_str: A JSON string containing log entry fields.

            :returns: A StructuredLogEntry instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        entry = cls.from_dict(data)
        return entry

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            log level, logger name, and correlation identifier.

            :returns: A repr string for debugging.
        """
        repr_str = "StructuredLogEntry(level={!r}, logger_name={!r}, correlation_id={!r})".format(
            self._level, self._logger_name, self._correlation_id
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the timestamp,
            log level, logger name, message, and correlation identifier.

            :returns: A human-readable string.
        """
        str_val = "StructuredLogEntry: timestamp={}, level={}, logger_name={}, message={}, correlation_id={}".format(
            self._timestamp.isoformat(), self._level, self._logger_name,
            self._message, self._correlation_id
        )
        return str_val
