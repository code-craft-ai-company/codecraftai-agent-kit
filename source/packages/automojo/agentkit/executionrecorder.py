"""
    Defines the ExecutionRecorder class that captures ExecutionRecord
    objects during agent execution.

    The ExecutionRecorder maintains an ordered list of records with
    monotonically increasing sequence numbers starting from 1. It
    supports start, stop, record, get_recording, and clear operations.
    When not recording, the record method silently discards events.
"""

from datetime import datetime

from automojo.agentkit.executionrecord import ExecutionRecord
from automojo.agentkit.executionrecording import ExecutionRecording


class ExecutionRecorder:
    """
        A component that captures ExecutionRecord objects during agent
        execution, storing them in an ordered sequence for later replay
        and inspection.

        The recorder must be started before it will capture events.
        When not recording, calls to record are silently discarded.
        Sequence numbers are monotonically increasing starting from 1.

        :param agent_id: The agent identifier string for the agent
            whose execution is being recorded.
    """

    def __init__(self, agent_id: str) -> None:

        self._agent_id = agent_id
        self._records = []
        self._sequence_counter = 0
        self._is_recording = False
        self._start_time = None
        self._stop_time = None

        return

    @property
    def count(self) -> int:
        """
            The number of records currently captured.

            :returns: The record count integer.
        """
        return len(self._records)

    @property
    def is_recording(self) -> bool:
        """
            Whether the recorder is currently capturing events.

            :returns: True if recording is active, False otherwise.
        """
        return self._is_recording

    def start(self) -> None:
        """
            Starts recording execution events. Sets the start timestamp
            to the current UTC time and enables event capture.

            :returns: None.
        """
        self._is_recording = True
        self._start_time = datetime.utcnow()
        self._stop_time = None
        return

    def stop(self) -> None:
        """
            Stops recording execution events. Sets the stop timestamp
            to the current UTC time and disables event capture.

            :returns: None.
        """
        self._is_recording = False
        self._stop_time = datetime.utcnow()
        return

    def record(self, event_type: str, correlation_id: str,
               payload: dict = None) -> None:
        """
            Records an execution event if the recorder is currently
            active. When not recording, the event is silently discarded.

            Each recorded event receives a monotonically increasing
            sequence number starting from 1.

            :param event_type: The event type string identifying the
                kind of event.
            :param correlation_id: The correlation identifier string
                linking this event to a logical operation.
            :param payload: Optional dictionary of event-specific data.

            :returns: None.
        """
        if not self._is_recording:
            return

        self._sequence_counter += 1

        record = ExecutionRecord(
            sequence_number=self._sequence_counter,
            timestamp=datetime.utcnow(),
            event_type=event_type,
            agent_id=self._agent_id,
            correlation_id=correlation_id,
            payload=payload
        )

        self._records.append(record)

        return

    def get_recording(self) -> ExecutionRecording:
        """
            Returns an ExecutionRecording containing all captured records.

            The start_time is the time when start was called. The
            end_time is the time when stop was called, or the current
            UTC time if still recording.

            :returns: An ExecutionRecording instance with the captured
                records.
        """
        start_time = self._start_time
        if start_time is None:
            start_time = datetime.utcnow()

        end_time = self._stop_time
        if end_time is None:
            end_time = datetime.utcnow()

        recording = ExecutionRecording(
            agent_id=self._agent_id,
            start_time=start_time,
            end_time=end_time,
            records=list(self._records)
        )
        return recording

    def clear(self) -> None:
        """
            Clears all captured records and resets the sequence counter
            to zero.

            :returns: None.
        """
        self._records = []
        self._sequence_counter = 0
        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, record count, and recording state.

            :returns: A repr string for debugging.
        """
        record_count = len(self._records)
        repr_str = "ExecutionRecorder(agent_id={!r}, count={}, is_recording={})".format(
            self._agent_id, record_count, self._is_recording
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent identifier,
            record count, and recording state.

            :returns: A human-readable string.
        """
        record_count = len(self._records)
        str_val = "ExecutionRecorder: agent_id={}, count={}, is_recording={}".format(
            self._agent_id, record_count, self._is_recording
        )
        return str_val
