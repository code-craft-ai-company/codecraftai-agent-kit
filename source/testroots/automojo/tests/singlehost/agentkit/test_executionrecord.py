"""
    Unit tests for the automojo.agentkit.executionrecord module.

    Tests the ExecutionRecord class: construction, read-only properties,
    serialization (as_dict, to_json, from_dict, from_json), __repr__,
    and __str__.
"""

import json

from datetime import datetime

from automojo.agentkit.executionrecord import ExecutionRecord


def test_construction_stores_all_fields():
    """
        Verify that all fields provided at construction are stored correctly.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="lifecycle",
        agent_id="agent-001",
        correlation_id="corr-abc",
        payload={"state": "running"}
    )

    assert record.sequence_number == 1, "sequence_number should be 1"
    assert record.timestamp == timestamp, "timestamp should match"
    assert record.event_type == "lifecycle", "event_type should be lifecycle"
    assert record.agent_id == "agent-001", "agent_id should be agent-001"
    assert record.correlation_id == "corr-abc", "correlation_id should be corr-abc"
    assert record.payload == {"state": "running"}, "payload should match"
    return


def test_payload_defaults_to_empty_dict():
    """
        Verify that payload defaults to an empty dict when not provided.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="tool",
        agent_id="agent-001",
        correlation_id="corr-abc"
    )

    payload = record.payload
    assert payload == {}, "payload should default to empty dict"
    return


def test_payload_is_defensive_copy():
    """
        Verify that the payload property returns a copy, not the internal dict.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    original_payload = {"key": "value"}
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="tool",
        agent_id="agent-001",
        correlation_id="corr-abc",
        payload=original_payload
    )

    returned_payload = record.payload
    returned_payload["new_key"] = "new_value"

    assert "new_key" not in record.payload, "Modifying returned payload should not affect internal state"
    return


def test_as_dict_returns_all_fields():
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=5,
        timestamp=timestamp,
        event_type="llm",
        agent_id="agent-002",
        correlation_id="corr-xyz",
        payload={"model": "gpt-4"}
    )

    result = record.as_dict()

    assert result["sequence_number"] == 5, "as_dict sequence_number should be 5"
    assert result["timestamp"] == "2025-06-15T10:30:00", "as_dict timestamp should be ISO format"
    assert result["event_type"] == "llm", "as_dict event_type should be llm"
    assert result["agent_id"] == "agent-002", "as_dict agent_id should be agent-002"
    assert result["correlation_id"] == "corr-xyz", "as_dict correlation_id should be corr-xyz"
    assert result["payload"] == {"model": "gpt-4"}, "as_dict payload should match"
    return


def test_to_json_returns_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="lifecycle",
        agent_id="agent-001",
        correlation_id="corr-abc"
    )

    json_str = record.to_json()
    parsed = json.loads(json_str)

    assert parsed["sequence_number"] == 1, "JSON sequence_number should be 1"
    assert parsed["event_type"] == "lifecycle", "JSON event_type should be lifecycle"
    return


def test_from_dict_reconstructs_record():
    """
        Verify that from_dict reconstructs an ExecutionRecord from a dictionary.
    """
    data = {
        "sequence_number": 3,
        "timestamp": "2025-06-15T10:30:00",
        "event_type": "tool",
        "agent_id": "agent-003",
        "correlation_id": "corr-123",
        "payload": {"tool_name": "search"}
    }

    record = ExecutionRecord.from_dict(data)

    assert record.sequence_number == 3, "from_dict sequence_number should be 3"
    assert record.timestamp == datetime(2025, 6, 15, 10, 30, 0), "from_dict timestamp should match"
    assert record.event_type == "tool", "from_dict event_type should be tool"
    assert record.agent_id == "agent-003", "from_dict agent_id should be agent-003"
    assert record.correlation_id == "corr-123", "from_dict correlation_id should be corr-123"
    assert record.payload == {"tool_name": "search"}, "from_dict payload should match"
    return


def test_from_json_reconstructs_record():
    """
        Verify that from_json reconstructs an ExecutionRecord from a JSON string.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    original = ExecutionRecord(
        sequence_number=2,
        timestamp=timestamp,
        event_type="memory",
        agent_id="agent-004",
        correlation_id="corr-456",
        payload={"operation": "read"}
    )

    json_str = original.to_json()
    reconstructed = ExecutionRecord.from_json(json_str)

    assert reconstructed.sequence_number == 2, "from_json sequence_number should be 2"
    assert reconstructed.event_type == "memory", "from_json event_type should be memory"
    assert reconstructed.payload == {"operation": "read"}, "from_json payload should match"
    return


def test_json_round_trip():
    """
        Verify that to_json then from_json produces equal fields.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    original = ExecutionRecord(
        sequence_number=7,
        timestamp=timestamp,
        event_type="workflow",
        agent_id="agent-005",
        correlation_id="corr-789",
        payload={"step": "validate"}
    )

    json_str = original.to_json()
    reconstructed = ExecutionRecord.from_json(json_str)

    assert reconstructed.sequence_number == original.sequence_number
    assert reconstructed.timestamp == original.timestamp
    assert reconstructed.event_type == original.event_type
    assert reconstructed.agent_id == original.agent_id
    assert reconstructed.correlation_id == original.correlation_id
    assert reconstructed.payload == original.payload
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="lifecycle",
        agent_id="agent-001",
        correlation_id="corr-abc"
    )

    repr_str = repr(record)
    assert "ExecutionRecord" in repr_str, "__repr__ should contain class name"
    return


def test_repr_contains_event_type():
    """
        Verify that __repr__ contains the event type.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="lifecycle",
        agent_id="agent-001",
        correlation_id="corr-abc"
    )

    repr_str = repr(record)
    assert "lifecycle" in repr_str, "__repr__ should contain event_type"
    return


def test_str_contains_event_type():
    """
        Verify that __str__ contains the event type.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="lifecycle",
        agent_id="agent-001",
        correlation_id="corr-abc"
    )

    str_val = str(record)
    assert "lifecycle" in str_val, "__str__ should contain event_type"
    return


def test_str_contains_agent_id():
    """
        Verify that __str__ contains the agent identifier.
    """
    timestamp = datetime(2025, 6, 15, 10, 30, 0)
    record = ExecutionRecord(
        sequence_number=1,
        timestamp=timestamp,
        event_type="lifecycle",
        agent_id="agent-001",
        correlation_id="corr-abc"
    )

    str_val = str(record)
    assert "agent-001" in str_val, "__str__ should contain agent_id"
    return
