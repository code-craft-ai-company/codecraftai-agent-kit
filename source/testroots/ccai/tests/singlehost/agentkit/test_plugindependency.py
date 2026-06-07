"""
    Unit tests for the ccai.agentkit.plugindependency module.

    Tests the PluginDependency immutable data type including constructor,
    read-only properties, is_satisfied_by logic, serialization,
    deserialization, and string representations.
"""

import json

from ccai.agentkit.plugindependency import PluginDependency


# ---- Constructor Tests ----


def test_constructor_stores_name():
    """
        Verify that the constructor stores the name field correctly.
    """
    dep = PluginDependency(name="auth-plugin")
    stored_name = dep.name
    assert stored_name == "auth-plugin", "constructor should store the name field"
    return


def test_constructor_stores_version_constraint():
    """
        Verify that the constructor stores the version_constraint field correctly.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    stored_constraint = dep.version_constraint
    assert stored_constraint == "1.0.0", "constructor should store the version_constraint field"
    return


def test_constructor_defaults_version_constraint_to_none():
    """
        Verify that version_constraint defaults to None when not provided.
    """
    dep = PluginDependency(name="logging-plugin")
    stored_constraint = dep.version_constraint
    assert stored_constraint is None, "version_constraint should default to None"
    return


# ---- Read-Only Property Tests ----


def test_name_property_returns_expected_value():
    """
        Verify that the name read-only property returns the expected value.
    """
    dep = PluginDependency(name="metrics-plugin", version_constraint="2.0.0")
    result = dep.name
    assert result == "metrics-plugin", "name property should return 'metrics-plugin'"
    return


def test_version_constraint_property_returns_expected_value():
    """
        Verify that the version_constraint read-only property returns the expected value.
    """
    dep = PluginDependency(name="metrics-plugin", version_constraint="2.0.0")
    result = dep.version_constraint
    assert result == "2.0.0", "version_constraint property should return '2.0.0'"
    return


def test_version_constraint_property_returns_none_when_not_set():
    """
        Verify that the version_constraint property returns None when not provided.
    """
    dep = PluginDependency(name="cache-plugin")
    result = dep.version_constraint
    assert result is None, "version_constraint property should return None when not set"
    return


# ---- is_satisfied_by Tests ----


def test_is_satisfied_by_matching_name_no_version_constraint():
    """
        Verify that is_satisfied_by returns True when the name matches
        and no version constraint is set.
    """
    dep = PluginDependency(name="auth-plugin")
    result = dep.is_satisfied_by("auth-plugin", "3.0.0")
    assert result is True, "is_satisfied_by should return True for matching name with no version constraint"
    return


def test_is_satisfied_by_non_matching_name():
    """
        Verify that is_satisfied_by returns False when the name does not match.
    """
    dep = PluginDependency(name="auth-plugin")
    result = dep.is_satisfied_by("other-plugin", "1.0.0")
    assert result is False, "is_satisfied_by should return False for non-matching name"
    return


def test_is_satisfied_by_matching_name_and_matching_version():
    """
        Verify that is_satisfied_by returns True when the name matches
        and the version matches the constraint.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    result = dep.is_satisfied_by("auth-plugin", "1.0.0")
    assert result is True, "is_satisfied_by should return True for matching name and matching version"
    return


def test_is_satisfied_by_matching_name_but_non_matching_version():
    """
        Verify that is_satisfied_by returns False when the name matches
        but the version does not match the constraint.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    result = dep.is_satisfied_by("auth-plugin", "2.0.0")
    assert result is False, "is_satisfied_by should return False for matching name but non-matching version"
    return


def test_is_satisfied_by_non_matching_name_with_version_constraint():
    """
        Verify that is_satisfied_by returns False when the name does not match,
        even if a version constraint is set.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    result = dep.is_satisfied_by("other-plugin", "1.0.0")
    assert result is False, "is_satisfied_by should return False when name does not match"
    return


# ---- as_dict Tests ----


def test_as_dict_with_version_constraint():
    """
        Verify that as_dict produces a dictionary with name and version_constraint.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    result = dep.as_dict()
    expected = {"name": "auth-plugin", "version_constraint": "1.0.0"}
    assert result == expected, "as_dict should produce correct output with version_constraint"
    return


def test_as_dict_without_version_constraint():
    """
        Verify that as_dict produces a dictionary with version_constraint as None.
    """
    dep = PluginDependency(name="logging-plugin")
    result = dep.as_dict()
    expected = {"name": "logging-plugin", "version_constraint": None}
    assert result == expected, "as_dict should produce correct output with version_constraint as None"
    return


# ---- to_json Tests ----


def test_to_json_with_version_constraint():
    """
        Verify that to_json produces a valid JSON string with all fields.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    json_str = dep.to_json()
    parsed = json.loads(json_str)
    assert parsed["name"] == "auth-plugin", "to_json should include the name field"
    assert parsed["version_constraint"] == "1.0.0", "to_json should include the version_constraint field"
    return


def test_to_json_without_version_constraint():
    """
        Verify that to_json produces a valid JSON string with version_constraint as null.
    """
    dep = PluginDependency(name="logging-plugin")
    json_str = dep.to_json()
    parsed = json.loads(json_str)
    assert parsed["name"] == "logging-plugin", "to_json should include the name field"
    assert parsed["version_constraint"] is None, "to_json should include version_constraint as null"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_with_version_constraint():
    """
        Verify that from_dict reconstructs an equivalent PluginDependency
        when version_constraint is present.
    """
    data = {"name": "auth-plugin", "version_constraint": "1.0.0"}
    dep = PluginDependency.from_dict(data)
    assert dep.name == "auth-plugin", "from_dict should reconstruct the name field"
    assert dep.version_constraint == "1.0.0", "from_dict should reconstruct the version_constraint field"
    return


def test_from_dict_reconstructs_without_version_constraint():
    """
        Verify that from_dict reconstructs an equivalent PluginDependency
        when version_constraint is absent from the dictionary.
    """
    data = {"name": "logging-plugin"}
    dep = PluginDependency.from_dict(data)
    assert dep.name == "logging-plugin", "from_dict should reconstruct the name field"
    assert dep.version_constraint is None, "from_dict should default version_constraint to None"
    return


def test_from_dict_round_trip():
    """
        Verify that as_dict followed by from_dict produces an equivalent object.
    """
    original = PluginDependency(name="cache-plugin", version_constraint="3.2.1")
    data = original.as_dict()
    reconstructed = PluginDependency.from_dict(data)
    assert reconstructed.name == original.name, "round-trip should preserve name"
    assert reconstructed.version_constraint == original.version_constraint, "round-trip should preserve version_constraint"
    return


# ---- __repr__ Tests ----


def test_repr_includes_class_name():
    """
        Verify that __repr__ includes the class name 'PluginDependency'.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    repr_str = repr(dep)
    contains_class_name = "PluginDependency" in repr_str
    assert contains_class_name is True, "__repr__ should include the class name"
    return


def test_repr_includes_name():
    """
        Verify that __repr__ includes the dependency name.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    repr_str = repr(dep)
    contains_name = "auth-plugin" in repr_str
    assert contains_name is True, "__repr__ should include the dependency name"
    return


def test_repr_includes_version_constraint():
    """
        Verify that __repr__ includes the version constraint.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    repr_str = repr(dep)
    contains_constraint = "1.0.0" in repr_str
    assert contains_constraint is True, "__repr__ should include the version constraint"
    return


# ---- __str__ Tests ----


def test_str_includes_class_name():
    """
        Verify that __str__ includes the class name 'PluginDependency'.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="1.0.0")
    str_val = str(dep)
    contains_class_name = "PluginDependency" in str_val
    assert contains_class_name is True, "__str__ should include the class name"
    return


def test_str_includes_name():
    """
        Verify that __str__ includes the dependency name.
    """
    dep = PluginDependency(name="auth-plugin")
    str_val = str(dep)
    contains_name = "auth-plugin" in str_val
    assert contains_name is True, "__str__ should include the dependency name"
    return


def test_str_includes_version_constraint():
    """
        Verify that __str__ includes the version constraint value.
    """
    dep = PluginDependency(name="auth-plugin", version_constraint="2.5.0")
    str_val = str(dep)
    contains_constraint = "2.5.0" in str_val
    assert contains_constraint is True, "__str__ should include the version constraint"
    return
