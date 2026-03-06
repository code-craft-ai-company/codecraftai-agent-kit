"""
    Unit tests for the automojo.agentkit.traceevent module.

    Tests the TraceEvent class: construction, auto-timestamp,
    immutability, serialization (as_dict, to_json, from_dict,
    from_json), __repr__, and __str__.
"""

import json

from datetime import datetime

from automojo.agentkit.traceevent import TraceEvent


def test_construction_with_all_fields() -> None:
    """
        Verify that a TraceEvent can be constructed with all fields
        explicitly provided.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    attrs = {"key1": "value1", "key2": 42}

    event = TraceEvent(name="test-event", timestamp=ts, attributes=attrs)

    assert event.name == "test-event", "Name should match"
    assert event.timestamp == ts, "Timestamp should match"
    assert event.attributes == attrs, "Attributes should match"
    return


def test_auto_generated_timestamp() -> None:
    """
        Verify that when no timestamp is provided, the current UTC
        time is used automatically.
    """
    before = datetime.utcnow()
    event = TraceEvent(name="auto-ts-event")
    after = datetime.utcnow()

    assert before <= event.timestamp <= after, \
        "Auto-generated timestamp should be between before and after"
    return


def test_explicit_timestamp_preserved() -> None:
    """
        Verify that an explicitly provided timestamp is used as-is.
    """
    ts = datetime(2024, 6, 1, 12, 0, 0)
    event = TraceEvent(name="explicit-ts", timestamp=ts)

    assert event.timestamp == ts, "Explicit timestamp should be preserved"
    return


def test_empty_attributes_default() -> None:
    """
        Verify that attributes default to an empty dict when not provided.
    """
    event = TraceEvent(name="no-attrs")

    assert event.attributes == {}, "Default attributes should be empty dict"
    return


def test_attributes_are_copied() -> None:
    """
        Verify that the attributes property returns a copy, preserving
        immutability of the original event.
    """
    original_attrs = {"key": "value"}
    event = TraceEvent(name="copy-test", attributes=original_attrs)

    returned_attrs = event.attributes
    returned_attrs["new_key"] = "new_value"

    assert "new_key" not in event.attributes, \
        "Modifying returned attributes should not affect the event"
    return


def test_constructor_copies_attributes() -> None:
    """
        Verify that the constructor copies the attributes dict so
        external mutations do not affect the event.
    """
    original_attrs = {"key": "value"}
    event = TraceEvent(name="ctor-copy-test", attributes=original_attrs)

    original_attrs["injected"] = "bad"

    assert "injected" not in event.attributes, \
        "Mutating the original dict should not affect the event"
    return


def test_name_property() -> None:
    """
        Verify that the name property returns the correct value.
    """
    event = TraceEvent(name="my-event")

    assert event.name == "my-event", "Name property should return correct value"
    return


def test_as_dict_returns_dictionary() -> None:
    """
        Verify that as_dict returns a dictionary with all expected fields.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    attrs = {"key1": "value1"}
    event = TraceEvent(name="dict-event", timestamp=ts, attributes=attrs)

    data = event.as_dict()

    assert isinstance(data, dict), "as_dict should return a dict"
    assert data["name"] == "dict-event", "name should match"
    assert data["timestamp"] == ts.isoformat(), "timestamp should be ISO format"
    assert data["attributes"] == {"key1": "value1"}, "attributes should match"
    return


def test_from_dict_reconstructs_event() -> None:
    """
        Verify that from_dict correctly reconstructs a TraceEvent
        from a dictionary.
    """
    data = {
        "name": "restored-event",
        "timestamp": "2025-01-15T10:30:00",
        "attributes": {"key1": "value1"}
    }
    event = TraceEvent.from_dict(data)

    assert event.name == "restored-event", "Reconstructed name should match"
    assert event.timestamp == datetime(2025, 1, 15, 10, 30, 0), \
        "Reconstructed timestamp should match"
    assert event.attributes == {"key1": "value1"}, \
        "Reconstructed attributes should match"
    return


def test_dict_round_trip() -> None:
    """
        Verify that as_dict followed by from_dict produces an equivalent
        TraceEvent.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    original = TraceEvent(
        name="round-trip",
        timestamp=ts,
        attributes={"key": "value"}
    )
    data = original.as_dict()
    restored = TraceEvent.from_dict(data)

    assert restored.name == original.name, "Round-trip name should match"
    assert restored.timestamp == original.timestamp, \
        "Round-trip timestamp should match"
    assert restored.attributes == original.attributes, \
        "Round-trip attributes should match"
    return


def test_to_json_returns_valid_json_string() -> None:
    """
        Verify that to_json returns a valid JSON string.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = TraceEvent(name="json-event", timestamp=ts)

    json_str = event.to_json()
    data = json.loads(json_str)

    assert isinstance(data, dict), "to_json should produce valid JSON"
    assert data["name"] == "json-event", "JSON name should match"
    return


def test_from_json_reconstructs_event() -> None:
    """
        Verify that from_json correctly reconstructs a TraceEvent
        from a JSON string.
    """
    json_str = json.dumps({
        "name": "json-restored",
        "timestamp": "2025-01-15T10:30:00",
        "attributes": {"k": "v"}
    })
    event = TraceEvent.from_json(json_str)

    assert event.name == "json-restored", "Reconstructed name should match"
    assert event.attributes == {"k": "v"}, "Reconstructed attributes should match"
    return


def test_json_round_trip() -> None:
    """
        Verify that to_json followed by from_json produces an equivalent
        TraceEvent.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    original = TraceEvent(
        name="json-round-trip",
        timestamp=ts,
        attributes={"key": "value"}
    )
    json_str = original.to_json()
    restored = TraceEvent.from_json(json_str)

    assert restored.name == original.name, "Round-trip name should match"
    assert restored.timestamp == original.timestamp, \
        "Round-trip timestamp should match"
    assert restored.attributes == original.attributes, \
        "Round-trip attributes should match"
    return


def test_repr_contains_name() -> None:
    """
        Verify that __repr__ includes the event name.
    """
    event = TraceEvent(name="repr-event")
    repr_str = repr(event)

    assert "repr-event" in repr_str, "__repr__ should include name"
    return


def test_repr_contains_timestamp() -> None:
    """
        Verify that __repr__ includes the timestamp.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = TraceEvent(name="repr-ts", timestamp=ts)
    repr_str = repr(event)

    assert ts.isoformat() in repr_str, "__repr__ should include timestamp"
    return


def test_repr_contains_class_name() -> None:
    """
        Verify that __repr__ includes the class name 'TraceEvent'.
    """
    event = TraceEvent(name="repr-class")
    repr_str = repr(event)

    assert "TraceEvent" in repr_str, "__repr__ should include class name"
    return


def test_str_contains_name() -> None:
    """
        Verify that __str__ includes the event name.
    """
    event = TraceEvent(name="str-event")
    str_val = str(event)

    assert "str-event" in str_val, "__str__ should include name"
    return


def test_str_contains_timestamp() -> None:
    """
        Verify that __str__ includes the timestamp.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = TraceEvent(name="str-ts", timestamp=ts)
    str_val = str(event)

    assert ts.isoformat() in str_val, "__str__ should include timestamp"
    return
