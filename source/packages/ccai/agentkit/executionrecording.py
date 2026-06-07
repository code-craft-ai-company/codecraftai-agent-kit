"""
    Defines the ExecutionRecording class representing an immutable
    complete recording of agent execution.

    An ExecutionRecording contains the agent identifier, a start
    timestamp, an end timestamp, and an ordered list of ExecutionRecord
    objects. It supports filtering by event type and serialization
    to and from JSON and dictionary representations.
"""

import json

from datetime import datetime

from ccai.agentkit.executionrecord import ExecutionRecord


class ExecutionRecording:
    """
        An immutable object representing a complete recording of agent
        execution.

        Contains the agent identifier, a start timestamp, an end
        timestamp, and an ordered list of ExecutionRecord objects.
        All fields are read-only after construction.

        :param agent_id: The agent identifier string for the agent
            whose execution was recorded.
        :param start_time: The timestamp when recording started.
        :param end_time: The timestamp when recording ended.
        :param records: Optional list of ExecutionRecord objects in
            sequence order.
    """

    def __init__(self, agent_id: str, start_time: datetime,
                 end_time: datetime, records: list = None) -> None:

        self._agent_id = agent_id
        self._start_time = start_time
        self._end_time = end_time

        if records is not None:
            self._records = list(records)
        else:
            self._records = []

        return

    @property
    def agent_id(self) -> str:
        """
            The agent identifier string for the agent whose execution
            was recorded.

            :returns: The agent identifier string.
        """
        return self._agent_id

    @property
    def start_time(self) -> datetime:
        """
            The timestamp when recording started.

            :returns: The start datetime timestamp.
        """
        return self._start_time

    @property
    def end_time(self) -> datetime:
        """
            The timestamp when recording ended.

            :returns: The end datetime timestamp.
        """
        return self._end_time

    @property
    def records(self) -> list:
        """
            A copy of the ordered list of ExecutionRecord objects.
            Returns a copy to preserve immutability.

            :returns: A list copy of the ExecutionRecord objects.
        """
        result = list(self._records)
        return result

    @property
    def duration(self) -> float:
        """
            The elapsed time in seconds between the start and end
            timestamps.

            :returns: The duration as a float in seconds.
        """
        delta = self._end_time - self._start_time
        elapsed = delta.total_seconds()
        return elapsed

    def filter_by_event_type(self, event_type: str) -> "ExecutionRecording":
        """
            Returns a new ExecutionRecording containing only the records
            that match the specified event type. The agent_id, start_time,
            and end_time are preserved from the original recording.

            :param event_type: The event type string to filter by.

            :returns: A new ExecutionRecording with matching records.
        """
        matching_records = []

        for record in self._records:
            if record.event_type == event_type:
                matching_records.append(record)

        filtered = ExecutionRecording(
            agent_id=self._agent_id,
            start_time=self._start_time,
            end_time=self._end_time,
            records=matching_records
        )
        return filtered

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the execution recording
            fields.

            The timestamps are serialized as ISO format strings. Each
            ExecutionRecord is serialized via its own as_dict method.

            :returns: A dictionary containing all execution recording fields.
        """
        record_dicts = []
        for record in self._records:
            record_dicts.append(record.as_dict())

        result = {
            "agent_id": self._agent_id,
            "start_time": self._start_time.isoformat(),
            "end_time": self._end_time.isoformat(),
            "records": record_dicts
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the execution recording
            fields.

            :returns: A JSON string containing all execution recording fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionRecording":
        """
            Constructs an ExecutionRecording from a dictionary.

            The timestamp fields are expected to be ISO format strings
            and are parsed back into datetime objects. Each record
            dictionary is deserialized via ExecutionRecord.from_dict.

            :param data: A dictionary containing execution recording fields.

            :returns: An ExecutionRecording instance reconstructed from
                the dictionary.
        """
        agent_id = data["agent_id"]
        start_time = datetime.fromisoformat(data["start_time"])
        end_time = datetime.fromisoformat(data["end_time"])

        records = []
        raw_records = data.get("records", [])
        for record_data in raw_records:
            record = ExecutionRecord.from_dict(record_data)
            records.append(record)

        recording = cls(
            agent_id=agent_id,
            start_time=start_time,
            end_time=end_time,
            records=records
        )
        return recording

    @classmethod
    def from_json(cls, json_str: str) -> "ExecutionRecording":
        """
            Deserializes a JSON string into an ExecutionRecording instance.

            :param json_str: A JSON string containing execution recording
                fields.

            :returns: An ExecutionRecording instance reconstructed from
                the JSON data.
        """
        data = json.loads(json_str)
        recording = cls.from_dict(data)
        return recording

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, and record count.

            :returns: A repr string for debugging.
        """
        record_count = len(self._records)
        repr_str = "ExecutionRecording(agent_id={!r}, record_count={})".format(
            self._agent_id, record_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent identifier,
            start time, end time, duration, and record count.

            :returns: A human-readable string.
        """
        record_count = len(self._records)
        elapsed = self.duration
        str_val = "ExecutionRecording: agent_id={}, start_time={}, end_time={}, duration={:.3f}s, records={}".format(
            self._agent_id, self._start_time.isoformat(),
            self._end_time.isoformat(), elapsed, record_count
        )
        return str_val
