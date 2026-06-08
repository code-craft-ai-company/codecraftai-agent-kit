"""
    Unit tests for the ccai.agentkit.structuredlogentry module.

    Tests the StructuredLogEntry class: construction, read-only properties,
    immutability, metadata copy behavior, serialization (as_dict, to_json,
    from_dict, from_json), JSON round-trip, __repr__, and __str__.
"""

import json

from datetime import datetime

from ccai.agentkit.structuredlogentry import StructuredLogEntry


def test_construction_stores_all_fields():
    """
        Verify that all constructor arguments are stored and accessible
        via properties.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="Agent started",
        logger_name="ccai.agentkit.observability",
        correlation_id="corr-001",
        agent_id="agent-001",
        metadata={"key": "value"}
    )

    assert entry.timestamp == ts, "timestamp should match the provided value"
    assert entry.level == "info", "level should match the provided value"
    assert entry.message == "Agent started", "message should match the provided value"
    assert entry.logger_name == "ccai.agentkit.observability", "logger_name should match"
    assert entry.correlation_id == "corr-001", "correlation_id should match"
    assert entry.agent_id == "agent-001", "agent_id should match"
    assert entry.metadata == {"key": "value"}, "metadata should match"
    return


def test_metadata_defaults_to_empty_dict():
    """
        Verify that metadata defaults to an empty dictionary when not provided.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="debug",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-002",
        agent_id="agent-002"
    )

    metadata = entry.metadata
    assert metadata == {}, "metadata should default to empty dict"
    return


def test_metadata_property_returns_copy():
    """
        Verify that the metadata property returns a copy, so mutating
        the returned dict does not affect the entry.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-003",
        agent_id="agent-003",
        metadata={"original": "data"}
    )

    returned_metadata = entry.metadata
    returned_metadata["injected"] = "bad"

    original_metadata = entry.metadata
    has_injected = "injected" in original_metadata
    assert has_injected is False, "Mutating returned metadata should not affect the entry"
    return


def test_constructor_copies_metadata_dict():
    """
        Verify that the constructor copies the metadata dict, so mutating
        the original dict does not affect the entry.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    original_meta = {"key": "value"}
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-004",
        agent_id="agent-004",
        metadata=original_meta
    )

    original_meta["injected"] = "bad"

    entry_metadata = entry.metadata
    has_injected = "injected" in entry_metadata
    assert has_injected is False, "Mutating original dict should not affect the entry"
    return


def test_timestamp_property_is_read_only():
    """
        Verify that the timestamp property cannot be set directly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-005",
        agent_id="agent-005"
    )

    raised = False
    try:
        entry.timestamp = datetime(2026, 1, 1)
    except AttributeError:
        raised = True

    assert raised is True, "timestamp should be read-only"
    return


def test_level_property_is_read_only():
    """
        Verify that the level property cannot be set directly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-006",
        agent_id="agent-006"
    )

    raised = False
    try:
        entry.level = "error"
    except AttributeError:
        raised = True

    assert raised is True, "level should be read-only"
    return


def test_message_property_is_read_only():
    """
        Verify that the message property cannot be set directly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-007",
        agent_id="agent-007"
    )

    raised = False
    try:
        entry.message = "new message"
    except AttributeError:
        raised = True

    assert raised is True, "message should be read-only"
    return


def test_as_dict_returns_all_fields():
    """
        Verify that as_dict returns a dictionary with all entry fields
        and the timestamp serialized as ISO format.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="warning",
        message="Low memory",
        logger_name="test.logger",
        correlation_id="corr-008",
        agent_id="agent-008",
        metadata={"mem_pct": 95}
    )

    result = entry.as_dict()

    assert result["timestamp"] == "2025-01-15T10:30:00", "timestamp should be ISO format"
    assert result["level"] == "warning", "level should match"
    assert result["message"] == "Low memory", "message should match"
    assert result["logger_name"] == "test.logger", "logger_name should match"
    assert result["correlation_id"] == "corr-008", "correlation_id should match"
    assert result["agent_id"] == "agent-008", "agent_id should match"
    assert result["metadata"] == {"mem_pct": 95}, "metadata should match"
    return


def test_as_dict_with_empty_metadata():
    """
        Verify that as_dict includes an empty metadata dict when no
        metadata was provided.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-009",
        agent_id="agent-009"
    )

    result = entry.as_dict()
    assert result["metadata"] == {}, "metadata should be empty dict"
    return


def test_to_json_returns_valid_json():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="error",
        message="Something failed",
        logger_name="test.logger",
        correlation_id="corr-010",
        agent_id="agent-010"
    )

    json_str = entry.to_json()
    parsed = json.loads(json_str)

    assert parsed["level"] == "error", "Parsed JSON should contain the level"
    assert parsed["message"] == "Something failed", "Parsed JSON should contain the message"
    return


def test_from_dict_reconstructs_entry():
    """
        Verify that from_dict reconstructs a StructuredLogEntry from a dictionary.
    """
    data = {
        "timestamp": "2025-01-15T10:30:00",
        "level": "info",
        "message": "Reconstructed",
        "logger_name": "test.logger",
        "correlation_id": "corr-011",
        "agent_id": "agent-011",
        "metadata": {"source": "test"}
    }

    entry = StructuredLogEntry.from_dict(data)

    assert entry.timestamp == datetime(2025, 1, 15, 10, 30, 0), "timestamp should be parsed"
    assert entry.level == "info", "level should match"
    assert entry.message == "Reconstructed", "message should match"
    assert entry.logger_name == "test.logger", "logger_name should match"
    assert entry.correlation_id == "corr-011", "correlation_id should match"
    assert entry.agent_id == "agent-011", "agent_id should match"
    assert entry.metadata == {"source": "test"}, "metadata should match"
    return


def test_from_json_reconstructs_entry():
    """
        Verify that from_json reconstructs a StructuredLogEntry from a JSON string.
    """
    data = {
        "timestamp": "2025-01-15T10:30:00",
        "level": "critical",
        "message": "System down",
        "logger_name": "test.logger",
        "correlation_id": "corr-012",
        "agent_id": "agent-012",
        "metadata": {}
    }
    json_str = json.dumps(data)

    entry = StructuredLogEntry.from_json(json_str)

    assert entry.level == "critical", "level should match"
    assert entry.message == "System down", "message should match"
    return


def test_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent entry.
    """
    ts = datetime(2025, 6, 20, 14, 0, 0)
    original = StructuredLogEntry(
        timestamp=ts,
        level="debug",
        message="Round trip test",
        logger_name="test.logger",
        correlation_id="corr-013",
        agent_id="agent-013",
        metadata={"round": "trip"}
    )

    json_str = original.to_json()
    restored = StructuredLogEntry.from_json(json_str)

    assert restored.timestamp == original.timestamp, "timestamp should survive round-trip"
    assert restored.level == original.level, "level should survive round-trip"
    assert restored.message == original.message, "message should survive round-trip"
    assert restored.logger_name == original.logger_name, "logger_name should survive round-trip"
    assert restored.correlation_id == original.correlation_id, "correlation_id should survive round-trip"
    assert restored.agent_id == original.agent_id, "agent_id should survive round-trip"
    assert restored.metadata == original.metadata, "metadata should survive round-trip"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name StructuredLogEntry.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-014",
        agent_id="agent-014"
    )

    repr_str = repr(entry)
    has_class_name = "StructuredLogEntry" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_level():
    """
        Verify that __repr__ includes the log level.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="warning",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-015",
        agent_id="agent-015"
    )

    repr_str = repr(entry)
    has_level = "warning" in repr_str
    assert has_level is True, "repr should contain the log level"
    return


def test_repr_contains_logger_name():
    """
        Verify that __repr__ includes the logger name.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="my.custom.logger",
        correlation_id="corr-016",
        agent_id="agent-016"
    )

    repr_str = repr(entry)
    has_logger = "my.custom.logger" in repr_str
    assert has_logger is True, "repr should contain the logger name"
    return


def test_repr_contains_correlation_id():
    """
        Verify that __repr__ includes the correlation identifier.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-unique-017",
        agent_id="agent-017"
    )

    repr_str = repr(entry)
    has_corr_id = "corr-unique-017" in repr_str
    assert has_corr_id is True, "repr should contain the correlation_id"
    return


def test_str_contains_timestamp():
    """
        Verify that __str__ includes the timestamp.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-018",
        agent_id="agent-018"
    )

    str_val = str(entry)
    has_timestamp = "2025-01-15T10:30:00" in str_val
    assert has_timestamp is True, "str should contain the timestamp"
    return


def test_str_contains_level():
    """
        Verify that __str__ includes the log level.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="error",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-019",
        agent_id="agent-019"
    )

    str_val = str(entry)
    has_level = "error" in str_val
    assert has_level is True, "str should contain the log level"
    return


def test_str_contains_message():
    """
        Verify that __str__ includes the message.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="Agent initialized successfully",
        logger_name="test.logger",
        correlation_id="corr-020",
        agent_id="agent-020"
    )

    str_val = str(entry)
    has_message = "Agent initialized successfully" in str_val
    assert has_message is True, "str should contain the message"
    return


def test_str_contains_correlation_id():
    """
        Verify that __str__ includes the correlation identifier.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    entry = StructuredLogEntry(
        timestamp=ts,
        level="info",
        message="test",
        logger_name="test.logger",
        correlation_id="corr-unique-021",
        agent_id="agent-021"
    )

    str_val = str(entry)
    has_corr_id = "corr-unique-021" in str_val
    assert has_corr_id is True, "str should contain the correlation_id"
    return
