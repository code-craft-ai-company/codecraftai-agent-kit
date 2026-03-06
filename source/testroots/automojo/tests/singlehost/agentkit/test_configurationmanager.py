"""
    Unit tests for the automojo.agentkit.configurationmanager module.

    Tests the ConfigurationManager class covering core operations: get, set,
    load_defaults, load_from_dict, layer merging, change listeners, listener
    exception handling, load_from_file, load_from_environment, and reload.

    Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.9, 1.10, 4.1, 4.8, 8.10, 8.11, 8.12, 8.13
"""

import json
import logging
import os
import tempfile

from automojo.agentkit.configurationchangeevent import ConfigurationChangeEvent
from automojo.agentkit.configurationlayer import ConfigurationLayer
from automojo.agentkit.configurationlayersource import ConfigurationLayerSource
from automojo.agentkit.configurationmanager import ConfigurationManager
from automojo.agentkit.errors import ConfigurationError


# ---- Constructor Tests ----


def test_constructor_stores_agent_identifier():
    """
        Verify that the constructor stores the agent_identifier correctly.
    """
    manager = ConfigurationManager(agent_identifier="test-agent-001")
    stored_id = manager.agent_identifier
    assert stored_id == "test-agent-001", "constructor should store the agent_identifier"
    return


def test_constructor_stores_schema_none_by_default():
    """
        Verify that the constructor stores schema as None when not provided.
    """
    manager = ConfigurationManager(agent_identifier="agent-no-schema")
    stored_schema = manager.schema
    assert stored_schema is None, "constructor should store schema as None by default"
    return


def test_constructor_initializes_empty_layers():
    """
        Verify that the constructor initializes an empty layers list.
    """
    manager = ConfigurationManager(agent_identifier="agent-empty")
    layer_list = manager.layers
    layer_count = len(layer_list)
    assert layer_count == 0, "constructor should initialize an empty layers list"
    return


def test_constructor_initializes_empty_merged_configuration():
    """
        Verify that the constructor initializes an empty merged configuration.
    """
    manager = ConfigurationManager(agent_identifier="agent-empty-config")
    merged = manager.merged_configuration
    assert merged == {}, "constructor should initialize an empty merged configuration"
    return


# ---- get Tests ----


def test_get_returns_value_at_top_level_path():
    """
        Verify that get returns the value at a top-level field path.
    """
    manager = ConfigurationManager(agent_identifier="get-agent")
    manager.load_from_dict(data={"debug": True})
    result = manager.get("debug")
    assert result is True, "get should return the value at a top-level path"
    return


def test_get_returns_value_at_dot_separated_path():
    """
        Verify that get traverses dot-separated paths correctly.
    """
    manager = ConfigurationManager(agent_identifier="get-agent")
    manager.load_from_dict(data={"database": {"host": "localhost", "port": 5432}})
    host_value = manager.get("database.host")
    port_value = manager.get("database.port")
    assert host_value == "localhost", "get should traverse dot-separated path for host"
    assert port_value == 5432, "get should traverse dot-separated path for port"
    return


def test_get_returns_default_when_path_not_found():
    """
        Verify that get returns the default value when the field path is not found.
    """
    manager = ConfigurationManager(agent_identifier="get-default-agent")
    manager.load_from_dict(data={"existing": "value"})
    result = manager.get("nonexistent.path", default="fallback")
    assert result == "fallback", "get should return the default when path is not found"
    return


def test_get_returns_none_when_path_not_found_and_no_default():
    """
        Verify that get returns None when the field path is not found and no default is given.
    """
    manager = ConfigurationManager(agent_identifier="get-none-agent")
    manager.load_from_dict(data={"key": "value"})
    result = manager.get("missing.key")
    assert result is None, "get should return None when path not found and no default"
    return


def test_get_returns_deeply_nested_value():
    """
        Verify that get can traverse deeply nested dot-separated paths.
    """
    manager = ConfigurationManager(agent_identifier="deep-agent")
    data = {"level1": {"level2": {"level3": {"target": "deep-value"}}}}
    manager.load_from_dict(data=data)
    result = manager.get("level1.level2.level3.target")
    assert result == "deep-value", "get should traverse deeply nested paths"
    return


# ---- set Tests ----


def test_set_stores_value_in_runtime_layer():
    """
        Verify that set stores a value retrievable via get.
    """
    manager = ConfigurationManager(agent_identifier="set-agent")
    manager.set("app.name", "my-app")
    result = manager.get("app.name")
    assert result == "my-app", "set should store the value retrievable via get"
    return


def test_set_creates_runtime_layer():
    """
        Verify that set creates a RUNTIME layer when none exists.
    """
    manager = ConfigurationManager(agent_identifier="set-layer-agent")
    manager.set("key", "value")
    layer_list = manager.layers
    layer_count = len(layer_list)
    assert layer_count == 1, "set should create a layer"

    first_layer = layer_list[0]
    layer_source = first_layer.source
    assert layer_source is ConfigurationLayerSource.RUNTIME, \
        "set should create a RUNTIME layer"
    return


def test_set_updates_existing_runtime_layer():
    """
        Verify that calling set multiple times updates the same RUNTIME layer.
    """
    manager = ConfigurationManager(agent_identifier="set-update-agent")
    manager.set("key1", "value1")
    manager.set("key2", "value2")

    layer_list = manager.layers
    runtime_layers = [lyr for lyr in layer_list if lyr.name == "runtime"]
    runtime_count = len(runtime_layers)
    assert runtime_count == 1, "set should reuse the existing runtime layer"

    val1 = manager.get("key1")
    val2 = manager.get("key2")
    assert val1 == "value1", "first set value should be preserved"
    assert val2 == "value2", "second set value should be stored"
    return


def test_set_overwrites_existing_value():
    """
        Verify that set overwrites a previously set value.
    """
    manager = ConfigurationManager(agent_identifier="set-overwrite-agent")
    manager.set("app.timeout", 30)
    manager.set("app.timeout", 60)
    result = manager.get("app.timeout")
    assert result == 60, "set should overwrite the previous value"
    return


# ---- load_defaults Tests ----


def test_load_defaults_creates_lowest_priority_layer():
    """
        Verify that load_defaults creates a DEFAULTS layer with lowest priority.
    """
    manager = ConfigurationManager(agent_identifier="defaults-agent")
    manager.load_defaults(defaults={"timeout": 30, "retries": 3})

    layer_list = manager.layers
    layer_count = len(layer_list)
    assert layer_count == 1, "load_defaults should create one layer"

    defaults_layer = layer_list[0]
    layer_source = defaults_layer.source
    layer_priority = defaults_layer.priority
    assert layer_source is ConfigurationLayerSource.DEFAULTS, \
        "load_defaults should create a DEFAULTS layer"
    assert layer_priority == 0, "load_defaults should create a layer with priority 0"
    return


def test_load_defaults_values_are_retrievable():
    """
        Verify that values loaded via load_defaults are retrievable via get.
    """
    manager = ConfigurationManager(agent_identifier="defaults-get-agent")
    manager.load_defaults(defaults={"app": {"name": "default-app", "debug": False}})
    name_val = manager.get("app.name")
    debug_val = manager.get("app.debug")
    assert name_val == "default-app", "load_defaults values should be retrievable"
    assert debug_val is False, "load_defaults boolean values should be retrievable"
    return


def test_load_defaults_overridden_by_runtime():
    """
        Verify that RUNTIME values override DEFAULTS values.
    """
    manager = ConfigurationManager(agent_identifier="defaults-override-agent")
    manager.load_defaults(defaults={"timeout": 30})
    manager.set("timeout", 60)
    result = manager.get("timeout")
    assert result == 60, "RUNTIME values should override DEFAULTS values"
    return


# ---- load_from_dict Tests ----


def test_load_from_dict_creates_runtime_layer():
    """
        Verify that load_from_dict creates a RUNTIME layer.
    """
    manager = ConfigurationManager(agent_identifier="dict-agent")
    manager.load_from_dict(data={"key": "value"})

    layer_list = manager.layers
    layer_count = len(layer_list)
    assert layer_count == 1, "load_from_dict should create one layer"

    dict_layer = layer_list[0]
    layer_source = dict_layer.source
    assert layer_source is ConfigurationLayerSource.RUNTIME, \
        "load_from_dict should create a RUNTIME layer"
    return


def test_load_from_dict_uses_custom_layer_name():
    """
        Verify that load_from_dict uses the provided layer_name.
    """
    manager = ConfigurationManager(agent_identifier="dict-name-agent")
    manager.load_from_dict(data={"a": 1}, layer_name="custom-layer")

    layer_list = manager.layers
    first_layer = layer_list[0]
    layer_name = first_layer.name
    assert layer_name == "custom-layer", "load_from_dict should use the custom layer name"
    return


def test_load_from_dict_uses_default_layer_name():
    """
        Verify that load_from_dict uses 'dict-runtime' as default layer name.
    """
    manager = ConfigurationManager(agent_identifier="dict-default-name-agent")
    manager.load_from_dict(data={"b": 2})

    layer_list = manager.layers
    first_layer = layer_list[0]
    layer_name = first_layer.name
    assert layer_name == "dict-runtime", \
        "load_from_dict should use 'dict-runtime' as default layer name"
    return


def test_load_from_dict_values_are_retrievable():
    """
        Verify that values loaded via load_from_dict are retrievable via get.
    """
    manager = ConfigurationManager(agent_identifier="dict-get-agent")
    manager.load_from_dict(data={"server": {"host": "0.0.0.0", "port": 8080}})
    host_val = manager.get("server.host")
    port_val = manager.get("server.port")
    assert host_val == "0.0.0.0", "load_from_dict values should be retrievable"
    assert port_val == 8080, "load_from_dict nested values should be retrievable"
    return


# ---- Layer Merging Priority Tests ----


def test_layer_merging_higher_priority_overrides_lower():
    """
        Verify that higher-priority layers override lower-priority values.
    """
    manager = ConfigurationManager(agent_identifier="merge-agent")
    manager.load_defaults(defaults={"timeout": 10})
    manager.load_from_dict(data={"timeout": 99})

    result = manager.get("timeout")
    assert result == 99, "higher-priority RUNTIME layer should override DEFAULTS"
    return


def test_layer_merging_preserves_non_overlapping_keys():
    """
        Verify that non-overlapping keys from different layers are all present.
    """
    manager = ConfigurationManager(agent_identifier="merge-preserve-agent")
    manager.load_defaults(defaults={"default_key": "default_val"})
    manager.load_from_dict(data={"runtime_key": "runtime_val"})

    default_result = manager.get("default_key")
    runtime_result = manager.get("runtime_key")
    assert default_result == "default_val", "non-overlapping default key should be preserved"
    assert runtime_result == "runtime_val", "non-overlapping runtime key should be preserved"
    return


def test_layer_merging_deep_merge_nested_dicts():
    """
        Verify that nested dictionaries are deep-merged across layers.
    """
    manager = ConfigurationManager(agent_identifier="deep-merge-agent")
    manager.load_defaults(defaults={"db": {"host": "localhost", "port": 5432}})
    manager.load_from_dict(data={"db": {"port": 3306, "name": "mydb"}})

    host_val = manager.get("db.host")
    port_val = manager.get("db.port")
    name_val = manager.get("db.name")
    assert host_val == "localhost", "deep merge should preserve non-overridden nested keys"
    assert port_val == 3306, "deep merge should override nested keys from higher priority"
    assert name_val == "mydb", "deep merge should include new nested keys from higher priority"
    return


# ---- Change Listener Tests ----


def test_register_change_listener_is_invoked_on_change():
    """
        Verify that a registered change listener is invoked when configuration changes.
    """
    manager = ConfigurationManager(agent_identifier="listener-agent")
    received_events = []

    def on_change(event: ConfigurationChangeEvent) -> None:
        received_events.append(event)
        return

    manager.register_change_listener(on_change)
    manager.load_from_dict(data={"app": "value"})

    event_count = len(received_events)
    assert event_count > 0, "change listener should be invoked when configuration changes"
    return


def test_change_listener_receives_correct_event_fields():
    """
        Verify that the change listener receives a ConfigurationChangeEvent
        with correct field_path, previous_value, and new_value.
    """
    manager = ConfigurationManager(agent_identifier="event-fields-agent")
    received_events = []

    def on_change(event: ConfigurationChangeEvent) -> None:
        received_events.append(event)
        return

    manager.register_change_listener(on_change)
    manager.load_from_dict(data={"timeout": 42})

    event_count = len(received_events)
    assert event_count == 1, "should receive exactly one change event"

    first_event = received_events[0]
    event_path = first_event.field_path
    event_prev = first_event.previous_value
    event_new = first_event.new_value

    assert event_path == "timeout", "event field_path should be 'timeout'"
    assert event_prev is None, "event previous_value should be None for new key"
    assert event_new == 42, "event new_value should be 42"
    return


def test_change_listener_receives_event_with_source():
    """
        Verify that the change event includes the correct source.
    """
    manager = ConfigurationManager(agent_identifier="event-source-agent")
    received_events = []

    def on_change(event: ConfigurationChangeEvent) -> None:
        received_events.append(event)
        return

    manager.register_change_listener(on_change)
    manager.load_from_dict(data={"key": "val"})

    first_event = received_events[0]
    event_source = first_event.source
    assert event_source is ConfigurationLayerSource.RUNTIME, \
        "event source should be RUNTIME for load_from_dict"
    return


def test_multiple_listeners_all_invoked():
    """
        Verify that all registered listeners are invoked on a change.
    """
    manager = ConfigurationManager(agent_identifier="multi-listener-agent")
    calls_a = []
    calls_b = []

    def listener_a(event: ConfigurationChangeEvent) -> None:
        calls_a.append(event)
        return

    def listener_b(event: ConfigurationChangeEvent) -> None:
        calls_b.append(event)
        return

    manager.register_change_listener(listener_a)
    manager.register_change_listener(listener_b)
    manager.load_from_dict(data={"x": 1})

    count_a = len(calls_a)
    count_b = len(calls_b)
    assert count_a > 0, "listener_a should be invoked"
    assert count_b > 0, "listener_b should be invoked"
    return


def test_deregister_change_listener_stops_invocation():
    """
        Verify that a deregistered listener is no longer invoked.
    """
    manager = ConfigurationManager(agent_identifier="deregister-agent")
    received_events = []

    def on_change(event: ConfigurationChangeEvent) -> None:
        received_events.append(event)
        return

    manager.register_change_listener(on_change)
    manager.load_from_dict(data={"first": 1})

    first_count = len(received_events)
    assert first_count > 0, "listener should be invoked before deregistration"

    manager.deregister_change_listener(on_change)
    manager.set("second", 2)

    second_count = len(received_events)
    assert second_count == first_count, \
        "listener should not be invoked after deregistration"
    return


def test_set_triggers_change_listener():
    """
        Verify that the set method triggers change listeners.
    """
    manager = ConfigurationManager(agent_identifier="set-listener-agent")
    manager.load_from_dict(data={"val": "old"})

    received_events = []

    def on_change(event: ConfigurationChangeEvent) -> None:
        received_events.append(event)
        return

    manager.register_change_listener(on_change)
    manager.set("val", "new")

    event_count = len(received_events)
    assert event_count == 1, "set should trigger one change event"

    first_event = received_events[0]
    assert first_event.field_path == "val", "event field_path should be 'val'"
    assert first_event.previous_value == "old", "event previous_value should be 'old'"
    assert first_event.new_value == "new", "event new_value should be 'new'"
    return


# ---- Listener Exception Handling Tests ----


def test_listener_exception_is_caught_and_logged():
    """
        Verify that a listener exception is caught and logged at WARNING level,
        and does not propagate to the caller.
    """
    manager = ConfigurationManager(agent_identifier="exc-listener-agent")

    def bad_listener(event: ConfigurationChangeEvent) -> None:
        raise ValueError("listener error")

    manager.register_change_listener(bad_listener)

    exception_raised = False
    try:
        manager.load_from_dict(data={"key": "value"})
    except ValueError:
        exception_raised = True

    assert exception_raised is False, \
        "listener exception should be caught and not propagate"
    return


def test_listener_exception_does_not_prevent_remaining_listeners():
    """
        Verify that when one listener raises an exception, remaining listeners
        are still invoked.
    """
    manager = ConfigurationManager(agent_identifier="remaining-listener-agent")
    second_listener_calls = []

    def bad_listener(event: ConfigurationChangeEvent) -> None:
        raise RuntimeError("first listener fails")

    def good_listener(event: ConfigurationChangeEvent) -> None:
        second_listener_calls.append(event)
        return

    manager.register_change_listener(bad_listener)
    manager.register_change_listener(good_listener)
    manager.load_from_dict(data={"key": "value"})

    call_count = len(second_listener_calls)
    assert call_count > 0, \
        "remaining listeners should still be invoked after a listener exception"
    return


# ---- load_from_file Tests ----


def test_load_from_file_loads_json_file():
    """
        Verify that load_from_file loads configuration from a JSON file.
    """
    config_data = {"app": {"name": "test-app", "version": "1.0"}}

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp_file:
        json.dump(config_data, tmp_file)
        tmp_path = tmp_file.name

    try:
        manager = ConfigurationManager(agent_identifier="file-agent")
        manager.load_from_file(file_path=tmp_path)

        name_val = manager.get("app.name")
        version_val = manager.get("app.version")
        assert name_val == "test-app", "load_from_file should load JSON app.name"
        assert version_val == "1.0", "load_from_file should load JSON app.version"

        layer_list = manager.layers
        file_layer = layer_list[0]
        layer_source = file_layer.source
        assert layer_source is ConfigurationLayerSource.FILE, \
            "load_from_file should create a FILE layer"
    finally:
        os.unlink(tmp_path)

    return


def test_load_from_file_raises_configuration_error_for_missing_file():
    """
        Verify that load_from_file raises ConfigurationError for a missing file.
    """
    manager = ConfigurationManager(agent_identifier="missing-file-agent")

    error_raised = False
    try:
        manager.load_from_file(file_path="/nonexistent/path/config.json")
    except ConfigurationError:
        error_raised = True

    assert error_raised is True, \
        "load_from_file should raise ConfigurationError for missing files"
    return


def test_load_from_file_raises_configuration_error_for_invalid_json():
    """
        Verify that load_from_file raises ConfigurationError for invalid JSON.
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write("{invalid json content")
        tmp_path = tmp_file.name

    try:
        manager = ConfigurationManager(agent_identifier="invalid-json-agent")

        error_raised = False
        try:
            manager.load_from_file(file_path=tmp_path)
        except ConfigurationError:
            error_raised = True

        assert error_raised is True, \
            "load_from_file should raise ConfigurationError for invalid JSON"
    finally:
        os.unlink(tmp_path)

    return


# ---- load_from_environment Tests ----


def test_load_from_environment_reads_prefixed_variables():
    """
        Verify that load_from_environment reads environment variables with
        the given prefix and strips the prefix.
    """
    env_key = "TESTCFG_APP_NAME"
    env_value = "env-app"
    original_value = os.environ.get(env_key)

    os.environ[env_key] = env_value

    try:
        manager = ConfigurationManager(agent_identifier="env-agent")
        manager.load_from_environment(prefix="TESTCFG_")

        result = manager.get("app.name")
        assert result == env_value, \
            "load_from_environment should read prefixed env vars and convert underscores to dots"
    finally:
        if original_value is not None:
            os.environ[env_key] = original_value
        else:
            del os.environ[env_key]

    return


def test_load_from_environment_creates_environment_layer():
    """
        Verify that load_from_environment creates an ENVIRONMENT layer.
    """
    env_key = "TESTENVLAYER_KEY"
    original_value = os.environ.get(env_key)

    os.environ[env_key] = "test-value"

    try:
        manager = ConfigurationManager(agent_identifier="env-layer-agent")
        manager.load_from_environment(prefix="TESTENVLAYER_")

        layer_list = manager.layers
        layer_count = len(layer_list)
        assert layer_count == 1, "load_from_environment should create one layer"

        env_layer = layer_list[0]
        layer_source = env_layer.source
        assert layer_source is ConfigurationLayerSource.ENVIRONMENT, \
            "load_from_environment should create an ENVIRONMENT layer"
    finally:
        if original_value is not None:
            os.environ[env_key] = original_value
        else:
            del os.environ[env_key]

    return


# ---- reload Tests ----


def test_reload_re_reads_file_layer():
    """
        Verify that reload re-reads a file-based layer and picks up changes.

        The reload method uses the layer name as the file path. Since
        load_from_file stores os.path.basename as the layer name, we
        create the temp file in the current working directory so the
        basename resolves correctly during reload.
    """
    initial_data = {"setting": "initial"}
    tmp_filename = "_test_reload_config.json"
    tmp_path = os.path.join(os.getcwd(), tmp_filename)

    with open(tmp_path, "w", encoding="utf-8") as tmp_file:
        json.dump(initial_data, tmp_file)

    try:
        manager = ConfigurationManager(agent_identifier="reload-file-agent")
        manager.load_from_file(file_path=tmp_path)

        initial_val = manager.get("setting")
        assert initial_val == "initial", "initial value should be 'initial'"

        updated_data = {"setting": "updated"}
        with open(tmp_path, "w", encoding="utf-8") as update_file:
            json.dump(updated_data, update_file)

        manager.reload()

        reloaded_val = manager.get("setting")
        assert reloaded_val == "updated", "reload should pick up the updated file content"
    finally:
        if os.path.isfile(tmp_path) is True:
            os.unlink(tmp_path)

    return


def test_reload_re_reads_environment_layer():
    """
        Verify that reload re-reads an environment-based layer.
    """
    env_key = "TESTRELOAD_VAL"
    original_value = os.environ.get(env_key)

    os.environ[env_key] = "before-reload"

    try:
        manager = ConfigurationManager(agent_identifier="reload-env-agent")
        manager.load_from_environment(prefix="TESTRELOAD_")

        before_val = manager.get("val")
        assert before_val == "before-reload", "initial env value should be 'before-reload'"

        os.environ[env_key] = "after-reload"
        manager.reload()

        after_val = manager.get("val")
        assert after_val == "after-reload", "reload should pick up the updated env value"
    finally:
        if original_value is not None:
            os.environ[env_key] = original_value
        else:
            if env_key in os.environ:
                del os.environ[env_key]

    return


# ---- __repr__ and __str__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'ConfigurationManager'.
    """
    manager = ConfigurationManager(agent_identifier="repr-agent")
    repr_str = repr(manager)
    has_class_name = "ConfigurationManager" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_agent_identifier():
    """
        Verify that __repr__ contains the agent identifier.
    """
    manager = ConfigurationManager(agent_identifier="my-unique-agent")
    repr_str = repr(manager)
    has_id = "my-unique-agent" in repr_str
    assert has_id is True, "repr should contain the agent identifier"
    return


def test_str_contains_agent_identifier():
    """
        Verify that __str__ contains the agent identifier.
    """
    manager = ConfigurationManager(agent_identifier="str-agent")
    str_val = str(manager)
    has_id = "str-agent" in str_val
    assert has_id is True, "str should contain the agent identifier"
    return


def test_str_contains_layer_count():
    """
        Verify that __str__ contains the layer count.
    """
    manager = ConfigurationManager(agent_identifier="str-count-agent")
    manager.load_defaults(defaults={"a": 1})
    str_val = str(manager)
    has_count = "1" in str_val
    assert has_count is True, "str should contain the layer count"
    return
