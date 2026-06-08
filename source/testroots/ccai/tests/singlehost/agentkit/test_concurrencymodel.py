"""
    Tests for the ccai.agentkit.concurrencymodel module.

    Contains unit tests for the ConcurrencyModel enum.

    Feature: core-agent-framework
"""

from ccai.agentkit.concurrencymodel import ConcurrencyModel


# ---------------------------------------------------------------------------
# Unit tests for ConcurrencyModel enum values
# **Validates: Requirements 13.1**
# ---------------------------------------------------------------------------

def test_concurrency_model_has_asyncio():
    """
        Verify that ConcurrencyModel has an ASYNCIO value.
    """
    model = ConcurrencyModel.ASYNCIO
    value = model.value
    assert value == "ASYNCIO", (
        "ConcurrencyModel.ASYNCIO value should be 'ASYNCIO', got {!r}".format(value)
    )
    return


def test_concurrency_model_has_thread():
    """
        Verify that ConcurrencyModel has a THREAD value.
    """
    model = ConcurrencyModel.THREAD
    value = model.value
    assert value == "THREAD", (
        "ConcurrencyModel.THREAD value should be 'THREAD', got {!r}".format(value)
    )
    return


def test_concurrency_model_has_thread_pool():
    """
        Verify that ConcurrencyModel has a THREAD_POOL value.
    """
    model = ConcurrencyModel.THREAD_POOL
    value = model.value
    assert value == "THREAD_POOL", (
        "ConcurrencyModel.THREAD_POOL value should be 'THREAD_POOL', got {!r}".format(value)
    )
    return


def test_concurrency_model_has_exactly_three_members():
    """
        Verify that ConcurrencyModel has exactly three members.
    """
    members = list(ConcurrencyModel)
    member_count = len(members)
    assert member_count == 3, (
        "ConcurrencyModel should have exactly 3 members, got {}".format(member_count)
    )
    return


def test_concurrency_model_members_are_distinct():
    """
        Verify that all ConcurrencyModel members have distinct values.
    """
    values = [m.value for m in ConcurrencyModel]
    unique_values = set(values)
    values_count = len(values)
    unique_count = len(unique_values)
    assert values_count == unique_count, (
        "All ConcurrencyModel values should be distinct"
    )
    return


# ---------------------------------------------------------------------------
# Tests for ConcurrencyBridge
# **Validates: Requirements 13.8**
# ---------------------------------------------------------------------------

import asyncio

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.asyncagent import AsyncAgent
from ccai.agentkit.concurrencybridge import ConcurrencyBridge
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.threadedagent import ThreadedAgent
from ccai.agentkit.transitionrecord import TransitionRecord


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


class SimpleAgent(Agent):
    """
        A simple concrete Agent subclass for testing the bridge.
    """

    def initialize(self) -> None:
        """
            Transitions to INITIALIZED.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions to RUNNING.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions to PAUSED.
        """
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions to RUNNING from PAUSED.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        """
            Transitions to STOPPED.
        """
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets to INITIALIZED.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class SimpleAsyncAgent(AsyncAgent):
    """
        A simple concrete AsyncAgent subclass for testing the bridge.
    """

    async def async_initialize(self) -> None:
        """
            Async initialization.
        """
        await self._async_perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    async def async_start(self) -> None:
        """
            Async start.
        """
        await self._async_perform_transition(LifecycleState.RUNNING, "on_start")
        return

    async def async_pause(self) -> None:
        """
            Async pause.
        """
        await self._async_perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    async def async_resume(self) -> None:
        """
            Async resume.
        """
        await self._async_perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    async def async_stop(self) -> None:
        """
            Async stop.
        """
        await self._async_perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    async def async_reset(self) -> None:
        """
            Async reset.
        """
        await self._async_perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class SimpleThreadedAgent(ThreadedAgent):
    """
        A simple concrete ThreadedAgent subclass for testing the bridge.
    """

    def initialize(self) -> None:
        """
            Transitions to INITIALIZED.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions to RUNNING.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions to PAUSED.
        """
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions to RUNNING from PAUSED.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        """
            Transitions to STOPPED.
        """
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets to INITIALIZED.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def create_simple_agent(name: str = "simple-agent") -> SimpleAgent:
    """
        Creates a SimpleAgent for testing.

        :param name: The agent name.

        :returns: A SimpleAgent instance.
    """
    config_data = {"identity": {"name": name, "version": "1.0"}}
    config = AgentConfiguration.from_dict(config_data)
    agent = SimpleAgent(configuration=config)
    return agent


def create_simple_async_agent(name: str = "simple-async") -> SimpleAsyncAgent:
    """
        Creates a SimpleAsyncAgent for testing.

        :param name: The agent name.

        :returns: A SimpleAsyncAgent instance.
    """
    config_data = {"identity": {"name": name, "version": "1.0"}}
    config = AgentConfiguration.from_dict(config_data)
    agent = SimpleAsyncAgent(configuration=config)
    return agent


def create_simple_threaded_agent(name: str = "simple-threaded") -> SimpleThreadedAgent:
    """
        Creates a SimpleThreadedAgent for testing.

        :param name: The agent name.

        :returns: A SimpleThreadedAgent instance.
    """
    config_data = {"identity": {"name": name, "version": "1.0"}}
    config = AgentConfiguration.from_dict(config_data)
    agent = SimpleThreadedAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# Bridge tests
# ---------------------------------------------------------------------------

def test_bridge_invoke_lifecycle_on_standard_agent():
    """
        Verify that ConcurrencyBridge.invoke_lifecycle works on a
        standard synchronous agent.
    """
    reset_registry()

    agent = create_simple_agent(name="bridge-standard")
    ConcurrencyBridge.invoke_lifecycle(agent, "initialize")

    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "Agent should be INITIALIZED after bridge invoke, got {}".format(state)
    )
    return


def test_bridge_invoke_lifecycle_on_async_agent():
    """
        Verify that ConcurrencyBridge.invoke_lifecycle works on an
        AsyncAgent by calling the async version.
    """
    reset_registry()

    agent = create_simple_async_agent(name="bridge-async")
    ConcurrencyBridge.invoke_lifecycle(agent, "initialize")

    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "AsyncAgent should be INITIALIZED after bridge invoke, got {}".format(state)
    )
    return


def test_bridge_invoke_lifecycle_on_threaded_agent():
    """
        Verify that ConcurrencyBridge.invoke_lifecycle works on a
        ThreadedAgent.
    """
    reset_registry()

    agent = create_simple_threaded_agent(name="bridge-threaded")
    ConcurrencyBridge.invoke_lifecycle(agent, "initialize")

    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "ThreadedAgent should be INITIALIZED after bridge invoke, got {}".format(state)
    )
    return


def test_bridge_adapt_parent_child_different_models():
    """
        Verify that ConcurrencyBridge.adapt_parent_child works when
        parent and child use different concurrency models.
    """
    reset_registry()

    parent = create_simple_agent(name="bridge-parent")
    child = create_simple_async_agent(name="bridge-child-async")

    parent.add_sub_agent(child)

    ConcurrencyBridge.adapt_parent_child(parent, child, "initialize")

    child_state = child.state
    assert child_state is LifecycleState.INITIALIZED, (
        "Child should be INITIALIZED after bridge adapt, got {}".format(child_state)
    )
    return


def test_bridge_invoke_hook_sync_callback():
    """
        Verify that ConcurrencyBridge.invoke_hook works with a
        synchronous callback.
    """
    reset_registry()

    agent = create_simple_agent(name="bridge-hook-sync")
    agent.initialize()

    invocation_log = []

    def sync_hook(agent_arg, record_arg):
        """
            A synchronous hook callback.

            :param agent_arg: The agent instance.
            :param record_arg: The transition record.
        """
        invocation_log.append("sync_called")
        return

    from datetime import datetime
    from datetime import timezone

    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=datetime.now(tz=timezone.utc)
    )

    ConcurrencyBridge.invoke_hook(agent, sync_hook, record)

    call_count = len(invocation_log)
    assert call_count == 1, (
        "Sync hook should have been invoked once, got {}".format(call_count)
    )
    return


def test_bridge_invoke_hook_async_callback():
    """
        Verify that ConcurrencyBridge.invoke_hook works with an
        async callback.
    """
    reset_registry()

    agent = create_simple_agent(name="bridge-hook-async")
    agent.initialize()

    invocation_log = []

    async def async_hook(agent_arg, record_arg):
        """
            An async hook callback.

            :param agent_arg: The agent instance.
            :param record_arg: The transition record.
        """
        invocation_log.append("async_called")
        return

    from datetime import datetime
    from datetime import timezone

    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=datetime.now(tz=timezone.utc)
    )

    ConcurrencyBridge.invoke_hook(agent, async_hook, record)

    call_count = len(invocation_log)
    assert call_count == 1, (
        "Async hook should have been invoked once, got {}".format(call_count)
    )
    return
