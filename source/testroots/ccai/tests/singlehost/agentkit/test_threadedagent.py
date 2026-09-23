"""
    Tests for the ccai.agentkit.threadedagent module.

    Contains unit tests for the ThreadedAgent abstract base class.

    Feature: core-agent-framework
"""

import threading

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.concurrencymodel import ConcurrencyModel
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.threadedagent import ThreadedAgent


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


class ConcreteThreadedAgent(ThreadedAgent):
    """
        Concrete ThreadedAgent subclass for testing purposes.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        super().__init__(configuration)
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


def create_threaded_agent(name: str = "threaded-agent",
                          version: str = "1.0") -> ConcreteThreadedAgent:
    """
        Creates a ConcreteThreadedAgent with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.

        :returns: A ConcreteThreadedAgent instance.
    """
    config_data = {"identity": {"name": name, "version": version}}
    config = AgentConfiguration.from_dict(config_data)
    agent = ConcreteThreadedAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# Unit tests for ThreadedAgent
# **Validates: Requirements 13.3, 13.5**
# ---------------------------------------------------------------------------

def test_threaded_agent_extends_agent():
    """
        Verify that ThreadedAgent is a subclass of Agent.
    """
    is_subclass = issubclass(ThreadedAgent, Agent)
    assert is_subclass is True, "ThreadedAgent should be a subclass of Agent"
    return


def test_threaded_agent_concurrency_model():
    """
        Verify that ThreadedAgent has ConcurrencyModel.THREAD.
    """
    reset_registry()

    agent = create_threaded_agent(name="model-check")
    model = agent.concurrency_model
    assert model is ConcurrencyModel.THREAD, (
        "ThreadedAgent concurrency_model should be THREAD, got {}".format(model)
    )
    return


def test_threaded_agent_cannot_instantiate_directly():
    """
        Verify that ThreadedAgent cannot be instantiated directly because
        it has abstract methods.
    """
    reset_registry()

    raised = False
    try:
        config_data = {"identity": {"name": "abstract-threaded", "version": "1.0"}}
        config = AgentConfiguration.from_dict(config_data)
        ThreadedAgent(configuration=config)
    except TypeError:
        raised = True

    assert raised is True, "Instantiating ThreadedAgent directly should raise TypeError"
    return


def test_threaded_agent_thread_initially_none():
    """
        Verify that the thread property is None before run() is called.
    """
    reset_registry()

    agent = create_threaded_agent(name="thread-none-agent")
    thread = agent.thread
    assert thread is None, "Thread should be None before run() is called"
    return


def test_threaded_agent_direct_lifecycle():
    """
        Verify that ThreadedAgent supports direct lifecycle calls
        (without using run()).
    """
    reset_registry()

    agent = create_threaded_agent(name="direct-lifecycle")

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


def test_threaded_agent_run_starts_thread():
    """
        Verify that run() starts a dedicated thread that initializes
        and starts the agent.
    """
    reset_registry()

    agent = create_threaded_agent(name="run-thread-agent")
    agent.run()
    agent.join(timeout=5.0)

    state = agent.state
    assert state is LifecycleState.RUNNING, (
        "Agent should be RUNNING after run(), got {}".format(state)
    )

    thread = agent.thread
    assert thread is not None, "Thread should not be None after run()"

    return


def test_threaded_agent_run_uses_dedicated_thread():
    """
        Verify that lifecycle methods called via run() execute on
        a different thread than the main thread.
    """
    reset_registry()

    agent = create_threaded_agent(name="dedicated-thread-agent")
    main_thread_id = threading.current_thread().ident

    agent.run()
    agent.join(timeout=5.0)

    # Check that lifecycle methods ran on a different thread
    thread_id_count = len(agent._lifecycle_thread_ids)
    assert thread_id_count >= 1, "At least one lifecycle method should have recorded a thread ID"

    for tid in agent._lifecycle_thread_ids:
        is_different = tid != main_thread_id
        assert is_different is True, (
            "Lifecycle method should run on a different thread than main"
        )

    return


def test_threaded_agent_inherits_hooks():
    """
        Verify that ThreadedAgent inherits hook registration from Agent.
    """
    reset_registry()

    agent = create_threaded_agent(name="hook-threaded")

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


def test_threaded_agent_inherits_sub_agent_management():
    """
        Verify that ThreadedAgent inherits sub-agent management from Agent.
    """
    reset_registry()

    parent = create_threaded_agent(name="threaded-parent")
    child = create_threaded_agent(name="threaded-child")

    parent.add_sub_agent(child)

    sub_agents = parent.sub_agents
    sub_count = len(sub_agents)
    assert sub_count == 1, (
        "Parent should have 1 sub-agent, got {}".format(sub_count)
    )

    child_parent = child.parent
    assert child_parent is parent, "Child parent should be the parent agent"

    return


def test_threaded_agent_inherits_registry():
    """
        Verify that ThreadedAgent is automatically registered in the AgentRegistry.
    """
    reset_registry()

    agent = create_threaded_agent(name="registry-threaded")
    registry = AgentRegistry.instance()

    found = registry.lookup_by_id(agent.identity.identifier)
    assert found is agent, "ThreadedAgent should be registered in the AgentRegistry"

    return


def test_threaded_agent_thread_name():
    """
        Verify that the dedicated thread is named after the agent identifier.
    """
    reset_registry()

    agent = create_threaded_agent(name="named-thread-agent")
    agent.run()
    agent.join(timeout=5.0)

    thread = agent.thread
    thread_name = thread.name
    agent_id = agent.identity.identifier
    expected_prefix = "ThreadedAgent-"
    has_prefix = thread_name.startswith(expected_prefix)
    assert has_prefix is True, (
        "Thread name should start with {!r}, got {!r}".format(expected_prefix, thread_name)
    )

    has_id = agent_id in thread_name
    assert has_id is True, (
        "Thread name should contain agent identifier {!r}".format(agent_id)
    )

    return
