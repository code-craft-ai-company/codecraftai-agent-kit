"""
    Unit tests for the ccai.agentkit.configurationserializer module.

    Tests the ConfigurationSerializer class including JSON and YAML round-trip
    serialization, error handling for invalid input, credential filtering,
    and string representations.
"""

import json

from ccai.agentkit.configurationserializer import ConfigurationSerializer
from ccai.agentkit.errors import ConfigurationError


# ---- JSON Serialization Tests ----


def test_to_json_produces_valid_json_for_simple_dict():
    """
        Verify that to_json returns a valid JSON string for a simple dictionary.
    """
    serializer = ConfigurationSerializer()
    config = {"name": "agent-1", "timeout": 30}
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict), "to_json should produce a valid JSON string"
    return


def test_from_json_parses_valid_json():
    """
        Verify that from_json returns a dictionary from a valid JSON string.
    """
    serializer = ConfigurationSerializer()
    json_str = '{"name": "agent-1", "timeout": 30}'
    result = serializer.from_json(json_str)
    assert result["name"] == "agent-1", "from_json should parse the name field"
    assert result["timeout"] == 30, "from_json should parse the timeout field"
    return


def test_to_json_from_json_round_trip_with_nested_dict():
    """
        Verify that to_json followed by from_json preserves nested dictionary
        structures when no credential keys are present.
    """
    serializer = ConfigurationSerializer()
    config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "options": {"ssl": True, "timeout": 10}
        },
        "logging": {"level": "INFO"}
    }
    json_str = serializer.to_json(config)
    restored = serializer.from_json(json_str)
    assert restored == config, "round-trip should preserve nested dictionary structures"
    return


def test_from_json_raises_configuration_error_for_invalid_json():
    """
        Verify that from_json raises ConfigurationError for invalid JSON input.
    """
    serializer = ConfigurationSerializer()
    raised = False
    try:
        serializer.from_json("{invalid json content")
    except ConfigurationError:
        raised = True
    assert raised is True, "from_json should raise ConfigurationError for invalid JSON"
    return


# ---- YAML Serialization Tests ----


def test_to_yaml_produces_valid_yaml_for_simple_dict():
    """
        Verify that to_yaml returns a valid YAML string for a simple dictionary.
    """
    serializer = ConfigurationSerializer()
    config = {"name": "agent-1", "timeout": 30}
    yaml_str = serializer.to_yaml(config)
    assert isinstance(yaml_str, str), "to_yaml should return a string"
    assert len(yaml_str) > 0, "to_yaml should return a non-empty string"
    return


def test_from_yaml_parses_valid_yaml():
    """
        Verify that from_yaml returns a dictionary from a valid YAML string.
    """
    serializer = ConfigurationSerializer()
    yaml_str = "name: agent-1\ntimeout: 30\n"
    result = serializer.from_yaml(yaml_str)
    assert result["name"] == "agent-1", "from_yaml should parse the name field"
    assert result["timeout"] == 30, "from_yaml should parse the timeout field"
    return


def test_to_yaml_from_yaml_round_trip_with_nested_dict():
    """
        Verify that to_yaml followed by from_yaml preserves nested dictionary
        structures when no credential keys are present.
    """
    serializer = ConfigurationSerializer()
    config = {
        "database": {
            "host": "localhost",
            "port": 5432
        },
        "logging": {"level": "INFO"}
    }
    yaml_str = serializer.to_yaml(config)
    restored = serializer.from_yaml(yaml_str)
    assert restored == config, "round-trip should preserve nested dictionary structures"
    return


def test_from_yaml_raises_configuration_error_for_invalid_yaml():
    """
        Verify that from_yaml raises ConfigurationError for invalid YAML input.
    """
    serializer = ConfigurationSerializer()
    raised = False
    try:
        serializer.from_yaml(":\n  :\n    - :\n  invalid: [unterminated")
    except ConfigurationError:
        raised = True
    assert raised is True, "from_yaml should raise ConfigurationError for invalid YAML"
    return


def test_from_yaml_returns_empty_dict_for_empty_yaml():
    """
        Verify that from_yaml returns an empty dictionary for empty YAML input.
    """
    serializer = ConfigurationSerializer()
    result = serializer.from_yaml("")
    assert result == {}, "from_yaml should return an empty dict for empty YAML"
    return


# ---- Credential Filtering Tests ----


def test_credential_key_password_is_redacted_in_to_json():
    """
        Verify that keys containing 'password' are redacted in to_json output.
    """
    serializer = ConfigurationSerializer()
    config = {"db_password": "secret123", "host": "localhost"}
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["db_password"] == "[REDACTED]", "password key should be redacted"
    assert parsed["host"] == "localhost", "non-credential key should be preserved"
    return


def test_credential_key_secret_is_redacted_in_to_json():
    """
        Verify that keys containing 'secret' are redacted in to_json output.
    """
    serializer = ConfigurationSerializer()
    config = {"api_secret": "abc123", "name": "agent-1"}
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["api_secret"] == "[REDACTED]", "secret key should be redacted"
    assert parsed["name"] == "agent-1", "non-credential key should be preserved"
    return


def test_credential_key_token_is_redacted_in_to_json():
    """
        Verify that keys containing 'token' are redacted in to_json output.
    """
    serializer = ConfigurationSerializer()
    config = {"auth_token": "tok-xyz", "timeout": 30}
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["auth_token"] == "[REDACTED]", "token key should be redacted"
    assert parsed["timeout"] == 30, "non-credential key should be preserved"
    return


def test_credential_key_credential_is_redacted_in_to_json():
    """
        Verify that keys containing 'credential' are redacted in to_json output.
    """
    serializer = ConfigurationSerializer()
    config = {"user_credential": "cred-abc", "host": "localhost"}
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["user_credential"] == "[REDACTED]", "credential key should be redacted"
    assert parsed["host"] == "localhost", "non-credential key should be preserved"
    return


def test_nested_credential_keys_are_redacted():
    """
        Verify that credential keys nested inside sub-dictionaries are redacted.
    """
    serializer = ConfigurationSerializer()
    config = {
        "database": {
            "host": "localhost",
            "password": "secret123"
        }
    }
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["database"]["password"] == "[REDACTED]", \
        "nested password key should be redacted"
    assert parsed["database"]["host"] == "localhost", \
        "nested non-credential key should be preserved"
    return


def test_values_with_resolved_key_are_redacted():
    """
        Verify that dict values containing a '_resolved' key are replaced
        with the redacted placeholder.
    """
    serializer = ConfigurationSerializer()
    config = {
        "api_key_ref": {"_resolved": True, "value": "real-secret"},
        "host": "localhost"
    }
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["api_key_ref"] == "[REDACTED]", \
        "value with _resolved key should be redacted"
    assert parsed["host"] == "localhost", "non-credential key should be preserved"
    return


def test_non_credential_keys_are_preserved():
    """
        Verify that keys not matching credential patterns are preserved in output.
    """
    serializer = ConfigurationSerializer()
    config = {
        "name": "agent-1",
        "timeout": 30,
        "enabled": True,
        "tags": ["a", "b"]
    }
    json_str = serializer.to_json(config)
    parsed = json.loads(json_str)
    assert parsed["name"] == "agent-1", "name should be preserved"
    assert parsed["timeout"] == 30, "timeout should be preserved"
    assert parsed["enabled"] is True, "enabled should be preserved"
    assert parsed["tags"] == ["a", "b"], "tags should be preserved"
    return


def test_credential_filtering_in_to_yaml():
    """
        Verify that credential keys are redacted in to_yaml output.
    """
    serializer = ConfigurationSerializer()
    config = {
        "db_password": "secret123",
        "api_secret": "abc",
        "host": "localhost"
    }
    yaml_str = serializer.to_yaml(config)
    restored = serializer.from_yaml(yaml_str)
    assert restored["db_password"] == "[REDACTED]", \
        "password key should be redacted in YAML output"
    assert restored["api_secret"] == "[REDACTED]", \
        "secret key should be redacted in YAML output"
    assert restored["host"] == "localhost", \
        "non-credential key should be preserved in YAML output"
    return


# ---- String Representation Tests ----


def test_repr_returns_expected_string():
    """
        Verify that __repr__ returns the expected string including the class name.
    """
    serializer = ConfigurationSerializer()
    repr_str = repr(serializer)
    assert "ConfigurationSerializer" in repr_str, \
        "__repr__ should include the class name"
    return


def test_str_returns_expected_string():
    """
        Verify that __str__ returns a human-readable string including supported formats.
    """
    serializer = ConfigurationSerializer()
    str_val = str(serializer)
    assert "json" in str_val, "__str__ should include json format"
    assert "yaml" in str_val, "__str__ should include yaml format"
    return
