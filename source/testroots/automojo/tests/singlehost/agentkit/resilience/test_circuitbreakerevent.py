"""
    Unit tests for the automojo.agentkit.circuitbreakerevent module.

    Tests CircuitBreakerEvent construction, properties, and serialization.
"""

import json

from datetime import datetime

from automojo.agentkit.circuitbreakerevent import CircuitBreakerEvent
from automojo.agentkit.circuitbreakerstate import CircuitBreakerState


def test_event_construction():
    """
        Verify that CircuitBreakerEvent stores all fields correctly.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    event = CircuitBreakerEvent(
        name="cb-payments",
        previous_state=CircuitBreakerState.CLOSED,
        new_state=CircuitBreakerState.OPEN,
        reason="failure threshold reached",
        timestamp=ts
    )
    assert event.name == "cb-payments", "name should match"
    assert event.previous_state is CircuitBreakerState.CLOSED, "previous_state should be CLOSED"
    assert event.new_state is CircuitBreakerState.OPEN, "new_state should be OPEN"
    assert event.reason == "failure threshold reached", "reason should match"
    assert event.timestamp == ts, "timestamp should match"
    return


def test_event_default_timestamp():
    """
        Verify that CircuitBreakerEvent generates a timestamp when not provided.
    """
    event = CircuitBreakerEvent(
        name="cb-test",
        previous_state=CircuitBreakerState.OPEN,
        new_state=CircuitBreakerState.HALF_OPEN,
        reason="timeout elapsed"
    )
    assert event.timestamp is not None, "timestamp should be auto-generated"
    return


def test_event_as_dict():
    """
        Verify that as_dict returns the expected dictionary.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    event = CircuitBreakerEvent(
        name="cb-1", previous_state=CircuitBreakerState.CLOSED,
        new_state=CircuitBreakerState.OPEN, reason="failures", timestamp=ts
    )
    data = event.as_dict()
    assert data["name"] == "cb-1", "name should match"
    assert data["previous_state"] == "CLOSED", "previous_state should be string"
    assert data["new_state"] == "OPEN", "new_state should be string"
    return


def test_event_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    original = CircuitBreakerEvent(
        name="cb-payments",
        previous_state=CircuitBreakerState.CLOSED,
        new_state=CircuitBreakerState.OPEN,
        reason="failure threshold reached",
        timestamp=ts
    )
    json_str = original.to_json()
    restored = CircuitBreakerEvent.from_json(json_str)

    assert restored.name == original.name, "name should match"
    assert restored.previous_state == original.previous_state, "previous_state should match"
    assert restored.new_state == original.new_state, "new_state should match"
    assert restored.reason == original.reason, "reason should match"
    assert restored.timestamp == original.timestamp, "timestamp should match"
    return


def test_event_repr():
    """
        Verify that __repr__ includes class name and key fields.
    """
    event = CircuitBreakerEvent(
        name="cb-1", previous_state=CircuitBreakerState.CLOSED,
        new_state=CircuitBreakerState.OPEN, reason="test"
    )
    repr_str = repr(event)
    assert "CircuitBreakerEvent" in repr_str, "repr should contain class name"
    assert "cb-1" in repr_str, "repr should contain name"
    return


def test_event_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    event = CircuitBreakerEvent(
        name="cb-1", previous_state=CircuitBreakerState.CLOSED,
        new_state=CircuitBreakerState.OPEN, reason="threshold"
    )
    str_val = str(event)
    assert "cb-1" in str_val, "str should contain name"
    assert "CLOSED" in str_val, "str should contain previous state"
    assert "OPEN" in str_val, "str should contain new state"
    return
