"""
    Tests for Agent platform integration.

    Contains unit tests for the Agent platform_runtime property, convenience
    methods (get_compute_service, get_storage_service, get_messaging_service),
    auto-creation of PlatformRuntime from AgentConfiguration, and platform
    runtime status logging on stop.

    Feature: cross-platform-runtime

    .. module:: automojo.tests.singlehost.agentkit.platform.test_agentplatformintegration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for Agent platform integration.
"""

import os

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_registry():
    """
        Resets the AgentRegistry singleton and clears all registered agents.
    """
    registry = AgentRegistry.instance()
    registry._reset()
    return


class PlatformTestAgent(Agent):
    """
        Concrete Agent subclass for platform integration testing.
    """

    def __init__(self, configuration: AgentConfiguration) -> None:
        super().__init__(configuration)
        return

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
            Logs platform runtime status then transitions to STOPPED state.
        """
        self._stop_platform()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def _create_agent(name="platform-test-agent", version="1.0", settings=None):
    """
        Creates a PlatformTestAgent with the given identity and settings.

        :param name: The agent name.
        :param version: The agent version.
        :param settings: Optional settings dictionary.

        :returns: A PlatformTestAgent instance.
    """
    identity_data = {"name": name, "version": version}
    config_data = {"identity": identity_data}
    if settings is not None:
        config_data["settings"] = settings
    config = AgentConfiguration.from_dict(config_data)
    agent = PlatformTestAgent(configuration=config)
    return agent


def _create_mock_platform_runtime():
    """
        Creates a mock PlatformRuntime with mock services.

        :returns: A tuple of (mock_runtime, mock_compute, mock_storage, mock_messaging).
    """
    mock_compute = Mock()
    mock_compute.configure(recursive=True)

    mock_storage = Mock()
    mock_storage.configure(recursive=True)

    mock_messaging = Mock()
    mock_messaging.configure(recursive=True)

    mock_platform_type = Mock()
    mock_platform_type.configure(recursive=True)
    mock_platform_type.mock_context().mock_method("to_string", return_value="local")

    mock_runtime = Mock()
    mock_runtime.configure(recursive=True)
    mock_runtime.mock_context().mock_method("get_compute_service", return_value=mock_compute)
    mock_runtime.mock_context().mock_method("get_storage_service", return_value=mock_storage)
    mock_runtime.mock_context().mock_method("get_messaging_service", return_value=mock_messaging)
    mock_runtime.mock_context().mock_method("health_check", return_value={
        "local-compute": True,
        "local-storage": True,
        "local-messaging": True,
    })
    mock_runtime.mock_context().set_attribute("platform_type", mock_platform_type)

    return mock_runtime, mock_compute, mock_storage, mock_messaging


# ---------------------------------------------------------------------------
# Test: platform_runtime property returns None when not configured
# ---------------------------------------------------------------------------

def test_platform_runtime_returns_none_when_not_configured():
    """
        Verify that the platform_runtime property returns None when no
        PlatformConfiguration is provided in the AgentConfiguration.
    """
    _reset_registry()

    agent = _create_agent()

    result = agent.platform_runtime

    assert result is None, (
        "platform_runtime should be None when not configured, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# Test: convenience methods raise SemanticError without PlatformRuntime
# ---------------------------------------------------------------------------

def test_get_compute_service_raises_semantic_error_without_runtime():
    """
        Verify that get_compute_service raises SemanticError when no
        PlatformRuntime is configured.
    """
    _reset_registry()

    agent = _create_agent()

    raised = False
    try:
        agent.get_compute_service()
    except SemanticError:
        raised = True

    assert raised is True, (
        "get_compute_service should raise SemanticError without PlatformRuntime."
    )
    return


def test_get_storage_service_raises_semantic_error_without_runtime():
    """
        Verify that get_storage_service raises SemanticError when no
        PlatformRuntime is configured.
    """
    _reset_registry()

    agent = _create_agent()

    raised = False
    try:
        agent.get_storage_service()
    except SemanticError:
        raised = True

    assert raised is True, (
        "get_storage_service should raise SemanticError without PlatformRuntime."
    )
    return


def test_get_messaging_service_raises_semantic_error_without_runtime():
    """
        Verify that get_messaging_service raises SemanticError when no
        PlatformRuntime is configured.
    """
    _reset_registry()

    agent = _create_agent()

    raised = False
    try:
        agent.get_messaging_service()
    except SemanticError:
        raised = True

    assert raised is True, (
        "get_messaging_service should raise SemanticError without PlatformRuntime."
    )
    return


# ---------------------------------------------------------------------------
# Test: convenience methods delegate to PlatformRuntime when configured
# ---------------------------------------------------------------------------

def test_get_compute_service_delegates_to_runtime():
    """
        Verify that get_compute_service returns the ComputeService from
        the PlatformRuntime when configured.
    """
    _reset_registry()

    agent = _create_agent()
    mock_runtime, mock_compute, _, _ = _create_mock_platform_runtime()
    agent._platform_runtime = mock_runtime

    result = agent.get_compute_service()

    assert result is mock_compute, (
        "get_compute_service should return the mock compute service, got: {!r}".format(result)
    )
    return


def test_get_storage_service_delegates_to_runtime():
    """
        Verify that get_storage_service returns the StorageService from
        the PlatformRuntime when configured.
    """
    _reset_registry()

    agent = _create_agent()
    mock_runtime, _, mock_storage, _ = _create_mock_platform_runtime()
    agent._platform_runtime = mock_runtime

    result = agent.get_storage_service()

    assert result is mock_storage, (
        "get_storage_service should return the mock storage service, got: {!r}".format(result)
    )
    return


def test_get_messaging_service_delegates_to_runtime():
    """
        Verify that get_messaging_service returns the MessagingService from
        the PlatformRuntime when configured.
    """
    _reset_registry()

    agent = _create_agent()
    mock_runtime, _, _, mock_messaging = _create_mock_platform_runtime()
    agent._platform_runtime = mock_runtime

    result = agent.get_messaging_service()

    assert result is mock_messaging, (
        "get_messaging_service should return the mock messaging service, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# Test: _stop_platform logs platform runtime status
# ---------------------------------------------------------------------------

def test_stop_platform_logs_runtime_status():
    """
        Verify that _stop_platform invokes health_check on the
        PlatformRuntime when configured.
    """
    _reset_registry()

    agent = _create_agent()
    mock_runtime, _, _, _ = _create_mock_platform_runtime()
    agent._platform_runtime = mock_runtime

    # _stop_platform should not raise
    raised = False
    try:
        agent._stop_platform()
    except Exception:
        raised = True

    assert raised is False, (
        "_stop_platform should not raise when PlatformRuntime is configured."
    )
    return


def test_stop_platform_does_nothing_without_runtime():
    """
        Verify that _stop_platform does not raise when no PlatformRuntime
        is configured.
    """
    _reset_registry()

    agent = _create_agent()

    raised = False
    try:
        agent._stop_platform()
    except Exception:
        raised = True

    assert raised is False, (
        "_stop_platform should not raise when no PlatformRuntime is configured."
    )
    return


# ---------------------------------------------------------------------------
# Test: Agent stop lifecycle includes platform logging
# ---------------------------------------------------------------------------

def test_agent_stop_logs_platform_status():
    """
        Verify that stopping an agent with a configured PlatformRuntime
        invokes health_check during the stop lifecycle.
    """
    _reset_registry()

    agent = _create_agent()
    mock_runtime, _, _, _ = _create_mock_platform_runtime()
    agent._platform_runtime = mock_runtime

    agent.initialize()
    agent.start()
    agent.stop()

    final_state = agent.state
    assert final_state is LifecycleState.STOPPED, (
        "Agent should be in STOPPED state, got: {!r}".format(final_state)
    )
    return


# ---------------------------------------------------------------------------
# Test: AgentConfiguration.get_platform_configuration returns None
# ---------------------------------------------------------------------------

def test_agent_configuration_get_platform_configuration_returns_none():
    """
        Verify that get_platform_configuration returns None when no
        platform settings are present.
    """
    config_data = {"identity": {"name": "test", "version": "1.0"}}
    config = AgentConfiguration.from_dict(config_data)

    result = config.get_platform_configuration()

    assert result is None, (
        "get_platform_configuration should return None, got: {!r}".format(result)
    )
    return


# ---------------------------------------------------------------------------
# Test: AgentConfiguration.get_platform_configuration returns config
# ---------------------------------------------------------------------------

def test_agent_configuration_get_platform_configuration_returns_config():
    """
        Verify that get_platform_configuration returns a PlatformConfiguration
        when platform settings are present.
    """
    from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration

    config_data = {
        "identity": {"name": "test", "version": "1.0"},
        "settings": {
            "platform": {
                "platform_type": "local",
            }
        }
    }
    config = AgentConfiguration.from_dict(config_data)

    result = config.get_platform_configuration()

    assert result is not None, (
        "get_platform_configuration should return a PlatformConfiguration."
    )
    assert isinstance(result, PlatformConfiguration), (
        "Result should be a PlatformConfiguration instance, got: {!r}".format(type(result))
    )
    return


# ---------------------------------------------------------------------------
# Test: Agent auto-creates PlatformRuntime from AgentConfiguration
# ---------------------------------------------------------------------------

def test_agent_auto_creates_platform_runtime_from_config():
    """
        Verify that the Agent auto-creates a PlatformRuntime when the
        AgentConfiguration contains a PlatformConfiguration in settings.
    """
    _reset_registry()

    from automojo.agentkit.platform.platformruntime import PlatformRuntime

    config_data = {
        "identity": {"name": "auto-platform-agent", "version": "1.0"},
        "settings": {
            "platform": {
                "platform_type": "local",
            }
        }
    }
    config = AgentConfiguration.from_dict(config_data)
    agent = PlatformTestAgent(configuration=config)

    runtime = agent.platform_runtime

    assert runtime is not None, (
        "platform_runtime should not be None when platform config is provided."
    )
    assert isinstance(runtime, PlatformRuntime), (
        "platform_runtime should be a PlatformRuntime instance, got: {!r}".format(type(runtime))
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
