"""
    Unit tests for the automojo.agentkit.agentaddress module.

    Tests AgentAddress construction, property access, as_dict, to_json,
    from_dict, from_json, __eq__, __hash__, __repr__, __str__, and usage
    as dictionary keys and set members.

    Requirements: 7.1-7.11
"""

import json

from automojo.agentkit.agentaddress import AgentAddress


# =========================================================================
# Construction and property access (Requirements 7.1, 7.2)
# =========================================================================

def test_construction_with_all_fields():
    """
        Verify AgentAddress stores agent_identifier, transport_name,
        and endpoint when all fields are provided.
    """
    endpoint = {"host": "localhost", "port": "8080"}
    addr = AgentAddress(
        agent_identifier="agent-001",
        transport_name="http",
        endpoint=endpoint,
    )

    assert addr.agent_identifier == "agent-001", \
        "agent_identifier should be 'agent-001'"
    assert addr.transport_name == "http", \
        "transport_name should be 'http'"
    assert addr.endpoint == {"host": "localhost", "port": "8080"}, \
        "endpoint should match the provided dictionary"
    return


def test_construction_without_endpoint():
    """
        Verify AgentAddress defaults endpoint to an empty dict when
        no endpoint is provided.
    """
    addr = AgentAddress(
        agent_identifier="agent-002",
        transport_name="grpc",
    )

    assert addr.endpoint == {}, \
        "endpoint should default to an empty dict"
    return


def test_construction_with_none_endpoint():
    """
        Verify AgentAddress treats None endpoint the same as omitted.
    """
    addr = AgentAddress(
        agent_identifier="agent-003",
        transport_name="ws",
        endpoint=None,
    )

    assert addr.endpoint == {}, \
        "endpoint should be empty dict when None is passed"
    return


def test_endpoint_returns_defensive_copy():
    """
        Verify that the endpoint property returns a copy, so mutations
        do not affect the internal state.
    """
    endpoint = {"host": "10.0.0.1"}
    addr = AgentAddress(
        agent_identifier="agent-004",
        transport_name="http",
        endpoint=endpoint,
    )

    copy = addr.endpoint
    copy["host"] = "modified"

    assert addr.endpoint["host"] == "10.0.0.1", \
        "Modifying the returned endpoint should not affect the original"
    return


# =========================================================================
# as_dict (Requirement 7.3)
# =========================================================================

def test_as_dict_returns_all_fields():
    """
        Verify as_dict returns a dictionary with agent_identifier,
        transport_name, and endpoint.
    """
    addr = AgentAddress(
        agent_identifier="agent-010",
        transport_name="http",
        endpoint={"host": "example.com", "port": "443"},
    )

    result = addr.as_dict()

    assert result["agent_identifier"] == "agent-010", \
        "as_dict agent_identifier mismatch"
    assert result["transport_name"] == "http", \
        "as_dict transport_name mismatch"
    assert result["endpoint"] == {"host": "example.com", "port": "443"}, \
        "as_dict endpoint mismatch"
    return


def test_as_dict_with_empty_endpoint():
    """
        Verify as_dict works when endpoint is empty.
    """
    addr = AgentAddress(
        agent_identifier="agent-011",
        transport_name="grpc",
    )

    result = addr.as_dict()

    assert result["endpoint"] == {}, \
        "as_dict endpoint should be empty dict"
    return


# =========================================================================
# to_json (Requirement 7.4)
# =========================================================================

def test_to_json_returns_valid_json():
    """
        Verify to_json returns a valid JSON string containing all fields.
    """
    addr = AgentAddress(
        agent_identifier="agent-020",
        transport_name="ws",
        endpoint={"path": "/events"},
    )

    json_str = addr.to_json()
    parsed = json.loads(json_str)

    assert parsed["agent_identifier"] == "agent-020", \
        "JSON agent_identifier mismatch"
    assert parsed["transport_name"] == "ws", \
        "JSON transport_name mismatch"
    assert parsed["endpoint"] == {"path": "/events"}, \
        "JSON endpoint mismatch"
    return


# =========================================================================
# from_dict (Requirement 7.5)
# =========================================================================

def test_from_dict_constructs_address():
    """
        Verify from_dict constructs an AgentAddress from a dictionary.
    """
    data = {
        "agent_identifier": "agent-030",
        "transport_name": "mq",
        "endpoint": {"queue_name": "tasks"},
    }

    addr = AgentAddress.from_dict(data)

    assert addr.agent_identifier == "agent-030", \
        "from_dict agent_identifier mismatch"
    assert addr.transport_name == "mq", \
        "from_dict transport_name mismatch"
    assert addr.endpoint == {"queue_name": "tasks"}, \
        "from_dict endpoint mismatch"
    return


def test_from_dict_without_endpoint_key():
    """
        Verify from_dict defaults endpoint to empty dict when the key
        is absent.
    """
    data = {
        "agent_identifier": "agent-031",
        "transport_name": "http",
    }

    addr = AgentAddress.from_dict(data)

    assert addr.endpoint == {}, \
        "from_dict should default endpoint to empty dict"
    return


# =========================================================================
# from_json (Requirement 7.6)
# =========================================================================

def test_from_json_constructs_address():
    """
        Verify from_json deserializes a JSON string into an AgentAddress.
    """
    data = {
        "agent_identifier": "agent-040",
        "transport_name": "grpc",
        "endpoint": {"host": "grpc.example.com", "port": "50051"},
    }
    json_str = json.dumps(data)

    addr = AgentAddress.from_json(json_str)

    assert addr.agent_identifier == "agent-040", \
        "from_json agent_identifier mismatch"
    assert addr.transport_name == "grpc", \
        "from_json transport_name mismatch"
    assert addr.endpoint == {"host": "grpc.example.com", "port": "50051"}, \
        "from_json endpoint mismatch"
    return


# =========================================================================
# __eq__ (Requirement 7.10)
# =========================================================================

def test_eq_same_identifier_and_transport():
    """
        Verify two AgentAddress instances with the same agent_identifier
        and transport_name are equal, even if endpoints differ.
    """
    addr_a = AgentAddress("agent-050", "http", {"host": "a.com"})
    addr_b = AgentAddress("agent-050", "http", {"host": "b.com"})

    assert addr_a == addr_b, \
        "Addresses with same id and transport should be equal"
    return


def test_eq_different_identifier():
    """
        Verify two AgentAddress instances with different agent_identifiers
        are not equal.
    """
    addr_a = AgentAddress("agent-051", "http")
    addr_b = AgentAddress("agent-052", "http")

    assert addr_a != addr_b, \
        "Addresses with different identifiers should not be equal"
    return


def test_eq_different_transport():
    """
        Verify two AgentAddress instances with different transport_names
        are not equal.
    """
    addr_a = AgentAddress("agent-053", "http")
    addr_b = AgentAddress("agent-053", "grpc")

    assert addr_a != addr_b, \
        "Addresses with different transports should not be equal"
    return


def test_eq_with_non_agentaddress():
    """
        Verify comparing an AgentAddress with a non-AgentAddress object
        returns NotImplemented (which Python translates to not-equal).
    """
    addr = AgentAddress("agent-054", "http")

    assert addr != "not-an-address", \
        "AgentAddress should not be equal to a string"
    assert addr != 42, \
        "AgentAddress should not be equal to an integer"
    return


# =========================================================================
# __hash__ (Requirement 7.11)
# =========================================================================

def test_hash_equal_addresses_have_same_hash():
    """
        Verify that equal AgentAddress instances produce the same hash.
    """
    addr_a = AgentAddress("agent-060", "ws", {"path": "/a"})
    addr_b = AgentAddress("agent-060", "ws", {"path": "/b"})

    assert hash(addr_a) == hash(addr_b), \
        "Equal addresses should have the same hash"
    return


def test_hash_different_addresses_likely_differ():
    """
        Verify that different AgentAddress instances are likely to produce
        different hashes (not guaranteed, but expected for distinct inputs).
    """
    addr_a = AgentAddress("agent-061", "http")
    addr_b = AgentAddress("agent-062", "grpc")

    # This is a probabilistic check; collisions are possible but unlikely
    # for these distinct inputs.
    hash_a = hash(addr_a)
    hash_b = hash(addr_b)

    assert hash_a != hash_b, \
        "Different addresses should likely have different hashes"
    return


# =========================================================================
# AgentAddress as dict key and set member (Requirement 7.11)
# =========================================================================

def test_agentaddress_as_dict_key():
    """
        Verify AgentAddress can be used as a dictionary key and that
        equal addresses map to the same entry.
    """
    addr_a = AgentAddress("agent-070", "http", {"host": "a.com"})
    addr_b = AgentAddress("agent-070", "http", {"host": "b.com"})

    lookup = {addr_a: "value-a"}

    assert lookup[addr_b] == "value-a", \
        "Equal AgentAddress instances should resolve to the same dict entry"
    return


def test_agentaddress_as_set_member():
    """
        Verify AgentAddress can be used in a set and that equal addresses
        are deduplicated.
    """
    addr_a = AgentAddress("agent-071", "ws")
    addr_b = AgentAddress("agent-071", "ws")
    addr_c = AgentAddress("agent-072", "ws")

    address_set = {addr_a, addr_b, addr_c}

    assert len(address_set) == 2, \
        "Set should contain 2 unique addresses, not {}".format(len(address_set))
    return


# =========================================================================
# __repr__ (Requirement 7.8)
# =========================================================================

def test_repr_contains_class_name_and_fields():
    """
        Verify __repr__ includes the class name, agent_identifier,
        and transport_name.
    """
    addr = AgentAddress("agent-080", "grpc")
    repr_str = repr(addr)

    assert "AgentAddress" in repr_str, \
        "repr should contain 'AgentAddress'"
    assert "agent-080" in repr_str, \
        "repr should contain the agent_identifier"
    assert "grpc" in repr_str, \
        "repr should contain the transport_name"
    return


# =========================================================================
# __str__ (Requirement 7.9)
# =========================================================================

def test_str_contains_human_readable_summary():
    """
        Verify __str__ returns a human-readable summary including the
        agent identifier, transport name, and endpoint information.
    """
    addr = AgentAddress("agent-090", "http", {"host": "example.com"})
    str_val = str(addr)

    assert "agent-090" in str_val, \
        "str should contain the agent_identifier"
    assert "http" in str_val, \
        "str should contain the transport_name"
    assert "example.com" in str_val, \
        "str should contain endpoint information"
    return


# =========================================================================
# Entrypoint
# =========================================================================

if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
