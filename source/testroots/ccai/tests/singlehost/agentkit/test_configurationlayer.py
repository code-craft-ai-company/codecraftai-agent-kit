"""
    Unit tests for the ccai.agentkit.configurationlayer module.

    Tests the ConfigurationLayer immutable data type including constructor,
    read-only properties, serialization, deserialization, and string representations.
"""

import json

from ccai.agentkit.configurationlayer import ConfigurationLayer
from ccai.agentkit.configurationlayersource import ConfigurationLayerSource


# ---- Constructor Tests ----


def test_constructor_stores_name():
    """
        Verify that the constructor stores the name field correctly.
    """
    layer = ConfigurationLayer(
        name="defaults",
        priority=0,
        source=ConfigurationLayerSource.DEFAULTS,
        configuration={"key": "value"}
    )
    stored_name = layer.name
    assert stored_name == "defaults", "constructor should store the name field"
    return


def test_constructor_stores_priority():
    """
        Verify that the constructor stores the priority field correctly.
    """
    layer = ConfigurationLayer(
        name="runtime",
        priority=100,
        source=ConfigurationLayerSource.RUNTIME,
        configuration={}
    )
    stored_priority = layer.priority
    assert stored_priority == 100, "constructor should store the priority field"
    return


def test_constructor_stores_source():
    """
        Verify that the constructor stores the source field correctly.
    """
    layer = ConfigurationLayer(
        name="env-layer",
        priority=50,
        source=ConfigurationLayerSource.ENVIRONMENT,
        configuration={}
    )
    stored_source = layer.source
    assert stored_source is ConfigurationLayerSource.ENVIRONMENT, "constructor should store the source field"
    return



def test_constructor_stores_configuration():
    """
        Verify that the constructor stores the configuration dictionary correctly.
    """
    config = {"database": {"host": "localhost", "port": 5432}}
    layer = ConfigurationLayer(
        name="file-layer",
        priority=10,
        source=ConfigurationLayerSource.FILE,
        configuration=config
    )
    stored_config = layer.configuration
    assert stored_config == {"database": {"host": "localhost", "port": 5432}}, \
        "constructor should store the configuration dictionary"
    return


def test_constructor_handles_none_configuration_as_empty_dict():
    """
        Verify that passing None for configuration results in an empty dictionary.
    """
    layer = ConfigurationLayer(
        name="empty-layer",
        priority=0,
        source=ConfigurationLayerSource.DEFAULTS,
        configuration=None
    )
    stored_config = layer.configuration
    assert stored_config == {}, "None configuration should be stored as an empty dict"
    return


# ---- Read-Only Property Tests ----


def test_name_property_returns_expected_value():
    """
        Verify that the name property returns the expected value.
    """
    layer = ConfigurationLayer(
        name="test-layer",
        priority=5,
        source=ConfigurationLayerSource.FILE,
        configuration={"a": 1}
    )
    name_value = layer.name
    assert name_value == "test-layer", "name property should return the expected value"
    return


def test_priority_property_returns_expected_value():
    """
        Verify that the priority property returns the expected value.
    """
    layer = ConfigurationLayer(
        name="priority-layer",
        priority=42,
        source=ConfigurationLayerSource.OVERRIDE,
        configuration={}
    )
    priority_value = layer.priority
    assert priority_value == 42, "priority property should return the expected value"
    return


def test_source_property_returns_expected_value():
    """
        Verify that the source property returns the expected ConfigurationLayerSource.
    """
    layer = ConfigurationLayer(
        name="source-layer",
        priority=20,
        source=ConfigurationLayerSource.RUNTIME,
        configuration={}
    )
    source_value = layer.source
    assert source_value is ConfigurationLayerSource.RUNTIME, \
        "source property should return the expected ConfigurationLayerSource"
    return


def test_configuration_property_returns_defensive_copy():
    """
        Verify that the configuration property returns a defensive copy,
        so modifications to the returned dict do not affect the layer.
    """
    original_config = {"key": "original"}
    layer = ConfigurationLayer(
        name="copy-layer",
        priority=0,
        source=ConfigurationLayerSource.DEFAULTS,
        configuration=original_config
    )
    first_copy = layer.configuration
    first_copy["key"] = "modified"
    first_copy["new_key"] = "injected"

    second_copy = layer.configuration
    key_value = second_copy.get("key")
    has_new_key = "new_key" in second_copy
    assert key_value == "original", "configuration should return a defensive copy, original value preserved"
    assert has_new_key is False, "configuration should return a defensive copy, injected key not present"
    return


# ---- as_dict Tests ----


def test_as_dict_returns_correct_dictionary():
    """
        Verify that as_dict returns a dictionary with all fields,
        including source as its string value.
    """
    layer = ConfigurationLayer(
        name="dict-layer",
        priority=10,
        source=ConfigurationLayerSource.FILE,
        configuration={"timeout": 30}
    )
    result = layer.as_dict()

    result_name = result["name"]
    result_priority = result["priority"]
    result_source = result["source"]
    result_config = result["configuration"]

    assert result_name == "dict-layer", "as_dict name should match"
    assert result_priority == 10, "as_dict priority should match"
    assert result_source == "FILE", "as_dict source should be the string value of the enum"
    assert result_config == {"timeout": 30}, "as_dict configuration should match"
    return


# ---- to_json Tests ----


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    layer = ConfigurationLayer(
        name="json-layer",
        priority=5,
        source=ConfigurationLayerSource.ENVIRONMENT,
        configuration={"debug": True}
    )
    json_str = layer.to_json()
    parsed = json.loads(json_str)

    parsed_name = parsed["name"]
    parsed_priority = parsed["priority"]
    parsed_source = parsed["source"]
    parsed_config = parsed["configuration"]

    assert parsed_name == "json-layer", "to_json name should match after parsing"
    assert parsed_priority == 5, "to_json priority should match after parsing"
    assert parsed_source == "ENVIRONMENT", "to_json source should be the string value"
    assert parsed_config == {"debug": True}, "to_json configuration should match after parsing"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs a ConfigurationLayer with equivalent fields.
    """
    data = {
        "name": "reconstructed-layer",
        "priority": 25,
        "source": "RUNTIME",
        "configuration": {"retries": 3}
    }
    layer = ConfigurationLayer.from_dict(data)

    layer_name = layer.name
    layer_priority = layer.priority
    layer_source = layer.source
    layer_config = layer.configuration

    assert layer_name == "reconstructed-layer", "from_dict should reconstruct the name"
    assert layer_priority == 25, "from_dict should reconstruct the priority"
    assert layer_source is ConfigurationLayerSource.RUNTIME, "from_dict should reconstruct the source"
    assert layer_config == {"retries": 3}, "from_dict should reconstruct the configuration"
    return


# ---- from_json Tests ----


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs a ConfigurationLayer with equivalent fields.
    """
    json_str = json.dumps({
        "name": "json-reconstructed",
        "priority": 50,
        "source": "OVERRIDE",
        "configuration": {"max_connections": 10}
    })
    layer = ConfigurationLayer.from_json(json_str)

    layer_name = layer.name
    layer_priority = layer.priority
    layer_source = layer.source
    layer_config = layer.configuration

    assert layer_name == "json-reconstructed", "from_json should reconstruct the name"
    assert layer_priority == 50, "from_json should reconstruct the priority"
    assert layer_source is ConfigurationLayerSource.OVERRIDE, "from_json should reconstruct the source"
    assert layer_config == {"max_connections": 10}, "from_json should reconstruct the configuration"
    return


# ---- Round-Trip Tests ----


def test_as_dict_from_dict_round_trip():
    """
        Verify that as_dict followed by from_dict produces an equivalent object.
    """
    original = ConfigurationLayer(
        name="round-trip",
        priority=15,
        source=ConfigurationLayerSource.FILE,
        configuration={"nested": {"key": "value"}, "list_val": [1, 2, 3]}
    )
    data = original.as_dict()
    reconstructed = ConfigurationLayer.from_dict(data)

    assert reconstructed.name == original.name, "round-trip name should match"
    assert reconstructed.priority == original.priority, "round-trip priority should match"
    assert reconstructed.source is original.source, "round-trip source should match"
    assert reconstructed.configuration == original.configuration, "round-trip configuration should match"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'ConfigurationLayer'.
    """
    layer = ConfigurationLayer(
        name="repr-layer",
        priority=7,
        source=ConfigurationLayerSource.DEFAULTS,
        configuration={}
    )
    repr_str = repr(layer)
    has_class_name = "ConfigurationLayer" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_layer_name():
    """
        Verify that __repr__ contains the layer name.
    """
    layer = ConfigurationLayer(
        name="my-special-layer",
        priority=7,
        source=ConfigurationLayerSource.DEFAULTS,
        configuration={}
    )
    repr_str = repr(layer)
    has_layer_name = "my-special-layer" in repr_str
    assert has_layer_name is True, "repr should contain the layer name"
    return


def test_repr_contains_priority():
    """
        Verify that __repr__ contains the priority value.
    """
    layer = ConfigurationLayer(
        name="priority-repr",
        priority=99,
        source=ConfigurationLayerSource.RUNTIME,
        configuration={}
    )
    repr_str = repr(layer)
    has_priority = "99" in repr_str
    assert has_priority is True, "repr should contain the priority value"
    return


def test_repr_contains_source():
    """
        Verify that __repr__ contains the source value.
    """
    layer = ConfigurationLayer(
        name="source-repr",
        priority=1,
        source=ConfigurationLayerSource.FILE,
        configuration={}
    )
    repr_str = repr(layer)
    has_source = "FILE" in repr_str
    assert has_source is True, "repr should contain the source value"
    return


# ---- __str__ Tests ----


def test_str_contains_layer_name():
    """
        Verify that __str__ contains the layer name.
    """
    layer = ConfigurationLayer(
        name="str-layer",
        priority=3,
        source=ConfigurationLayerSource.ENVIRONMENT,
        configuration={}
    )
    str_val = str(layer)
    has_layer_name = "str-layer" in str_val
    assert has_layer_name is True, "str should contain the layer name"
    return


def test_str_contains_priority():
    """
        Verify that __str__ contains the priority value.
    """
    layer = ConfigurationLayer(
        name="str-priority",
        priority=77,
        source=ConfigurationLayerSource.OVERRIDE,
        configuration={}
    )
    str_val = str(layer)
    has_priority = "77" in str_val
    assert has_priority is True, "str should contain the priority value"
    return


def test_str_contains_source():
    """
        Verify that __str__ contains the source value.
    """
    layer = ConfigurationLayer(
        name="str-source",
        priority=2,
        source=ConfigurationLayerSource.RUNTIME,
        configuration={}
    )
    str_val = str(layer)
    has_source = "RUNTIME" in str_val
    assert has_source is True, "str should contain the source value"
    return
