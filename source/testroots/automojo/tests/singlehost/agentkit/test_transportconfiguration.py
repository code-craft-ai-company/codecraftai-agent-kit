"""
    Unit tests for the automojo.agentkit.transportconfiguration module.

    Tests TransportConfiguration construction, validation errors, from_dict,
    as_dict, to_json, to_yaml, from_json, from_yaml, __repr__, and __str__.

    Requirements: 2.1-2.19
"""

import json

import yaml

from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.transportconfiguration import TransportConfiguration


# =========================================================================
# Construction with all fields (Requirement 2.1)
# =========================================================================

def test_construction_with_all_fields():
    """
        Verify TransportConfiguration stores all fields when explicitly
        provided.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="example.com",
        port=8080,
        path="/api/v1",
        headers={"authorization": "Bearer token123"},
        timeout=60.0,
        options={"keep_alive": True},
        credential_references={"api_key": "ref-001"},
    )

    assert cfg.protocol_type == "http", \
        "protocol_type should be 'http'"
    assert cfg.host == "example.com", \
        "host should be 'example.com'"
    assert cfg.port == 8080, \
        "port should be 8080"
    assert cfg.path == "/api/v1", \
        "path should be '/api/v1'"
    assert cfg.headers == {"authorization": "Bearer token123"}, \
        "headers should match the provided dictionary"
    assert cfg.timeout == 60.0, \
        "timeout should be 60.0"
    assert cfg.options == {"keep_alive": True}, \
        "options should match the provided dictionary"
    assert cfg.credential_references == {"api_key": "ref-001"}, \
        "credential_references should match the provided dictionary"
    return


def test_construction_with_defaults():
    """
        Verify TransportConfiguration uses default values for optional
        fields when not provided.
    """
    cfg = TransportConfiguration(
        protocol_type="grpc",
        host="grpc.example.com",
        port=50051,
    )

    assert cfg.path is None, \
        "path should default to None"
    assert cfg.headers == {}, \
        "headers should default to an empty dict"
    assert cfg.timeout == 30.0, \
        "timeout should default to 30.0"
    assert cfg.options == {}, \
        "options should default to an empty dict"
    assert cfg.credential_references == {}, \
        "credential_references should default to an empty dict"
    return


# =========================================================================
# Validation errors (Requirements 2.6, 2.9)
# =========================================================================

def test_missing_protocol_type_raises_configuration_error():
    """
        Verify ConfigurationError is raised when protocol_type is None.
    """
    raised = False
    try:
        TransportConfiguration(
            protocol_type=None,
            host="example.com",
            port=8080,
        )
    except ConfigurationError as err:
        raised = True
        assert "protocol_type" in err.message, \
            "Error message should mention 'protocol_type'"

    assert raised, \
        "Should raise ConfigurationError for missing protocol_type"
    return


def test_missing_host_raises_configuration_error():
    """
        Verify ConfigurationError is raised when host is None.
    """
    raised = False
    try:
        TransportConfiguration(
            protocol_type="http",
            host=None,
            port=8080,
        )
    except ConfigurationError as err:
        raised = True
        assert "host" in err.message, \
            "Error message should mention 'host'"

    assert raised, \
        "Should raise ConfigurationError for missing host"
    return


def test_missing_port_raises_configuration_error():
    """
        Verify ConfigurationError is raised when port is None.
    """
    raised = False
    try:
        TransportConfiguration(
            protocol_type="http",
            host="example.com",
            port=None,
        )
    except ConfigurationError as err:
        raised = True
        assert "port" in err.message, \
            "Error message should mention 'port'"

    assert raised, \
        "Should raise ConfigurationError for missing port"
    return


def test_empty_host_raises_configuration_error():
    """
        Verify ConfigurationError is raised when host is an empty string.
    """
    raised = False
    try:
        TransportConfiguration(
            protocol_type="http",
            host="",
            port=8080,
        )
    except ConfigurationError as err:
        raised = True
        assert "host" in err.message, \
            "Error message should mention 'host'"

    assert raised, \
        "Should raise ConfigurationError for empty host"
    return


def test_multiple_missing_fields_raises_configuration_error():
    """
        Verify ConfigurationError lists all missing fields when multiple
        required fields are absent.
    """
    raised = False
    try:
        TransportConfiguration(
            protocol_type=None,
            host=None,
            port=None,
        )
    except ConfigurationError as err:
        raised = True
        assert "protocol_type" in err.message, \
            "Error message should mention 'protocol_type'"
        assert "host" in err.message, \
            "Error message should mention 'host'"
        assert "port" in err.message, \
            "Error message should mention 'port'"

    assert raised, \
        "Should raise ConfigurationError for multiple missing fields"
    return


def test_invalid_protocol_type_raises_configuration_error():
    """
        Verify ConfigurationError is raised for an invalid protocol type.
    """
    raised = False
    try:
        TransportConfiguration(
            protocol_type="ftp",
            host="example.com",
            port=21,
        )
    except ConfigurationError as err:
        raised = True
        assert "ftp" in err.message, \
            "Error message should mention the invalid type 'ftp'"

    assert raised, \
        "Should raise ConfigurationError for invalid protocol type"
    return


# =========================================================================
# Valid protocol types (Requirement 2.1)
# =========================================================================

def test_valid_protocol_type_http():
    """
        Verify 'http' is accepted as a valid protocol type.
    """
    cfg = TransportConfiguration(protocol_type="http", host="h", port=80)
    assert cfg.protocol_type == "http"
    return


def test_valid_protocol_type_websocket():
    """
        Verify 'websocket' is accepted as a valid protocol type.
    """
    cfg = TransportConfiguration(protocol_type="websocket", host="h", port=80)
    assert cfg.protocol_type == "websocket"
    return


def test_valid_protocol_type_grpc():
    """
        Verify 'grpc' is accepted as a valid protocol type.
    """
    cfg = TransportConfiguration(protocol_type="grpc", host="h", port=50051)
    assert cfg.protocol_type == "grpc"
    return


def test_valid_protocol_type_message_queue():
    """
        Verify 'message_queue' is accepted as a valid protocol type.
    """
    cfg = TransportConfiguration(protocol_type="message_queue", host="h", port=5672)
    assert cfg.protocol_type == "message_queue"
    return


# =========================================================================
# as_dict (Requirement 2.10)
# =========================================================================

def test_as_dict_includes_required_fields():
    """
        Verify as_dict always includes protocol_type, host, port, and
        timeout.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="example.com",
        port=8080,
    )

    result = cfg.as_dict()

    assert result["protocol_type"] == "http", \
        "as_dict protocol_type mismatch"
    assert result["host"] == "example.com", \
        "as_dict host mismatch"
    assert result["port"] == 8080, \
        "as_dict port mismatch"
    assert result["timeout"] == 30.0, \
        "as_dict timeout mismatch"
    return


def test_as_dict_excludes_empty_optional_fields():
    """
        Verify as_dict excludes path, headers, options, and
        credential_references when they are empty or None.
    """
    cfg = TransportConfiguration(
        protocol_type="grpc",
        host="grpc.example.com",
        port=50051,
    )

    result = cfg.as_dict()

    assert "path" not in result, \
        "as_dict should not include 'path' when None"
    assert "headers" not in result, \
        "as_dict should not include 'headers' when empty"
    assert "options" not in result, \
        "as_dict should not include 'options' when empty"
    assert "credential_references" not in result, \
        "as_dict should not include 'credential_references' when empty"
    return


def test_as_dict_includes_non_empty_optional_fields():
    """
        Verify as_dict includes path, headers, options, and
        credential_references when they are non-empty.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="example.com",
        port=443,
        path="/api",
        headers={"x-key": "val"},
        options={"tls": True},
        credential_references={"cert": "ref-cert"},
    )

    result = cfg.as_dict()

    assert result["path"] == "/api", \
        "as_dict path mismatch"
    assert result["headers"] == {"x-key": "val"}, \
        "as_dict headers mismatch"
    assert result["options"] == {"tls": True}, \
        "as_dict options mismatch"
    assert result["credential_references"] == {"cert": "ref-cert"}, \
        "as_dict credential_references mismatch"
    return


# =========================================================================
# from_dict (Requirement 2.2, 2.13)
# =========================================================================

def test_from_dict_constructs_configuration():
    """
        Verify from_dict constructs a TransportConfiguration from a
        dictionary.
    """
    data = {
        "protocol_type": "websocket",
        "host": "ws.example.com",
        "port": 9090,
        "path": "/ws",
        "headers": {"upgrade": "websocket"},
        "timeout": 45.0,
        "options": {"compression": "gzip"},
    }

    cfg = TransportConfiguration.from_dict(data)

    assert cfg.protocol_type == "websocket", \
        "from_dict protocol_type mismatch"
    assert cfg.host == "ws.example.com", \
        "from_dict host mismatch"
    assert cfg.port == 9090, \
        "from_dict port mismatch"
    assert cfg.path == "/ws", \
        "from_dict path mismatch"
    assert cfg.headers == {"upgrade": "websocket"}, \
        "from_dict headers mismatch"
    assert cfg.timeout == 45.0, \
        "from_dict timeout mismatch"
    assert cfg.options == {"compression": "gzip"}, \
        "from_dict options mismatch"
    return


# =========================================================================
# to_json / from_json (Requirements 2.11, 2.14, 2.16)
# =========================================================================

def test_to_json_returns_valid_json():
    """
        Verify to_json returns a valid JSON string containing all fields.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="example.com",
        port=8080,
        path="/api",
        timeout=15.0,
    )

    json_str = cfg.to_json()
    parsed = json.loads(json_str)

    assert parsed["protocol_type"] == "http", \
        "JSON protocol_type mismatch"
    assert parsed["host"] == "example.com", \
        "JSON host mismatch"
    assert parsed["port"] == 8080, \
        "JSON port mismatch"
    assert parsed["path"] == "/api", \
        "JSON path mismatch"
    assert parsed["timeout"] == 15.0, \
        "JSON timeout mismatch"
    return


def test_from_json_constructs_configuration():
    """
        Verify from_json deserializes a JSON string into a
        TransportConfiguration.
    """
    data = {
        "protocol_type": "grpc",
        "host": "grpc.example.com",
        "port": 50051,
        "timeout": 20.0,
    }
    json_str = json.dumps(data)

    cfg = TransportConfiguration.from_json(json_str)

    assert cfg.protocol_type == "grpc", \
        "from_json protocol_type mismatch"
    assert cfg.host == "grpc.example.com", \
        "from_json host mismatch"
    assert cfg.port == 50051, \
        "from_json port mismatch"
    assert cfg.timeout == 20.0, \
        "from_json timeout mismatch"
    return


def test_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent
        TransportConfiguration object.
    """
    original = TransportConfiguration(
        protocol_type="http",
        host="roundtrip.example.com",
        port=443,
        path="/v2",
        headers={"accept": "application/json"},
        timeout=25.0,
        options={"retry": 3},
    )

    json_str = original.to_json()
    restored = TransportConfiguration.from_json(json_str)

    assert restored.protocol_type == original.protocol_type, \
        "Round-trip protocol_type mismatch"
    assert restored.host == original.host, \
        "Round-trip host mismatch"
    assert restored.port == original.port, \
        "Round-trip port mismatch"
    assert restored.path == original.path, \
        "Round-trip path mismatch"
    assert restored.headers == original.headers, \
        "Round-trip headers mismatch"
    assert restored.timeout == original.timeout, \
        "Round-trip timeout mismatch"
    assert restored.options == original.options, \
        "Round-trip options mismatch"
    return


# =========================================================================
# to_yaml / from_yaml (Requirements 2.12, 2.15, 2.17)
# =========================================================================

def test_to_yaml_returns_valid_yaml():
    """
        Verify to_yaml returns a valid YAML string containing all fields.
    """
    cfg = TransportConfiguration(
        protocol_type="message_queue",
        host="mq.example.com",
        port=5672,
        options={"queue_name": "tasks"},
    )

    yaml_str = cfg.to_yaml()
    parsed = yaml.safe_load(yaml_str)

    assert parsed["protocol_type"] == "message_queue", \
        "YAML protocol_type mismatch"
    assert parsed["host"] == "mq.example.com", \
        "YAML host mismatch"
    assert parsed["port"] == 5672, \
        "YAML port mismatch"
    assert parsed["options"] == {"queue_name": "tasks"}, \
        "YAML options mismatch"
    return


def test_from_yaml_constructs_configuration():
    """
        Verify from_yaml deserializes a YAML string into a
        TransportConfiguration.
    """
    yaml_str = (
        "protocol_type: websocket\n"
        "host: ws.example.com\n"
        "port: 9090\n"
        "timeout: 10.0\n"
    )

    cfg = TransportConfiguration.from_yaml(yaml_str)

    assert cfg.protocol_type == "websocket", \
        "from_yaml protocol_type mismatch"
    assert cfg.host == "ws.example.com", \
        "from_yaml host mismatch"
    assert cfg.port == 9090, \
        "from_yaml port mismatch"
    assert cfg.timeout == 10.0, \
        "from_yaml timeout mismatch"
    return


def test_yaml_round_trip():
    """
        Verify that to_yaml followed by from_yaml produces an equivalent
        TransportConfiguration object.
    """
    original = TransportConfiguration(
        protocol_type="grpc",
        host="yaml.example.com",
        port=50051,
        path="/service",
        headers={"x-api-key": "abc"},
        timeout=35.0,
        options={"max_retries": 5},
    )

    yaml_str = original.to_yaml()
    restored = TransportConfiguration.from_yaml(yaml_str)

    assert restored.protocol_type == original.protocol_type, \
        "YAML round-trip protocol_type mismatch"
    assert restored.host == original.host, \
        "YAML round-trip host mismatch"
    assert restored.port == original.port, \
        "YAML round-trip port mismatch"
    assert restored.path == original.path, \
        "YAML round-trip path mismatch"
    assert restored.headers == original.headers, \
        "YAML round-trip headers mismatch"
    assert restored.timeout == original.timeout, \
        "YAML round-trip timeout mismatch"
    assert restored.options == original.options, \
        "YAML round-trip options mismatch"
    return


# =========================================================================
# __repr__ (Requirement 2.18)
# =========================================================================

def test_repr_contains_class_name_and_fields():
    """
        Verify __repr__ includes the class name, protocol type, host,
        and port.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="repr.example.com",
        port=8080,
    )

    repr_str = repr(cfg)

    assert "TransportConfiguration" in repr_str, \
        "repr should contain 'TransportConfiguration'"
    assert "http" in repr_str, \
        "repr should contain the protocol type"
    assert "repr.example.com" in repr_str, \
        "repr should contain the host"
    assert "8080" in repr_str, \
        "repr should contain the port"
    return


# =========================================================================
# __str__ (Requirement 2.19)
# =========================================================================

def test_str_contains_human_readable_summary():
    """
        Verify __str__ returns a human-readable summary including the
        protocol type, host, port, and timeout.
    """
    cfg = TransportConfiguration(
        protocol_type="websocket",
        host="str.example.com",
        port=9090,
        timeout=45.0,
    )

    str_val = str(cfg)

    assert "websocket" in str_val, \
        "str should contain the protocol type"
    assert "str.example.com" in str_val, \
        "str should contain the host"
    assert "9090" in str_val, \
        "str should contain the port"
    assert "45.0" in str_val, \
        "str should contain the timeout"
    return


# =========================================================================
# Defensive copies (Requirement 2.1)
# =========================================================================

def test_headers_returns_defensive_copy():
    """
        Verify that the headers property returns a copy, so mutations
        do not affect the internal state.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="example.com",
        port=80,
        headers={"x-key": "original"},
    )

    copy = cfg.headers
    copy["x-key"] = "modified"

    assert cfg.headers["x-key"] == "original", \
        "Modifying the returned headers should not affect the original"
    return


def test_options_returns_defensive_copy():
    """
        Verify that the options property returns a copy, so mutations
        do not affect the internal state.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="example.com",
        port=80,
        options={"retry": 3},
    )

    copy = cfg.options
    copy["retry"] = 99

    assert cfg.options["retry"] == 3, \
        "Modifying the returned options should not affect the original"
    return


# =========================================================================
# Entrypoint
# =========================================================================

if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
