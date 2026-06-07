"""
    Property-based tests for the ccai.agentkit.agentaddress module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 9: AgentAddress JSON round-trip consistency
    - Property 10: AgentAddress equality and hash consistency
    - Property 11 (partial): Defensive copy for AgentAddress endpoint

    **Validates: Requirements 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10**
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.agentaddress import AgentAddress


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_identifier_strategy = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
)

_transport_name_strategy = st.text(
    min_size=1,
    max_size=15,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
)

_endpoint_key_strategy = st.sampled_from(["host", "port", "path"])

_endpoint_value_strategy = st.text(
    min_size=1,
    max_size=15,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
)

_endpoint_strategy = st.dictionaries(
    keys=_endpoint_key_strategy,
    values=_endpoint_value_strategy,
    min_size=0,
    max_size=3,
)


# ---------------------------------------------------------------------------
# Property: AgentAddress JSON round-trip consistency
# ---------------------------------------------------------------------------

@given(
    agent_identifier=_identifier_strategy,
    transport_name=_transport_name_strategy,
    endpoint=_endpoint_strategy,
    constraints={"max_examples": 30},
)
def test_agentaddress_json_roundtrip(
    agent_identifier: str,
    transport_name: str,
    endpoint: dict,
) -> None:
    """
        **Validates: Requirements 7.7, 24.10**

        For all valid AgentAddress instances, serializing to JSON via
        to_json and then deserializing via from_json produces an
        equivalent AgentAddress object with identical agent_identifier,
        transport_name, and endpoint values.
    """
    address = AgentAddress(
        agent_identifier=agent_identifier,
        transport_name=transport_name,
        endpoint=endpoint,
    )

    json_str = address.to_json()
    restored = AgentAddress.from_json(json_str)

    testbase.assert_equal(
        restored.agent_identifier, address.agent_identifier,
        "agent_identifier mismatch after JSON roundtrip: "
        "{!r} != {!r}".format(restored.agent_identifier, address.agent_identifier),
    )

    testbase.assert_equal(
        restored.transport_name, address.transport_name,
        "transport_name mismatch after JSON roundtrip: "
        "{!r} != {!r}".format(restored.transport_name, address.transport_name),
    )

    testbase.assert_equal(
        restored.endpoint, address.endpoint,
        "endpoint mismatch after JSON roundtrip: "
        "{!r} != {!r}".format(restored.endpoint, address.endpoint),
    )

    return


# ---------------------------------------------------------------------------
# Property 10: AgentAddress equality and hash consistency
# ---------------------------------------------------------------------------

@given(
    agent_identifier=_identifier_strategy,
    transport_name=_transport_name_strategy,
    endpoint_a=_endpoint_strategy,
    endpoint_b=_endpoint_strategy,
    other_identifier=_identifier_strategy,
    other_transport=_transport_name_strategy,
    constraints={"max_examples": 15},
)
def test_agentaddress_equality_and_hash_consistency(
    agent_identifier: str,
    transport_name: str,
    endpoint_a: dict,
    endpoint_b: dict,
    other_identifier: str,
    other_transport: str,
) -> None:
    """
        **Validates: Requirements 9.9, 9.10**

        Same (agent_identifier, transport_name) implies equal and same hash,
        regardless of endpoint differences. Different agent_identifier or
        transport_name implies not equal.
    """
    addr_a = AgentAddress(
        agent_identifier=agent_identifier,
        transport_name=transport_name,
        endpoint=endpoint_a,
    )
    addr_b = AgentAddress(
        agent_identifier=agent_identifier,
        transport_name=transport_name,
        endpoint=endpoint_b,
    )

    testbase.assert_equal(
        addr_a, addr_b,
        "Addresses with same identifier and transport should be equal: "
        "agent_identifier={!r}, transport_name={!r}, "
        "endpoint_a={!r}, endpoint_b={!r}".format(
            agent_identifier, transport_name, endpoint_a, endpoint_b),
    )

    testbase.assert_equal(
        hash(addr_a), hash(addr_b),
        "Addresses with same identifier and transport should have same hash: "
        "agent_identifier={!r}, transport_name={!r}".format(
            agent_identifier, transport_name),
    )

    differs_in_identifier = (other_identifier != agent_identifier)
    differs_in_transport = (other_transport != transport_name)

    if differs_in_identifier:
        addr_diff_id = AgentAddress(
            agent_identifier=other_identifier,
            transport_name=transport_name,
            endpoint=endpoint_a,
        )
        testbase.assert_false(
            addr_a == addr_diff_id,
            "Addresses with different agent_identifier should not be equal: "
            "{!r} vs {!r}".format(agent_identifier, other_identifier),
        )

    if differs_in_transport:
        addr_diff_transport = AgentAddress(
            agent_identifier=agent_identifier,
            transport_name=other_transport,
            endpoint=endpoint_a,
        )
        testbase.assert_false(
            addr_a == addr_diff_transport,
            "Addresses with different transport_name should not be equal: "
            "{!r} vs {!r}".format(transport_name, other_transport),
        )

    return


# ---------------------------------------------------------------------------
# Property 11 (partial): Defensive copy for AgentAddress endpoint
# ---------------------------------------------------------------------------

@given(
    agent_identifier=_identifier_strategy,
    transport_name=_transport_name_strategy,
    endpoint=_endpoint_strategy,
    constraints={"max_examples": 30},
)
def test_agentaddress_endpoint_defensive_copy(
    agent_identifier: str,
    transport_name: str,
    endpoint: dict,
) -> None:
    """
        **Validates: Requirements 9.3**

        Modifying the dictionary returned by the endpoint property does not
        affect the internal state of the AgentAddress.
    """
    address = AgentAddress(
        agent_identifier=agent_identifier,
        transport_name=transport_name,
        endpoint=endpoint,
    )

    original_endpoint = address.endpoint

    returned_endpoint = address.endpoint
    returned_endpoint["__injected_key__"] = "injected_value"

    after_mutation_endpoint = address.endpoint

    testbase.assert_equal(
        after_mutation_endpoint, original_endpoint,
        "Endpoint should not be affected by mutation of returned copy: "
        "expected {!r}, got {!r} (agent_identifier={!r}, "
        "transport_name={!r})".format(
            original_endpoint, after_mutation_endpoint,
            agent_identifier, transport_name),
    )

    testbase.assert_false(
        "__injected_key__" in after_mutation_endpoint,
        "Injected key should not appear in endpoint after mutating "
        "returned copy (agent_identifier={!r}, "
        "transport_name={!r})".format(agent_identifier, transport_name),
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
