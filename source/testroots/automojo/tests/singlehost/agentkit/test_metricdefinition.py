"""
    Unit tests for the automojo.agentkit.metricdefinition module.

    Tests the MetricDefinition class: construction, read-only properties,
    serialization (as_dict, to_json, from_dict, from_json), __repr__,
    and __str__.
"""

import json

from automojo.agentkit.metricdefinition import MetricDefinition
from automojo.agentkit.metrictype import MetricType


def test_construction_stores_all_fields() -> None:
    """
        Verify that all constructor arguments are stored correctly.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="count",
        metric_type=MetricType.COUNTER
    )

    assert defn.name == "test.metric", "name should be stored"
    assert defn.description == "A test metric", "description should be stored"
    assert defn.unit == "count", "unit should be stored"
    assert defn.metric_type == MetricType.COUNTER, "metric_type should be stored"
    return


def test_name_property_is_read_only() -> None:
    """
        Verify that the name property cannot be set directly.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="count",
        metric_type=MetricType.COUNTER
    )

    caught = False
    try:
        defn.name = "other"
    except AttributeError:
        caught = True

    assert caught is True, "name property should be read-only"
    return


def test_as_dict_returns_all_fields() -> None:
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="seconds",
        metric_type=MetricType.HISTOGRAM
    )
    result = defn.as_dict()

    assert result["name"] == "test.metric", "as_dict should include name"
    assert result["description"] == "A test metric", "as_dict should include description"
    assert result["unit"] == "seconds", "as_dict should include unit"
    assert result["metric_type"] == "HISTOGRAM", "as_dict should include metric_type as string"
    return


def test_to_json_returns_valid_json() -> None:
    """
        Verify that to_json returns a valid JSON string.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="count",
        metric_type=MetricType.GAUGE
    )
    json_str = defn.to_json()
    data = json.loads(json_str)

    assert data["name"] == "test.metric", "JSON should contain name"
    assert data["metric_type"] == "GAUGE", "JSON should contain metric_type"
    return


def test_from_dict_reconstructs_definition() -> None:
    """
        Verify that from_dict reconstructs a MetricDefinition correctly.
    """
    data = {
        "name": "test.metric",
        "description": "A test metric",
        "unit": "count",
        "metric_type": "COUNTER"
    }
    defn = MetricDefinition.from_dict(data)

    assert defn.name == "test.metric", "from_dict should reconstruct name"
    assert defn.description == "A test metric", "from_dict should reconstruct description"
    assert defn.unit == "count", "from_dict should reconstruct unit"
    assert defn.metric_type == MetricType.COUNTER, "from_dict should reconstruct metric_type"
    return


def test_json_round_trip() -> None:
    """
        Verify that to_json followed by from_json produces an equivalent
        MetricDefinition.
    """
    original = MetricDefinition(
        name="round.trip.metric",
        description="Round trip test",
        unit="tokens",
        metric_type=MetricType.HISTOGRAM
    )
    json_str = original.to_json()
    restored = MetricDefinition.from_json(json_str)

    assert restored.name == original.name, "Round-trip should preserve name"
    assert restored.description == original.description, "Round-trip should preserve description"
    assert restored.unit == original.unit, "Round-trip should preserve unit"
    assert restored.metric_type == original.metric_type, "Round-trip should preserve metric_type"
    return


def test_repr_contains_class_name() -> None:
    """
        Verify that __repr__ includes the class name.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="count",
        metric_type=MetricType.COUNTER
    )
    repr_str = repr(defn)

    assert "MetricDefinition" in repr_str, "__repr__ should include class name"
    return


def test_repr_contains_name_and_type() -> None:
    """
        Verify that __repr__ includes the metric name and type.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="count",
        metric_type=MetricType.COUNTER
    )
    repr_str = repr(defn)

    assert "test.metric" in repr_str, "__repr__ should include metric name"
    assert "COUNTER" in repr_str, "__repr__ should include metric type"
    return


def test_str_contains_name_type_and_unit() -> None:
    """
        Verify that __str__ includes the metric name, type, and unit.
    """
    defn = MetricDefinition(
        name="test.metric",
        description="A test metric",
        unit="seconds",
        metric_type=MetricType.HISTOGRAM
    )
    str_val = str(defn)

    assert "test.metric" in str_val, "__str__ should include metric name"
    assert "HISTOGRAM" in str_val, "__str__ should include metric type"
    assert "seconds" in str_val, "__str__ should include unit"
    return
