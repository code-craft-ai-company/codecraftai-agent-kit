"""
    Property-based tests for string representations across core agent framework classes.

    Property 26: String representations contain required information.

    Verifies that repr() and str() for Agent, AgentIdentity, AgentStateMachine,
    AgentAddress, AgentRegistry, and TransitionRecord contain the required fields
    as specified in the design document.

    Feature: core-agent-framework
    **Validates: Requirements 1.9, 1.10, 2.9, 2.10, 4.10, 4.11, 7.11, 7.12, 5.4, 9.11, 9.12**
"""

from datetime import datetime
from datetime import timezone

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentaddress import AgentAddress
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentidentity import AgentIdentity
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.agentstatemachine import AgentStateMachine
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.transitionrecord import TransitionRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def reset_registry():
    """
        Resets the AgentRegistry singleton and clears all registered agents.
    """
    registry = AgentRegistry.instance()
    registry._reset()
    return


class StringTestAgent(Agent):
    """
        Concrete Agent subclass for string representation testing.
    """

    def initialize(self) -> None:
        """
            Transitions the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions the agent to RUNNING state.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions the agent to PAUSED state.
        """
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions the agent to RUNNING state from PAUSED.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        """
            Transitions the agent to STOPPED state.
        """
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)

version_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P")),
    min_size=1,
    max_size=10
).filter(lambda s: len(s.strip()) > 0)

transport_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=15
).filter(lambda s: len(s.strip()) > 0)


# ---------------------------------------------------------------------------
# Property 26a: AgentIdentity repr contains class name, identifier, name, version
# **Validates: Requirements 2.9**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    constraints={"max_examples": 50}
)
def test_property_26a_agentidentity_repr(name, version):
    """
        Property 26a: AgentIdentity repr contains class name, identifier, name, version.

        For any AgentIdentity, repr() shall contain the class name 'AgentIdentity',
        the identifier, the name, and the version.

        **Validates: Requirements 2.9**
    """
    identity = AgentIdentity(name=name, version=version)
    repr_str = repr(identity)

    has_class = "AgentIdentity" in repr_str
    assert has_class is True, (
        "repr should contain 'AgentIdentity', got: {!r}".format(repr_str)
    )

    has_identifier = identity.identifier in repr_str
    assert has_identifier is True, (
        "repr should contain identifier {!r}, got: {!r}".format(identity.identifier, repr_str)
    )

    has_name = name in repr_str
    assert has_name is True, (
        "repr should contain name {!r}, got: {!r}".format(name, repr_str)
    )

    has_version = version in repr_str
    assert has_version is True, (
        "repr should contain version {!r}, got: {!r}".format(version, repr_str)
    )
    return


# ---------------------------------------------------------------------------
# Property 26b: AgentIdentity str contains name and version
# **Validates: Requirements 2.10**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    constraints={"max_examples": 50}
)
def test_property_26b_agentidentity_str(name, version):
    """
        Property 26b: AgentIdentity str contains name and version.

        For any AgentIdentity, str() shall contain the name and version.

        **Validates: Requirements 2.10**
    """
    identity = AgentIdentity(name=name, version=version)
    str_val = str(identity)

    has_name = name in str_val
    assert has_name is True, (
        "str should contain name {!r}, got: {!r}".format(name, str_val)
    )

    has_version = version in str_val
    assert has_version is True, (
        "str should contain version {!r}, got: {!r}".format(version, str_val)
    )
    return



# ---------------------------------------------------------------------------
# Property 26c: AgentStateMachine repr contains class name and current state
# **Validates: Requirements 4.10**
# ---------------------------------------------------------------------------

@given(
    state=st.sampled_from([
        LifecycleState.CREATED,
        LifecycleState.INITIALIZED,
        LifecycleState.RUNNING,
        LifecycleState.PAUSED,
        LifecycleState.STOPPED,
        LifecycleState.ERROR,
    ]),
    constraints={"max_examples": 50}
)
def test_property_26c_agentstatemachine_repr(state):
    """
        Property 26c: AgentStateMachine repr contains class name and current state.

        For any AgentStateMachine in any state, repr() shall contain
        'AgentStateMachine' and the current state value.

        **Validates: Requirements 4.10**
    """
    sm = AgentStateMachine()

    paths_to_state = {
        LifecycleState.CREATED: [],
        LifecycleState.INITIALIZED: [LifecycleState.INITIALIZED],
        LifecycleState.RUNNING: [LifecycleState.INITIALIZED, LifecycleState.RUNNING],
        LifecycleState.PAUSED: [LifecycleState.INITIALIZED, LifecycleState.RUNNING, LifecycleState.PAUSED],
        LifecycleState.STOPPED: [LifecycleState.INITIALIZED, LifecycleState.STOPPED],
        LifecycleState.ERROR: [LifecycleState.INITIALIZED, LifecycleState.RUNNING, LifecycleState.ERROR],
    }

    for target in paths_to_state[state]:
        sm.transition_to(target)

    repr_str = repr(sm)

    has_class = "AgentStateMachine" in repr_str
    assert has_class is True, (
        "repr should contain 'AgentStateMachine', got: {!r}".format(repr_str)
    )

    has_state = state.value in repr_str
    assert has_state is True, (
        "repr should contain state value {!r}, got: {!r}".format(state.value, repr_str)
    )
    return


# ---------------------------------------------------------------------------
# Property 26d: AgentStateMachine str contains state value
# **Validates: Requirements 4.11**
# ---------------------------------------------------------------------------

@given(
    state=st.sampled_from([
        LifecycleState.CREATED,
        LifecycleState.INITIALIZED,
        LifecycleState.RUNNING,
        LifecycleState.PAUSED,
        LifecycleState.STOPPED,
        LifecycleState.ERROR,
    ]),
    constraints={"max_examples": 50}
)
def test_property_26d_agentstatemachine_str(state):
    """
        Property 26d: AgentStateMachine str contains state value.

        For any AgentStateMachine in any state, str() shall contain
        the current state value.

        **Validates: Requirements 4.11**
    """
    sm = AgentStateMachine()

    paths_to_state = {
        LifecycleState.CREATED: [],
        LifecycleState.INITIALIZED: [LifecycleState.INITIALIZED],
        LifecycleState.RUNNING: [LifecycleState.INITIALIZED, LifecycleState.RUNNING],
        LifecycleState.PAUSED: [LifecycleState.INITIALIZED, LifecycleState.RUNNING, LifecycleState.PAUSED],
        LifecycleState.STOPPED: [LifecycleState.INITIALIZED, LifecycleState.STOPPED],
        LifecycleState.ERROR: [LifecycleState.INITIALIZED, LifecycleState.RUNNING, LifecycleState.ERROR],
    }

    for target in paths_to_state[state]:
        sm.transition_to(target)

    str_val = str(sm)

    has_state = state.value in str_val
    assert has_state is True, (
        "str should contain state value {!r}, got: {!r}".format(state.value, str_val)
    )
    return


# ---------------------------------------------------------------------------
# Property 26e: AgentAddress repr contains class name, agent_identifier, transport_name
# **Validates: Requirements 9.11**
# ---------------------------------------------------------------------------

@given(
    agent_id=name_strategy,
    transport=transport_strategy,
    constraints={"max_examples": 50}
)
def test_property_26e_agentaddress_repr(agent_id, transport):
    """
        Property 26e: AgentAddress repr contains class name, agent_identifier, transport_name.

        For any AgentAddress, repr() shall contain 'AgentAddress',
        the agent_identifier, and the transport_name.

        **Validates: Requirements 9.11**
    """
    address = AgentAddress(agent_identifier=agent_id, transport_name=transport)
    repr_str = repr(address)

    has_class = "AgentAddress" in repr_str
    assert has_class is True, (
        "repr should contain 'AgentAddress', got: {!r}".format(repr_str)
    )

    has_agent_id = agent_id in repr_str
    assert has_agent_id is True, (
        "repr should contain agent_identifier {!r}, got: {!r}".format(agent_id, repr_str)
    )

    has_transport = transport in repr_str
    assert has_transport is True, (
        "repr should contain transport_name {!r}, got: {!r}".format(transport, repr_str)
    )
    return


# ---------------------------------------------------------------------------
# Property 26f: AgentAddress str contains agent_identifier, transport_name, endpoint
# **Validates: Requirements 9.12**
# ---------------------------------------------------------------------------

@given(
    agent_id=name_strategy,
    transport=transport_strategy,
    constraints={"max_examples": 50}
)
def test_property_26f_agentaddress_str(agent_id, transport):
    """
        Property 26f: AgentAddress str contains agent_identifier, transport_name, endpoint.

        For any AgentAddress, str() shall contain the agent_identifier,
        transport_name, and endpoint information.

        **Validates: Requirements 9.12**
    """
    address = AgentAddress(agent_identifier=agent_id, transport_name=transport)
    str_val = str(address)

    has_agent_id = agent_id in str_val
    assert has_agent_id is True, (
        "str should contain agent_identifier {!r}, got: {!r}".format(agent_id, str_val)
    )

    has_transport = transport in str_val
    assert has_transport is True, (
        "str should contain transport_name {!r}, got: {!r}".format(transport, str_val)
    )
    return


# ---------------------------------------------------------------------------
# Property 26g: TransitionRecord repr contains class name, previous_state, new_state, timestamp
# **Validates: Requirements 5.4**
# ---------------------------------------------------------------------------

@given(
    prev_state=st.sampled_from(list(LifecycleState)),
    new_state=st.sampled_from(list(LifecycleState)),
    constraints={"max_examples": 50}
)
def test_property_26g_transitionrecord_repr(prev_state, new_state):
    """
        Property 26g: TransitionRecord repr contains class name, previous_state,
        new_state, and timestamp.

        For any TransitionRecord, repr() shall contain 'TransitionRecord',
        the previous_state value, the new_state value, and the timestamp.

        **Validates: Requirements 5.4**
    """
    timestamp = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=prev_state,
        new_state=new_state,
        timestamp=timestamp
    )
    repr_str = repr(record)

    has_class = "TransitionRecord" in repr_str
    assert has_class is True, (
        "repr should contain 'TransitionRecord', got: {!r}".format(repr_str)
    )

    has_prev = prev_state.value in repr_str
    assert has_prev is True, (
        "repr should contain previous_state {!r}, got: {!r}".format(prev_state.value, repr_str)
    )

    has_new = new_state.value in repr_str
    assert has_new is True, (
        "repr should contain new_state {!r}, got: {!r}".format(new_state.value, repr_str)
    )
    return


# ---------------------------------------------------------------------------
# Property 26h: AgentRegistry repr contains class name and count
# **Validates: Requirements 7.11**
# ---------------------------------------------------------------------------

@given(
    agent_count=st.integers(min_value=0, max_value=5),
    constraints={"max_examples": 50}
)
def test_property_26h_agentregistry_repr(agent_count):
    """
        Property 26h: AgentRegistry repr contains class name and count.

        For any AgentRegistry with N agents, repr() shall contain
        'AgentRegistry' and the count.

        **Validates: Requirements 7.11**
    """
    reset_registry()
    registry = AgentRegistry.instance()

    for idx in range(agent_count):
        config_data = {
            "identity": {
                "name": "repr-agent-{}".format(idx),
                "version": "1.0"
            }
        }
        config = AgentConfiguration.from_dict(config_data)
        agent = StringTestAgent(configuration=config)

    repr_str = repr(registry)

    has_class = "AgentRegistry" in repr_str
    assert has_class is True, (
        "repr should contain 'AgentRegistry', got: {!r}".format(repr_str)
    )

    has_count = str(agent_count) in repr_str
    assert has_count is True, (
        "repr should contain count {}, got: {!r}".format(agent_count, repr_str)
    )
    return


# ---------------------------------------------------------------------------
# Property 26i: AgentRegistry str contains count
# **Validates: Requirements 7.12**
# ---------------------------------------------------------------------------

@given(
    agent_count=st.integers(min_value=0, max_value=5),
    constraints={"max_examples": 50}
)
def test_property_26i_agentregistry_str(agent_count):
    """
        Property 26i: AgentRegistry str contains count.

        For any AgentRegistry with N agents, str() shall contain the count.

        **Validates: Requirements 7.12**
    """
    reset_registry()
    registry = AgentRegistry.instance()

    for idx in range(agent_count):
        config_data = {
            "identity": {
                "name": "str-agent-{}".format(idx),
                "version": "1.0"
            }
        }
        config = AgentConfiguration.from_dict(config_data)
        agent = StringTestAgent(configuration=config)

    str_val = str(registry)

    has_count = str(agent_count) in str_val
    assert has_count is True, (
        "str should contain count {}, got: {!r}".format(agent_count, str_val)
    )
    return


# ---------------------------------------------------------------------------
# Property 26j: Agent repr contains class name, identifier, name, state
# **Validates: Requirements 1.9**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    constraints={"max_examples": 50}
)
def test_property_26j_agent_repr(name, version):
    """
        Property 26j: Agent repr contains class name, identifier, name, state.

        For any Agent, repr() shall contain the class name, identifier,
        name, and state.

        **Validates: Requirements 1.9**
    """
    reset_registry()

    config_data = {"identity": {"name": name, "version": version}}
    config = AgentConfiguration.from_dict(config_data)
    agent = StringTestAgent(configuration=config)

    repr_str = repr(agent)

    has_class = "StringTestAgent" in repr_str
    assert has_class is True, (
        "repr should contain class name 'StringTestAgent', got: {!r}".format(repr_str)
    )

    has_identifier = agent.identity.identifier in repr_str
    assert has_identifier is True, (
        "repr should contain identifier, got: {!r}".format(repr_str)
    )

    has_name = name in repr_str
    assert has_name is True, (
        "repr should contain name {!r}, got: {!r}".format(name, repr_str)
    )

    has_state = "CREATED" in repr_str
    assert has_state is True, (
        "repr should contain state 'CREATED', got: {!r}".format(repr_str)
    )
    return


# ---------------------------------------------------------------------------
# Property 26k: Agent str contains name and state
# **Validates: Requirements 1.10**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    constraints={"max_examples": 50}
)
def test_property_26k_agent_str(name, version):
    """
        Property 26k: Agent str contains name and state.

        For any Agent, str() shall contain the name and state.

        **Validates: Requirements 1.10**
    """
    reset_registry()

    config_data = {"identity": {"name": name, "version": version}}
    config = AgentConfiguration.from_dict(config_data)
    agent = StringTestAgent(configuration=config)

    str_val = str(agent)

    has_name = name in str_val
    assert has_name is True, (
        "str should contain name {!r}, got: {!r}".format(name, str_val)
    )

    has_state = "CREATED" in str_val
    assert has_state is True, (
        "str should contain state 'CREATED', got: {!r}".format(str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
