"""
    Tests for the automojo.agentkit.agent module.

    Contains property-based tests (using automojo.testbase.properties) and unit tests
    for the Agent abstract base class.

    Feature: core-agent-framework
"""

import logging
import os

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentidentity import AgentIdentity
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.agentstatemachine import AgentStateMachine
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


class TestAgent(Agent):
    """
        Concrete Agent subclass for testing purposes.
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
            Stops all sub-agents then transitions to STOPPED state.
        """
        for sub in list(self.sub_agents):
            sub_state = sub.state
            if sub_state is not LifecycleState.STOPPED:
                sub.stop()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def force_error(self) -> None:
        """
            Forces the agent into ERROR state for testing.
        """
        self._perform_transition(LifecycleState.ERROR, "on_error")
        return


def create_test_agent(name: str = "test-agent", version: str = "1.0",
                      tags: dict = None, identifier: str = None) -> TestAgent:
    """
        Creates a TestAgent with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.
        :param tags: Optional tags dictionary.
        :param identifier: Optional explicit identifier.

        :returns: A TestAgent instance.
    """
    identity_data = {"name": name, "version": version}

    if tags is not None:
        identity_data["tags"] = tags

    if identifier is not None:
        identity_data["identifier"] = identifier

    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    agent = TestAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# testbase property strategies
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

hook_count_strategy = st.integers(min_value=1, max_value=10)


# ---------------------------------------------------------------------------
# Property 12: Hooks invoked in registration order with correct arguments
# **Validates: Requirements 5.1, 5.2, 5.3**
# ---------------------------------------------------------------------------

@given(
    hook_count=hook_count_strategy,
    settings=settings(max_examples=100)
)
def test_property_12_hooks_invoked_in_registration_order(hook_count):
    """
        Property 12: Hooks invoked in registration order with correct arguments.

        For any Agent and any list of N hooks registered for a transition point,
        when the transition occurs, all N hooks shall be invoked in registration
        order, each receiving the Agent instance and TransitionRecord.

        **Validates: Requirements 5.1, 5.2, 5.3**
    """
    reset_registry()

    agent = create_test_agent(name="hook-order-agent")

    invocation_log = []

    for idx in range(hook_count):
        hook_idx = idx

        def make_hook(index):
            """
                Creates a hook that records its invocation index and arguments.

                :param index: The index of this hook in registration order.

                :returns: A hook callable.
            """
            def hook(agent_arg, record_arg):
                invocation_log.append({
                    "index": index,
                    "agent": agent_arg,
                    "record": record_arg,
                })
                return
            return hook

        agent.register_hook("on_initialize", make_hook(hook_idx))

    agent.initialize()

    # Assert all hooks were invoked
    actual_count = len(invocation_log)
    assert actual_count == hook_count, (
        "Expected {} hooks invoked, got {}".format(hook_count, actual_count)
    )

    # Assert invocation order
    for idx in range(hook_count):
        entry = invocation_log[idx]
        actual_index = entry["index"]
        assert actual_index == idx, (
            "Hook at position {} was invoked out of order (got index {})".format(idx, actual_index)
        )

    # Assert each hook received the correct Agent and TransitionRecord
    for entry in invocation_log:
        received_agent = entry["agent"]
        received_record = entry["record"]
        assert received_agent is agent, "Hook should receive the Agent instance"
        assert isinstance(received_record, TransitionRecord), (
            "Hook should receive a TransitionRecord"
        )

    return


# ---------------------------------------------------------------------------
# Property 13: Hook exception does not prevent remaining hooks
# **Validates: Requirements 5.4**
# ---------------------------------------------------------------------------

@given(
    hook_count=st.integers(min_value=2, max_value=10),
    failing_index=st.integers(min_value=0, max_value=9),
    settings=settings(max_examples=100)
)
def test_property_13_hook_exception_does_not_prevent_remaining(hook_count, failing_index):
    """
        Property 13: Hook exception does not prevent remaining hooks.

        For any Agent with N hooks where hook K raises an exception,
        hooks K+1 through N-1 shall still be invoked.

        **Validates: Requirements 5.4**
    """
    reset_registry()

    agent = create_test_agent(name="hook-exception-agent")

    # Clamp failing_index to valid range for the drawn hook_count
    if failing_index >= hook_count:
        failing_index = hook_count - 1

    invocation_log = []

    for idx in range(hook_count):
        hook_idx = idx
        should_fail = (hook_idx == failing_index)

        def make_hook(index, fail):
            """
                Creates a hook that optionally raises an exception.

                :param index: The index of this hook.
                :param fail: Whether this hook should raise.

                :returns: A hook callable.
            """
            def hook(agent_arg, record_arg):
                invocation_log.append(index)
                if fail is True:
                    raise RuntimeError("Hook {} failed".format(index))
                return
            return hook

        agent.register_hook("on_initialize", make_hook(hook_idx, should_fail))

    agent.initialize()

    # All hooks should have been invoked despite the exception
    actual_count = len(invocation_log)
    assert actual_count == hook_count, (
        "Expected {} hooks invoked (including failing), got {}".format(hook_count, actual_count)
    )

    # Verify hooks after the failing one were still called
    for idx in range(failing_index + 1, hook_count):
        is_present = idx in invocation_log
        assert is_present is True, (
            "Hook {} should have been invoked after failing hook {}".format(idx, failing_index)
        )

    return


# ---------------------------------------------------------------------------
# Property 14: Hook deregistration removes hook
# **Validates: Requirements 5.5**
# ---------------------------------------------------------------------------

@given(
    hook_count=st.integers(min_value=2, max_value=10),
    deregister_index=st.integers(min_value=0, max_value=9),
    settings=settings(max_examples=100)
)
def test_property_14_hook_deregistration_removes_hook(hook_count, deregister_index):
    """
        Property 14: Hook deregistration removes hook.

        Register a hook, deregister it, trigger transition.
        Assert deregistered hook is not invoked.

        **Validates: Requirements 5.5**
    """
    reset_registry()

    agent = create_test_agent(name="hook-deregister-agent")

    # Clamp deregister_index to valid range for the drawn hook_count
    if deregister_index >= hook_count:
        deregister_index = hook_count - 1

    invocation_log = []
    hooks = []

    for idx in range(hook_count):
        hook_idx = idx

        def make_hook(index):
            """
                Creates a hook that records its invocation.

                :param index: The index of this hook.

                :returns: A hook callable.
            """
            def hook(agent_arg, record_arg):
                invocation_log.append(index)
                return
            return hook

        hook_fn = make_hook(hook_idx)
        hooks.append(hook_fn)
        agent.register_hook("on_initialize", hook_fn)

    # Deregister the selected hook
    agent.deregister_hook("on_initialize", hooks[deregister_index])

    agent.initialize()

    # The deregistered hook should not have been invoked
    is_deregistered_invoked = deregister_index in invocation_log
    assert is_deregistered_invoked is not True, (
        "Deregistered hook at index {} should not have been invoked".format(deregister_index)
    )

    # All other hooks should have been invoked
    expected_count = hook_count - 1
    actual_count = len(invocation_log)
    assert actual_count == expected_count, (
        "Expected {} hooks invoked after deregistration, got {}".format(expected_count, actual_count)
    )

    return


# ---------------------------------------------------------------------------
# Property 17: Sub-agent add and remove correctness
# **Validates: Requirements 7.1, 7.2**
# ---------------------------------------------------------------------------

@given(
    child_count=st.integers(min_value=1, max_value=5),
    settings=settings(max_examples=100)
)
def test_property_17_sub_agent_add_and_remove(child_count):
    """
        Property 17: Sub-agent add and remove correctness.

        Add child as sub-agent, assert in sub_agents and parent set.
        Remove by identifier, assert reversed.

        **Validates: Requirements 7.1, 7.2**
    """
    reset_registry()

    parent = create_test_agent(name="parent-agent")
    children = []

    for idx in range(child_count):
        child = create_test_agent(name="child-{}".format(idx))
        children.append(child)

    # Add all children
    for child in children:
        parent.add_sub_agent(child)

    # Assert all children are in sub_agents
    sub_agents = parent.sub_agents
    sub_count = len(sub_agents)
    assert sub_count == child_count, (
        "Expected {} sub-agents, got {}".format(child_count, sub_count)
    )

    # Assert parent is set on each child
    for child in children:
        child_parent = child.parent
        assert child_parent is parent, "Child parent should be the parent agent"

    # Remove each child and verify
    for child in children:
        child_id = child.identity.identifier
        parent.remove_sub_agent(child_id)

        # Verify child is no longer in sub_agents
        remaining = parent.sub_agents
        is_still_present = False
        for remaining_agent in remaining:
            if remaining_agent.identity.identifier == child_id:
                is_still_present = True
                break
        assert is_still_present is not True, (
            "Child {} should have been removed from sub_agents".format(child_id)
        )

        # Verify parent is cleared
        child_parent_after = child.parent
        assert child_parent_after is None, "Child parent should be None after removal"

    # Final check: no sub-agents remain
    final_count = len(parent.sub_agents)
    assert final_count == 0, "All sub-agents should have been removed"

    return


# ---------------------------------------------------------------------------
# Property 18: Parent lifecycle cascades to sub-agents
# **Validates: Requirements 7.5, 7.6, 7.7**
# ---------------------------------------------------------------------------

@given(
    child_count=st.integers(min_value=1, max_value=4),
    settings=settings(max_examples=100)
)
def test_property_18_parent_lifecycle_cascades(child_count):
    """
        Property 18: Parent lifecycle cascades to sub-agents.

        Create parent with RUNNING sub-agents.
        Assert stop cascades to all sub-agents.

        **Validates: Requirements 7.5, 7.6, 7.7**
    """
    reset_registry()

    parent = create_test_agent(name="cascade-parent")
    children = []

    for idx in range(child_count):
        child = create_test_agent(name="cascade-child-{}".format(idx))
        parent.add_sub_agent(child)
        children.append(child)

    # Bring parent and children to RUNNING
    parent.initialize()
    parent.start()

    for child in children:
        child.initialize()
        child.start()

    # Verify all are RUNNING
    for child in children:
        child_state = child.state
        assert child_state is LifecycleState.RUNNING, (
            "Child should be RUNNING, got {}".format(child_state)
        )

    # Stop parent — should cascade stop to children
    parent.stop()

    parent_state = parent.state
    assert parent_state is LifecycleState.STOPPED, (
        "Parent should be STOPPED, got {}".format(parent_state)
    )

    for child in children:
        child_state = child.state
        assert child_state is LifecycleState.STOPPED, (
            "Child should be STOPPED after parent stop, got {}".format(child_state)
        )

    return


# ---------------------------------------------------------------------------
# Property 19: Sub-agent error notifies parent
# **Validates: Requirements 7.8**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy,
    settings=settings(max_examples=100)
)
def test_property_19_sub_agent_error_notifies_parent(name, version):
    """
        Property 19: Sub-agent error notifies parent.

        Create parent-child pair, transition child to ERROR.
        Assert parent on_error hooks invoked with child identity in record metadata.

        **Validates: Requirements 7.8**
    """
    reset_registry()

    parent = create_test_agent(name="error-parent")
    child = create_test_agent(name=name, version=version)
    parent.add_sub_agent(child)

    parent_error_records = []

    def on_error_hook(agent_arg, record_arg):
        """
            Records error notifications received by the parent.

            :param agent_arg: The agent instance.
            :param record_arg: The transition record.
        """
        parent_error_records.append(record_arg)
        return

    parent.register_hook("on_error", on_error_hook)

    # Bring child to RUNNING so it can transition to ERROR
    child.initialize()
    child.start()
    child.force_error()

    # Assert parent on_error hook was invoked
    notification_count = len(parent_error_records)
    assert notification_count >= 1, (
        "Parent on_error hook should have been invoked, got {} notifications".format(notification_count)
    )

    # Assert the record contains child identity in metadata
    error_record = parent_error_records[0]
    metadata = error_record.metadata
    has_child_id = "child_identifier" in metadata
    assert has_child_id is True, "Error record metadata should contain child_identifier"

    child_id_in_metadata = metadata["child_identifier"]
    expected_child_id = child.identity.identifier
    assert child_id_in_metadata == expected_child_id, (
        "child_identifier in metadata should be {!r}, got {!r}".format(
            expected_child_id, child_id_in_metadata
        )
    )

    has_child_name = "child_name" in metadata
    assert has_child_name is True, "Error record metadata should contain child_name"

    child_name_in_metadata = metadata["child_name"]
    expected_child_name = child.identity.name
    assert child_name_in_metadata == expected_child_name, (
        "child_name in metadata should be {!r}, got {!r}".format(
            expected_child_name, child_name_in_metadata
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 20: Cycle detection prevents circular relationships
# **Validates: Requirements 7.9, 7.10**
# ---------------------------------------------------------------------------

@given(
    chain_length=st.integers(min_value=2, max_value=5),
    settings=settings(max_examples=100)
)
def test_property_20_cycle_detection(chain_length):
    """
        Property 20: Cycle detection prevents circular parent-child relationships.

        Assert adding ancestor as sub-agent of descendant (or self) raises SemanticError.

        **Validates: Requirements 7.9, 7.10**
    """
    reset_registry()

    # Build a chain: agent_0 -> agent_1 -> ... -> agent_N
    agents = []
    for idx in range(chain_length):
        agent = create_test_agent(name="chain-agent-{}".format(idx))
        agents.append(agent)

    for idx in range(chain_length - 1):
        agents[idx].add_sub_agent(agents[idx + 1])

    # Try to add the root as a sub-agent of the leaf — should raise SemanticError
    leaf = agents[chain_length - 1]
    root = agents[0]

    raised = False
    try:
        leaf.add_sub_agent(root)
    except SemanticError:
        raised = True

    assert raised is True, (
        "Adding ancestor as sub-agent of descendant should raise SemanticError"
    )

    # Try to add self as sub-agent — should raise SemanticError
    self_raised = False
    try:
        root.add_sub_agent(root)
    except SemanticError:
        self_raised = True

    assert self_raised is True, (
        "Adding agent as sub-agent of itself should raise SemanticError"
    )

    return


# ---------------------------------------------------------------------------
# Unit tests for Agent base class edge cases (Task 8.9)
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2, 11.3,
#              11.4, 15.1, 15.2, 15.3, 15.4, 16.1, 16.2**
# ---------------------------------------------------------------------------

def test_abstract_method_enforcement():
    """
        Verify that Agent cannot be instantiated directly because it
        has abstract methods.
    """
    reset_registry()

    raised = False
    try:
        config_data = {"identity": {"name": "abstract-test", "version": "1.0"}}
        config = AgentConfiguration.from_dict(config_data)
        agent = Agent(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, "Instantiating Agent directly should raise TypeError"
    return


def test_read_only_state_property():
    """
        Verify that the state property returns the current lifecycle state.
    """
    reset_registry()

    agent = create_test_agent(name="state-prop-agent")
    state = agent.state
    assert state is LifecycleState.CREATED, (
        "Initial state should be CREATED, got {}".format(state)
    )
    return


def test_read_only_identity_property():
    """
        Verify that the identity property returns an AgentIdentity.
    """
    reset_registry()

    agent = create_test_agent(name="identity-prop-agent", version="2.0")
    identity = agent.identity
    assert isinstance(identity, AgentIdentity), "identity should be an AgentIdentity"

    identity_name = identity.name
    assert identity_name == "identity-prop-agent", (
        "Identity name should be 'identity-prop-agent', got {!r}".format(identity_name)
    )
    return


def test_read_only_configuration_property():
    """
        Verify that the configuration property returns the AgentConfiguration.
    """
    reset_registry()

    agent = create_test_agent(name="config-prop-agent")
    config = agent.configuration
    assert isinstance(config, AgentConfiguration), "configuration should be an AgentConfiguration"
    return


def test_read_only_parent_property_none():
    """
        Verify that parent is None when agent has no parent.
    """
    reset_registry()

    agent = create_test_agent(name="no-parent-agent")
    parent = agent.parent
    assert parent is None, "Parent should be None for agent with no parent"
    return


def test_read_only_sub_agents_property_empty():
    """
        Verify that sub_agents is an empty list when no sub-agents added.
    """
    reset_registry()

    agent = create_test_agent(name="no-sub-agents")
    sub_agents = agent.sub_agents
    sub_count = len(sub_agents)
    assert sub_count == 0, "sub_agents should be empty initially"
    return


def test_read_only_extensions_property_empty():
    """
        Verify that extensions is an empty list initially.
    """
    reset_registry()

    agent = create_test_agent(name="no-extensions")
    extensions = agent.extensions
    ext_count = len(extensions)
    assert ext_count == 0, "extensions should be empty initially"
    return


def test_structured_logging_transition_at_info():
    """
        Verify that lifecycle transitions are logged at INFO level.
    """
    reset_registry()

    agent = create_test_agent(name="log-info-agent")
    logger = agent.get_logger()

    log_records = []

    class TestHandler(logging.Handler):
        """
            A logging handler that captures log records for testing.
        """

        def emit(self, record: logging.LogRecord) -> None:
            """
                Captures a log record.

                :param record: The log record to capture.
            """
            log_records.append(record)
            return

    handler = TestHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        agent.initialize()

        # Find INFO records about the transition
        info_records = [r for r in log_records if r.levelno == logging.INFO]
        info_count = len(info_records)
        assert info_count >= 1, (
            "At least one INFO log record should be emitted for a transition, got {}".format(info_count)
        )

        # Verify the message contains transition info
        first_info = info_records[0]
        message = first_info.getMessage()
        has_created = "CREATED" in message
        has_initialized = "INITIALIZED" in message
        assert has_created is True, "INFO log should mention CREATED state"
        assert has_initialized is True, "INFO log should mention INITIALIZED state"
    finally:
        logger.removeHandler(handler)

    return


def test_structured_logging_hook_exception_at_warning():
    """
        Verify that hook exceptions are logged at WARNING level.
    """
    reset_registry()

    agent = create_test_agent(name="log-warning-agent")
    logger = agent.get_logger()

    log_records = []

    class TestHandler(logging.Handler):
        """
            A logging handler that captures log records for testing.
        """

        def emit(self, record: logging.LogRecord) -> None:
            """
                Captures a log record.

                :param record: The log record to capture.
            """
            log_records.append(record)
            return

    handler = TestHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    def failing_hook(agent_arg, record_arg):
        """
            A hook that always raises an exception.

            :param agent_arg: The agent instance.
            :param record_arg: The transition record.
        """
        raise RuntimeError("Test hook failure")

    agent.register_hook("on_initialize", failing_hook)

    try:
        agent.initialize()

        # Find WARNING records
        warning_records = [r for r in log_records if r.levelno == logging.WARNING]
        warning_count = len(warning_records)
        assert warning_count >= 1, (
            "At least one WARNING log record should be emitted for hook exception, got {}".format(
                warning_count
            )
        )

        # Verify the warning message contains relevant info
        first_warning = warning_records[0]
        message = first_warning.getMessage()
        has_hook_info = "on_initialize" in message
        assert has_hook_info is True, "WARNING log should mention the transition point"
    finally:
        logger.removeHandler(handler)

    return


def test_agent_scoped_logger_naming():
    """
        Verify that get_logger returns a logger with the correct naming pattern.
    """
    reset_registry()

    agent = create_test_agent(name="logger-name-agent")
    logger = agent.get_logger()

    expected_prefix = "automojo.agentkit.agent."
    logger_name = logger.name
    has_prefix = logger_name.startswith(expected_prefix)
    assert has_prefix is True, (
        "Logger name should start with {!r}, got {!r}".format(expected_prefix, logger_name)
    )

    agent_id = agent.identity.identifier
    expected_name = "automojo.agentkit.agent.{}".format(agent_id)
    assert logger_name == expected_name, (
        "Logger name should be {!r}, got {!r}".format(expected_name, logger_name)
    )
    return


def test_repr_output_format():
    """
        Verify that __repr__ includes class name, identifier, name, and state.
    """
    reset_registry()

    agent = create_test_agent(name="repr-agent", version="1.0")
    repr_str = repr(agent)

    has_class_name = "TestAgent" in repr_str
    assert has_class_name is True, "repr should include class name 'TestAgent'"

    has_name = "repr-agent" in repr_str
    assert has_name is True, "repr should include agent name"

    has_identifier = agent.identity.identifier in repr_str
    assert has_identifier is True, "repr should include agent identifier"

    return


def test_str_output_format():
    """
        Verify that __str__ returns a human-readable summary with name and state.
    """
    reset_registry()

    agent = create_test_agent(name="str-agent", version="1.0")
    str_val = str(agent)

    has_name = "str-agent" in str_val
    assert has_name is True, "str should include agent name"

    has_state = "CREATED" in str_val
    assert has_state is True, "str should include current state"

    return


def test_register_hook_invalid_transition_point():
    """
        Verify that registering a hook with an invalid transition point
        raises SemanticError.
    """
    reset_registry()

    agent = create_test_agent(name="invalid-hook-agent")

    raised = False
    try:
        agent.register_hook("on_invalid", lambda a, r: None)
    except SemanticError:
        raised = True

    assert raised is True, "Registering hook with invalid transition point should raise SemanticError"
    return


def test_deregister_hook_invalid_transition_point():
    """
        Verify that deregistering a hook with an invalid transition point
        raises SemanticError.
    """
    reset_registry()

    agent = create_test_agent(name="invalid-deregister-agent")

    raised = False
    try:
        agent.deregister_hook("on_invalid", lambda a, r: None)
    except SemanticError:
        raised = True

    assert raised is True, "Deregistering hook with invalid transition point should raise SemanticError"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
