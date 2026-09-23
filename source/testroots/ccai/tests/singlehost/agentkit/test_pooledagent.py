"""
    Tests for the ccai.agentkit.pooledagent module.

    Contains unit tests for the PooledAgent abstract base class.

    Feature: core-agent-framework
"""

import threading

from concurrent.futures import ThreadPoolExecutor

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.concurrencymodel import ConcurrencyModel
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.pooledagent import PooledAgent


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


def reset_pool():
    """
        Resets the PooledAgent shared pool for test isolation.
    """
    PooledAgent._reset_pool()
    return


class ConcretePooledAgent(PooledAgent):
    """
        Concrete PooledAgent subclass for testing purposes.
    """

    def __init__(self, configuration: AgentConfiguration,
                 max_workers: int = None) -> None:
        super().__init__(configuration, max_workers=max_workers)
        self._lifecycle_calls: list = []
        self._lifecycle_thread_ids: list = []
        return

    def initialize(self) -> None:
        """
            Transitions the agent to INITIALIZED state.
        """
        self._lifecycle_calls.append("initialize")
        self._lifecycle_thread_ids.append(threading.current_thread().ident)
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions the agent to RUNNING state.
        """
        self._lifecycle_calls.append("start")
        self._lifecycle_thread_ids.append(threading.current_thread().ident)
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions the agent to PAUSED state.
        """
        self._lifecycle_calls.append("pause")
        self._lifecycle_thread_ids.append(threading.current_thread().ident)
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions the agent to RUNNING state from PAUSED.
        """
        self._lifecycle_calls.append("resume")
        self._lifecycle_thread_ids.append(threading.current_thread().ident)
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        """
            Transitions the agent to STOPPED state.
        """
        self._lifecycle_calls.append("stop")
        self._lifecycle_thread_ids.append(threading.current_thread().ident)
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._lifecycle_calls.append("reset")
        self._lifecycle_thread_ids.append(threading.current_thread().ident)
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def create_pooled_agent(name: str = "pooled-agent", version: str = "1.0",
                        max_workers: int = None) -> ConcretePooledAgent:
    """
        Creates a ConcretePooledAgent with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.
        :param max_workers: Optional max workers for the pool.

        :returns: A ConcretePooledAgent instance.
    """
    config_data = {"identity": {"name": name, "version": version}}
    config = AgentConfiguration.from_dict(config_data)
    agent = ConcretePooledAgent(configuration=config, max_workers=max_workers)
    return agent


# ---------------------------------------------------------------------------
# Unit tests for PooledAgent
# **Validates: Requirements 13.4, 13.5**
# ---------------------------------------------------------------------------

def test_pooled_agent_extends_agent():
    """
        Verify that PooledAgent is a subclass of Agent.
    """
    is_subclass = issubclass(PooledAgent, Agent)
    assert is_subclass is True, "PooledAgent should be a subclass of Agent"
    return


def test_pooled_agent_concurrency_model():
    """
        Verify that PooledAgent has ConcurrencyModel.THREAD_POOL.
    """
    reset_registry()
    reset_pool()

    agent = create_pooled_agent(name="model-check")
    model = agent.concurrency_model
    assert model is ConcurrencyModel.THREAD_POOL, (
        "PooledAgent concurrency_model should be THREAD_POOL, got {}".format(model)
    )
    return


def test_pooled_agent_cannot_instantiate_directly():
    """
        Verify that PooledAgent cannot be instantiated directly because
        it has abstract methods.
    """
    reset_registry()
    reset_pool()

    raised = False
    try:
        config_data = {"identity": {"name": "abstract-pooled", "version": "1.0"}}
        config = AgentConfiguration.from_dict(config_data)
        PooledAgent(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, "Instantiating PooledAgent directly should raise TypeError"
    return


def test_pooled_agent_direct_lifecycle():
    """
        Verify that PooledAgent supports direct lifecycle calls.
    """
    reset_registry()
    reset_pool()

    agent = create_pooled_agent(name="direct-lifecycle")

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

    agent.stop()
    state = agent.state
    assert state is LifecycleState.STOPPED, (
        "Expected STOPPED, got {}".format(state)
    )

    return


def test_pooled_agent_get_pool_returns_executor():
    """
        Verify that get_pool() returns a ThreadPoolExecutor.
    """
    reset_registry()
    reset_pool()

    pool = PooledAgent.get_pool(max_workers=2)
    is_executor = isinstance(pool, ThreadPoolExecutor)
    assert is_executor is True, "get_pool() should return a ThreadPoolExecutor"

    # Cleanup
    PooledAgent.shutdown_pool(wait=True)
    return


def test_pooled_agent_get_pool_returns_same_instance():
    """
        Verify that get_pool() returns the same pool instance on repeated calls.
    """
    reset_registry()
    reset_pool()

    pool1 = PooledAgent.get_pool(max_workers=2)
    pool2 = PooledAgent.get_pool(max_workers=4)

    is_same = pool1 is pool2
    assert is_same is True, "get_pool() should return the same instance"

    # Cleanup
    PooledAgent.shutdown_pool(wait=True)
    return


def test_pooled_agent_shutdown_pool():
    """
        Verify that shutdown_pool() shuts down the pool and resets it.
    """
    reset_registry()
    reset_pool()

    pool = PooledAgent.get_pool(max_workers=2)
    PooledAgent.shutdown_pool(wait=True)

    # After shutdown, get_pool should create a new pool
    new_pool = PooledAgent.get_pool(max_workers=2)
    is_different = pool is not new_pool
    assert is_different is True, "After shutdown, get_pool should create a new pool"

    # Cleanup
    PooledAgent.shutdown_pool(wait=True)
    return


def test_pooled_agent_submit_lifecycle():
    """
        Verify that submit_lifecycle() submits a lifecycle method to the pool.
    """
    reset_registry()
    reset_pool()

    agent = create_pooled_agent(name="submit-agent", max_workers=2)

    future = agent.submit_lifecycle("initialize")
    future.result(timeout=5.0)

    state = agent.state
    assert state is LifecycleState.INITIALIZED, (
        "Agent should be INITIALIZED after submit_lifecycle('initialize'), got {}".format(state)
    )

    # Cleanup
    PooledAgent.shutdown_pool(wait=True)
    return


def test_pooled_agent_submit_lifecycle_runs_on_pool_thread():
    """
        Verify that submit_lifecycle() runs the method on a pool thread,
        not the main thread.
    """
    reset_registry()
    reset_pool()

    agent = create_pooled_agent(name="pool-thread-agent", max_workers=2)
    main_thread_id = threading.current_thread().ident

    future = agent.submit_lifecycle("initialize")
    future.result(timeout=5.0)

    thread_id_count = len(agent._lifecycle_thread_ids)
    assert thread_id_count >= 1, "At least one lifecycle method should have recorded a thread ID"

    pool_thread_id = agent._lifecycle_thread_ids[0]
    is_different = pool_thread_id != main_thread_id
    assert is_different is True, (
        "Lifecycle method should run on a pool thread, not the main thread"
    )

    # Cleanup
    PooledAgent.shutdown_pool(wait=True)
    return


def test_pooled_agent_inherits_hooks():
    """
        Verify that PooledAgent inherits hook registration from Agent.
    """
    reset_registry()
    reset_pool()

    agent = create_pooled_agent(name="hook-pooled")

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


def test_pooled_agent_inherits_sub_agent_management():
    """
        Verify that PooledAgent inherits sub-agent management from Agent.
    """
    reset_registry()
    reset_pool()

    parent = create_pooled_agent(name="pooled-parent")
    child = create_pooled_agent(name="pooled-child")

    parent.add_sub_agent(child)

    sub_agents = parent.sub_agents
    sub_count = len(sub_agents)
    assert sub_count == 1, (
        "Parent should have 1 sub-agent, got {}".format(sub_count)
    )

    child_parent = child.parent
    assert child_parent is parent, "Child parent should be the parent agent"

    return


def test_pooled_agent_inherits_registry():
    """
        Verify that PooledAgent is automatically registered in the AgentRegistry.
    """
    reset_registry()
    reset_pool()

    agent = create_pooled_agent(name="registry-pooled")
    registry = AgentRegistry.instance()

    found = registry.lookup_by_id(agent.identity.identifier)
    assert found is agent, "PooledAgent should be registered in the AgentRegistry"

    return
