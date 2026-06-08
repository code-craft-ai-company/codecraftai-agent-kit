"""
    Unit tests for the ccai.agentkit.transportregistry module.

    Tests TransportRegistry register, deregister, lookup, lookup_by_protocol,
    lookup_by_tags, list_all, has_transport, count, __repr__, and __str__.
    Uses a minimal concrete Transport subclass for creating test instances.

    Requirements: 3.1-3.11
"""

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.transport import Transport
from ccai.agentkit.transportconfiguration import TransportConfiguration
from ccai.agentkit.transportregistry import TransportRegistry


# =========================================================================
# Minimal concrete Transport subclass for testing
# =========================================================================

class StubTransport(Transport):
    """
        A minimal concrete Transport subclass used for unit testing
        the TransportRegistry.
    """

    def connect(self) -> None:
        self._connected = True
        return

    def disconnect(self) -> None:
        self._connected = False
        return

    def send(self, message: Message) -> MessageEnvelope:
        return None

    def receive(self) -> Message:
        return None


def _create_configuration(protocol_type="http"):
    """
        Creates a minimal TransportConfiguration for use in tests.
    """
    cfg = TransportConfiguration(
        protocol_type=protocol_type,
        host="localhost",
        port=8080,
    )
    return cfg


def _create_transport(name="test-transport", protocol_type="http", tags=None):
    """
        Creates a StubTransport with the given name and protocol type.
    """
    cfg = _create_configuration(protocol_type=protocol_type)
    transport = StubTransport(
        name=name,
        protocol_type=protocol_type,
        configuration=cfg,
        tags=tags,
    )
    return transport


# =========================================================================
# register (Requirement 3.1)
# =========================================================================

def test_register_adds_transport():
    """
        Verify register stores the transport and it can be looked up.
    """
    registry = TransportRegistry()
    transport = _create_transport(name="http-main")

    registry.register(transport)

    result = registry.lookup("http-main")
    assert result is transport, \
        "lookup should return the registered transport"
    return


# =========================================================================
# Duplicate registration (Requirement 3.2)
# =========================================================================

def test_register_duplicate_raises_semantic_error():
    """
        Verify SemanticError is raised when registering a transport
        with a duplicate name.
    """
    registry = TransportRegistry()
    transport_a = _create_transport(name="http-main")
    transport_b = _create_transport(name="http-main")

    registry.register(transport_a)

    raised = False
    try:
        registry.register(transport_b)
    except SemanticError as err:
        raised = True
        assert "http-main" in err.message, \
            "Error message should include the duplicate transport name"

    assert raised is True, \
        "SemanticError should be raised for duplicate registration"
    return


# =========================================================================
# deregister (Requirement 3.3)
# =========================================================================

def test_deregister_removes_transport():
    """
        Verify deregister removes the transport from the registry.
    """
    registry = TransportRegistry()
    transport = _create_transport(name="http-main")

    registry.register(transport)
    registry.deregister("http-main")

    result = registry.lookup("http-main")
    assert result is None, \
        "lookup should return None after deregistration"
    return


def test_deregister_nonexistent_is_noop():
    """
        Verify deregister does not raise when the name is not found.
    """
    registry = TransportRegistry()

    raised = False
    try:
        registry.deregister("nonexistent")
    except Exception:
        raised = True

    assert raised is False, \
        "deregister should not raise for a nonexistent name"
    return


# =========================================================================
# lookup (Requirement 3.4)
# =========================================================================

def test_lookup_returns_transport():
    """
        Verify lookup returns the registered transport by name.
    """
    registry = TransportRegistry()
    transport = _create_transport(name="ws-main")

    registry.register(transport)

    result = registry.lookup("ws-main")
    assert result is transport, \
        "lookup should return the registered transport"
    return


def test_lookup_returns_none_for_unknown():
    """
        Verify lookup returns None when the name is not found.
    """
    registry = TransportRegistry()

    result = registry.lookup("unknown")
    assert result is None, \
        "lookup should return None for an unknown name"
    return


# =========================================================================
# lookup_by_protocol (Requirement 3.5)
# =========================================================================

def test_lookup_by_protocol_returns_matching():
    """
        Verify lookup_by_protocol returns transports matching the
        protocol type.
    """
    registry = TransportRegistry()
    http_transport = _create_transport(name="http-1", protocol_type="http")
    ws_transport = _create_transport(name="ws-1", protocol_type="websocket")
    http_transport_2 = _create_transport(name="http-2", protocol_type="http")

    registry.register(http_transport)
    registry.register(ws_transport)
    registry.register(http_transport_2)

    results = registry.lookup_by_protocol("http")

    assert len(results) == 2, \
        "lookup_by_protocol should return 2 http transports"
    assert http_transport in results, \
        "Results should include http-1"
    assert http_transport_2 in results, \
        "Results should include http-2"
    return


def test_lookup_by_protocol_returns_empty_for_no_match():
    """
        Verify lookup_by_protocol returns an empty list when no
        transports match.
    """
    registry = TransportRegistry()
    transport = _create_transport(name="http-1", protocol_type="http")
    registry.register(transport)

    results = registry.lookup_by_protocol("grpc")

    assert results == [], \
        "lookup_by_protocol should return empty list for no match"
    return


# =========================================================================
# lookup_by_tags (Requirement 3.6)
# =========================================================================

def test_lookup_by_tags_returns_matching():
    """
        Verify lookup_by_tags returns transports matching all tag
        criteria.
    """
    registry = TransportRegistry()
    t1 = _create_transport(
        name="http-prod",
        protocol_type="http",
        tags={"env": "production", "region": "us-east-1"},
    )
    t2 = _create_transport(
        name="http-dev",
        protocol_type="http",
        tags={"env": "development", "region": "us-east-1"},
    )
    t3 = _create_transport(
        name="ws-prod",
        protocol_type="websocket",
        tags={"env": "production", "region": "eu-west-1"},
    )

    registry.register(t1)
    registry.register(t2)
    registry.register(t3)

    results = registry.lookup_by_tags(env="production")

    assert len(results) == 2, \
        "lookup_by_tags should return 2 production transports"
    assert t1 in results, \
        "Results should include http-prod"
    assert t3 in results, \
        "Results should include ws-prod"
    return


def test_lookup_by_tags_multiple_criteria():
    """
        Verify lookup_by_tags matches ALL provided tag criteria.
    """
    registry = TransportRegistry()
    t1 = _create_transport(
        name="http-prod-east",
        protocol_type="http",
        tags={"env": "production", "region": "us-east-1"},
    )
    t2 = _create_transport(
        name="http-prod-west",
        protocol_type="http",
        tags={"env": "production", "region": "eu-west-1"},
    )

    registry.register(t1)
    registry.register(t2)

    results = registry.lookup_by_tags(env="production", region="us-east-1")

    assert len(results) == 1, \
        "lookup_by_tags should return 1 transport matching both tags"
    assert t1 in results, \
        "Results should include http-prod-east"
    return


def test_lookup_by_tags_returns_empty_for_no_match():
    """
        Verify lookup_by_tags returns an empty list when no transports
        match.
    """
    registry = TransportRegistry()
    t1 = _create_transport(
        name="http-dev",
        protocol_type="http",
        tags={"env": "development"},
    )
    registry.register(t1)

    results = registry.lookup_by_tags(env="production")

    assert results == [], \
        "lookup_by_tags should return empty list for no match"
    return


# =========================================================================
# list_all (Requirement 3.7)
# =========================================================================

def test_list_all_returns_all_transports():
    """
        Verify list_all returns all registered transports.
    """
    registry = TransportRegistry()
    t1 = _create_transport(name="http-1")
    t2 = _create_transport(name="ws-1", protocol_type="websocket")

    registry.register(t1)
    registry.register(t2)

    results = registry.list_all()

    assert len(results) == 2, \
        "list_all should return 2 transports"
    assert t1 in results, \
        "Results should include http-1"
    assert t2 in results, \
        "Results should include ws-1"
    return


def test_list_all_empty_registry():
    """
        Verify list_all returns an empty list for an empty registry.
    """
    registry = TransportRegistry()

    results = registry.list_all()

    assert results == [], \
        "list_all should return empty list for empty registry"
    return


# =========================================================================
# has_transport (Requirement 3.9)
# =========================================================================

def test_has_transport_returns_true():
    """
        Verify has_transport returns True for a registered name.
    """
    registry = TransportRegistry()
    transport = _create_transport(name="http-main")
    registry.register(transport)

    assert registry.has_transport("http-main") is True, \
        "has_transport should return True for a registered name"
    return


def test_has_transport_returns_false():
    """
        Verify has_transport returns False for an unregistered name.
    """
    registry = TransportRegistry()

    assert registry.has_transport("unknown") is False, \
        "has_transport should return False for an unregistered name"
    return


# =========================================================================
# count property (Requirement 3.8)
# =========================================================================

def test_count_empty_registry():
    """
        Verify count is 0 for an empty registry.
    """
    registry = TransportRegistry()

    assert registry.count == 0, \
        "count should be 0 for an empty registry"
    return


def test_count_after_registrations():
    """
        Verify count reflects the number of registered transports.
    """
    registry = TransportRegistry()
    registry.register(_create_transport(name="t1"))
    registry.register(_create_transport(name="t2"))
    registry.register(_create_transport(name="t3"))

    assert registry.count == 3, \
        "count should be 3 after registering 3 transports"
    return


def test_count_after_deregister():
    """
        Verify count decreases after deregistration.
    """
    registry = TransportRegistry()
    registry.register(_create_transport(name="t1"))
    registry.register(_create_transport(name="t2"))

    registry.deregister("t1")

    assert registry.count == 1, \
        "count should be 1 after deregistering one transport"
    return


# =========================================================================
# __repr__ (Requirement 3.10)
# =========================================================================

def test_repr_contains_class_name_and_count():
    """
        Verify __repr__ includes the class name and count.
    """
    registry = TransportRegistry()
    registry.register(_create_transport(name="t1"))

    repr_str = repr(registry)

    assert "TransportRegistry" in repr_str, \
        "__repr__ should include the class name"
    assert "1" in repr_str, \
        "__repr__ should include the count"
    return


# =========================================================================
# __str__ (Requirement 3.11)
# =========================================================================

def test_str_empty_registry():
    """
        Verify __str__ for an empty registry.
    """
    registry = TransportRegistry()

    str_val = str(registry)

    assert "0" in str_val, \
        "__str__ should indicate 0 transports"
    return


def test_str_with_transports():
    """
        Verify __str__ lists registered transport names and protocol
        types.
    """
    registry = TransportRegistry()
    registry.register(_create_transport(name="http-main", protocol_type="http"))
    registry.register(_create_transport(name="ws-main", protocol_type="websocket"))

    str_val = str(registry)

    assert "http-main" in str_val, \
        "__str__ should include 'http-main'"
    assert "ws-main" in str_val, \
        "__str__ should include 'ws-main'"
    assert "2" in str_val, \
        "__str__ should include the count"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
