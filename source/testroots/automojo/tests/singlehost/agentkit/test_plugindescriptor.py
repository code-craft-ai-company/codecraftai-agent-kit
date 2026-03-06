"""
    Unit tests for the automojo.agentkit.plugindescriptor module.

    Tests the PluginDescriptor immutable data type including constructor,
    read-only properties, defensive copies, serialization, deserialization,
    round-trip, and string representations.
"""

import json

from automojo.agentkit.plugindescriptor import PluginDescriptor
from automojo.agentkit.plugindependency import PluginDependency
from automojo.agentkit.pluginstatus import PluginStatus


# ---- Constructor Tests ----


def test_constructor_stores_name():
    """
        Verify that the constructor stores the name field correctly.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX"
    )
    stored_name = descriptor.name
    assert stored_name == "auth-plugin", "constructor should store the name field"
    return


def test_constructor_stores_version():
    """
        Verify that the constructor stores the version field correctly.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="2.3.1",
        description="Authentication plugin",
        author="AutomationX"
    )
    stored_version = descriptor.version
    assert stored_version == "2.3.1", "constructor should store the version field"
    return


def test_constructor_stores_description():
    """
        Verify that the constructor stores the description field correctly.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Handles authentication",
        author="AutomationX"
    )
    stored_description = descriptor.description
    assert stored_description == "Handles authentication", "constructor should store the description field"
    return


def test_constructor_stores_author():
    """
        Verify that the constructor stores the author field correctly.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="TeamAlpha"
    )
    stored_author = descriptor.author
    assert stored_author == "TeamAlpha", "constructor should store the author field"
    return


def test_constructor_stores_extension_points():
    """
        Verify that the constructor stores the extension_points list correctly.
    """
    ext_points = ["hook.before_start", "hook.after_stop"]
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        extension_points=ext_points
    )
    stored_points = descriptor.extension_points
    assert stored_points == ["hook.before_start", "hook.after_stop"], \
        "constructor should store the extension_points list"
    return


def test_constructor_stores_dependencies():
    """
        Verify that the constructor stores the dependencies list correctly.
    """
    dep = PluginDependency(name="logging-plugin", version_constraint="1.0.0")
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        dependencies=[dep]
    )
    stored_deps = descriptor.dependencies
    assert len(stored_deps) == 1, "constructor should store one dependency"
    assert stored_deps[0].name == "logging-plugin", "dependency name should match"
    return


def test_constructor_stores_status():
    """
        Verify that the constructor stores the status field correctly.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        status=PluginStatus.ACTIVE
    )
    stored_status = descriptor.status
    assert stored_status == PluginStatus.ACTIVE, "constructor should store the status field"
    return


# ---- Default Value Tests ----


def test_extension_points_defaults_to_empty_list_when_none():
    """
        Verify that extension_points defaults to an empty list when None is provided.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        extension_points=None
    )
    stored_points = descriptor.extension_points
    assert stored_points == [], "extension_points should default to empty list when None"
    return


def test_dependencies_defaults_to_empty_list_when_none():
    """
        Verify that dependencies defaults to an empty list when None is provided.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        dependencies=None
    )
    stored_deps = descriptor.dependencies
    assert stored_deps == [], "dependencies should default to empty list when None"
    return


def test_status_defaults_to_discovered():
    """
        Verify that status defaults to PluginStatus.DISCOVERED when not provided.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX"
    )
    stored_status = descriptor.status
    assert stored_status == PluginStatus.DISCOVERED, "status should default to DISCOVERED"
    return


# ---- Read-Only Property Tests ----


def test_name_property_returns_expected_value():
    """
        Verify that the name read-only property returns the expected value.
    """
    descriptor = PluginDescriptor(
        name="metrics-plugin",
        version="3.0.0",
        description="Metrics collection",
        author="AutomationX"
    )
    result = descriptor.name
    assert result == "metrics-plugin", "name property should return 'metrics-plugin'"
    return


def test_version_property_returns_expected_value():
    """
        Verify that the version read-only property returns the expected value.
    """
    descriptor = PluginDescriptor(
        name="metrics-plugin",
        version="3.0.0",
        description="Metrics collection",
        author="AutomationX"
    )
    result = descriptor.version
    assert result == "3.0.0", "version property should return '3.0.0'"
    return


def test_description_property_returns_expected_value():
    """
        Verify that the description read-only property returns the expected value.
    """
    descriptor = PluginDescriptor(
        name="metrics-plugin",
        version="3.0.0",
        description="Metrics collection",
        author="AutomationX"
    )
    result = descriptor.description
    assert result == "Metrics collection", "description property should return 'Metrics collection'"
    return


def test_author_property_returns_expected_value():
    """
        Verify that the author read-only property returns the expected value.
    """
    descriptor = PluginDescriptor(
        name="metrics-plugin",
        version="3.0.0",
        description="Metrics collection",
        author="TeamBeta"
    )
    result = descriptor.author
    assert result == "TeamBeta", "author property should return 'TeamBeta'"
    return


def test_status_property_returns_expected_value():
    """
        Verify that the status read-only property returns the expected value.
    """
    descriptor = PluginDescriptor(
        name="metrics-plugin",
        version="3.0.0",
        description="Metrics collection",
        author="AutomationX",
        status=PluginStatus.LOADED
    )
    result = descriptor.status
    assert result == PluginStatus.LOADED, "status property should return LOADED"
    return


# ---- Defensive Copy Tests ----


def test_extension_points_returns_defensive_copy():
    """
        Verify that the extension_points property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        extension_points=["hook.before_start"]
    )
    copy_one = descriptor.extension_points
    copy_one.append("hook.injected")
    copy_two = descriptor.extension_points
    assert len(copy_two) == 1, "extension_points should return a defensive copy"
    assert "hook.injected" not in copy_two, "modification should not affect internal state"
    return


def test_dependencies_returns_defensive_copy():
    """
        Verify that the dependencies property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    dep = PluginDependency(name="logging-plugin")
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        dependencies=[dep]
    )
    copy_one = descriptor.dependencies
    copy_one.append(PluginDependency(name="injected-plugin"))
    copy_two = descriptor.dependencies
    assert len(copy_two) == 1, "dependencies should return a defensive copy"
    return


# ---- as_dict Tests ----


def test_as_dict_produces_correct_output():
    """
        Verify that as_dict produces a dictionary with all fields,
        dependencies serialized via their as_dict, and status as string value.
    """
    dep = PluginDependency(name="logging-plugin", version_constraint="1.0.0")
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="2.0.0",
        description="Authentication plugin",
        author="AutomationX",
        extension_points=["hook.before_start"],
        dependencies=[dep],
        status=PluginStatus.ACTIVE
    )
    result = descriptor.as_dict()
    assert result["name"] == "auth-plugin", "as_dict should include name"
    assert result["version"] == "2.0.0", "as_dict should include version"
    assert result["description"] == "Authentication plugin", "as_dict should include description"
    assert result["author"] == "AutomationX", "as_dict should include author"
    assert result["extension_points"] == ["hook.before_start"], "as_dict should include extension_points"
    assert result["status"] == "ACTIVE", "as_dict should serialize status as string value"
    assert len(result["dependencies"]) == 1, "as_dict should include one dependency"
    assert result["dependencies"][0]["name"] == "logging-plugin", \
        "as_dict should serialize dependency via its as_dict"
    assert result["dependencies"][0]["version_constraint"] == "1.0.0", \
        "as_dict should serialize dependency version_constraint"
    return


def test_as_dict_with_empty_extension_points_and_dependencies():
    """
        Verify that as_dict produces correct output when extension_points
        and dependencies are empty lists.
    """
    descriptor = PluginDescriptor(
        name="simple-plugin",
        version="0.1.0",
        description="A simple plugin",
        author="AutomationX"
    )
    result = descriptor.as_dict()
    assert result["extension_points"] == [], "as_dict should include empty extension_points list"
    assert result["dependencies"] == [], "as_dict should include empty dependencies list"
    assert result["status"] == "DISCOVERED", "as_dict should serialize default status as DISCOVERED"
    return


# ---- to_json Tests ----


def test_to_json_produces_valid_json_with_all_fields():
    """
        Verify that to_json produces a valid JSON string containing all fields.
    """
    dep = PluginDependency(name="cache-plugin", version_constraint="2.0.0")
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.5.0",
        description="Authentication plugin",
        author="AutomationX",
        extension_points=["hook.init"],
        dependencies=[dep],
        status=PluginStatus.LOADED
    )
    json_str = descriptor.to_json()
    parsed = json.loads(json_str)
    assert parsed["name"] == "auth-plugin", "to_json should include name"
    assert parsed["version"] == "1.5.0", "to_json should include version"
    assert parsed["description"] == "Authentication plugin", "to_json should include description"
    assert parsed["author"] == "AutomationX", "to_json should include author"
    assert parsed["extension_points"] == ["hook.init"], "to_json should include extension_points"
    assert parsed["status"] == "LOADED", "to_json should include status as string"
    assert len(parsed["dependencies"]) == 1, "to_json should include dependencies"
    assert parsed["dependencies"][0]["name"] == "cache-plugin", "to_json should serialize dependency name"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs an equivalent PluginDescriptor
        including dependencies and status.
    """
    data = {
        "name": "auth-plugin",
        "version": "1.0.0",
        "description": "Authentication plugin",
        "author": "AutomationX",
        "extension_points": ["hook.before_start"],
        "dependencies": [
            {"name": "logging-plugin", "version_constraint": "1.0.0"}
        ],
        "status": "ACTIVE"
    }
    descriptor = PluginDescriptor.from_dict(data)
    assert descriptor.name == "auth-plugin", "from_dict should reconstruct name"
    assert descriptor.version == "1.0.0", "from_dict should reconstruct version"
    assert descriptor.description == "Authentication plugin", "from_dict should reconstruct description"
    assert descriptor.author == "AutomationX", "from_dict should reconstruct author"
    assert descriptor.extension_points == ["hook.before_start"], \
        "from_dict should reconstruct extension_points"
    assert len(descriptor.dependencies) == 1, "from_dict should reconstruct one dependency"
    assert descriptor.dependencies[0].name == "logging-plugin", \
        "from_dict should reconstruct dependency name"
    assert descriptor.dependencies[0].version_constraint == "1.0.0", \
        "from_dict should reconstruct dependency version_constraint"
    assert descriptor.status == PluginStatus.ACTIVE, "from_dict should reconstruct status"
    return


def test_from_dict_defaults_status_to_discovered():
    """
        Verify that from_dict defaults status to DISCOVERED when not present.
    """
    data = {
        "name": "simple-plugin",
        "version": "0.1.0",
        "description": "A simple plugin",
        "author": "AutomationX"
    }
    descriptor = PluginDescriptor.from_dict(data)
    assert descriptor.status == PluginStatus.DISCOVERED, \
        "from_dict should default status to DISCOVERED"
    return


# ---- from_json Tests ----


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs an equivalent PluginDescriptor.
    """
    data = {
        "name": "auth-plugin",
        "version": "2.0.0",
        "description": "Authentication plugin",
        "author": "TeamAlpha",
        "extension_points": ["hook.init", "hook.cleanup"],
        "dependencies": [
            {"name": "cache-plugin", "version_constraint": None}
        ],
        "status": "LOADED"
    }
    json_str = json.dumps(data)
    descriptor = PluginDescriptor.from_json(json_str)
    assert descriptor.name == "auth-plugin", "from_json should reconstruct name"
    assert descriptor.version == "2.0.0", "from_json should reconstruct version"
    assert descriptor.description == "Authentication plugin", "from_json should reconstruct description"
    assert descriptor.author == "TeamAlpha", "from_json should reconstruct author"
    assert descriptor.extension_points == ["hook.init", "hook.cleanup"], \
        "from_json should reconstruct extension_points"
    assert len(descriptor.dependencies) == 1, "from_json should reconstruct one dependency"
    assert descriptor.dependencies[0].name == "cache-plugin", \
        "from_json should reconstruct dependency name"
    assert descriptor.status == PluginStatus.LOADED, "from_json should reconstruct status"
    return


# ---- Round-Trip Tests ----


def test_round_trip_as_dict_from_dict_preserves_all_fields():
    """
        Verify that as_dict followed by from_dict preserves all fields.
    """
    dep = PluginDependency(name="logging-plugin", version_constraint="3.0.0")
    original = PluginDescriptor(
        name="auth-plugin",
        version="1.2.3",
        description="Authentication plugin",
        author="AutomationX",
        extension_points=["hook.before_start", "hook.after_stop"],
        dependencies=[dep],
        status=PluginStatus.LOADED
    )
    data = original.as_dict()
    reconstructed = PluginDescriptor.from_dict(data)
    assert reconstructed.name == original.name, "round-trip should preserve name"
    assert reconstructed.version == original.version, "round-trip should preserve version"
    assert reconstructed.description == original.description, "round-trip should preserve description"
    assert reconstructed.author == original.author, "round-trip should preserve author"
    assert reconstructed.extension_points == original.extension_points, \
        "round-trip should preserve extension_points"
    assert len(reconstructed.dependencies) == len(original.dependencies), \
        "round-trip should preserve dependency count"
    assert reconstructed.dependencies[0].name == original.dependencies[0].name, \
        "round-trip should preserve dependency name"
    assert reconstructed.dependencies[0].version_constraint == original.dependencies[0].version_constraint, \
        "round-trip should preserve dependency version_constraint"
    assert reconstructed.status == original.status, "round-trip should preserve status"
    return


# ---- __repr__ Tests ----


def test_repr_includes_class_name():
    """
        Verify that __repr__ includes the class name 'PluginDescriptor'.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX"
    )
    repr_str = repr(descriptor)
    contains_class_name = "PluginDescriptor" in repr_str
    assert contains_class_name is True, "__repr__ should include the class name"
    return


def test_repr_includes_plugin_name():
    """
        Verify that __repr__ includes the plugin name.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX"
    )
    repr_str = repr(descriptor)
    contains_name = "auth-plugin" in repr_str
    assert contains_name is True, "__repr__ should include the plugin name"
    return


def test_repr_includes_version():
    """
        Verify that __repr__ includes the version.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="4.5.6",
        description="Authentication plugin",
        author="AutomationX"
    )
    repr_str = repr(descriptor)
    contains_version = "4.5.6" in repr_str
    assert contains_version is True, "__repr__ should include the version"
    return


def test_repr_includes_status():
    """
        Verify that __repr__ includes the status value.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        status=PluginStatus.FAILED
    )
    repr_str = repr(descriptor)
    contains_status = "FAILED" in repr_str
    assert contains_status is True, "__repr__ should include the status"
    return


# ---- __str__ Tests ----


def test_str_includes_plugin_name():
    """
        Verify that __str__ includes the plugin name.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX"
    )
    str_val = str(descriptor)
    contains_name = "auth-plugin" in str_val
    assert contains_name is True, "__str__ should include the plugin name"
    return


def test_str_includes_version():
    """
        Verify that __str__ includes the version.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="7.8.9",
        description="Authentication plugin",
        author="AutomationX"
    )
    str_val = str(descriptor)
    contains_version = "7.8.9" in str_val
    assert contains_version is True, "__str__ should include the version"
    return


def test_str_includes_description():
    """
        Verify that __str__ includes the description.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Handles user authentication",
        author="AutomationX"
    )
    str_val = str(descriptor)
    contains_description = "Handles user authentication" in str_val
    assert contains_description is True, "__str__ should include the description"
    return


def test_str_includes_status():
    """
        Verify that __str__ includes the status value.
    """
    descriptor = PluginDescriptor(
        name="auth-plugin",
        version="1.0.0",
        description="Authentication plugin",
        author="AutomationX",
        status=PluginStatus.DISABLED
    )
    str_val = str(descriptor)
    contains_status = "DISABLED" in str_val
    assert contains_status is True, "__str__ should include the status"
    return
