"""
    Unit tests for the automojo.agentkit.metricssnapshot module.

    Tests the MetricsSnapshot class: construction, get_metric,
    read-only properties, serialization (as_dict, to_json, from_dict,
    from_json), __repr__, and __str__.
"""

import json

from datetime import datetime

from automojo.agentkit.metricssnapshot import MetricsSnapshot


def test_construction_stores_all_fields() -> None:
    """
        Verify that all constructor arguments are stored correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    metrics = {
        "cpu.usage": {"value": 75.5, "labels": {"host": "server-1"}},
        "mem.usage": {"value": 60.0, "labels": {"host": "server-1"}}
    }

    snapshot = MetricsSnapshot(timestamp=ts, metrics=metrics)

    assert snapshot.timestamp == ts, "timestamp should be stored"
    assert snapshot.metrics == metrics, "metrics should be stored"
    return


def test_metrics_returns_copy() -> None:
    """
        Verify that the metrics property returns a copy, not the
        internal dict.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    metrics = {"cpu.usage": {"value": 75.5}}

    snapshot = MetricsSnapshot(timestamp=ts, metrics=metrics)
    returned = snapshot.metrics
    returned["new.metric"] = {"value": 0.0}

    assert "new.metric" not in snapshot.metrics, \
        "Modifying returned metrics should not affect internal state"
    return


def test_get_metric_returns_value_for_existing_name() -> None:
    """
        Verify that get_metric returns the value for an existing metric.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    metrics = {
        "cpu.usage": {"value": 75.5, "labels": {"host": "server-1"}}
    }

    snapshot = MetricsSnapshot(timestamp=ts, metrics=metrics)
    result = snapshot.get_metric("cpu.usage")

    assert result is not None, "get_metric should return value for existing metric"
    assert result["value"] == 75.5, "get_metric should return correct value"
    return


def test_get_metric_returns_none_for_missing_name() -> None:
    """
        Verify that get_metric returns None for a non-existent metric.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    snapshot = MetricsSnapshot(timestamp=ts, metrics={})
    result = snapshot.get_metric("nonexistent")

    assert result is None, "get_metric should return None for missing metric"
    return


def test_as_dict_returns_all_fields() -> None:
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    metrics = {"cpu.usage": {"value": 75.5}}

    snapshot = MetricsSnapshot(timestamp=ts, metrics=metrics)
    result = snapshot.as_dict()

    assert result["timestamp"] == ts.isoformat(), \
        "as_dict should include timestamp as ISO string"
    assert result["metrics"] == metrics, "as_dict should include metrics"
    return


def test_to_json_returns_valid_json() -> None:
    """
        Verify that to_json returns a valid JSON string.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    metrics = {"cpu.usage": {"value": 75.5}}

    snapshot = MetricsSnapshot(timestamp=ts, metrics=metrics)
    json_str = snapshot.to_json()
    data = json.loads(json_str)

    assert "timestamp" in data, "JSON should contain timestamp"
    assert "metrics" in data, "JSON should contain metrics"
    return


def test_from_dict_reconstructs_snapshot() -> None:
    """
        Verify that from_dict reconstructs a MetricsSnapshot correctly.
    """
    data = {
        "timestamp": "2025-01-15T10:30:00",
        "metrics": {"cpu.usage": {"value": 75.5}}
    }
    snapshot = MetricsSnapshot.from_dict(data)

    assert snapshot.timestamp == datetime(2025, 1, 15, 10, 30, 0), \
        "from_dict should reconstruct timestamp"
    assert snapshot.metrics == {"cpu.usage": {"value": 75.5}}, \
        "from_dict should reconstruct metrics"
    return


def test_json_round_trip() -> None:
    """
        Verify that to_json followed by from_json produces an equivalent
        MetricsSnapshot.
    """
    ts = datetime(2025, 6, 1, 12, 0, 0)
    metrics = {
        "cpu.usage": {"value": 75.5, "labels": {"host": "server-1"}},
        "mem.usage": {"value": 60.0}
    }

    original = MetricsSnapshot(timestamp=ts, metrics=metrics)
    json_str = original.to_json()
    restored = MetricsSnapshot.from_json(json_str)

    assert restored.timestamp == original.timestamp, \
        "Round-trip should preserve timestamp"
    assert restored.metrics == original.metrics, \
        "Round-trip should preserve metrics"
    return


def test_json_round_trip_empty_metrics() -> None:
    """
        Verify that JSON round-trip works with empty metrics dict.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    original = MetricsSnapshot(timestamp=ts, metrics={})
    json_str = original.to_json()
    restored = MetricsSnapshot.from_json(json_str)

    assert restored.timestamp == original.timestamp, \
        "Round-trip should preserve timestamp"
    assert restored.metrics == {}, \
        "Round-trip should preserve empty metrics"
    return


def test_repr_contains_class_name() -> None:
    """
        Verify that __repr__ includes the class name.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    snapshot = MetricsSnapshot(timestamp=ts, metrics={"a": 1})
    repr_str = repr(snapshot)

    assert "MetricsSnapshot" in repr_str, "__repr__ should include class name"
    return


def test_repr_contains_metric_count() -> None:
    """
        Verify that __repr__ includes the count of metrics.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    snapshot = MetricsSnapshot(timestamp=ts, metrics={"a": 1, "b": 2})
    repr_str = repr(snapshot)

    assert "2" in repr_str, "__repr__ should include metric count"
    return


def test_str_contains_timestamp_and_metric_names() -> None:
    """
        Verify that __str__ includes the timestamp and metric names.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    snapshot = MetricsSnapshot(
        timestamp=ts,
        metrics={"cpu.usage": {"value": 75.5}}
    )
    str_val = str(snapshot)

    assert "2025-01-15" in str_val, "__str__ should include timestamp"
    assert "cpu.usage" in str_val, "__str__ should include metric names"
    return
