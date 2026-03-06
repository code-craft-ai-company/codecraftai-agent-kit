"""
    Unit tests for the automojo.agentkit.pluginconfiguration module.

    Tests the PluginConfiguration class including constructor defaults,
    read-only properties, defensive copies, serialization, deserialization,
    round-trip, file loading, error handling, and string representations.
"""

import json
import os
import tempfile

from automojo.agentkit.pluginconfiguration import PluginConfiguration
from automojo.agentkit.errors import ConfigurationError


# ---- Constructor Default Tests ----


def test_constructor_defaults_automatic_discovery_enabled_to_true():
    """
        Verify that the constructor defaults automatic_discovery_enabled to True.
    """
    config = PluginConfiguration()
    result = config.automatic_discovery_enabled
    assert result is True, "automatic_discovery_enabled should default to True"
    return


def test_constructor_defaults_enabled_plugins_to_empty_list():
    """
        Verify that the constructor defaults enabled_plugins to an empty list.
    """
    config = PluginConfiguration()
    result = config.enabled_plugins
    assert result == [], "enabled_plugins should default to empty list"
    return


def test_constructor_defaults_disabled_plugins_to_empty_list():
    """
        Verify that the constructor defaults disabled_plugins to an empty list.
    """
    config = PluginConfiguration()
    result = config.disabled_plugins
    assert result == [], "disabled_plugins should default to empty list"
    return


def test_constructor_defaults_search_paths_to_empty_list():
    """
        Verify that the constructor defaults search_paths to an empty list.
    """
    config = PluginConfiguration()
    result = config.search_paths
    assert result == [], "search_paths should default to empty list"
    return


# ---- Constructor Stores All Fields Tests ----


def test_constructor_stores_enabled_plugins():
    """
        Verify that the constructor stores the enabled_plugins list correctly.
    """
    config = PluginConfiguration(enabled_plugins=["auth-plugin", "cache-plugin"])
    result = config.enabled_plugins
    assert result == ["auth-plugin", "cache-plugin"], "constructor should store enabled_plugins"
    return


def test_constructor_stores_disabled_plugins():
    """
        Verify that the constructor stores the disabled_plugins list correctly.
    """
    config = PluginConfiguration(disabled_plugins=["legacy-plugin"])
    result = config.disabled_plugins
    assert result == ["legacy-plugin"], "constructor should store disabled_plugins"
    return


def test_constructor_stores_search_paths():
    """
        Verify that the constructor stores the search_paths list correctly.
    """
    config = PluginConfiguration(search_paths=["/opt/plugins", "/usr/local/plugins"])
    result = config.search_paths
    assert result == ["/opt/plugins", "/usr/local/plugins"], "constructor should store search_paths"
    return


def test_constructor_stores_automatic_discovery_enabled_false():
    """
        Verify that the constructor stores automatic_discovery_enabled as False when provided.
    """
    config = PluginConfiguration(automatic_discovery_enabled=False)
    result = config.automatic_discovery_enabled
    assert result is False, "constructor should store automatic_discovery_enabled as False"
    return


def test_constructor_stores_all_fields_together():
    """
        Verify that the constructor stores all fields correctly when all are provided.
    """
    config = PluginConfiguration(
        enabled_plugins=["auth-plugin"],
        disabled_plugins=["legacy-plugin"],
        search_paths=["/opt/plugins"],
        automatic_discovery_enabled=False
    )
    assert config.enabled_plugins == ["auth-plugin"], "should store enabled_plugins"
    assert config.disabled_plugins == ["legacy-plugin"], "should store disabled_plugins"
    assert config.search_paths == ["/opt/plugins"], "should store search_paths"
    assert config.automatic_discovery_enabled is False, "should store automatic_discovery_enabled"
    return


# ---- Read-Only Property Tests ----


def test_enabled_plugins_property_returns_expected_value():
    """
        Verify that the enabled_plugins property returns the expected list.
    """
    config = PluginConfiguration(enabled_plugins=["metrics-plugin"])
    result = config.enabled_plugins
    assert result == ["metrics-plugin"], "enabled_plugins property should return expected value"
    return


def test_disabled_plugins_property_returns_expected_value():
    """
        Verify that the disabled_plugins property returns the expected list.
    """
    config = PluginConfiguration(disabled_plugins=["old-plugin", "deprecated-plugin"])
    result = config.disabled_plugins
    assert result == ["old-plugin", "deprecated-plugin"], "disabled_plugins property should return expected value"
    return


def test_search_paths_property_returns_expected_value():
    """
        Verify that the search_paths property returns the expected list.
    """
    config = PluginConfiguration(search_paths=["/home/plugins"])
    result = config.search_paths
    assert result == ["/home/plugins"], "search_paths property should return expected value"
    return


def test_automatic_discovery_enabled_property_returns_expected_value():
    """
        Verify that the automatic_discovery_enabled property returns the expected value.
    """
    config = PluginConfiguration(automatic_discovery_enabled=True)
    result = config.automatic_discovery_enabled
    assert result is True, "automatic_discovery_enabled property should return True"
    return


# ---- Defensive Copy Tests ----


def test_enabled_plugins_returns_defensive_copy():
    """
        Verify that the enabled_plugins property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    config = PluginConfiguration(enabled_plugins=["auth-plugin"])
    copy_one = config.enabled_plugins
    copy_one.append("injected-plugin")
    copy_two = config.enabled_plugins
    assert len(copy_two) == 1, "enabled_plugins should return a defensive copy"
    assert "injected-plugin" not in copy_two, "modification should not affect internal state"
    return


def test_disabled_plugins_returns_defensive_copy():
    """
        Verify that the disabled_plugins property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    config = PluginConfiguration(disabled_plugins=["legacy-plugin"])
    copy_one = config.disabled_plugins
    copy_one.append("injected-plugin")
    copy_two = config.disabled_plugins
    assert len(copy_two) == 1, "disabled_plugins should return a defensive copy"
    assert "injected-plugin" not in copy_two, "modification should not affect internal state"
    return


def test_search_paths_returns_defensive_copy():
    """
        Verify that the search_paths property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    config = PluginConfiguration(search_paths=["/opt/plugins"])
    copy_one = config.search_paths
    copy_one.append("/injected/path")
    copy_two = config.search_paths
    assert len(copy_two) == 1, "search_paths should return a defensive copy"
    assert "/injected/path" not in copy_two, "modification should not affect internal state"
    return


# ---- as_dict Tests ----


def test_as_dict_produces_correct_output():
    """
        Verify that as_dict produces a dictionary with all fields.
    """
    config = PluginConfiguration(
        enabled_plugins=["auth-plugin", "cache-plugin"],
        disabled_plugins=["legacy-plugin"],
        search_paths=["/opt/plugins"],
        automatic_discovery_enabled=False
    )
    result = config.as_dict()
    assert result["enabled_plugins"] == ["auth-plugin", "cache-plugin"], \
        "as_dict should include enabled_plugins"
    assert result["disabled_plugins"] == ["legacy-plugin"], \
        "as_dict should include disabled_plugins"
    assert result["search_paths"] == ["/opt/plugins"], \
        "as_dict should include search_paths"
    assert result["automatic_discovery_enabled"] is False, \
        "as_dict should include automatic_discovery_enabled"
    return


def test_as_dict_with_defaults():
    """
        Verify that as_dict produces correct output with default values.
    """
    config = PluginConfiguration()
    result = config.as_dict()
    assert result["enabled_plugins"] == [], "as_dict should include empty enabled_plugins"
    assert result["disabled_plugins"] == [], "as_dict should include empty disabled_plugins"
    assert result["search_paths"] == [], "as_dict should include empty search_paths"
    assert result["automatic_discovery_enabled"] is True, \
        "as_dict should include automatic_discovery_enabled as True"
    return


# ---- to_json Tests ----


def test_to_json_produces_valid_json_with_all_fields():
    """
        Verify that to_json produces a valid JSON string containing all fields.
    """
    config = PluginConfiguration(
        enabled_plugins=["auth-plugin"],
        disabled_plugins=["legacy-plugin"],
        search_paths=["/opt/plugins"],
        automatic_discovery_enabled=False
    )
    json_str = config.to_json()
    parsed = json.loads(json_str)
    assert parsed["enabled_plugins"] == ["auth-plugin"], "to_json should include enabled_plugins"
    assert parsed["disabled_plugins"] == ["legacy-plugin"], "to_json should include disabled_plugins"
    assert parsed["search_paths"] == ["/opt/plugins"], "to_json should include search_paths"
    assert parsed["automatic_discovery_enabled"] is False, \
        "to_json should include automatic_discovery_enabled"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs an equivalent PluginConfiguration.
    """
    data = {
        "enabled_plugins": ["auth-plugin", "cache-plugin"],
        "disabled_plugins": ["legacy-plugin"],
        "search_paths": ["/opt/plugins", "/usr/local/plugins"],
        "automatic_discovery_enabled": False
    }
    config = PluginConfiguration.from_dict(data)
    assert config.enabled_plugins == ["auth-plugin", "cache-plugin"], \
        "from_dict should reconstruct enabled_plugins"
    assert config.disabled_plugins == ["legacy-plugin"], \
        "from_dict should reconstruct disabled_plugins"
    assert config.search_paths == ["/opt/plugins", "/usr/local/plugins"], \
        "from_dict should reconstruct search_paths"
    assert config.automatic_discovery_enabled is False, \
        "from_dict should reconstruct automatic_discovery_enabled"
    return


def test_from_dict_with_missing_keys_uses_defaults():
    """
        Verify that from_dict uses defaults when keys are missing.
    """
    data = {}
    config = PluginConfiguration.from_dict(data)
    assert config.enabled_plugins == [], "from_dict should default enabled_plugins to empty list"
    assert config.disabled_plugins == [], "from_dict should default disabled_plugins to empty list"
    assert config.search_paths == [], "from_dict should default search_paths to empty list"
    assert config.automatic_discovery_enabled is True, \
        "from_dict should default automatic_discovery_enabled to True"
    return


# ---- from_json Tests ----


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs an equivalent PluginConfiguration.
    """
    data = {
        "enabled_plugins": ["metrics-plugin"],
        "disabled_plugins": ["old-plugin"],
        "search_paths": ["/home/plugins"],
        "automatic_discovery_enabled": True
    }
    json_str = json.dumps(data)
    config = PluginConfiguration.from_json(json_str)
    assert config.enabled_plugins == ["metrics-plugin"], \
        "from_json should reconstruct enabled_plugins"
    assert config.disabled_plugins == ["old-plugin"], \
        "from_json should reconstruct disabled_plugins"
    assert config.search_paths == ["/home/plugins"], \
        "from_json should reconstruct search_paths"
    assert config.automatic_discovery_enabled is True, \
        "from_json should reconstruct automatic_discovery_enabled"
    return


# ---- Round-Trip Tests ----


def test_round_trip_as_dict_from_dict_preserves_all_fields():
    """
        Verify that as_dict followed by from_dict preserves all fields.
    """
    original = PluginConfiguration(
        enabled_plugins=["auth-plugin", "cache-plugin"],
        disabled_plugins=["legacy-plugin", "deprecated-plugin"],
        search_paths=["/opt/plugins", "/usr/local/plugins"],
        automatic_discovery_enabled=False
    )
    data = original.as_dict()
    reconstructed = PluginConfiguration.from_dict(data)
    assert reconstructed.enabled_plugins == original.enabled_plugins, \
        "round-trip should preserve enabled_plugins"
    assert reconstructed.disabled_plugins == original.disabled_plugins, \
        "round-trip should preserve disabled_plugins"
    assert reconstructed.search_paths == original.search_paths, \
        "round-trip should preserve search_paths"
    assert reconstructed.automatic_discovery_enabled == original.automatic_discovery_enabled, \
        "round-trip should preserve automatic_discovery_enabled"
    return


# ---- from_json_file Tests ----


def test_from_json_file_loads_from_json_file():
    """
        Verify that from_json_file loads a PluginConfiguration from a JSON file.
    """
    data = {
        "enabled_plugins": ["auth-plugin"],
        "disabled_plugins": ["legacy-plugin"],
        "search_paths": ["/opt/plugins"],
        "automatic_discovery_enabled": False
    }
    json_content = json.dumps(data)

    temp_fd, temp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(temp_fd, "w") as temp_file:
            temp_file.write(json_content)

        config = PluginConfiguration.from_json_file(temp_path)
        assert config.enabled_plugins == ["auth-plugin"], \
            "from_json_file should load enabled_plugins"
        assert config.disabled_plugins == ["legacy-plugin"], \
            "from_json_file should load disabled_plugins"
        assert config.search_paths == ["/opt/plugins"], \
            "from_json_file should load search_paths"
        assert config.automatic_discovery_enabled is False, \
            "from_json_file should load automatic_discovery_enabled"
    finally:
        if os.path.exists(temp_path) is True:
            os.remove(temp_path)

    return


def test_from_json_file_raises_configuration_error_for_missing_file():
    """
        Verify that from_json_file raises ConfigurationError for a missing file.
    """
    missing_path = "/nonexistent/path/plugin_config.json"
    raised = False
    try:
        PluginConfiguration.from_json_file(missing_path)
    except ConfigurationError:
        raised = True

    assert raised is True, "from_json_file should raise ConfigurationError for missing file"
    return


def test_from_json_file_raises_configuration_error_for_invalid_json():
    """
        Verify that from_json_file raises ConfigurationError for invalid JSON content.
    """
    temp_fd, temp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(temp_fd, "w") as temp_file:
            temp_file.write("this is not valid json {{{")

        raised = False
        try:
            PluginConfiguration.from_json_file(temp_path)
        except ConfigurationError:
            raised = True

        assert raised is True, "from_json_file should raise ConfigurationError for invalid JSON"
    finally:
        if os.path.exists(temp_path) is True:
            os.remove(temp_path)

    return


# ---- from_yaml_file Tests ----


def test_from_yaml_file_loads_from_yaml_file():
    """
        Verify that from_yaml_file loads a PluginConfiguration from a YAML file.
    """
    yaml_content = (
        "enabled_plugins:\n"
        "  - auth-plugin\n"
        "  - cache-plugin\n"
        "disabled_plugins:\n"
        "  - legacy-plugin\n"
        "search_paths:\n"
        "  - /opt/plugins\n"
        "automatic_discovery_enabled: false\n"
    )

    temp_fd, temp_path = tempfile.mkstemp(suffix=".yaml")
    try:
        with os.fdopen(temp_fd, "w") as temp_file:
            temp_file.write(yaml_content)

        config = PluginConfiguration.from_yaml_file(temp_path)
        assert config.enabled_plugins == ["auth-plugin", "cache-plugin"], \
            "from_yaml_file should load enabled_plugins"
        assert config.disabled_plugins == ["legacy-plugin"], \
            "from_yaml_file should load disabled_plugins"
        assert config.search_paths == ["/opt/plugins"], \
            "from_yaml_file should load search_paths"
        assert config.automatic_discovery_enabled is False, \
            "from_yaml_file should load automatic_discovery_enabled"
    finally:
        if os.path.exists(temp_path) is True:
            os.remove(temp_path)

    return


# ---- __repr__ Tests ----


def test_repr_includes_class_name():
    """
        Verify that __repr__ includes the class name 'PluginConfiguration'.
    """
    config = PluginConfiguration()
    repr_str = repr(config)
    contains_class_name = "PluginConfiguration" in repr_str
    assert contains_class_name is True, "__repr__ should include the class name"
    return


def test_repr_includes_enabled_plugin_count():
    """
        Verify that __repr__ includes the enabled plugin count.
    """
    config = PluginConfiguration(enabled_plugins=["auth-plugin", "cache-plugin"])
    repr_str = repr(config)
    contains_count = "enabled_plugins=2" in repr_str
    assert contains_count is True, "__repr__ should include enabled plugin count"
    return


def test_repr_includes_auto_discovery_status():
    """
        Verify that __repr__ includes the automatic discovery enabled status.
    """
    config = PluginConfiguration(automatic_discovery_enabled=False)
    repr_str = repr(config)
    contains_auto_discovery = "automatic_discovery_enabled=False" in repr_str
    assert contains_auto_discovery is True, "__repr__ should include auto-discovery status"
    return


# ---- __str__ Tests ----


def test_str_includes_enabled_count():
    """
        Verify that __str__ includes the enabled plugin count.
    """
    config = PluginConfiguration(enabled_plugins=["auth-plugin", "cache-plugin", "metrics-plugin"])
    str_val = str(config)
    contains_enabled = "enabled=3" in str_val
    assert contains_enabled is True, "__str__ should include enabled count"
    return


def test_str_includes_disabled_count():
    """
        Verify that __str__ includes the disabled plugin count.
    """
    config = PluginConfiguration(disabled_plugins=["legacy-plugin", "old-plugin"])
    str_val = str(config)
    contains_disabled = "disabled=2" in str_val
    assert contains_disabled is True, "__str__ should include disabled count"
    return


def test_str_includes_auto_discovery_status():
    """
        Verify that __str__ includes the automatic discovery enabled status.
    """
    config = PluginConfiguration(automatic_discovery_enabled=True)
    str_val = str(config)
    contains_auto_discovery = "automatic_discovery_enabled=True" in str_val
    assert contains_auto_discovery is True, "__str__ should include auto-discovery status"
    return
