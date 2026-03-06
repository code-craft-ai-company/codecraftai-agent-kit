"""
    Integration tests for the automojo.agentkit package.

    Tests end-to-end agent lifecycle, sub-agent hierarchy with lifecycle
    cascading, and registry tracking through the full lifecycle.

    Feature: core-agent-framework
"""

import os

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentidentity import AgentIdentity
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.agentstatemachine import AgentStateMachine
from automojo.agentkit.concurrencymodel import ConcurrencyModel
from automojo.agentkit.errors import AgentKitError
from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.errors import LifecycleError
from automojo.agentkit.errors import SemanticError
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


class IntegrationAgent(Agent):
    """
        Concrete Agent subclass for integration testing.

        Tracks lifecycle method invocations for verification.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        super().__init__(configuration)
        self._lifecycle_calls: list = []
        return

    @property
    def lifecycle_calls(self) -> list:
        """
            Returns the list of lifecycle method names invoked on this agent.

            :returns: A list of strings.
        """
        return list(self._lifecycle_calls)

    def initialize(self) -> None:
        """
            Transitions the agent to INITIALIZED state.
        """
        self._lifecycle_calls.append("initialize")
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions the agent to RUNNING state.
        """
        self._lifecycle_calls.append("start")
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions the agent to PAUSED state.

            Cascades pause to RUNNING sub-agents.
        """
        self._lifecycle_calls.append("pause")
        for sub in list(self.sub_agents):
            if sub.state is LifecycleState.RUNNING:
                sub.pause()
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions the agent to RUNNING state from PAUSED.

            Cascades resume to PAUSED sub-agents.
        """
        self._lifecycle_calls.append("resume")
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        for sub in list(self.sub_agents):
            if sub.state is LifecycleState.PAUSED:
                sub.resume()
        return

    def stop(self) -> None:
        """
            Stops all sub-agents then transitions to STOPPED state.
        """
        self._lifecycle_calls.append("stop")
        for sub in list(self.sub_agents):
            if sub.state is not LifecycleState.STOPPED:
                sub.stop()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._lifecycle_calls.append("reset")
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def force_error(self) -> None:
        """
            Forces the agent into ERROR state for testing.
        """
        self._lifecycle_calls.append("force_error")
        self._perform_transition(LifecycleState.ERROR, "on_error")
        return


def create_integration_agent(name: str = "integration-agent", version: str = "1.0",
                             tags: dict = None, identifier: str = None) -> IntegrationAgent:
    """
        Creates an IntegrationAgent with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.
        :param tags: Optional tags dictionary.
        :param identifier: Optional explicit identifier.

        :returns: An IntegrationAgent instance.
    """
    identity_data = {"name": name, "version": version}

    if tags is not None:
        identity_data["tags"] = tags

    if identifier is not None:
        identity_data["identifier"] = identifier

    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    agent = IntegrationAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# Integration Test: Full lifecycle (create -> initialize -> start ->
#                   pause -> resume -> stop)
# ---------------------------------------------------------------------------

def test_full_lifecycle_transitions():
    """
        Tests the complete agent lifecycle from creation through all
        state transitions: CREATED -> INITIALIZED -> RUNNING -> PAUSED ->
        RUNNING -> STOPPED.

        Verifies that each transition updates the state correctly and
        that the transition history records all transitions.
    """
    reset_registry()

    agent = create_integration_agent(name="lifecycle-agent", version="2.0")

    initial_state = agent.state
    assert initial_state is LifecycleState.CREATED, \
        "Expected CREATED but got {}".format(initial_state)

    agent.initialize()
    state_after_init = agent.state
    assert state_after_init is LifecycleState.INITIALIZED, \
        "Expected INITIALIZED but got {}".format(state_after_init)

    agent.start()
    state_after_start = agent.state
    assert state_after_start is LifecycleState.RUNNING, \
        "Expected RUNNING but got {}".format(state_after_start)

    agent.pause()
    state_after_pause = agent.state
    assert state_after_pause is LifecycleState.PAUSED, \
        "Expected PAUSED but got {}".format(state_after_pause)

    agent.resume()
    state_after_resume = agent.state
    assert state_after_resume is LifecycleState.RUNNING, \
        "Expected RUNNING after resume but got {}".format(state_after_resume)

    agent.stop()
    state_after_stop = agent.state
    assert state_after_stop is LifecycleState.STOPPED, \
        "Expected STOPPED but got {}".format(state_after_stop)

    expected_calls = ["initialize", "start", "pause", "resume", "stop"]
    actual_calls = agent.lifecycle_calls
    assert actual_calls == expected_calls, \
        "Expected lifecycle calls {} but got {}".format(expected_calls, actual_calls)

    history = agent._state_machine.transition_history
    history_len = len(history)
    assert history_len == 5, \
        "Expected 5 transition records but got {}".format(history_len)

    expected_transitions = [
        (LifecycleState.CREATED, LifecycleState.INITIALIZED),
        (LifecycleState.INITIALIZED, LifecycleState.RUNNING),
        (LifecycleState.RUNNING, LifecycleState.PAUSED),
        (LifecycleState.PAUSED, LifecycleState.RUNNING),
        (LifecycleState.RUNNING, LifecycleState.STOPPED),
    ]

    for idx in range(history_len):
        record = history[idx]
        expected_prev = expected_transitions[idx][0]
        expected_new = expected_transitions[idx][1]
        assert record.previous_state is expected_prev, \
            "Record {} previous_state: expected {} got {}".format(idx, expected_prev, record.previous_state)
        assert record.new_state is expected_new, \
            "Record {} new_state: expected {} got {}".format(idx, expected_new, record.new_state)

    return


# ---------------------------------------------------------------------------
# Integration Test: Lifecycle with hooks
# ---------------------------------------------------------------------------

def test_lifecycle_with_hooks():
    """
        Tests that hooks are invoked at each lifecycle transition point
        during a full lifecycle sequence.
    """
    reset_registry()

    hook_invocations = []

    def on_initialize_hook(agent, record):
        hook_invocations.append("on_initialize")
        return

    def on_start_hook(agent, record):
        hook_invocations.append("on_start")
        return

    def on_pause_hook(agent, record):
        hook_invocations.append("on_pause")
        return

    def on_resume_hook(agent, record):
        hook_invocations.append("on_resume")
        return

    def on_stop_hook(agent, record):
        hook_invocations.append("on_stop")
        return

    agent = create_integration_agent(name="hook-agent", version="1.0")

    agent.register_hook("on_initialize", on_initialize_hook)
    agent.register_hook("on_start", on_start_hook)
    agent.register_hook("on_pause", on_pause_hook)
    agent.register_hook("on_resume", on_resume_hook)
    agent.register_hook("on_stop", on_stop_hook)

    agent.initialize()
    agent.start()
    agent.pause()
    agent.resume()
    agent.stop()

    expected_hooks = ["on_initialize", "on_start", "on_pause", "on_resume", "on_stop"]
    assert hook_invocations == expected_hooks, \
        "Expected hook invocations {} but got {}".format(expected_hooks, hook_invocations)

    return


# ---------------------------------------------------------------------------
# Integration Test: Sub-agent hierarchy with lifecycle cascading
# ---------------------------------------------------------------------------

def test_sub_agent_hierarchy_stop_cascading():
    """
        Tests that stopping a parent agent cascades stop to all
        sub-agents in the hierarchy.
    """
    reset_registry()

    parent = create_integration_agent(name="parent", version="1.0")
    child_a = create_integration_agent(name="child-a", version="1.0")
    child_b = create_integration_agent(name="child-b", version="1.0")

    parent.add_sub_agent(child_a)
    parent.add_sub_agent(child_b)

    parent.initialize()
    parent.start()
    child_a.initialize()
    child_a.start()
    child_b.initialize()
    child_b.start()

    parent_state = parent.state
    child_a_state = child_a.state
    child_b_state = child_b.state
    assert parent_state is LifecycleState.RUNNING, \
        "Expected parent RUNNING but got {}".format(parent_state)
    assert child_a_state is LifecycleState.RUNNING, \
        "Expected child_a RUNNING but got {}".format(child_a_state)
    assert child_b_state is LifecycleState.RUNNING, \
        "Expected child_b RUNNING but got {}".format(child_b_state)

    parent.stop()

    parent_state_after = parent.state
    child_a_state_after = child_a.state
    child_b_state_after = child_b.state
    assert parent_state_after is LifecycleState.STOPPED, \
        "Expected parent STOPPED but got {}".format(parent_state_after)
    assert child_a_state_after is LifecycleState.STOPPED, \
        "Expected child_a STOPPED but got {}".format(child_a_state_after)
    assert child_b_state_after is LifecycleState.STOPPED, \
        "Expected child_b STOPPED but got {}".format(child_b_state_after)

    return


def test_sub_agent_hierarchy_pause_cascading():
    """
        Tests that pausing a parent agent cascades pause to RUNNING
        sub-agents.
    """
    reset_registry()

    parent = create_integration_agent(name="parent", version="1.0")
    child = create_integration_agent(name="child", version="1.0")

    parent.add_sub_agent(child)

    parent.initialize()
    parent.start()
    child.initialize()
    child.start()

    parent.pause()

    parent_state = parent.state
    child_state = child.state
    assert parent_state is LifecycleState.PAUSED, \
        "Expected parent PAUSED but got {}".format(parent_state)
    assert child_state is LifecycleState.PAUSED, \
        "Expected child PAUSED but got {}".format(child_state)

    return


def test_sub_agent_hierarchy_resume_cascading():
    """
        Tests that resuming a parent agent cascades resume to PAUSED
        sub-agents.
    """
    reset_registry()

    parent = create_integration_agent(name="parent", version="1.0")
    child = create_integration_agent(name="child", version="1.0")

    parent.add_sub_agent(child)

    parent.initialize()
    parent.start()
    child.initialize()
    child.start()

    parent.pause()

    parent_state = parent.state
    child_state = child.state
    assert parent_state is LifecycleState.PAUSED, \
        "Expected parent PAUSED but got {}".format(parent_state)
    assert child_state is LifecycleState.PAUSED, \
        "Expected child PAUSED but got {}".format(child_state)

    parent.resume()

    parent_state_after = parent.state
    child_state_after = child.state
    assert parent_state_after is LifecycleState.RUNNING, \
        "Expected parent RUNNING but got {}".format(parent_state_after)
    assert child_state_after is LifecycleState.RUNNING, \
        "Expected child RUNNING but got {}".format(child_state_after)

    return


# ---------------------------------------------------------------------------
# Integration Test: Registry tracks agents through full lifecycle
# ---------------------------------------------------------------------------

def test_registry_tracks_agents_through_lifecycle():
    """
        Tests that the AgentRegistry correctly tracks agents as they
        are created, go through lifecycle transitions, and are deregistered.
    """
    reset_registry()

    registry = AgentRegistry.instance()

    agent_a = create_integration_agent(name="tracked-a", version="1.0",
                                       tags={"role": "worker"})
    agent_b = create_integration_agent(name="tracked-b", version="2.0",
                                       tags={"role": "manager"})

    count_after_create = registry.count
    assert count_after_create == 2, \
        "Expected 2 registered agents but got {}".format(count_after_create)

    found_a = registry.lookup_by_id(agent_a.identity.identifier)
    assert found_a is agent_a, \
        "Expected to find agent_a by identifier"

    found_b = registry.lookup_by_id(agent_b.identity.identifier)
    assert found_b is agent_b, \
        "Expected to find agent_b by identifier"

    found_by_name = registry.lookup_by_name("tracked-a")
    found_by_name_len = len(found_by_name)
    assert found_by_name_len == 1, \
        "Expected 1 agent named tracked-a but got {}".format(found_by_name_len)
    assert found_by_name[0] is agent_a, \
        "Expected agent_a in name lookup result"

    found_by_tags = registry.lookup_by_tags(role="manager")
    found_by_tags_len = len(found_by_tags)
    assert found_by_tags_len == 1, \
        "Expected 1 agent with role=manager but got {}".format(found_by_tags_len)
    assert found_by_tags[0] is agent_b, \
        "Expected agent_b in tag lookup result"

    agent_a.initialize()
    agent_a.start()
    agent_a.stop()

    state_after_stop = agent_a.state
    assert state_after_stop is LifecycleState.STOPPED, \
        "Expected agent_a STOPPED but got {}".format(state_after_stop)

    still_found = registry.lookup_by_id(agent_a.identity.identifier)
    assert still_found is agent_a, \
        "Expected agent_a still in registry after stop"

    registry.deregister(agent_a.identity.identifier)

    count_after_deregister = registry.count
    assert count_after_deregister == 1, \
        "Expected 1 registered agent after deregister but got {}".format(count_after_deregister)

    not_found = registry.lookup_by_id(agent_a.identity.identifier)
    assert not_found is None, \
        "Expected None after deregistering agent_a"

    all_agents = registry.list_all()
    all_agents_len = len(all_agents)
    assert all_agents_len == 1, \
        "Expected 1 agent in list_all but got {}".format(all_agents_len)
    assert all_agents[0] is agent_b, \
        "Expected agent_b in list_all result"

    return


# ---------------------------------------------------------------------------
# Integration Test: Package imports from __init__.py
# ---------------------------------------------------------------------------

def test_package_imports():
    """
        Tests that all public classes can be imported from the
        automojo.agentkit package namespace.
    """
    import automojo.agentkit as agentkit

    has_agent = hasattr(agentkit, "Agent")
    assert has_agent is True, "Agent not found in agentkit namespace"

    has_identity = hasattr(agentkit, "AgentIdentity")
    assert has_identity is True, "AgentIdentity not found in agentkit namespace"

    has_config = hasattr(agentkit, "AgentConfiguration")
    assert has_config is True, "AgentConfiguration not found in agentkit namespace"

    has_sm = hasattr(agentkit, "AgentStateMachine")
    assert has_sm is True, "AgentStateMachine not found in agentkit namespace"

    has_registry = hasattr(agentkit, "AgentRegistry")
    assert has_registry is True, "AgentRegistry not found in agentkit namespace"

    has_lifecycle = hasattr(agentkit, "LifecycleState")
    assert has_lifecycle is True, "LifecycleState not found in agentkit namespace"

    has_record = hasattr(agentkit, "TransitionRecord")
    assert has_record is True, "TransitionRecord not found in agentkit namespace"

    has_concurrency = hasattr(agentkit, "ConcurrencyModel")
    assert has_concurrency is True, "ConcurrencyModel not found in agentkit namespace"

    has_async = hasattr(agentkit, "AsyncAgent")
    assert has_async is True, "AsyncAgent not found in agentkit namespace"

    has_threaded = hasattr(agentkit, "ThreadedAgent")
    assert has_threaded is True, "ThreadedAgent not found in agentkit namespace"

    has_pooled = hasattr(agentkit, "PooledAgent")
    assert has_pooled is True, "PooledAgent not found in agentkit namespace"

    has_base_error = hasattr(agentkit, "AgentKitError")
    assert has_base_error is True, "AgentKitError not found in agentkit namespace"

    has_config_error = hasattr(agentkit, "ConfigurationError")
    assert has_config_error is True, "ConfigurationError not found in agentkit namespace"

    has_semantic_error = hasattr(agentkit, "SemanticError")
    assert has_semantic_error is True, "SemanticError not found in agentkit namespace"

    has_lifecycle_error = hasattr(agentkit, "LifecycleError")
    assert has_lifecycle_error is True, "LifecycleError not found in agentkit namespace"

    has_bridge = hasattr(agentkit, "ConcurrencyBridge")
    assert has_bridge is True, "ConcurrencyBridge not found in agentkit namespace"

    return


# ---------------------------------------------------------------------------
# Integration Test: Reset and re-initialize lifecycle
# ---------------------------------------------------------------------------

def test_stop_reset_reinitialize_lifecycle():
    """
        Tests that an agent can be stopped, then reset back to
        INITIALIZED, and started again.
    """
    reset_registry()

    agent = create_integration_agent(name="reset-agent", version="1.0")

    agent.initialize()
    agent.start()
    agent.stop()

    state_after_stop = agent.state
    assert state_after_stop is LifecycleState.STOPPED, \
        "Expected STOPPED but got {}".format(state_after_stop)

    agent.reset()

    state_after_reset = agent.state
    assert state_after_reset is LifecycleState.INITIALIZED, \
        "Expected INITIALIZED after reset but got {}".format(state_after_reset)

    agent.start()

    state_after_restart = agent.state
    assert state_after_restart is LifecycleState.RUNNING, \
        "Expected RUNNING after restart but got {}".format(state_after_restart)

    expected_calls = ["initialize", "start", "stop", "reset", "start"]
    actual_calls = agent.lifecycle_calls
    assert actual_calls == expected_calls, \
        "Expected lifecycle calls {} but got {}".format(expected_calls, actual_calls)

    return


# ---------------------------------------------------------------------------
# Integration Test: Sub-agent error notification to parent
# ---------------------------------------------------------------------------

def test_sub_agent_error_notifies_parent():
    """
        Tests that when a sub-agent transitions to ERROR state,
        the parent's on_error hooks are invoked with the child
        identity in the record metadata.
    """
    reset_registry()

    error_notifications = []

    def parent_error_hook(agent, record):
        error_notifications.append({
            "child_identifier": record.metadata.get("child_identifier"),
            "child_name": record.metadata.get("child_name"),
        })
        return

    parent = create_integration_agent(name="parent", version="1.0")
    child = create_integration_agent(name="child", version="1.0")

    parent.add_sub_agent(child)
    parent.register_hook("on_error", parent_error_hook)

    parent.initialize()
    parent.start()
    child.initialize()
    child.start()

    child.force_error()

    child_state = child.state
    assert child_state is LifecycleState.ERROR, \
        "Expected child ERROR but got {}".format(child_state)

    notifications_len = len(error_notifications)
    assert notifications_len == 1, \
        "Expected 1 error notification but got {}".format(notifications_len)

    notification = error_notifications[0]
    assert notification["child_identifier"] == child.identity.identifier, \
        "Expected child identifier in notification"
    assert notification["child_name"] == "child", \
        "Expected child name in notification"

    return
