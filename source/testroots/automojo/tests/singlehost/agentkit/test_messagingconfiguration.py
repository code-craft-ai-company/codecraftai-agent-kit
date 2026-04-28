"""
    Unit tests for the automojo.agentkit.messagingconfiguration module.

    Tests MessagingConfiguration construction, validation errors, from_dict,
    as_dict, to_json, from_json, __repr__, and __str__.

    Requirements: 20.1-20.15
"""

import json

from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.messagingconfiguration import MessagingConfiguration


# =========================================================================
# Construction with all required fields (Requirement 20.1)
# =========================================================================

def test_construction_with_required_fields():
    """
        Verify MessagingConfiguration stores all required fields when
        explicitly provided.
    """
    cfg = MessagingConfiguration(
        default_transport="http-transport",
        default_serialization_format="json",
        default_request_timeout=30.0,
    )

    assert cfg.default_transport == "http-transport", \
        "default_transport should be 'http-transport'"
    assert cfg.default_serialization_format == "json", \
        "default_serialization_format should be 'json'"
    assert cfg.default_request_timeout == 30.0, \
        "default_request_timeout should be 30.0"
    return


# =========================================================================
# Construction with all optional fields (Requirement 20.1)
# =========================================================================

def test_construction_with_all_optional_fields():
    """
        Verify MessagingConfiguration stores all optional fields when
        explicitly provided.
    """
    cfg = MessagingConfiguration(
        default_transport="ws-transport",
        default_serialization_format="msgpack",
        default_request_timeout=60.0,
        transport_configurations={"ws": {"protocol_type": "websocket"}},
        pubsub_settings={"max_topics": 100},
        credential_references={"api_key": "ref-001"},
        options={"retry_count": 3},
    )

    assert cfg.default_transport == "ws-transport", \
        "default_transport should be 'ws-transport'"
    assert cfg.default_serialization_format == "msgpack", \
        "default_serialization_format should be 'msgpack'"
    assert cfg.default_request_timeout == 60.0, \
        "default_request_timeout should be 60.0"
    assert cfg.transport_configurations == {"ws": {"protocol_type": "websocket"}}, \
        "transport_configurations should match the provided dictionary"
    assert cfg.pubsub_settings == {"max_topics": 100}, \
        "pubsub_settings should match the provided dictionary"
    assert cfg.credential_references == {"api_key": "ref-001"}, \
        "credential_references should match the provided dictionary"
    assert cfg.options == {"retry_count": 3}, \
        "options should match the provided dictionary"
    return


# =========================================================================
# Validation errors - missing default_transport (Requirement 20.6)
# =========================================================================

def test_missing_default_transport_raises_configuration_error():
    """
        Verify ConfigurationError is raised when default_transport is None.
    """
    raised = False
    try:
        MessagingConfiguration(
            default_transport=None,
            default_serialization_format="json",
            default_request_timeout=30.0,
        )
    except ConfigurationError as err:
        raised = True
        assert "default_transport" in err.message, \
            "Error message should mention 'default_transport'"

    assert raised, \
        "Should raise ConfigurationError for missing default_transport"
    return


# =========================================================================
# Validation errors - missing default_serialization_format (Requirement 20.6)
# =========================================================================

def test_missing_default_serialization_format_raises_configuration_error():
    """
        Verify ConfigurationError is raised when default_serialization_format
        is None.
    """
    raised = False
    try:
        MessagingConfiguration(
            default_transport="http-transport",
            default_serialization_format=None,
            default_request_timeout=30.0,
        )
    except ConfigurationError as err:
        raised = True
        assert "default_serialization_format" in err.message, \
            "Error message should mention 'default_serialization_format'"

    assert raised, \
        "Should raise ConfigurationError for missing default_serialization_format"
    return


# =========================================================================
# Validation errors - missing default_request_timeout (Requirement 20.6)
# =========================================================================

def test_missing_default_request_timeout_raises_configuration_error():
    """
        Verify ConfigurationError is raised when default_request_timeout
        is None.
    """
    raised = False
    try:
        MessagingConfiguration(
            default_transport="http-transport",
            default_serialization_format="json",
            default_request_timeout=None,
        )
    except ConfigurationError as err:
        raised = True
        assert "default_request_timeout" in err.message, \
            "Error message should mention 'default_request_timeout'"

    assert raised, \
        "Should raise ConfigurationError for missing default_request_timeout"
    return


# =========================================================================
# Validation errors - empty string default_transport (Requirement 20.6)
# =========================================================================

def test_empty_default_transport_raises_configuration_error():
    """
        Verify ConfigurationError is raised when default_transport is an
        empty string.
    """
    raised = False
    try:
        MessagingConfiguration(
            default_transport="",
            default_serialization_format="json",
            default_request_timeout=30.0,
        )
    except ConfigurationError as err:
        raised = True
        assert "default_transport" in err.message, \
            "Error message should mention 'default_transport'"

    assert raised, \
        "Should raise ConfigurationError for empty default_transport"
    return


# =========================================================================
# Property access for all fields (Requirement 20.1)
# =========================================================================

def test_property_access_all_fields():
    """
        Verify all properties return the correct values including
        optional fields that default to empty dicts.
    """
    cfg = MessagingConfiguration(
        default_transport="grpc-transport",
        default_serialization_format="protobuf",
        default_request_timeout=15.0,
    )

    assert cfg.default_transport == "grpc-transport", \
        "default_transport property mismatch"
    assert cfg.default_serialization_format == "protobuf", \
        "default_serialization_format property mismatch"
    assert cfg.default_request_timeout == 15.0, \
        "default_request_timeout property mismatch"
    assert cfg.transport_configurations == {}, \
        "transport_configurations should default to empty dict"
    assert cfg.pubsub_settings == {}, \
        "pubsub_settings should default to empty dict"
    assert cfg.credential_references == {}, \
        "credential_references should default to empty dict"
    assert cfg.options == {}, \
        "options should default to empty dict"
    return


# =========================================================================
# as_dict returns correct dictionary (Requirement 20.9)
# =========================================================================

def test_as_dict_returns_correct_dictionary():
    """
        Verify as_dict always includes the three required fields.
    """
    cfg = MessagingConfiguration(
        default_transport="http-transport",
        default_serialization_format="json",
        default_request_timeout=30.0,
    )

    result = cfg.as_dict()

    assert result["default_transport"] == "http-transport", \
        "as_dict default_transport mismatch"
    assert result["default_serialization_format"] == "json", \
        "as_dict default_serialization_format mismatch"
    assert result["default_request_timeout"] == 30.0, \
        "as_dict default_request_timeout mismatch"
    return


# =========================================================================
# as_dict excludes empty optional fields (Requirement 20.9)
# =========================================================================

def test_as_dict_excludes_empty_optional_fields():
    """
        Verify as_dict excludes transport_configurations, pubsub_settings,
        credential_references, and options when they are empty.
    """
    cfg = MessagingConfiguration(
        default_transport="http-transport",
        default_serialization_format="json",
        default_request_timeout=30.0,
    )

    result = cfg.as_dict()

    assert "transport_configurations" not in result, \
        "as_dict should not include 'transport_configurations' when empty"
    assert "pubsub_settings" not in result, \
        "as_dict should not include 'pubsub_settings' when empty"
    assert "credential_references" not in result, \
        "as_dict should not include 'credential_references' when empty"
    assert "options" not in result, \
        "as_dict should not include 'options' when empty"
    return


# =========================================================================
# to_json returns valid JSON string (Requirement 20.10)
# =========================================================================

def test_to_json_returns_valid_json():
    """
        Verify to_json returns a valid JSON string containing all
        required fields.
    """
    cfg = MessagingConfiguration(
        default_transport="http-transport",
        default_serialization_format="json",
        default_request_timeout=25.0,
        pubsub_settings={"max_topics": 50},
    )

    json_str = cfg.to_json()
    parsed = json.loads(json_str)

    assert parsed["default_transport"] == "http-transport", \
        "JSON default_transport mismatch"
    assert parsed["default_serialization_format"] == "json", \
        "JSON default_serialization_format mismatch"
    assert parsed["default_request_timeout"] == 25.0, \
        "JSON default_request_timeout mismatch"
    assert parsed["pubsub_settings"] == {"max_topics": 50}, \
        "JSON pubsub_settings mismatch"
    return


# =========================================================================
# from_dict constructs correctly (Requirement 20.2, 20.11)
# =========================================================================

def test_from_dict_constructs_correctly():
    """
        Verify from_dict constructs a MessagingConfiguration from a
        dictionary.
    """
    data = {
        "default_transport": "ws-transport",
        "default_serialization_format": "msgpack",
        "default_request_timeout": 45.0,
        "transport_configurations": {"ws": {"protocol_type": "websocket"}},
        "pubsub_settings": {"max_topics": 200},
        "options": {"debug": True},
    }

    cfg = MessagingConfiguration.from_dict(data)

    assert cfg.default_transport == "ws-transport", \
        "from_dict default_transport mismatch"
    assert cfg.default_serialization_format == "msgpack", \
        "from_dict default_serialization_format mismatch"
    assert cfg.default_request_timeout == 45.0, \
        "from_dict default_request_timeout mismatch"
    assert cfg.transport_configurations == {"ws": {"protocol_type": "websocket"}}, \
        "from_dict transport_configurations mismatch"
    assert cfg.pubsub_settings == {"max_topics": 200}, \
        "from_dict pubsub_settings mismatch"
    assert cfg.options == {"debug": True}, \
        "from_dict options mismatch"
    return


# =========================================================================
# from_json constructs correctly (Requirement 20.12)
# =========================================================================

def test_from_json_constructs_correctly():
    """
        Verify from_json deserializes a JSON string into a
        MessagingConfiguration.
    """
    data = {
        "default_transport": "grpc-transport",
        "default_serialization_format": "protobuf",
        "default_request_timeout": 20.0,
    }
    json_str = json.dumps(data)

    cfg = MessagingConfiguration.from_json(json_str)

    assert cfg.default_transport == "grpc-transport", \
        "from_json default_transport mismatch"
    assert cfg.default_serialization_format == "protobuf", \
        "from_json default_serialization_format mismatch"
    assert cfg.default_request_timeout == 20.0, \
        "from_json default_request_timeout mismatch"
    return


# =========================================================================
# __repr__ (Requirement 20.14, 26.23)
# =========================================================================

def test_repr_includes_class_name_and_fields():
    """
        Verify __repr__ includes the class name, default_transport,
        and default_serialization_format.
    """
    cfg = MessagingConfiguration(
        default_transport="http-transport",
        default_serialization_format="json",
        default_request_timeout=30.0,
    )

    repr_str = repr(cfg)

    assert "MessagingConfiguration" in repr_str, \
        "repr should contain 'MessagingConfiguration'"
    assert "http-transport" in repr_str, \
        "repr should contain the default transport name"
    assert "json" in repr_str, \
        "repr should contain the default serialization format"
    return


# =========================================================================
# __str__ (Requirement 20.15, 26.24)
# =========================================================================

def test_str_includes_human_readable_summary():
    """
        Verify __str__ returns a human-readable summary including
        default_transport, default_serialization_format, and
        default_request_timeout.
    """
    cfg = MessagingConfiguration(
        default_transport="ws-transport",
        default_serialization_format="msgpack",
        default_request_timeout=45.0,
    )

    str_val = str(cfg)

    assert "ws-transport" in str_val, \
        "str should contain the default transport name"
    assert "msgpack" in str_val, \
        "str should contain the default serialization format"
    assert "45.0" in str_val, \
        "str should contain the default request timeout"
    return


# =========================================================================
# Entrypoint
# =========================================================================

if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
