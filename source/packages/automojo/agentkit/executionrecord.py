"""
    Defines the ExecutionRecord class representing an immutable recorded
    event during agent execution.

    An ExecutionRecord contains a sequence number, a timestamp, an event
    type string, the agent identifier, a correlation identifier, and a
    payload dictionary with event-specific data. All fields are exposed
    as read-only properties to preserve immutability after construction.
"""

import json

from datetime import datetime


class ExecutionRecord:
    """
        An immutable object representing a recorded event during agent
        execution.

        Contains a sequence number identifying the order of the event,
        a timestamp, an event type string, the agent identifier, a
        correlation identifier, and a payload dictionary. All fields
        are read-only after construction.

        :param sequence_number: The monotonically increasing sequence
            number for this record.
        :param timestamp: The timestamp when the event was recorded.
        :param event_type: The event type string identifying the kind
            of event recorded.
        :param agent_id: The agent identifier string for the agent that
            produced this record.
        :param correlation_id: The correlation identifier string linking
            this record to a logical operation.
        :param payload: Optional dictionary of event-specific data.
    """

    def __init__(self, sequence_number: int, timestamp: datetime,
                 event_type: str, agent_id: str, correlation_id: str,
                 payload: dict = None) -> None:

        self._sequence_number = sequence_number
        self._timestamp = timestamp
        self._event_type = event_type
        self._agent_id = agent_id
        self._correlation_id = correlation_id

        if payload is not None:
            self._payload = dict(payload)
        else:
            self._payload = {}

        return

    @property
    def sequence_number(self) -> int:
        """
            The monotonically increasing sequence number for this record.

            :returns: The sequence number integer.
        """
        return self._sequence_number

    @property
    def timestamp(self) -> datetime:
        """
            The timestamp when the event was recorded.

            :returns: The datetime timestamp.
        """
        return self._timestamp

    @property
    def event_type(self) -> str:
        """
            The event type string identifying the kind of event recorded.

            :returns: The event type string.
        """
        return self._event_type

    @property
    def agent_id(self) -> str:
        """
            The agent identifier string for the agent that produced
            this record.

            :returns: The agent identifier string.
        """
        return self._agent_id

    @property
    def correlation_id(self) -> str:
        """
            The correlation identifier string linking this record to
            a logical operation.

            :returns: The correlation identifier string.
        """
        return self._correlation_id

    @property
    def payload(self) -> dict:
        """
            A copy of the payload dictionary of event-specific data.
            Returns a copy to preserve immutability.

            :returns: A dictionary copy of the payload fields.
        """
        result = dict(self._payload)
        return result

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the execution record
            fields.

            The timestamp is serialized as an ISO format string for
            consistent representation.

            :returns: A dictionary containing all execution record fields.
        """
        result = {
            "sequence_number": self._sequence_number,
            "timestamp": self._timestamp.isoformat(),
            "event_type": self._event_type,
            "agent_id": self._agent_id,
            "correlation_id": self._correlation_id,
            "payload": dict(self._payload)
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the execution record
            fields.

            :returns: A JSON string containing all execution record fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionRecord":
        """
            Constructs an ExecutionRecord from a dictionary.

            The timestamp field is expected to be an ISO format string
            and is parsed back into a datetime object.

            :param data: A dictionary containing execution record fields.

            :returns: An ExecutionRecord instance reconstructed from
                the dictionary.
        """
        sequence_number = data["sequence_number"]
        timestamp = datetime.fromisoformat(data["timestamp"])
        event_type = data["event_type"]
        agent_id = data["agent_id"]
        correlation_id = data["correlation_id"]
        payload = data.get("payload", None)

        record = cls(
            sequence_number=sequence_number,
            timestamp=timestamp,
            event_type=event_type,
            agent_id=agent_id,
            correlation_id=correlation_id,
            payload=payload
        )
        return record

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionRecord":
        """
            Deserializes a JSON string into an ExecutionRecord instance.

            :param json_str: A JSON string containing execution record
                fields.

            :returns: An ExecutionRecord instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        record = cls.from_dict(data)
        return record

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            sequence number, event type, and agent identifier.

            :returns: A repr string for debugging.
        """
        repr_str = "ExecutionRecord(sequence_number={!r}, event_type={!r}, agent_id={!r})".format(
            self._sequence_number, self._event_type, self._agent_id
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the sequence number,
            timestamp, event type, agent identifier, and correlation
            identifier.

            :returns: A human-readable string.
        """
        str_val = "ExecutionRecord: sequence_number={}, timestamp={}, event_type={}, agent_id={}, correlation_id={}".format(
            self._sequence_number, self._timestamp.isoformat(),
            self._event_type, self._agent_id, self._correlation_id
        )
        return str_val
