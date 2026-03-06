"""
    Unit tests for the automojo.agentkit.featureflag module.

    Tests the FeatureFlag immutable data type including constructor,
    read-only properties, serialization, deserialization, and string
    representations.
"""

import json

from automojo.agentkit.featureflag import FeatureFlag


# ---- Constructor Tests ----


def test_constructor_stores_name():
    """
        Verify that the constructor stores the name field correctly.
    """
    flag = FeatureFlag(name="enable-logging", default_value=True)
    stored_name = flag.name
    assert stored_name == "enable-logging", "constructor should store the name field"
    return


def test_constructor_stores_default_value():
    """
        Verify that the constructor stores the default_value field correctly.
    """
    flag = FeatureFlag(name="debug-mode", default_value=True)
    stored_value = flag.default_value
    assert stored_value is True, "constructor should store the default_value field"
    return


def test_constructor_default_value_defaults_to_false():
    """
        Verify that default_value defaults to False when not provided.
    """
    flag = FeatureFlag(name="new-feature")
    stored_value = flag.default_value
    assert stored_value is False, "default_value should default to False"
    return


def test_constructor_stores_description():
    """
        Verify that the constructor stores the description field correctly.
    """
    flag = FeatureFlag(name="beta", description="Beta feature toggle")
    stored_desc = flag.description
    assert stored_desc == "Beta feature toggle", "constructor should store the description"
    return


def test_constructor_description_defaults_to_none():
    """
        Verify that description defaults to None when not provided.
    """
    flag = FeatureFlag(name="simple")
    stored_desc = flag.description
    assert stored_desc is None, "description should default to None"
    return


def test_constructor_stores_metadata():
    """
        Verify that the constructor stores the metadata dictionary correctly.
    """
    meta = {"team": "platform", "priority": "high"}
    flag = FeatureFlag(name="with-meta", metadata=meta)
    stored_meta = flag.metadata
    assert stored_meta == {"team": "platform", "priority": "high"}, \
        "constructor should store the metadata dictionary"
    return


def test_constructor_metadata_defaults_to_empty_dict():
    """
        Verify that metadata defaults to an empty dict when not provided.
    """
    flag = FeatureFlag(name="no-meta")
    stored_meta = flag.metadata
    assert stored_meta == {}, "metadata should default to an empty dict"
    return


# ---- Read-Only Property Tests ----


def test_metadata_returns_defensive_copy():
    """
        Verify that the metadata property returns a defensive copy.
    """
    original_meta = {"key": "original"}
    flag = FeatureFlag(name="copy-test", metadata=original_meta)
    first_copy = flag.metadata
    first_copy["key"] = "modified"
    first_copy["injected"] = "value"

    second_copy = flag.metadata
    key_value = second_copy.get("key")
    has_injected = "injected" in second_copy
    assert key_value == "original", "metadata should return a defensive copy"
    assert has_injected is False, "metadata should not contain injected keys"
    return


# ---- as_dict Tests ----


def test_as_dict_returns_correct_dictionary():
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    flag = FeatureFlag(
        name="test-flag",
        default_value=True,
        description="A test flag",
        metadata={"env": "prod"}
    )
    result = flag.as_dict()

    assert result["name"] == "test-flag", "as_dict name should match"
    assert result["default_value"] is True, "as_dict default_value should match"
    assert result["description"] == "A test flag", "as_dict description should match"
    assert result["metadata"] == {"env": "prod"}, "as_dict metadata should match"
    return


# ---- to_json Tests ----


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    flag = FeatureFlag(
        name="json-flag",
        default_value=False,
        description="JSON test",
        metadata={"version": "1"}
    )
    json_str = flag.to_json()
    parsed = json.loads(json_str)

    assert parsed["name"] == "json-flag", "to_json name should match"
    assert parsed["default_value"] is False, "to_json default_value should match"
    assert parsed["description"] == "JSON test", "to_json description should match"
    assert parsed["metadata"] == {"version": "1"}, "to_json metadata should match"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs a FeatureFlag with equivalent fields.
    """
    data = {
        "name": "reconstructed",
        "default_value": True,
        "description": "Rebuilt flag",
        "metadata": {"source": "test"}
    }
    flag = FeatureFlag.from_dict(data)

    assert flag.name == "reconstructed", "from_dict should reconstruct the name"
    assert flag.default_value is True, "from_dict should reconstruct the default_value"
    assert flag.description == "Rebuilt flag", "from_dict should reconstruct the description"
    assert flag.metadata == {"source": "test"}, "from_dict should reconstruct the metadata"
    return


# ---- from_json Tests ----


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs a FeatureFlag with equivalent fields.
    """
    json_str = json.dumps({
        "name": "json-rebuilt",
        "default_value": False,
        "description": "From JSON",
        "metadata": {}
    })
    flag = FeatureFlag.from_json(json_str)

    assert flag.name == "json-rebuilt", "from_json should reconstruct the name"
    assert flag.default_value is False, "from_json should reconstruct the default_value"
    assert flag.description == "From JSON", "from_json should reconstruct the description"
    assert flag.metadata == {}, "from_json should reconstruct the metadata"
    return


# ---- Round-Trip Tests ----


def test_as_dict_from_dict_round_trip():
    """
        Verify that as_dict followed by from_dict produces an equivalent object.
    """
    original = FeatureFlag(
        name="round-trip",
        default_value=True,
        description="Round trip test",
        metadata={"key": "value"}
    )
    data = original.as_dict()
    reconstructed = FeatureFlag.from_dict(data)

    assert reconstructed.name == original.name, "round-trip name should match"
    assert reconstructed.default_value == original.default_value, "round-trip default_value should match"
    assert reconstructed.description == original.description, "round-trip description should match"
    assert reconstructed.metadata == original.metadata, "round-trip metadata should match"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'FeatureFlag'.
    """
    flag = FeatureFlag(name="repr-test")
    repr_str = repr(flag)
    has_class_name = "FeatureFlag" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_flag_name():
    """
        Verify that __repr__ contains the flag name.
    """
    flag = FeatureFlag(name="my-flag")
    repr_str = repr(flag)
    has_flag_name = "my-flag" in repr_str
    assert has_flag_name is True, "repr should contain the flag name"
    return


def test_repr_contains_default_value():
    """
        Verify that __repr__ contains the default value.
    """
    flag = FeatureFlag(name="default-repr", default_value=True)
    repr_str = repr(flag)
    has_default = "True" in repr_str
    assert has_default is True, "repr should contain the default value"
    return


# ---- __str__ Tests ----


def test_str_contains_flag_name():
    """
        Verify that __str__ contains the flag name.
    """
    flag = FeatureFlag(name="str-flag", default_value=False, description="Test")
    str_val = str(flag)
    has_flag_name = "str-flag" in str_val
    assert has_flag_name is True, "str should contain the flag name"
    return


def test_str_contains_default_value():
    """
        Verify that __str__ contains the default value.
    """
    flag = FeatureFlag(name="str-default", default_value=True)
    str_val = str(flag)
    has_default = "True" in str_val
    assert has_default is True, "str should contain the default value"
    return


def test_str_contains_description():
    """
        Verify that __str__ contains the description.
    """
    flag = FeatureFlag(name="str-desc", description="My description")
    str_val = str(flag)
    has_desc = "My description" in str_val
    assert has_desc is True, "str should contain the description"
    return
