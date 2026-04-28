"""
    Unit tests for the automojo.agentkit.transport module.

    Tests the Transport abstract base class including construction
    validation, property access, is_connected, __repr__, and __str__.
    A minimal concrete Transport subclass is used for testing.

    Requirements: 1.1-1.11
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.message import Message
from automojo.agentkit.messageenvelope import MessageEnvelope
from automojo.agentkit.transport import Transport
from automojo.agentkit.transportconfiguration import TransportConfiguration


# =========================================================================
# Minimal concrete Transport subclass for testing
# =========================================================================

class StubTransport(Transport):
    """
        A minimal concrete Transport subclass that implements the
        abstract methods with no-op behavior, used for unit testing
        the Transport base class.
    """

    def connect(self) -> None:
        self._connected = True
        return

    def disconnect(self) -> None:
        self._connected = False
        return

    def send(self, message: Message) -> MessageEnvelope:
        envelope = MessageEnvelope(
            message=message,
            transport_name=self.name,
            attempt_count=1,
            delivery_status="delivered",
        )
        return envelope

    def receive(self) -> Message:
        return None


def _create_configuration():
    """
        Creates a minimal TransportConfiguration for use in tests.
    """
    cfg = TransportConfiguration(
        protocol_type="http",
        host="localhost",
        port=8080,
    )
    return cfg


# =========================================================================
# Construction validation (Requirements 1.8, 1.9)
# =========================================================================

def test_missing_name_raises_semantic_error():
    """
        Verify SemanticError is raised when name is None.
    """
    cfg = _create_configuration()
    raised = False

    try:
        StubTransport(
            name=None,
            protocol_type="http",
            configuration=cfg,
        )
    except SemanticError as err:
        raised = True
        assert "name" in err.message.lower(), \
            "Error message should mention 'name'"

    assert raised is True, \
        "SemanticError should be raised for None name"
    return


def test_empty_name_raises_semantic_error():
    """
        Verify SemanticError is raised when name is an empty string.
    """
    cfg = _create_configuration()
    raised = False

    try:
        StubTransport(
            name="",
            protocol_type="http",
            configuration=cfg,
        )
    except SemanticError as err:
        raised = True
        assert "name" in err.message.lower(), \
            "Error message should mention 'name'"

    assert raised is True, \
        "SemanticError should be raised for empty name"
    return


def test_whitespace_name_raises_semantic_error():
    """
        Verify SemanticError is raised when name is whitespace only.
    """
    cfg = _create_configuration()
    raised = False

    try:
        StubTransport(
            name="   ",
            protocol_type="http",
            configuration=cfg,
        )
    except SemanticError as err:
        raised = True
        assert "name" in err.message.lower(), \
            "Error message should mention 'name'"

    assert raised is True, \
        "SemanticError should be raised for whitespace-only name"
    return


def test_missing_protocol_type_raises_semantic_error():
    """
        Verify SemanticError is raised when protocol_type is None.
    """
    cfg = _create_configuration()
    raised = False

    try:
        StubTransport(
            name="test-transport",
            protocol_type=None,
            configuration=cfg,
        )
    except SemanticError as err:
        raised = True
        assert "protocol type" in err.message.lower(), \
            "Error message should mention 'protocol type'"

    assert raised is True, \
        "SemanticError should be raised for None protocol_type"
    return


def test_empty_protocol_type_raises_semantic_error():
    """
        Verify SemanticError is raised when protocol_type is empty.
    """
    cfg = _create_configuration()
    raised = False

    try:
        StubTransport(
            name="test-transport",
            protocol_type="",
            configuration=cfg,
        )
    except SemanticError as err:
        raised = True
        assert "protocol type" in err.message.lower(), \
            "Error message should mention 'protocol type'"

    assert raised is True, \
        "SemanticError should be raised for empty protocol_type"
    return


# =========================================================================
# Property access (Requirements 1.3, 1.4, 1.5, 1.6, 1.7)
# =========================================================================

def test_name_property():
    """
        Verify the name property returns the transport name.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    assert transport.name == "my-http", \
        "name property should return 'my-http'"
    return


def test_protocol_type_property():
    """
        Verify the protocol_type property returns the protocol type.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    assert transport.protocol_type == "http", \
        "protocol_type property should return 'http'"
    return


def test_configuration_property():
    """
        Verify the configuration property returns the TransportConfiguration.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    assert transport.configuration is cfg, \
        "configuration property should return the same configuration object"
    return


def test_tags_property_default():
    """
        Verify the tags property defaults to an empty dict.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    assert transport.tags == {}, \
        "tags should default to an empty dict"
    return


def test_tags_property_with_values():
    """
        Verify the tags property returns the provided tags.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
        tags={"env": "production", "region": "us-east-1"},
    )

    assert transport.tags == {"env": "production", "region": "us-east-1"}, \
        "tags should match the provided dictionary"
    return


def test_tags_returns_defensive_copy():
    """
        Verify the tags property returns a defensive copy.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
        tags={"env": "dev"},
    )

    tags_copy = transport.tags
    tags_copy["extra"] = "value"

    assert "extra" not in transport.tags, \
        "Modifying the returned tags should not affect the transport"
    return


def test_credential_names_property_default():
    """
        Verify the credential_names property defaults to an empty list.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    assert transport.credential_names == [], \
        "credential_names should default to an empty list"
    return


def test_credential_names_property_with_values():
    """
        Verify the credential_names property returns the provided names.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
        credential_names=["api-key", "tls-cert"],
    )

    assert transport.credential_names == ["api-key", "tls-cert"], \
        "credential_names should match the provided list"
    return


def test_credential_names_returns_defensive_copy():
    """
        Verify the credential_names property returns a defensive copy.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
        credential_names=["api-key"],
    )

    names_copy = transport.credential_names
    names_copy.append("extra")

    assert len(transport.credential_names) == 1, \
        "Modifying the returned list should not affect the transport"
    return


# =========================================================================
# is_connected (Requirement 1.1)
# =========================================================================

def test_is_connected_default_false():
    """
        Verify is_connected returns False before connect is called.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    assert transport.is_connected() is False, \
        "is_connected should return False before connect"
    return


def test_is_connected_true_after_connect():
    """
        Verify is_connected returns True after connect is called.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    transport.connect()

    assert transport.is_connected() is True, \
        "is_connected should return True after connect"
    return


def test_is_connected_false_after_disconnect():
    """
        Verify is_connected returns False after disconnect is called.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    transport.connect()
    transport.disconnect()

    assert transport.is_connected() is False, \
        "is_connected should return False after disconnect"
    return


# =========================================================================
# __repr__ and __str__ (Requirements 1.10, 1.11)
# =========================================================================

def test_repr_contains_class_name_and_fields():
    """
        Verify __repr__ includes the class name, transport name, and
        protocol type.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    repr_str = repr(transport)

    assert "StubTransport" in repr_str, \
        "__repr__ should include the class name"
    assert "my-http" in repr_str, \
        "__repr__ should include the transport name"
    assert "http" in repr_str, \
        "__repr__ should include the protocol type"
    return


def test_str_contains_human_readable_summary():
    """
        Verify __str__ returns a human-readable summary including
        the transport name, protocol type, and connection status.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    str_val = str(transport)

    assert "my-http" in str_val, \
        "__str__ should include the transport name"
    assert "http" in str_val, \
        "__str__ should include the protocol type"
    assert "disconnected" in str_val, \
        "__str__ should include the connection status"
    return


def test_str_shows_connected_status():
    """
        Verify __str__ shows 'connected' after connect is called.
    """
    cfg = _create_configuration()
    transport = StubTransport(
        name="my-http",
        protocol_type="http",
        configuration=cfg,
    )

    transport.connect()
    str_val = str(transport)

    assert "connected" in str_val, \
        "__str__ should show 'connected' after connect"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
