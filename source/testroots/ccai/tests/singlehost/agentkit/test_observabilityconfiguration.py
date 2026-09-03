"""
    Unit tests for the ccai.agentkit.observabilityconfiguration module.

    Tests the ObservabilityConfiguration class: construction, defaults,
    validation errors (invalid log_level, log_format, sampling_rate),
    serialization (JSON and YAML), credential exclusion from serialization,
    and file loading with mocked AppContext.
"""

import json
import os
import tempfile

from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.observabilityconfiguration import ObservabilityConfiguration
from ccai.testbase.mocking import Mock


def test_construction_with_defaults():
    """
        Verify that default values are applied when no arguments are provided.
    """
    config = ObservabilityConfiguration()

    assert config.log_level == "info", "Default log_level should be 'info'"
    assert config.log_format == "human_readable", "Default log_format should be 'human_readable'"
    assert config.tracing_enabled is False, "Default tracing_enabled should be False"
    assert config.metrics_enabled is False, "Default metrics_enabled should be False"
    assert config.recording_enabled is False, "Default recording_enabled should be False"
    assert config.debug_mode_enabled is False, "Default debug_mode_enabled should be False"
    assert config.sampling_rate == 1.0, "Default sampling_rate should be 1.0"
    assert config.exporter_settings == {}, "Default exporter_settings should be empty dict"
    return


def test_construction_with_all_arguments():
    """
        Verify that all provided arguments are stored correctly.
    """
    exporter_settings = {"log_exporters": ["console"]}
    config = ObservabilityConfiguration(
        log_level="debug",
        log_format="json",
        tracing_enabled=True,
        metrics_enabled=True,
        recording_enabled=True,
        debug_mode_enabled=True,
        sampling_rate=0.5,
        exporter_settings=exporter_settings,
    )

    assert config.log_level == "debug", "log_level should be 'debug'"
    assert config.log_format == "json", "log_format should be 'json'"
    assert config.tracing_enabled is True, "tracing_enabled should be True"
    assert config.metrics_enabled is True, "metrics_enabled should be True"
    assert config.recording_enabled is True, "recording_enabled should be True"
    assert config.debug_mode_enabled is True, "debug_mode_enabled should be True"
    assert config.sampling_rate == 0.5, "sampling_rate should be 0.5"
    assert config.exporter_settings == exporter_settings, "exporter_settings should match"
    return


def test_all_valid_log_levels_accepted():
    """
        Verify that all valid log levels are accepted without error.
    """
    for level in ObservabilityConfiguration.VALID_LOG_LEVELS:
        config = ObservabilityConfiguration(log_level=level)
        assert config.log_level == level, "log_level should be {}".format(level)

    return


def test_all_valid_log_formats_accepted():
    """
        Verify that all valid log formats are accepted without error.
    """
    for fmt in ObservabilityConfiguration.VALID_LOG_FORMATS:
        config = ObservabilityConfiguration(log_format=fmt)
        assert config.log_format == fmt, "log_format should be {}".format(fmt)

    return


def test_invalid_log_level_raises_configuration_error():
    """
        Verify that an invalid log_level raises ConfigurationError.
    """
    raised = False
    try:
        ObservabilityConfiguration(log_level="verbose")
    except ConfigurationError:
        raised = True

    assert raised is True, "Invalid log_level should raise ConfigurationError"
    return


def test_invalid_log_level_error_message_contains_value():
    """
        Verify that the ConfigurationError message contains the invalid log level.
    """
    try:
        ObservabilityConfiguration(log_level="verbose")
    except ConfigurationError as err:
        assert "verbose" in str(err), "Error message should contain the invalid log level"
    return


def test_invalid_log_format_raises_configuration_error():
    """
        Verify that an invalid log_format raises ConfigurationError.
    """
    raised = False
    try:
        ObservabilityConfiguration(log_format="xml")
    except ConfigurationError:
        raised = True

    assert raised is True, "Invalid log_format should raise ConfigurationError"
    return


def test_invalid_log_format_error_message_contains_value():
    """
        Verify that the ConfigurationError message contains the invalid log format.
    """
    try:
        ObservabilityConfiguration(log_format="xml")
    except ConfigurationError as err:
        assert "xml" in str(err), "Error message should contain the invalid log format"
    return


def test_sampling_rate_below_zero_raises_configuration_error():
    """
        Verify that a sampling_rate below 0.0 raises ConfigurationError.
    """
    raised = False
    try:
        ObservabilityConfiguration(sampling_rate=-0.1)
    except ConfigurationError:
        raised = True

    assert raised is True, "Sampling rate below 0.0 should raise ConfigurationError"
    return


def test_sampling_rate_above_one_raises_configuration_error():
    """
        Verify that a sampling_rate above 1.0 raises ConfigurationError.
    """
    raised = False
    try:
        ObservabilityConfiguration(sampling_rate=1.1)
    except ConfigurationError:
        raised = True

    assert raised is True, "Sampling rate above 1.0 should raise ConfigurationError"
    return


def test_sampling_rate_boundary_zero_accepted():
    """
        Verify that sampling_rate of 0.0 is accepted.
    """
    config = ObservabilityConfiguration(sampling_rate=0.0)
    assert config.sampling_rate == 0.0, "sampling_rate 0.0 should be accepted"
    return


def test_sampling_rate_boundary_one_accepted():
    """
        Verify that sampling_rate of 1.0 is accepted.
    """
    config = ObservabilityConfiguration(sampling_rate=1.0)
    assert config.sampling_rate == 1.0, "sampling_rate 1.0 should be accepted"
    return


def test_as_dict_returns_all_fields():
    """
        Verify that as_dict returns a dictionary with all configuration fields.
    """
    config = ObservabilityConfiguration(
        log_level="warning",
        log_format="json",
        tracing_enabled=True,
        metrics_enabled=True,
        recording_enabled=False,
        debug_mode_enabled=False,
        sampling_rate=0.75,
        exporter_settings={"log_exporters": ["console"]},
    )

    result = config.as_dict()

    assert result["log_level"] == "warning", "as_dict log_level should be warning"
    assert result["log_format"] == "json", "as_dict log_format should be json"
    assert result["tracing_enabled"] is True, "as_dict tracing_enabled should be True"
    assert result["metrics_enabled"] is True, "as_dict metrics_enabled should be True"
    assert result["recording_enabled"] is False, "as_dict recording_enabled should be False"
    assert result["debug_mode_enabled"] is False, "as_dict debug_mode_enabled should be False"
    assert result["sampling_rate"] == 0.75, "as_dict sampling_rate should be 0.75"
    assert "exporter_settings" in result, "as_dict should contain exporter_settings"
    return


def test_credential_manager_missing_key_raises_configuration_error():
    """
        Verify that a real CredentialManager missing the key is translated
        into the kit's ConfigurationError carrying the credential name.

        CredentialManager.lookup_credential raises the core
        ConfigurationError, which derives from BaseException; a bare
        ``except Exception`` would let it escape untranslated.
    """
    from ccai.credentials.credentialmanager import CredentialManager

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("credential_manager", CredentialManager())

    raised = False
    error_message = ""
    try:
        ObservabilityConfiguration.from_dict(
            {"credentials": {"api_key": {"provider": "vault", "key": "nonexistent-key"}}},
            app_context=mock_app_context,
        )
    except ConfigurationError as exc:
        raised = True
        error_message = exc.message

    assert raised is True, (
        "Expected the kit's ConfigurationError when the CredentialManager "
        "has no such key"
    )
    assert "api_key" in error_message and "nonexistent-key" in error_message
    return


def test_as_dict_excludes_resolved_credentials():
    """
        Verify that as_dict does not include resolved credential secret values.
    """
    config = ObservabilityConfiguration(
        credentials={"api_key": {"provider": "vault", "key": "my-key"}},
        resolved_credentials={"api_key": "super-secret-value-12345"},
    )

    result = config.as_dict()

    result_str = json.dumps(result)
    assert "super-secret-value-12345" not in result_str, (
        "as_dict should not contain resolved credential secret values"
    )
    return


def test_to_json_produces_valid_json():
    """
        Verify that to_json produces a valid JSON string.
    """
    config = ObservabilityConfiguration(log_level="error", log_format="key_value")

    json_str = config.to_json()
    parsed = json.loads(json_str)

    assert parsed["log_level"] == "error", "JSON log_level should be error"
    assert parsed["log_format"] == "key_value", "JSON log_format should be key_value"
    return


def test_to_json_excludes_resolved_credentials():
    """
        Verify that to_json does not include resolved credential secret values.
    """
    config = ObservabilityConfiguration(
        credentials={"api_key": {"provider": "vault", "key": "my-key"}},
        resolved_credentials={"api_key": "secret-token-xyz"},
    )

    json_str = config.to_json()

    assert "secret-token-xyz" not in json_str, (
        "to_json should not contain resolved credential secret values"
    )
    return


def test_to_yaml_produces_valid_yaml():
    """
        Verify that to_yaml produces a valid YAML string.
    """
    import yaml

    config = ObservabilityConfiguration(log_level="critical", log_format="json")

    yaml_str = config.to_yaml()
    parsed = yaml.safe_load(yaml_str)

    assert parsed["log_level"] == "critical", "YAML log_level should be critical"
    assert parsed["log_format"] == "json", "YAML log_format should be json"
    return


def test_to_yaml_excludes_resolved_credentials():
    """
        Verify that to_yaml does not include resolved credential secret values.
    """
    config = ObservabilityConfiguration(
        credentials={"api_key": {"provider": "vault", "key": "my-key"}},
        resolved_credentials={"api_key": "yaml-secret-value"},
    )

    yaml_str = config.to_yaml()

    assert "yaml-secret-value" not in yaml_str, (
        "to_yaml should not contain resolved credential secret values"
    )
    return


def test_from_dict_creates_valid_configuration():
    """
        Verify that from_dict creates a valid ObservabilityConfiguration.
    """
    data = {
        "log_level": "debug",
        "log_format": "json",
        "tracing_enabled": True,
        "metrics_enabled": False,
        "sampling_rate": 0.5,
    }

    config = ObservabilityConfiguration.from_dict(data)

    assert config.log_level == "debug", "from_dict log_level should be debug"
    assert config.log_format == "json", "from_dict log_format should be json"
    assert config.tracing_enabled is True, "from_dict tracing_enabled should be True"
    assert config.sampling_rate == 0.5, "from_dict sampling_rate should be 0.5"
    return


def test_from_dict_applies_defaults():
    """
        Verify that from_dict applies defaults for missing fields.
    """
    data = {}

    config = ObservabilityConfiguration.from_dict(data)

    assert config.log_level == "info", "from_dict default log_level should be info"
    assert config.log_format == "human_readable", "from_dict default log_format should be human_readable"
    assert config.tracing_enabled is False, "from_dict default tracing_enabled should be False"
    return


def test_from_dict_invalid_log_level_raises_error():
    """
        Verify that from_dict raises ConfigurationError for invalid log_level.
    """
    data = {"log_level": "trace"}

    raised = False
    try:
        ObservabilityConfiguration.from_dict(data)
    except ConfigurationError:
        raised = True

    assert raised is True, "from_dict with invalid log_level should raise ConfigurationError"
    return


def test_from_json_creates_valid_configuration():
    """
        Verify that from_json creates a valid ObservabilityConfiguration.
    """
    data = {"log_level": "warning", "log_format": "key_value", "sampling_rate": 0.8}
    json_str = json.dumps(data)

    config = ObservabilityConfiguration.from_json(json_str)

    assert config.log_level == "warning", "from_json log_level should be warning"
    assert config.log_format == "key_value", "from_json log_format should be key_value"
    assert config.sampling_rate == 0.8, "from_json sampling_rate should be 0.8"
    return


def test_from_json_invalid_json_raises_error():
    """
        Verify that from_json raises ConfigurationError for invalid JSON.
    """
    raised = False
    try:
        ObservabilityConfiguration.from_json("not valid json{{{")
    except ConfigurationError:
        raised = True

    assert raised is True, "from_json with invalid JSON should raise ConfigurationError"
    return


def test_from_yaml_creates_valid_configuration():
    """
        Verify that from_yaml creates a valid ObservabilityConfiguration.
    """
    yaml_str = "log_level: error\nlog_format: json\nsampling_rate: 0.3\n"

    config = ObservabilityConfiguration.from_yaml(yaml_str)

    assert config.log_level == "error", "from_yaml log_level should be error"
    assert config.log_format == "json", "from_yaml log_format should be json"
    assert config.sampling_rate == 0.3, "from_yaml sampling_rate should be 0.3"
    return


def test_json_round_trip():
    """
        Verify that to_json then from_json produces equivalent configuration.
    """
    original = ObservabilityConfiguration(
        log_level="debug",
        log_format="json",
        tracing_enabled=True,
        metrics_enabled=True,
        recording_enabled=True,
        debug_mode_enabled=True,
        sampling_rate=0.42,
        exporter_settings={"log_exporters": ["console"]},
    )

    json_str = original.to_json()
    restored = ObservabilityConfiguration.from_json(json_str)

    assert restored.as_dict() == original.as_dict(), "JSON round-trip should produce equal as_dict"
    return


def test_yaml_round_trip():
    """
        Verify that to_yaml then from_yaml produces equivalent configuration.
    """
    original = ObservabilityConfiguration(
        log_level="warning",
        log_format="key_value",
        tracing_enabled=False,
        metrics_enabled=True,
        recording_enabled=False,
        debug_mode_enabled=False,
        sampling_rate=0.9,
        exporter_settings={"trace_exporters": ["file"]},
    )

    yaml_str = original.to_yaml()
    restored = ObservabilityConfiguration.from_yaml(yaml_str)

    assert restored.as_dict() == original.as_dict(), "YAML round-trip should produce equal as_dict"
    return


def test_from_json_file_loads_configuration():
    """
        Verify that from_json_file loads configuration from a JSON file.
    """
    data = {"log_level": "critical", "log_format": "json", "sampling_rate": 0.1}
    json_str = json.dumps(data)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp.write(json_str)
        tmp_path = tmp.name

    try:
        config = ObservabilityConfiguration.from_json_file(tmp_path)
        assert config.log_level == "critical", "from_json_file log_level should be critical"
        assert config.sampling_rate == 0.1, "from_json_file sampling_rate should be 0.1"
    finally:
        os.unlink(tmp_path)

    return


def test_from_yaml_file_loads_configuration():
    """
        Verify that from_yaml_file loads configuration from a YAML file.
    """
    yaml_content = "log_level: debug\nlog_format: key_value\nsampling_rate: 0.6\n"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write(yaml_content)
        tmp_path = tmp.name

    try:
        config = ObservabilityConfiguration.from_yaml_file(tmp_path)
        assert config.log_level == "debug", "from_yaml_file log_level should be debug"
        assert config.sampling_rate == 0.6, "from_yaml_file sampling_rate should be 0.6"
    finally:
        os.unlink(tmp_path)

    return


def test_from_json_file_with_app_context():
    """
        Verify that from_json_file resolves path relative to AppContext directory.
    """
    data = {"log_level": "info", "log_format": "human_readable"}
    json_str = json.dumps(data)

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "config.json")
        with open(file_path, "w") as fh:
            fh.write(json_str)

        mock_app_context = Mock()
        mock_app_context.configure(recursive=True)
        ctx = mock_app_context.mock_context()
        ctx.set_attribute("directory", tmpdir)

        config = ObservabilityConfiguration.from_json_file("config.json", app_context=mock_app_context)
        assert config.log_level == "info", "from_json_file with app_context should load correctly"

    return


def test_from_yaml_file_with_app_context():
    """
        Verify that from_yaml_file resolves path relative to AppContext directory.
    """
    yaml_content = "log_level: error\nlog_format: json\n"

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "config.yaml")
        with open(file_path, "w") as fh:
            fh.write(yaml_content)

        mock_app_context = Mock()
        mock_app_context.configure(recursive=True)
        ctx = mock_app_context.mock_context()
        ctx.set_attribute("directory", tmpdir)

        config = ObservabilityConfiguration.from_yaml_file("config.yaml", app_context=mock_app_context)
        assert config.log_level == "error", "from_yaml_file with app_context should load correctly"

    return


def test_from_json_file_missing_file_raises_error():
    """
        Verify that from_json_file raises ConfigurationError for missing file.
    """
    raised = False
    try:
        ObservabilityConfiguration.from_json_file("/nonexistent/path/config.json")
    except ConfigurationError:
        raised = True

    assert raised is True, "from_json_file with missing file should raise ConfigurationError"
    return


def test_from_yaml_file_missing_file_raises_error():
    """
        Verify that from_yaml_file raises ConfigurationError for missing file.
    """
    raised = False
    try:
        ObservabilityConfiguration.from_yaml_file("/nonexistent/path/config.yaml")
    except ConfigurationError:
        raised = True

    assert raised is True, "from_yaml_file with missing file should raise ConfigurationError"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    config = ObservabilityConfiguration()

    repr_str = repr(config)
    assert "ObservabilityConfiguration" in repr_str, "__repr__ should contain class name"
    return


def test_repr_contains_log_level_and_format():
    """
        Verify that __repr__ contains the log level and format.
    """
    config = ObservabilityConfiguration(log_level="error", log_format="json")

    repr_str = repr(config)
    assert "error" in repr_str, "__repr__ should contain log_level"
    assert "json" in repr_str, "__repr__ should contain log_format"
    return


def test_str_contains_all_settings():
    """
        Verify that __str__ contains all configuration settings.
    """
    config = ObservabilityConfiguration(
        log_level="debug",
        log_format="key_value",
        tracing_enabled=True,
        metrics_enabled=True,
        sampling_rate=0.5,
    )

    str_val = str(config)
    assert "debug" in str_val, "__str__ should contain log_level"
    assert "key_value" in str_val, "__str__ should contain log_format"
    assert "True" in str_val, "__str__ should contain enabled status"
    return


def test_exporter_settings_returns_defensive_copy():
    """
        Verify that exporter_settings returns a defensive copy.
    """
    original_settings = {"log_exporters": ["console"]}
    config = ObservabilityConfiguration(exporter_settings=original_settings)

    returned = config.exporter_settings
    returned["new_key"] = "new_value"

    assert "new_key" not in config.exporter_settings, (
        "Modifying returned exporter_settings should not affect internal state"
    )
    return