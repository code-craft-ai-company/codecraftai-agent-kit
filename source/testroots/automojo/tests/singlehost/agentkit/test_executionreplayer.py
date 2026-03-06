"""
    Unit tests for the automojo.agentkit.executionreplayer module.

    Tests the ExecutionReplayer class: next/previous traversal, boundary
    conditions, reset, seek valid/invalid, filter, current, position,
    total_count, __repr__, and __str__.
"""

from datetime import datetime

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.executionrecord import ExecutionRecord
from automojo.agentkit.executionrecording import ExecutionRecording
from automojo.agentkit.executionreplayer import ExecutionReplayer


def _make_recording(count=3):
    """
        Helper to create an ExecutionRecording with the specified number
        of records.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    records = []

    for i in range(1, count + 1):
        record = ExecutionRecord(
            sequence_number=i,
            timestamp=datetime(2025, 6, 15, 10, 0, i),
            event_type="lifecycle" if i % 2 == 1 else "tool",
            agent_id="agent-001",
            correlation_id="corr-abc",
            payload={"index": i}
        )
        records.append(record)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=records
    )
    return recording


def test_initial_position_is_negative_one():
    """
        Verify that the initial position is -1.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    assert replayer.position == -1, "initial position should be -1"
    return


def test_initial_current_is_none():
    """
        Verify that current is None before any traversal.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    assert replayer.current is None, "current should be None at initial position"
    return


def test_total_count_matches_records():
    """
        Verify that total_count matches the number of records.
    """
    recording = _make_recording(5)
    replayer = ExecutionReplayer(recording)

    assert replayer.total_count == 5, "total_count should be 5"
    return


def test_next_returns_first_record():
    """
        Verify that the first call to next returns the first record.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    record = replayer.next()

    assert record is not None, "next should return a record"
    assert record.sequence_number == 1, "first next should return seq 1"
    assert replayer.position == 0, "position should be 0 after first next"
    return


def test_next_traverses_all_records():
    """
        Verify that calling next repeatedly traverses all records in order.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    record1 = replayer.next()
    record2 = replayer.next()
    record3 = replayer.next()

    assert record1.sequence_number == 1, "first record should be seq 1"
    assert record2.sequence_number == 2, "second record should be seq 2"
    assert record3.sequence_number == 3, "third record should be seq 3"
    return


def test_next_returns_none_past_end():
    """
        Verify that next returns None when past the last record.
    """
    recording = _make_recording(2)
    replayer = ExecutionReplayer(recording)

    replayer.next()
    replayer.next()
    result = replayer.next()

    assert result is None, "next past end should return None"
    return


def test_previous_returns_previous_record():
    """
        Verify that previous returns the previous record.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    replayer.next()
    replayer.next()
    record = replayer.previous()

    assert record is not None, "previous should return a record"
    assert record.sequence_number == 1, "previous should return seq 1"
    assert replayer.position == 0, "position should be 0 after previous"
    return


def test_previous_returns_none_at_start():
    """
        Verify that previous returns None when at the start.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    result = replayer.previous()

    assert result is None, "previous at start should return None"
    return


def test_previous_returns_none_at_first_record():
    """
        Verify that previous returns None when at position 0.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    replayer.next()
    result = replayer.previous()

    assert result is None, "previous at position 0 should return None"
    return


def test_reset_returns_to_initial_position():
    """
        Verify that reset returns position to -1.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    replayer.next()
    replayer.next()
    replayer.reset()

    assert replayer.position == -1, "position should be -1 after reset"
    assert replayer.current is None, "current should be None after reset"
    return


def test_seek_valid_sequence_number():
    """
        Verify that seek moves to the record with the given sequence number.
    """
    recording = _make_recording(5)
    replayer = ExecutionReplayer(recording)

    record = replayer.seek(3)

    assert record.sequence_number == 3, "seek should return record with seq 3"
    assert replayer.position == 2, "position should be 2 (index of seq 3)"
    assert replayer.current.sequence_number == 3, "current should be seq 3"
    return


def test_seek_invalid_sequence_number_raises_semantic_error():
    """
        Verify that seek raises SemanticError for an invalid sequence number.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    caught = False
    try:
        replayer.seek(99)
    except SemanticError:
        caught = True

    assert caught is True, "seek with invalid sequence number should raise SemanticError"
    return


def test_filter_returns_new_replayer_with_matching_records():
    """
        Verify that filter returns a new ExecutionReplayer with only matching records.
    """
    recording = _make_recording(4)
    replayer = ExecutionReplayer(recording)

    filtered = replayer.filter("lifecycle")

    assert filtered.total_count == 2, "filtered should have 2 lifecycle records"
    assert filtered.position == -1, "filtered replayer should start at -1"

    record1 = filtered.next()
    record2 = filtered.next()

    assert record1.event_type == "lifecycle", "first filtered record should be lifecycle"
    assert record2.event_type == "lifecycle", "second filtered record should be lifecycle"
    return


def test_filter_returns_empty_for_no_match():
    """
        Verify that filter returns a replayer with 0 records when no match.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    filtered = replayer.filter("nonexistent")

    assert filtered.total_count == 0, "filtered should have 0 records"
    assert filtered.next() is None, "next on empty filtered should return None"
    return


def test_current_after_next():
    """
        Verify that current returns the record at the current position after next.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    replayer.next()
    current = replayer.current

    assert current is not None, "current should not be None after next"
    assert current.sequence_number == 1, "current should be seq 1"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    repr_str = repr(replayer)
    assert "ExecutionReplayer" in repr_str, "__repr__ should contain class name"
    return


def test_str_contains_total_count():
    """
        Verify that __str__ contains the total count.
    """
    recording = _make_recording(3)
    replayer = ExecutionReplayer(recording)

    str_val = str(replayer)
    assert "3" in str_val, "__str__ should contain total_count"
    return
