"""
    Unit tests for the automojo.agentkit.configurationchangeevent module.

    Tests the ConfigurationChangeEvent immutable data type including constructor,
    read-only properties, serialization, deserialization, and string representations.

    Requirements: 8.1, 8.2, 8.3, 8.4
"""

import json

from datetime import datetime

from automojo.agentkit.configurationchangeevent import ConfigurationChangeEvent
from automojo.agentkit.configurationlayersource import ConfigurationLayerSource


# ---- Constructor Tests ----


def test_constructor_stores_field_path():
    """
        Verify that the constructor stores the field_path field correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = ConfigurationChangeEvent(
        field_path="app.debug",
        previous_value=False,
        new_value=True,
        source=ConfigurationLayerSource.RUNTIME,
        timestamp=ts,
    )
    stored_path = event.field_path
    assert stored_path == "app.debug", "constructor should store the field_path"
    return


def test_constructor_stores_previous_value():
    """
        Verify that the constructor stores the previous_value field correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = ConfigurationChangeEvent(
        field_path="app.timeout",
        previous_value=30,
        new_value=60,
        source=ConfigurationLayerSource.FILE,
        timestamp=ts,
    )
    stored_prev = event.previous_value
    assert stored_prev == 30, "constructor should store the previous_value"
    return


def test_constructor_stores_new_value():
    """
        Verify that the constructor stores the new_value field correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = ConfigurationChangeEvent(
        field_path="app.timeout",
        previous_value=30,
        new_value=60,
        source=ConfigurationLayerSource.FILE,
        timestamp=ts,
    )
    stored_new = event.new_value
    assert stored_new == 60, "constructor should store the new_value"
    return


def test_constructor_stores_source():
    """
        Verify that the constructor stores the source field correctly.
    """
    ts = datetime(2025, 1, 15, 10, 30, 0)
    event = ConfigurationChangeEvent(
        field_path="db.host",
        previous_value="localhost",
        new_value="prod-db",
        source=ConfigurationLayerSource.ENVIRONMENT,
        timestamp=ts,
    )
    stored_source = event.source
    assert stored_source is ConfigurationLayerSource.ENVIRONMENT, "constructor should store the source"
    return


def test_constructor_stores_timestamp():
    """
        Verify that the constructor stores the timestamp field correctly.
    """
    ts = datetime(2025, 6, 1, 12, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="app.name",
        previous_value="old",
        new_value="new",
        source=ConfigurationLayerSource.RUNTIME,
        timestamp=ts,
    )
    stored_ts = event.timestamp
    assert stored_ts == ts, "constructor should store the timestamp"
    return


def test_constructor_stores_none_values():
    """
        Verify that the constructor stores None for previous_value and new_value.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="app.optional",
        previous_value=None,
        new_value=None,
        source=ConfigurationLayerSource.DEFAULTS,
        timestamp=ts,
    )
    stored_prev = event.previous_value
    stored_new = event.new_value
    assert stored_prev is None, "constructor should store None previous_value"
    assert stored_new is None, "constructor should store None new_value"
    return


# ---- Read-Only Property Tests ----


def test_field_path_property_returns_expected_value():
    """
        Verify that the field_path property returns the expected value.
    """
    ts = datetime(2025, 3, 10, 8, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="server.port",
        previous_value=8080,
        new_value=9090,
        source=ConfigurationLayerSource.OVERRIDE,
        timestamp=ts,
    )
    path_value = event.field_path
    assert path_value == "server.port", "field_path property should return the expected value"
    return


def test_source_property_returns_expected_value():
    """
        Verify that the source property returns the expected ConfigurationLayerSource.
    """
    ts = datetime(2025, 3, 10, 8, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="cache.ttl",
        previous_value=300,
        new_value=600,
        source=ConfigurationLayerSource.FILE,
        timestamp=ts,
    )
    source_value = event.source
    assert source_value is ConfigurationLayerSource.FILE, \
        "source property should return the expected ConfigurationLayerSource"
    return


# ---- as_dict Tests ----


def test_as_dict_returns_correct_dictionary():
    """
        Verify that as_dict returns a dictionary with all expected fields.
    """
    ts = datetime(2025, 7, 4, 14, 30, 0)
    event = ConfigurationChangeEvent(
        field_path="app.debug",
        previous_value=False,
        new_value=True,
        source=ConfigurationLayerSource.RUNTIME,
        timestamp=ts,
    )
    result = event.as_dict()

    result_path = result["field_path"]
    result_prev = result["previous_value"]
    result_new = result["new_value"]
    result_source = result["source"]
    result_ts = result["timestamp"]

    assert result_path == "app.debug", "as_dict field_path should match"
    assert result_prev is False, "as_dict previous_value should match"
    assert result_new is True, "as_dict new_value should match"
    assert result_source == "RUNTIME", "as_dict source should be the string value of the enum"
    assert result_ts == ts.isoformat(), "as_dict timestamp should be ISO format string"
    return


# ---- to_json Tests ----


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    ts = datetime(2025, 2, 20, 16, 45, 0)
    event = ConfigurationChangeEvent(
        field_path="db.port",
        previous_value=5432,
        new_value=5433,
        source=ConfigurationLayerSource.FILE,
        timestamp=ts,
    )
    json_str = event.to_json()
    parsed = json.loads(json_str)

    parsed_path = parsed["field_path"]
    parsed_prev = parsed["previous_value"]
    parsed_new = parsed["new_value"]
    parsed_source = parsed["source"]

    assert parsed_path == "db.port", "to_json field_path should match after parsing"
    assert parsed_prev == 5432, "to_json previous_value should match after parsing"
    assert parsed_new == 5433, "to_json new_value should match after parsing"
    assert parsed_source == "FILE", "to_json source should be the string value"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs a ConfigurationChangeEvent with equivalent fields.
    """
    data = {
        "field_path": "app.name",
        "previous_value": "old-name",
        "new_value": "new-name",
        "source": "ENVIRONMENT",
        "timestamp": "2025-05-15T09:00:00",
    }
    event = ConfigurationChangeEvent.from_dict(data)

    event_path = event.field_path
    event_prev = event.previous_value
    event_new = event.new_value
    event_source = event.source
    event_ts = event.timestamp

    assert event_path == "app.name", "from_dict should reconstruct field_path"
    assert event_prev == "old-name", "from_dict should reconstruct previous_value"
    assert event_new == "new-name", "from_dict should reconstruct new_value"
    assert event_source is ConfigurationLayerSource.ENVIRONMENT, "from_dict should reconstruct source"
    assert event_ts == datetime(2025, 5, 15, 9, 0, 0), "from_dict should reconstruct timestamp"
    return


# ---- from_json Tests ----


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs a ConfigurationChangeEvent with equivalent fields.
    """
    json_str = json.dumps({
        "field_path": "cache.enabled",
        "previous_value": True,
        "new_value": False,
        "source": "OVERRIDE",
        "timestamp": "2025-08-01T12:00:00",
    })
    event = ConfigurationChangeEvent.from_json(json_str)

    event_path = event.field_path
    event_prev = event.previous_value
    event_new = event.new_value
    event_source = event.source

    assert event_path == "cache.enabled", "from_json should reconstruct field_path"
    assert event_prev is True, "from_json should reconstruct previous_value"
    assert event_new is False, "from_json should reconstruct new_value"
    assert event_source is ConfigurationLayerSource.OVERRIDE, "from_json should reconstruct source"
    return


# ---- Round-Trip Tests ----


def test_to_json_from_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent object.
    """
    ts = datetime(2025, 4, 10, 11, 22, 33)
    original = ConfigurationChangeEvent(
        field_path="nested.deep.value",
        previous_value="alpha",
        new_value="beta",
        source=ConfigurationLayerSource.RUNTIME,
        timestamp=ts,
    )
    json_str = original.to_json()
    reconstructed = ConfigurationChangeEvent.from_json(json_str)

    assert reconstructed.field_path == original.field_path, "round-trip field_path should match"
    assert reconstructed.previous_value == original.previous_value, "round-trip previous_value should match"
    assert reconstructed.new_value == original.new_value, "round-trip new_value should match"
    assert reconstructed.source is original.source, "round-trip source should match"
    assert reconstructed.timestamp == original.timestamp, "round-trip timestamp should match"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'ConfigurationChangeEvent'.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="a.b",
        previous_value=1,
        new_value=2,
        source=ConfigurationLayerSource.DEFAULTS,
        timestamp=ts,
    )
    repr_str = repr(event)
    has_class_name = "ConfigurationChangeEvent" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_field_path():
    """
        Verify that __repr__ contains the field path.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="my.special.path",
        previous_value=None,
        new_value="value",
        source=ConfigurationLayerSource.FILE,
        timestamp=ts,
    )
    repr_str = repr(event)
    has_path = "my.special.path" in repr_str
    assert has_path is True, "repr should contain the field path"
    return


def test_repr_contains_source():
    """
        Verify that __repr__ contains the source value.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="x",
        previous_value=0,
        new_value=1,
        source=ConfigurationLayerSource.RUNTIME,
        timestamp=ts,
    )
    repr_str = repr(event)
    has_source = "RUNTIME" in repr_str
    assert has_source is True, "repr should contain the source value"
    return


# ---- __str__ Tests ----


def test_str_contains_field_path():
    """
        Verify that __str__ contains the field path.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="str.test.path",
        previous_value="old",
        new_value="new",
        source=ConfigurationLayerSource.ENVIRONMENT,
        timestamp=ts,
    )
    str_val = str(event)
    has_path = "str.test.path" in str_val
    assert has_path is True, "str should contain the field path"
    return


def test_str_contains_source():
    """
        Verify that __str__ contains the source value.
    """
    ts = datetime(2025, 1, 1, 0, 0, 0)
    event = ConfigurationChangeEvent(
        field_path="a",
        previous_value=1,
        new_value=2,
        source=ConfigurationLayerSource.OVERRIDE,
        timestamp=ts,
    )
    str_val = str(event)
    has_source = "OVERRIDE" in str_val
    assert has_source is True, "str should contain the source value"
    return
