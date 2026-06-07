"""
    Tests for the ccai.agentkit.agentregistry module.

    Contains property-based tests (using ccai.testbase.properties) and unit tests
    for the AgentRegistry class.

    Feature: core-agent-framework
"""

import threading


from ccai.testbase.properties import given, assume
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.agentidentity import AgentIdentity
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.errors import SemanticError
from ccai.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Helper: create a mock agent with an AgentIdentity
# ---------------------------------------------------------------------------

def create_mock_agent(name, version, tags=None, identifier=None):
    """
        Creates a mock agent with an AgentIdentity attached.

        :param name: The agent name.
        :param version: The agent version.
        :param tags: Optional dictionary of tags.
        :param identifier: Optional explicit identifier.

        :returns: A Mock object with an identity property.
    """
    identity = AgentIdentity(name=name, version=version, tags=tags, identifier=identifier)
    mock_agent = Mock()
    mock_agent.configure(recursive=True)
    ctx = mock_agent.mock_context()
    ctx.set_attribute("identity", identity)
    return mock_agent


def reset_registry():
    """
        Resets the AgentRegistry singleton and clears all registered agents.
    """
    registry = AgentRegistry.instance()
    registry._reset()
    return


# ---------------------------------------------------------------------------
# testbase property strategies for generating agent data
# ---------------------------------------------------------------------------

name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

version_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P")),
    min_size=1,
    max_size=15
).filter(lambda s: len(s.strip()) > 0)

tags_strategy = st.dictionaries(
    keys=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=15
    ),
    values=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=15
    ),
    max_size=5
)

@composite
def _uuid_string(draw):
    """
        Generates a valid UUID v4 string.

        :returns: A UUID v4 formatted string.
    """
    segments = [
        draw(st.integers(min_value=0, max_value=0xFFFFFFFF)),
        draw(st.integers(min_value=0, max_value=0xFFFF)),
        draw(st.integers(min_value=0x4000, max_value=0x4FFF)),
        draw(st.integers(min_value=0x8000, max_value=0xBFFF)),
        draw(st.integers(min_value=0, max_value=0xFFFFFFFFFFFF)),
    ]
    return f"{segments[0]:08x}-{segments[1]:04x}-{segments[2]:04x}-{segments[3]:04x}-{segments[4]:012x}"


identifier_strategy = _uuid_string()


@composite
def _property_15_data(draw, agent_count):
    """
        Generates test data for property 15: unique identifiers, names, versions, and tags.

        :param agent_count: Number of agents to generate data for.

        :returns: A tuple of (identifiers, names, versions, tags_list).
    """
    identifiers = []
    used = set()
    for _ in range(agent_count):
        ident = draw(identifier_strategy)
        while ident in used:
            ident = draw(identifier_strategy)
        used.add(ident)
        identifiers.append(ident)
    names = [draw(name_strategy) for _ in range(agent_count)]
    versions = [draw(version_strategy) for _ in range(agent_count)]
    tags_list = [draw(tags_strategy) for _ in range(agent_count)]
    return (identifiers, names, versions, tags_list)


# ---------------------------------------------------------------------------
# Property 15: Registry registration and lookup correctness
# **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.9**
# ---------------------------------------------------------------------------

@composite
def _property_15_agents(draw):
    """
        Generates a list of mock agents with unique identifiers for property 15.

        :returns: A list of mock agents.
    """
    agent_count = draw(st.integers(min_value=1, max_value=10))
    identifiers = []
    used = set()
    for _ in range(agent_count):
        ident = draw(identifier_strategy)
        while ident in used:
            ident = draw(identifier_strategy)
        used.add(ident)
        identifiers.append(ident)

    agents = []
    for idx in range(agent_count):
        name = draw(name_strategy)
        version = draw(version_strategy)
        tags = draw(tags_strategy)
        agent = create_mock_agent(
            name=name,
            version=version,
            tags=tags,
            identifier=identifiers[idx]
        )
        agents.append(agent)
    return agents


@given(
    agents=_property_15_agents(),
    constraints={"max_examples": 100})
def test_property_15_registration_and_lookup_correctness(agents):
    """
        Property 15: Registry registration and lookup correctness.

        For any set of N agents with unique identifiers:
        (a) count equals N,
        (b) lookup_by_id returns the correct agent or None,
        (c) lookup_by_name returns exactly matching agents,
        (d) lookup_by_tags returns agents matching all criteria,
        (e) list_all returns all N agents,
        (f) duplicate identifier raises SemanticError.

        **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.9**
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent_count = len(agents)

    # Register all agents
    for agent in agents:
        registry.register(agent)

    # (a) count equals N
    actual_count = registry.count
    assert actual_count == agent_count, (
        "Registry count should be {} but was {}".format(agent_count, actual_count)
    )

    # (b) lookup_by_id returns the correct agent
    for agent in agents:
        found = registry.lookup_by_id(agent.identity.identifier)
        assert found is agent, (
            "lookup_by_id should return the registered agent for identifier {!r}".format(
                agent.identity.identifier
            )
        )

    # lookup_by_id returns None for unknown identifier
    unknown_result = registry.lookup_by_id("nonexistent-identifier-xyz")
    assert unknown_result is None, "lookup_by_id should return None for unknown identifier"

    # (c) lookup_by_name returns exactly matching agents
    for agent in agents:
        agent_name = agent.identity.name
        found_by_name = registry.lookup_by_name(agent_name)
        is_in_results = agent in found_by_name
        assert is_in_results is True, (
            "lookup_by_name should include agent with name {!r}".format(agent_name)
        )
        # All results should have the matching name
        for found_agent in found_by_name:
            assert found_agent.identity.name == agent_name, (
                "All agents returned by lookup_by_name should have name {!r}".format(agent_name)
            )

    # (d) lookup_by_tags returns agents matching all criteria
    for agent in agents:
        agent_tags = agent.identity.tags
        if len(agent_tags) > 0:
            found_by_tags = registry.lookup_by_tags(**agent_tags)
            is_in_results = agent in found_by_tags
            assert is_in_results is True, (
                "lookup_by_tags should include agent matching tags {!r}".format(agent_tags)
            )

    # (e) list_all returns all N agents
    all_agents = registry.list_all()
    all_count = len(all_agents)
    assert all_count == agent_count, (
        "list_all should return {} agents but returned {}".format(agent_count, all_count)
    )
    for agent in agents:
        is_in_all = agent in all_agents
        assert is_in_all is True, "list_all should contain all registered agents"

    # (f) duplicate identifier raises SemanticError
    if len(agents) > 0:
        duplicate_agent = create_mock_agent(
            name="duplicate",
            version="1.0",
            identifier=agents[0].identity.identifier
        )
        raised = False
        try:
            registry.register(duplicate_agent)
        except SemanticError:
            raised = True

        assert raised is True, (
            "Registering a duplicate identifier should raise SemanticError"
        )

    return


# ---------------------------------------------------------------------------
# Property 16: Registry deregistration removes agent
# **Validates: Requirements 6.8**
# ---------------------------------------------------------------------------

@composite
def _property_16_data(draw):
    """
        Generates test data for property 16: agents and a deregister index.

        :returns: A tuple of (agents, deregister_idx).
    """
    agent_count = draw(st.integers(min_value=2, max_value=10))
    identifiers = []
    used = set()
    for _ in range(agent_count):
        ident = draw(identifier_strategy)
        while ident in used:
            ident = draw(identifier_strategy)
        used.add(ident)
        identifiers.append(ident)

    agents = []
    for idx in range(agent_count):
        name = draw(name_strategy)
        version = draw(version_strategy)
        agent = create_mock_agent(
            name=name,
            version=version,
            identifier=identifiers[idx]
        )
        agents.append(agent)

    deregister_idx = draw(st.integers(min_value=0, max_value=agent_count - 1))
    return (agents, deregister_idx)


@given(
    test_data=_property_16_data(),
    constraints={"max_examples": 100})
def test_property_16_deregistration_removes_agent(test_data):
    """
        Property 16: Registry deregistration removes agent.

        For any registered agent, deregister removes it so lookup_by_id
        returns None and count decreases by one.

        **Validates: Requirements 6.8**
    """
    agents, deregister_idx = test_data
    agent_count = len(agents)

    reset_registry()
    registry = AgentRegistry.instance()

    # Register all agents
    for agent in agents:
        registry.register(agent)

    initial_count = registry.count
    assert initial_count == agent_count, (
        "Initial count should be {} but was {}".format(agent_count, initial_count)
    )

    # Pick the agent to deregister
    agent_to_remove = agents[deregister_idx]
    remove_identifier = agent_to_remove.identity.identifier

    registry.deregister(remove_identifier)

    # Verify count decreased
    new_count = registry.count
    expected_count = agent_count - 1
    assert new_count == expected_count, (
        "Count after deregister should be {} but was {}".format(expected_count, new_count)
    )

    # Verify lookup_by_id returns None for deregistered agent
    lookup_result = registry.lookup_by_id(remove_identifier)
    assert lookup_result is None, (
        "lookup_by_id should return None for deregistered identifier {!r}".format(
            remove_identifier
        )
    )

    # Verify remaining agents are still present
    for idx in range(agent_count):
        if idx == deregister_idx:
            continue
        remaining_agent = agents[idx]
        found = registry.lookup_by_id(remaining_agent.identity.identifier)
        assert found is remaining_agent, (
            "Remaining agent with identifier {!r} should still be in registry".format(
                remaining_agent.identity.identifier
            )
        )

    return


# ---------------------------------------------------------------------------
# Unit tests for AgentRegistry edge cases (Task 7.4)
# **Validates: Requirements 6.1, 13.7**
# ---------------------------------------------------------------------------

def test_singleton_returns_same_instance():
    """
        Verify that AgentRegistry.instance() returns the same instance
        on multiple calls.
    """
    reset_registry()

    instance_one = AgentRegistry.instance()
    instance_two = AgentRegistry.instance()

    is_same = instance_one is instance_two
    assert is_same is True, "AgentRegistry.instance() should return the same singleton"
    return


def test_thread_safety_concurrent_registration():
    """
        Verify that concurrent registration does not corrupt the registry.

        Multiple threads register agents concurrently. The registry should
        remain consistent with no unexpected errors.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent_count = 20
    agents = []
    for idx in range(agent_count):
        agent = create_mock_agent(
            name="agent-{}".format(idx),
            version="1.0",
            identifier="concurrent-id-{}".format(idx)
        )
        agents.append(agent)

    errors = []

    def register_agent(agent_to_register):
        """
            Registers an agent, recording any unexpected errors.

            :param agent_to_register: The agent to register.
        """
        try:
            registry.register(agent_to_register)
        except Exception as exc:
            errors.append(exc)
        return

    threads = []
    for agent in agents:
        t = threading.Thread(target=register_agent, args=(agent,))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    unexpected_error_count = len(errors)
    assert unexpected_error_count == 0, (
        "No unexpected errors should occur during concurrent registration, got: {}".format(errors)
    )

    final_count = registry.count
    assert final_count == agent_count, (
        "Registry should contain {} agents after concurrent registration, got {}".format(
            agent_count, final_count
        )
    )
    return


def test_lookup_by_tags_no_matches_returns_empty_list():
    """
        Verify that lookup_by_tags returns an empty list when no agents match.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent = create_mock_agent(
        name="tagged-agent",
        version="1.0",
        tags={"env": "prod"},
        identifier="tagged-agent-id"
    )
    registry.register(agent)

    result = registry.lookup_by_tags(env="staging")
    result_count = len(result)
    assert result_count == 0, (
        "lookup_by_tags should return empty list when no agents match, got {}".format(result_count)
    )
    return


def test_lookup_by_tags_with_no_tags_returns_all():
    """
        Verify that lookup_by_tags with no tag criteria returns all agents.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent_one = create_mock_agent(
        name="agent-one",
        version="1.0",
        tags={"env": "prod"},
        identifier="agent-one-id"
    )
    agent_two = create_mock_agent(
        name="agent-two",
        version="2.0",
        tags={"env": "dev"},
        identifier="agent-two-id"
    )
    registry.register(agent_one)
    registry.register(agent_two)

    result = registry.lookup_by_tags()
    result_count = len(result)
    assert result_count == 2, (
        "lookup_by_tags with no criteria should return all agents, got {}".format(result_count)
    )
    return


def test_lookup_by_name_no_matches_returns_empty_list():
    """
        Verify that lookup_by_name returns an empty list when no agents match.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent = create_mock_agent(
        name="existing-agent",
        version="1.0",
        identifier="existing-agent-id"
    )
    registry.register(agent)

    result = registry.lookup_by_name("nonexistent-agent")
    result_count = len(result)
    assert result_count == 0, (
        "lookup_by_name should return empty list when no agents match, got {}".format(result_count)
    )
    return


def test_deregister_nonexistent_identifier_is_noop():
    """
        Verify that deregistering a nonexistent identifier does not raise an error.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent = create_mock_agent(
        name="agent",
        version="1.0",
        identifier="agent-id"
    )
    registry.register(agent)

    # Should not raise
    registry.deregister("nonexistent-id")

    count = registry.count
    assert count == 1, "Count should remain 1 after deregistering nonexistent identifier"
    return


def test_empty_registry_count_is_zero():
    """
        Verify that an empty registry has a count of zero.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    count = registry.count
    assert count == 0, "Empty registry should have count 0"
    return


def test_empty_registry_list_all_returns_empty():
    """
        Verify that list_all on an empty registry returns an empty list.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    all_agents = registry.list_all()
    count = len(all_agents)
    assert count == 0, "list_all on empty registry should return empty list"
    return


def test_lookup_by_tags_partial_match_excluded():
    """
        Verify that lookup_by_tags only returns agents matching ALL tag criteria,
        not partial matches.
    """
    reset_registry()
    registry = AgentRegistry.instance()

    agent = create_mock_agent(
        name="partial-agent",
        version="1.0",
        tags={"env": "prod"},
        identifier="partial-agent-id"
    )
    registry.register(agent)

    # Search for two tags, agent only has one
    result = registry.lookup_by_tags(env="prod", region="us-east")
    result_count = len(result)
    assert result_count == 0, (
        "lookup_by_tags should not return agents with only partial tag matches, got {}".format(
            result_count
        )
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
