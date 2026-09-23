"""
    Unit tests for the ccai.agentkit.configurationerrors module.

    Tests the ConfigurationValidationError and PluginLoadError exception classes.
"""

from ccai.agentkit.configurationerrors import ConfigurationValidationError
from ccai.agentkit.configurationerrors import PluginLoadError
from ccai.agentkit.errors import AgentKitError


# ---- ConfigurationValidationError Tests ----


def test_configuration_validation_error_inherits_from_agentkit_error():
    """
        Verify that ConfigurationValidationError inherits from AgentKitError.
    """
    err = ConfigurationValidationError("test-schema", ["error one"])
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "ConfigurationValidationError should inherit from AgentKitError"
    return


def test_configuration_validation_error_schema_name_property():
    """
        Verify that schema_name property returns the correct value.
    """
    err = ConfigurationValidationError("my-schema", ["some error"])
    schema_name = err.schema_name
    assert schema_name == "my-schema", "schema_name should return the provided schema name"
    return


def test_configuration_validation_error_errors_property():
    """
        Verify that errors property returns the list of errors.
    """
    error_list = ["field missing", "type mismatch"]
    err = ConfigurationValidationError("schema-a", error_list)
    errors = err.errors
    assert errors == ["field missing", "type mismatch"], "errors should return the provided error list"
    return


def test_configuration_validation_error_warnings_empty_by_default():
    """
        Verify that warnings property returns an empty list when not provided.
    """
    err = ConfigurationValidationError("schema-b", ["an error"])
    warnings = err.warnings
    assert warnings == [], "warnings should be an empty list when not provided"
    return


def test_configuration_validation_error_warnings_property():
    """
        Verify that warnings property returns the list when provided.
    """
    err = ConfigurationValidationError("schema-c", ["err"], warnings=["warn one", "warn two"])
    warnings = err.warnings
    assert warnings == ["warn one", "warn two"], "warnings should return the provided warning list"
    return


def test_configuration_validation_error_message_contains_schema_name():
    """
        Verify that the error message contains the schema name.
    """
    err = ConfigurationValidationError("agent-config", ["bad field"])
    message = err.message
    has_schema_name = "agent-config" in message
    assert has_schema_name is True, "error message should contain the schema name"
    return


def test_configuration_validation_error_message_contains_error_items():
    """
        Verify that the error message contains each error item.
    """
    error_list = ["missing required field 'name'", "invalid type for 'port'"]
    err = ConfigurationValidationError("schema-d", error_list)
    message = err.message
    has_first_error = "missing required field 'name'" in message
    has_second_error = "invalid type for 'port'" in message
    assert has_first_error is True, "error message should contain the first error item"
    assert has_second_error is True, "error message should contain the second error item"
    return


def test_configuration_validation_error_message_contains_warning_items():
    """
        Verify that the error message contains warning items when present.
    """
    err = ConfigurationValidationError(
        "schema-e", ["an error"], warnings=["deprecated field 'old_name'"]
    )
    message = err.message
    has_warning = "deprecated field 'old_name'" in message
    assert has_warning is True, "error message should contain the warning item"
    return


def test_configuration_validation_error_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    err = ConfigurationValidationError("repr-schema", ["err"])
    repr_str = repr(err)
    has_class_name = "ConfigurationValidationError" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_configuration_validation_error_repr_contains_schema_name():
    """
        Verify that __repr__ contains the schema_name.
    """
    err = ConfigurationValidationError("repr-schema", ["err"])
    repr_str = repr(err)
    has_schema_name = "repr-schema" in repr_str
    assert has_schema_name is True, "repr should contain the schema name"
    return


def test_configuration_validation_error_repr_contains_error_count():
    """
        Verify that __repr__ contains the error count.
    """
    err = ConfigurationValidationError("count-schema", ["e1", "e2", "e3"])
    repr_str = repr(err)
    has_error_count = "error_count=3" in repr_str
    assert has_error_count is True, "repr should contain the error count"
    return


def test_configuration_validation_error_errors_returns_defensive_copy():
    """
        Verify that errors property returns a defensive copy.
    """
    err = ConfigurationValidationError("copy-schema", ["original error"])
    errors_first = err.errors
    errors_first.append("injected error")
    errors_second = err.errors
    has_injected = "injected error" in errors_second
    assert has_injected is False, "errors should return a defensive copy, not the internal list"
    return


def test_configuration_validation_error_warnings_returns_defensive_copy():
    """
        Verify that warnings property returns a defensive copy.
    """
    err = ConfigurationValidationError("copy-schema", ["err"], warnings=["original warning"])
    warnings_first = err.warnings
    warnings_first.append("injected warning")
    warnings_second = err.warnings
    has_injected = "injected warning" in warnings_second
    assert has_injected is False, "warnings should return a defensive copy, not the internal list"
    return


# ---- PluginLoadError Tests ----


def test_plugin_load_error_inherits_from_agentkit_error():
    """
        Verify that PluginLoadError inherits from AgentKitError.
    """
    err = PluginLoadError("my-plugin", "failed to initialize")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "PluginLoadError should inherit from AgentKitError"
    return


def test_plugin_load_error_plugin_name_property():
    """
        Verify that plugin_name property returns the correct value.
    """
    err = PluginLoadError("auth-plugin", "module not found")
    plugin_name = err.plugin_name
    assert plugin_name == "auth-plugin", "plugin_name should return the provided plugin name"
    return


def test_plugin_load_error_cause_is_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = PluginLoadError("some-plugin", "load failed")
    cause = err.cause
    assert cause is None, "cause should be None when not provided"
    return


def test_plugin_load_error_cause_preserves_exception():
    """
        Verify that cause property returns the provided cause exception.
    """
    original = ImportError("no module named 'foo'")
    err = PluginLoadError("foo-plugin", "import failed", cause=original)
    cause = err.cause
    assert cause is original, "cause should be the original exception"
    return


def test_plugin_load_error_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    err = PluginLoadError("repr-plugin", "something broke")
    repr_str = repr(err)
    has_class_name = "PluginLoadError" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_plugin_load_error_repr_contains_plugin_name():
    """
        Verify that __repr__ contains the plugin_name.
    """
    err = PluginLoadError("repr-plugin", "something broke")
    repr_str = repr(err)
    has_plugin_name = "repr-plugin" in repr_str
    assert has_plugin_name is True, "repr should contain the plugin name"
    return


def test_plugin_load_error_message_contains_plugin_name():
    """
        Verify that the error message contains the plugin name.
    """
    err = PluginLoadError("msg-plugin", "dependency missing")
    message = err.message
    has_plugin_name = "msg-plugin" in message
    assert has_plugin_name is True, "error message should contain the plugin name"
    return


def test_plugin_load_error_catchable_as_agentkit_error():
    """
        Verify that PluginLoadError can be caught as AgentKitError.
    """
    caught = False
    try:
        raise PluginLoadError("catch-plugin", "test catch")
    except AgentKitError:
        caught = True

    assert caught is True, "PluginLoadError should be catchable as AgentKitError"
    return
