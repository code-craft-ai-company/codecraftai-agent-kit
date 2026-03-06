"""
    Defines the ExecutionReplayer class that reads an ExecutionRecording
    and allows step-by-step inspection of the recorded events.

    The ExecutionReplayer supports forward traversal via next, backward
    traversal via previous, reset to the beginning, seek to a specific
    sequence number, and filtering by event type. It raises SemanticError
    when seeking to an invalid sequence number.
"""

import os

from typing import Optional

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.executionrecord import ExecutionRecord
from automojo.agentkit.executionrecording import ExecutionRecording


class ExecutionReplayer:
    """
        A component that reads an ExecutionRecording and allows
        step-by-step inspection of the recorded events.

        Supports forward and backward traversal, reset, seek by
        sequence number, and filtering by event type. The position
        starts at -1 (before the first record).

        :param recording: The ExecutionRecording to replay.
    """

    def __init__(self, recording: ExecutionRecording) -> None:

        self._recording = recording
        self._position = -1

        return

    @property
    def current(self) -> Optional[ExecutionRecord]:
        """
            The ExecutionRecord at the current position, or None if
            the position is before the first record or after the last.

            :returns: The current ExecutionRecord or None.
        """
        records = self._recording.records

        if self._position < 0:
            return None

        if self._position >= len(records):
            return None

        record = records[self._position]
        return record

    @property
    def position(self) -> int:
        """
            The current position index in the recording. Starts at -1
            before any traversal.

            :returns: The current position integer.
        """
        return self._position

    @property
    def total_count(self) -> int:
        """
            The total number of records in the recording.

            :returns: The total record count integer.
        """
        records = self._recording.records
        count = len(records)
        return count

    def next(self) -> Optional[ExecutionRecord]:
        """
            Advances the position by one and returns the ExecutionRecord
            at the new position. Returns None if there are no more
            records to traverse.

            :returns: The next ExecutionRecord or None.
        """
        records = self._recording.records
        next_position = self._position + 1

        if next_position >= len(records):
            return None

        self._position = next_position
        record = records[self._position]
        return record

    def previous(self) -> Optional[ExecutionRecord]:
        """
            Moves the position back by one and returns the ExecutionRecord
            at the new position. Returns None if already at or before
            the first record.

            :returns: The previous ExecutionRecord or None.
        """
        prev_position = self._position - 1

        if prev_position < 0:
            return None

        self._position = prev_position
        records = self._recording.records
        record = records[self._position]
        return record

    def reset(self) -> None:
        """
            Resets the position to -1, before the first record.

            :returns: None.
        """
        self._position = -1
        return

    def seek(self, sequence_number: int) -> ExecutionRecord:
        """
            Moves the position to the record with the specified sequence
            number and returns it. Raises SemanticError if no record
            with the given sequence number exists.

            :param sequence_number: The sequence number to seek to.

            :returns: The ExecutionRecord at the specified sequence number.

            :raises SemanticError: If no record with the given sequence
                number exists in the recording.
        """
        records = self._recording.records

        for index, record in enumerate(records):
            if record.sequence_number == sequence_number:
                self._position = index
                return record

        error_lines = []
        error_lines.append("Cannot seek to sequence number {}.".format(sequence_number))
        error_lines.append("No record with that sequence number exists in the recording.")
        error_message = os.linesep.join(error_lines)
        raise SemanticError(error_message)

    def filter(self, event_type: str) -> "ExecutionReplayer":
        """
            Returns a new ExecutionReplayer with a filtered recording
            containing only records that match the specified event type.

            :param event_type: The event type string to filter by.

            :returns: A new ExecutionReplayer with the filtered recording.
        """
        filtered_recording = self._recording.filter_by_event_type(event_type)
        replayer = ExecutionReplayer(filtered_recording)
        return replayer

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            position, and total record count.

            :returns: A repr string for debugging.
        """
        total = self.total_count
        repr_str = "ExecutionReplayer(position={}, total_count={})".format(
            self._position, total
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the position
            and total record count.

            :returns: A human-readable string.
        """
        total = self.total_count
        str_val = "ExecutionReplayer: position={}, total_count={}".format(
            self._position, total
        )
        return str_val
