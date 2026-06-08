"""
    Tests for the ccai.agentkit.asyncagent module.

    Contains unit tests for the AsyncAgent abstract base class.

    Feature: core-agent-framework
"""

import asyncio

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.asyncagent import AsyncAgent
from ccai.agentkit.concurrencymodel import ConcurrencyModel
from ccai.agentkit.lifecyclestate import LifecycleState
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


class ConcreteAsyncAgent(AsyncAgent):
    """
        Concrete AsyncAgent subclass for testing purposes.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        super().__init__(configuration)
        self._async_calls: list = []
        return

    async def async_initialize(self) -> None:
        """
            Async initialization that transitions to INITIALIZED.
        """
        self._async_calls.append("async_initialize")
        await self._async_perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    async def async_start(self) -> None:
        """
            Async start that transitions to RUNNING.
        """
        self._async_calls.append("async_start")
        await self._async_perform_transition(LifecycleState.RUNNING, "on_start")
        return

    async def async_pause(self) -> None:
        """
            Async pause that transitions to PAUSED.
        """
        self._async_calls.append("async_pause")
        await self._async_perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    async def async_resume(self) -> None:
        """
            Async resume that transitions to RUNNING.
        """
        self._async_calls.append("async_resume")
        await self._async_perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    async def async_stop(self) -> None:
        """
            Async stop that transitions to STOPPED.
        """
        self._async_calls.append("async_stop")
        await self._async_perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    async def async_reset(self) -> None:
        """
            Async reset that transitions to INITIALIZED.
        """
        self._async_calls.append("async_reset")
        await self._async_perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def create_async_agent(name: str = "async-agent", version: str = "1.0") -> ConcreteAsyncAgent:
    """
        Creates a ConcreteAsyncAgent with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.

        :returns: A ConcreteAsyncAgent instance.
    """
    config_data = {"identity": {"name": name, "version": version}}
    config = AgentConfiguration.from_dict(config_data)
    agent = ConcreteAsyncAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# Unit tests for AsyncAgent
# **Validates: Requirements 13.2, 13.5**
# ---------------------------------------------------------------------------

def test_async_agent_extends_agent():
    """
        Verify that AsyncAgent is a subclass of Agent.
    """
    is_subclass = issubclass(AsyncAgent, Agent)
    assert is_subclass is True, "AsyncAgent should be a subclass of Agent"
    return


def test_async_agent_concurrency_model():
    """
        Verify that AsyncAgent has ConcurrencyModel.ASYNCIO.
    """
    reset_registry()

    agent = create_async_agent(name="model-check")
    model = agent.concurrency_model
    assert model is ConcurrencyModel.ASYNCIO, (
        "AsyncAgent concurrency_model should be ASYNCIO, got {}".format(model)
    )
    return


def test_async_agent_cannot_instantiate_directly():
    """
        Verify that AsyncAgent cannot be instantiated directly because
        it has abstract methods.
    """
    reset_registry()

    raised = False
    try:
        config_data = {"identity": {"name": "abstract-async", "version": "1.0"}}
        config = AgentConfiguration.from_dict(config_data)
        agent = AsyncAgent(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, "Instantiating AsyncAgent directly should raise TypeError"
    return


def test_async_agent_initialize_transitions_state():
    """
        Verify that calling initialize() on an AsyncAgent transitions
        to INITIALIZED state via the async_initialize coroutine.
    """
    reset_registry()

    agent = create_async_agent(name="init-agent")
    agent.initialize()

    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "State should be INITIALIZED after initialize(), got {}".format(state)
    )

    has_call = "async_initialize" in agent._async_calls
    assert has_call is True, "async_initialize should have been called"
    return


def test_async_agent_full_lifecycle():
    """
        Verify that AsyncAgent supports the full lifecycle:
        initialize -> start -> pause -> resume -> stop.
    """
    reset_registry()

    agent = create_async_agent(name="lifecycle-agent")

    agent.initialize()
    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "Expected INITIALIZED, got {}".format(state)
    )

    agent.start()
    state = agent.state
    assert state is LifecycleState.RUNNING, (
        "Expected RUNNING, got {}".format(state)
    )

    agent.pause()
    state = agent.state
    assert state is LifecycleState.PAUSED, (
        "Expected PAUSED, got {}".format(state)
    )

    agent.resume()
    state = agent.state
    assert state is LifecycleState.RUNNING, (
        "Expected RUNNING after resume, got {}".format(state)
    )

    agent.stop()
    state = agent.state
    assert state is LifecycleState.STOPPED, (
        "Expected STOPPED, got {}".format(state)
    )

    return


def test_async_agent_lifecycle_via_asyncio_run():
    """
        Verify that AsyncAgent async methods work when called
        directly via asyncio.run().
    """
    reset_registry()

    agent = create_async_agent(name="asyncio-run-agent")

    asyncio.run(agent.async_initialize())
    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "Expected INITIALIZED, got {}".format(state)
    )

    asyncio.run(agent.async_start())
    state = agent.state
    assert state is LifecycleState.RUNNING, (
        "Expected RUNNING, got {}".format(state)
    )

    asyncio.run(agent.async_stop())
    state = agent.state
    assert state is LifecycleState.STOPPED, (
        "Expected STOPPED, got {}".format(state)
    )

    return


def test_async_agent_inherits_hooks():
    """
        Verify that AsyncAgent inherits hook registration from Agent.
    """
    reset_registry()

    agent = create_async_agent(name="hook-agent")

    invocation_log = []

    def on_init_hook(agent_arg, record_arg):
        """
            Records hook invocation.

            :param agent_arg: The agent instance.
            :param record_arg: The transition record.
        """
        invocation_log.append("on_initialize")
        return

    agent.register_hook("on_initialize", on_init_hook)
    agent.initialize()

    hook_count = len(invocation_log)
    assert hook_count == 1, (
        "Hook should have been invoked once, got {}".format(hook_count)
    )
    return


def test_async_agent_inherits_sub_agent_management():
    """
        Verify that AsyncAgent inherits sub-agent management from Agent.
    """
    reset_registry()

    parent = create_async_agent(name="async-parent")
    child = create_async_agent(name="async-child")

    parent.add_sub_agent(child)

    sub_agents = parent.sub_agents
    sub_count = len(sub_agents)
    assert sub_count == 1, (
        "Parent should have 1 sub-agent, got {}".format(sub_count)
    )

    child_parent = child.parent
    assert child_parent is parent, "Child parent should be the parent agent"

    return


def test_async_agent_inherits_registry():
    """
        Verify that AsyncAgent is automatically registered in the AgentRegistry.
    """
    reset_registry()

    agent = create_async_agent(name="registry-agent")
    registry = AgentRegistry.instance()

    found = registry.lookup_by_id(agent.identity.identifier)
    assert found is agent, "AsyncAgent should be registered in the AgentRegistry"

    return


def test_async_agent_repr():
    """
        Verify that AsyncAgent __repr__ includes class name and state.
    """
    reset_registry()

    agent = create_async_agent(name="repr-async-agent")
    repr_str = repr(agent)

    has_class = "ConcreteAsyncAgent" in repr_str
    assert has_class is True, "repr should include the class name"

    has_name = "repr-async-agent" in repr_str
    assert has_name is True, "repr should include the agent name"

    return


def test_async_agent_str():
    """
        Verify that AsyncAgent __str__ includes name and state.
    """
    reset_registry()

    agent = create_async_agent(name="str-async-agent")
    str_val = str(agent)

    has_name = "str-async-agent" in str_val
    assert has_name is True, "str should include the agent name"

    has_state = "CREATED" in str_val
    assert has_state is True, "str should include the current state"

    return
