"""
    Unit tests for the ccai.agentkit.metricmeasurement module.

    Tests the MetricMeasurement class: construction, auto-timestamp,
    read-only properties, serialization (as_dict, to_json, from_dict,
    from_json), __repr__, and __str__.
"""

import json

from datetime import datetime

from ccai.agentkit.metricmeasurement import MetricMeasurement


def test_construction_stores_all_fields() -> None:
    """
        Verify that all constructor arguments are stored correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    labels = {"agent_id": "agent-1", "tool": "search"}

    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=42.0,
        timestamp=ts,
        labels=labels
    )

    assert measurement.metric_name == "test.counter", "metric_name should be stored"
    assert measurement.value == 42.0, "value should be stored"
    assert measurement.timestamp == ts, "timestamp should be stored"
    assert measurement.labels == labels, "labels should be stored"
    return


def test_auto_timestamp_when_not_provided() -> None:
    """
        Verify that a timestamp is auto-generated when not provided.
    """
    before = datetime.utcnow()
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=1.0
    )
    after = datetime.utcnow()

    assert measurement.timestamp >= before, \
        "Auto-generated timestamp should be >= time before construction"
    assert measurement.timestamp <= after, \
        "Auto-generated timestamp should be <= time after construction"
    return


def test_labels_default_to_empty_dict() -> None:
    """
        Verify that labels default to an empty dictionary when not provided.
    """
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=1.0,
        timestamp=datetime(2025, 1, 15, 10, 30, 0)
    )

    assert measurement.labels == {}, "labels should default to empty dict"
    return


def test_metric_name_property_is_read_only() -> None:
    """
        Verify that the metric_name property cannot be set directly.
    """
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=1.0,
        timestamp=datetime(2025, 1, 15, 10, 30, 0)
    )

    caught = False
    try:
        measurement.metric_name = "other"
    except AttributeError:
        caught = True

    assert caught is True, "metric_name property should be read-only"
    return


def test_labels_returns_copy() -> None:
    """
        Verify that the labels property returns a copy, not the internal dict.
    """
    original_labels = {"key": "value"}
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=1.0,
        timestamp=datetime(2025, 1, 15, 10, 30, 0),
        labels=original_labels
    )

    returned_labels = measurement.labels
    returned_labels["new_key"] = "new_value"

    assert "new_key" not in measurement.labels, \
        "Modifying returned labels should not affect internal state"
    return


def test_as_dict_returns_all_fields() -> None:
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=42.5,
        timestamp=ts,
        labels={"env": "prod"}
    )
    result = measurement.as_dict()

    assert result["metric_name"] == "test.counter", "as_dict should include metric_name"
    assert result["value"] == 42.5, "as_dict should include value"
    assert result["timestamp"] == ts.isoformat(), "as_dict should include timestamp as ISO string"
    assert result["labels"] == {"env": "prod"}, "as_dict should include labels"
    return


def test_to_json_returns_valid_json() -> None:
    """
        Verify that to_json returns a valid JSON string.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=10.0,
        timestamp=ts
    )
    json_str = measurement.to_json()
    data = json.loads(json_str)

    assert data["metric_name"] == "test.counter", "JSON should contain metric_name"
    assert data["value"] == 10.0, "JSON should contain value"
    return


def test_from_dict_reconstructs_measurement() -> None:
    """
        Verify that from_dict reconstructs a MetricMeasurement correctly.
    """
    data = {
        "metric_name": "test.gauge",
        "value": 99.9,
        "timestamp": "2025-01-15T10:30:00",
        "labels": {"region": "us-east"}
    }
    measurement = MetricMeasurement.from_dict(data)

    assert measurement.metric_name == "test.gauge", "from_dict should reconstruct metric_name"
    assert measurement.value == 99.9, "from_dict should reconstruct value"
    assert measurement.timestamp == datetime(2025, 1, 15, 10, 30, 0), \
        "from_dict should reconstruct timestamp"
    assert measurement.labels == {"region": "us-east"}, "from_dict should reconstruct labels"
    return


def test_json_round_trip() -> None:
    """
        Verify that to_json followed by from_json produces an equivalent
        MetricMeasurement.
    """
    ts = datetime(2025, 6, 1, 12, 0, 0)
    original = MetricMeasurement(
        metric_name="round.trip",
        value=3.14,
        timestamp=ts,
        labels={"key": "val"}
    )
    json_str = original.to_json()
    restored = MetricMeasurement.from_json(json_str)

    assert restored.metric_name == original.metric_name, "Round-trip should preserve metric_name"
    assert restored.value == original.value, "Round-trip should preserve value"
    assert restored.timestamp == original.timestamp, "Round-trip should preserve timestamp"
    assert restored.labels == original.labels, "Round-trip should preserve labels"
    return


def test_repr_contains_class_name_and_metric_name() -> None:
    """
        Verify that __repr__ includes the class name and metric name.
    """
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=5.0,
        timestamp=datetime(2025, 1, 15, 10, 30, 0)
    )
    repr_str = repr(measurement)

    assert "MetricMeasurement" in repr_str, "__repr__ should include class name"
    assert "test.counter" in repr_str, "__repr__ should include metric name"
    return


def test_str_contains_metric_name_and_value() -> None:
    """
        Verify that __str__ includes the metric name and value.
    """
    measurement = MetricMeasurement(
        metric_name="test.counter",
        value=5.0,
        timestamp=datetime(2025, 1, 15, 10, 30, 0)
    )
    str_val = str(measurement)

    assert "test.counter" in str_val, "__str__ should include metric name"
    assert "5.0" in str_val, "__str__ should include value"
    return
