"""
    Unit tests for the automojo.agentkit.degradationchangeevent module.
"""

from datetime import datetime

from automojo.agentkit.degradationchangeevent import DegradationChangeEvent
from automojo.agentkit.degradationlevel import DegradationLevel


def test_event_construction():
    """
        Verify that DegradationChangeEvent stores all fields correctly.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    event = DegradationChangeEvent(
        dependency_name="db",
        previous_level=DegradationLevel.NORMAL,
        new_level=DegradationLevel.DEGRADED,
        reason="connection lost",
        timestamp=ts
    )
    assert event.dependency_name == "db", "dependency_name should match"
    assert event.previous_level is DegradationLevel.NORMAL, "previous_level should match"
    assert event.new_level is DegradationLevel.DEGRADED, "new_level should match"
    assert event.reason == "connection lost", "reason should match"
    assert event.timestamp == ts, "timestamp should match"
    return


def test_event_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    ts = datetime(2026, 3, 1, 12, 0, 0)
    original = DegradationChangeEvent(
        dependency_name="cache",
        previous_level=DegradationLevel.DEGRADED,
        new_level=DegradationLevel.CRITICAL,
        reason="total failure",
        timestamp=ts
    )
    json_str = original.to_json()
    restored = DegradationChangeEvent.from_json(json_str)

    assert restored.dependency_name == original.dependency_name, "dependency_name should match"
    assert restored.previous_level == original.previous_level, "previous_level should match"
    assert restored.new_level == original.new_level, "new_level should match"
    assert restored.reason == original.reason, "reason should match"
    assert restored.timestamp == original.timestamp, "timestamp should match"
    return


def test_event_repr():
    """
        Verify that __repr__ includes key fields.
    """
    event = DegradationChangeEvent(
        "db", DegradationLevel.NORMAL, DegradationLevel.DEGRADED, "test"
    )
    repr_str = repr(event)
    assert "DegradationChangeEvent" in repr_str, "repr should contain class name"
    assert "db" in repr_str, "repr should contain dependency name"
    return
