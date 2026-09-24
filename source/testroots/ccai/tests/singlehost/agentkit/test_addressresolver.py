"""
    Unit tests for the ccai.agentkit.addressresolver module.

    Tests AddressResolver resolve, register_address, deregister_address,
    __repr__, and __str__. Verifies static resolution, dynamic resolution
    with mock AgentRegistry, and MessageRoutingError for unresolvable agents.

    Requirements: 8.1-8.8
"""

from ccai.agentkit.addressresolver import AddressResolver
from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.messagingerrors import MessageRoutingError
from ccai.testbase.mocking import Mock


# =========================================================================
# Test helpers
# =========================================================================

def _create_mock_registry(agent_identifier=None, agent=None):
    """
        Creates a mock AgentRegistry whose lookup_by_id returns the given
        agent for the given identifier.
    """
    mock_registry = Mock()
    mock_registry.configure(recursive=True)

    if agent_identifier is not None and agent is not None:
        def lookup_side_effect(identifier):
            if identifier == agent_identifier:
                return agent
            return None

        mock_registry.mock_context().mock_method("lookup_by_id", side_effect=lookup_side_effect)
    else:
        mock_registry.mock_context().mock_method("lookup_by_id", return_value=None)

    return mock_registry


# =========================================================================
# register_address and static resolution (Requirement 8.2, 8.5)
# =========================================================================

def test_register_address_stores_static_mapping():
    """
        Verify register_address stores a static mapping that can be
        resolved.
    """
    resolver = AddressResolver()

    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint={"host": "localhost", "port": 8080},
    )

    address = resolver.resolve("agent-001", "http")

    assert isinstance(address, AgentAddress), \
        "resolve should return an AgentAddress"
    assert address.agent_identifier == "agent-001", \
        "Resolved address should have correct agent_identifier"
    assert address.transport_name == "http", \
        "Resolved address should have correct transport_name"
    assert address.endpoint == {"host": "localhost", "port": 8080}, \
        "Resolved address should have correct endpoint"
    return


def test_register_address_overwrites_existing():
    """
        Verify register_address overwrites an existing static mapping
        for the same (agent_identifier, transport_name) key.
    """
    resolver = AddressResolver()

    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint={"host": "old-host", "port": 8080},
    )

    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint={"host": "new-host", "port": 9090},
    )

    address = resolver.resolve("agent-001", "http")

    assert address.endpoint == {"host": "new-host", "port": 9090}, \
        "Resolved address should reflect the latest registration"
    return


def test_register_address_different_transports():
    """
        Verify register_address stores separate mappings for different
        transport names.
    """
    resolver = AddressResolver()

    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint={"host": "http-host"},
    )
    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="grpc",
        endpoint={"host": "grpc-host"},
    )

    http_address = resolver.resolve("agent-001", "http")
    grpc_address = resolver.resolve("agent-001", "grpc")

    assert http_address.endpoint == {"host": "http-host"}, \
        "HTTP address should have correct endpoint"
    assert grpc_address.endpoint == {"host": "grpc-host"}, \
        "gRPC address should have correct endpoint"
    return


# =========================================================================
# deregister_address (Requirement 8.6)
# =========================================================================

def test_deregister_address_removes_static_mapping():
    """
        Verify deregister_address removes the static mapping.
    """
    resolver = AddressResolver()

    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint={"host": "localhost"},
    )

    resolver.deregister_address("agent-001", "http")

    raised = False
    try:
        resolver.resolve("agent-001", "http")
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised after deregistration"
    return


def test_deregister_address_nonexistent_is_noop():
    """
        Verify deregister_address with unknown key does not raise.
    """
    resolver = AddressResolver()

    resolver.deregister_address("nonexistent", "http")

    return


# =========================================================================
# resolve with static lookup (Requirement 8.1, 8.2)
# =========================================================================

def test_resolve_static_takes_priority_over_dynamic():
    """
        Verify static resolution takes priority over dynamic resolution.
    """
    mock_agent = Mock()
    mock_agent.configure(recursive=True)

    mock_registry = _create_mock_registry(
        agent_identifier="agent-001",
        agent=mock_agent,
    )

    resolver = AddressResolver(agent_registry=mock_registry)

    resolver.register_address(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint={"host": "static-host"},
    )

    address = resolver.resolve("agent-001", "http")

    assert address.endpoint == {"host": "static-host"}, \
        "Static resolution should take priority over dynamic"
    return


# =========================================================================
# resolve with dynamic AgentRegistry lookup (Requirement 8.3)
# =========================================================================

def test_resolve_dynamic_when_no_static_mapping():
    """
        Verify dynamic resolution is used when no static mapping exists.
    """
    mock_agent = Mock()
    mock_agent.configure(recursive=True)

    mock_registry = _create_mock_registry(
        agent_identifier="agent-002",
        agent=mock_agent,
    )

    resolver = AddressResolver(agent_registry=mock_registry)

    address = resolver.resolve("agent-002", "http")

    assert isinstance(address, AgentAddress), \
        "resolve should return an AgentAddress from dynamic resolution"
    assert address.agent_identifier == "agent-002", \
        "Resolved address should have correct agent_identifier"
    assert address.transport_name == "http", \
        "Resolved address should have correct transport_name"
    return


# =========================================================================
# resolve raises MessageRoutingError (Requirement 8.4)
# =========================================================================

def test_resolve_raises_routing_error_when_not_found():
    """
        Verify MessageRoutingError is raised when agent cannot be resolved
        through either static or dynamic resolution.
    """
    resolver = AddressResolver()

    raised = False
    error = None
    try:
        resolver.resolve("unknown-agent", "http")
    except MessageRoutingError as exc:
        raised = True
        error = exc

    assert raised is True, \
        "MessageRoutingError should be raised for unresolvable agent"
    assert "unknown-agent" in str(error), \
        "Error message should contain the agent identifier"
    return


class _IdentifiedAgent:
    """
        Minimal object with the identity.identifier shape AgentRegistry
        registers agents by.
    """

    def __init__(self, identifier):
        self.identity = _AgentIdentityStub(identifier)
        return


class _AgentIdentityStub:
    """
        Minimal identity carrying an identifier.
    """

    def __init__(self, identifier):
        self.identifier = identifier
        return


def test_resolve_dynamic_with_real_agent_registry():
    """
        Verify dynamic resolution works against a real AgentRegistry,
        which looks agents up with lookup_by_id.
    """
    registry = AgentRegistry()
    registry.register(_IdentifiedAgent("agent-real-001"))

    resolver = AddressResolver(agent_registry=registry)

    address = resolver.resolve("agent-real-001", "mq")

    assert address.agent_identifier == "agent-real-001", \
        "Resolved address should have the registered agent identifier"
    assert address.transport_name == "mq", \
        "Resolved address should have the requested transport name"

    raised = False
    try:
        resolver.resolve("agent-not-registered", "mq")
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "An agent missing from the real registry should raise MessageRoutingError"
    return


def test_resolve_raises_routing_error_with_registry_but_agent_not_found():
    """
        Verify MessageRoutingError is raised when the AgentRegistry
        does not contain the agent.
    """
    mock_registry = _create_mock_registry()

    resolver = AddressResolver(agent_registry=mock_registry)

    raised = False
    try:
        resolver.resolve("unknown-agent", "http")
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised when agent not in registry"
    return


def test_resolve_raises_routing_error_without_registry():
    """
        Verify MessageRoutingError is raised when no registry is
        configured and no static mapping exists.
    """
    resolver = AddressResolver()

    raised = False
    try:
        resolver.resolve("agent-001", "http")
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised without registry"
    return


# =========================================================================
# __repr__ (Requirement 8.7)
# =========================================================================

def test_repr_contains_class_name_and_count():
    """
        Verify __repr__ includes class name and count of static addresses.
    """
    resolver = AddressResolver()
    resolver.register_address("agent-001", "http", {"host": "localhost"})
    resolver.register_address("agent-002", "grpc", {"host": "localhost"})

    repr_str = repr(resolver)

    assert "AddressResolver" in repr_str, \
        "repr should contain class name"
    assert "2" in repr_str, \
        "repr should contain count of static addresses"
    return


def test_repr_empty_resolver():
    """
        Verify __repr__ for an empty resolver.
    """
    resolver = AddressResolver()

    repr_str = repr(resolver)

    assert "AddressResolver" in repr_str, \
        "repr should contain class name"
    assert "0" in repr_str, \
        "repr should contain 0 for empty resolver"
    return


# =========================================================================
# __str__ (Requirement 8.8)
# =========================================================================

def test_str_without_registry():
    """
        Verify __str__ indicates dynamic resolution is disabled.
    """
    resolver = AddressResolver()

    str_val = str(resolver)

    assert "AddressResolver" in str_val, \
        "str should contain class name"
    assert "0" in str_val, \
        "str should indicate 0 static addresses"
    assert "False" in str_val, \
        "str should indicate dynamic_resolution=False"
    return


def test_str_with_registry():
    """
        Verify __str__ indicates dynamic resolution is enabled.
    """
    mock_registry = Mock()
    mock_registry.configure(recursive=True)

    resolver = AddressResolver(agent_registry=mock_registry)
    resolver.register_address("agent-001", "http", {"host": "localhost"})

    str_val = str(resolver)

    assert "1" in str_val, \
        "str should indicate 1 static address"
    assert "True" in str_val, \
        "str should indicate dynamic_resolution=True"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
