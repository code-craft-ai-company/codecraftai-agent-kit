"""
    Unit tests for the automojo.agentkit.executionrecording module.

    Tests the ExecutionRecording class: construction, duration property,
    filter_by_event_type, serialization (as_dict, to_json, from_dict,
    from_json), __repr__, and __str__.
"""

import json

from datetime import datetime

from automojo.agentkit.executionrecord import ExecutionRecord
from automojo.agentkit.executionrecording import ExecutionRecording


def _make_record(seq, event_type="lifecycle"):
    """
        Helper to create an ExecutionRecord with minimal fields.
    """
    record = ExecutionRecord(
        sequence_number=seq,
        timestamp=datetime(2025, 6, 15, 10, 30, seq),
        event_type=event_type,
        agent_id="agent-001",
        correlation_id="corr-abc",
        payload={"seq": seq}
    )
    return record


def test_construction_stores_all_fields():
    """
        Verify that all fields provided at construction are stored correctly.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    records = [_make_record(1), _make_record(2)]

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=records
    )

    assert recording.agent_id == "agent-001", "agent_id should match"
    assert recording.start_time == start, "start_time should match"
    assert recording.end_time == end, "end_time should match"
    assert len(recording.records) == 2, "records should have 2 items"
    return


def test_records_defaults_to_empty_list():
    """
        Verify that records defaults to an empty list when not provided.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end
    )

    assert recording.records == [], "records should default to empty list"
    return


def test_duration_returns_elapsed_seconds():
    """
        Verify that duration returns the elapsed seconds between start and end.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end
    )

    duration = recording.duration
    assert duration == 300.0, "duration should be 300 seconds (5 minutes)"
    return


def test_filter_by_event_type_returns_matching_records():
    """
        Verify that filter_by_event_type returns only matching records.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    records = [
        _make_record(1, "lifecycle"),
        _make_record(2, "tool"),
        _make_record(3, "lifecycle"),
        _make_record(4, "llm"),
    ]

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=records
    )

    filtered = recording.filter_by_event_type("lifecycle")

    assert len(filtered.records) == 2, "filtered should have 2 lifecycle records"
    assert filtered.records[0].sequence_number == 1, "first filtered record should be seq 1"
    assert filtered.records[1].sequence_number == 3, "second filtered record should be seq 3"
    assert filtered.agent_id == "agent-001", "filtered agent_id should be preserved"
    return


def test_filter_by_event_type_returns_empty_for_no_match():
    """
        Verify that filter_by_event_type returns empty when no records match.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    records = [_make_record(1, "lifecycle")]

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=records
    )

    filtered = recording.filter_by_event_type("tool")

    assert len(filtered.records) == 0, "filtered should have 0 records"
    return


def test_as_dict_returns_all_fields():
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    records = [_make_record(1)]

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=records
    )

    result = recording.as_dict()

    assert result["agent_id"] == "agent-001", "as_dict agent_id should match"
    assert result["start_time"] == "2025-06-15T10:00:00", "as_dict start_time should be ISO"
    assert result["end_time"] == "2025-06-15T10:05:00", "as_dict end_time should be ISO"
    assert len(result["records"]) == 1, "as_dict records should have 1 item"
    return


def test_to_json_returns_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=[_make_record(1)]
    )

    json_str = recording.to_json()
    parsed = json.loads(json_str)

    assert parsed["agent_id"] == "agent-001", "JSON agent_id should match"
    return


def test_from_dict_reconstructs_recording():
    """
        Verify that from_dict reconstructs an ExecutionRecording from a dictionary.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    original = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=[_make_record(1)]
    )

    data = original.as_dict()
    reconstructed = ExecutionRecording.from_dict(data)

    assert reconstructed.agent_id == "agent-001", "from_dict agent_id should match"
    assert reconstructed.start_time == start, "from_dict start_time should match"
    assert reconstructed.end_time == end, "from_dict end_time should match"
    assert len(reconstructed.records) == 1, "from_dict records should have 1 item"
    return


def test_json_round_trip():
    """
        Verify that to_json then from_json produces equal fields.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)
    records = [_make_record(1), _make_record(2)]

    original = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end,
        records=records
    )

    json_str = original.to_json()
    reconstructed = ExecutionRecording.from_json(json_str)

    assert reconstructed.agent_id == original.agent_id
    assert reconstructed.start_time == original.start_time
    assert reconstructed.end_time == original.end_time
    assert len(reconstructed.records) == len(original.records)
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end
    )

    repr_str = repr(recording)
    assert "ExecutionRecording" in repr_str, "__repr__ should contain class name"
    return


def test_str_contains_agent_id():
    """
        Verify that __str__ contains the agent identifier.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end
    )

    str_val = str(recording)
    assert "agent-001" in str_val, "__str__ should contain agent_id"
    return


def test_str_contains_duration():
    """
        Verify that __str__ contains the duration.
    """
    start = datetime(2025, 6, 15, 10, 0, 0)
    end = datetime(2025, 6, 15, 10, 5, 0)

    recording = ExecutionRecording(
        agent_id="agent-001",
        start_time=start,
        end_time=end
    )

    str_val = str(recording)
    assert "300.000" in str_val, "__str__ should contain duration"
    return
