"""
    Integration tests for Agent configuration and extensibility integration
    in the codecraftai-agent-kit framework.

    Tests that the Agent base class correctly exposes configuration_manager,
    feature_flags, and plugin_manager properties, and that convenience methods
    delegate to the appropriate subsystems. Also tests configuration lifecycle
    helpers: _initialize_configuration, _initialize_plugins, _start_hot_reload,
    and _stop_configuration.

    Feature: configuration-extensibility
"""

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.configurationmanager import ConfigurationManager
from ccai.agentkit.featureflag import FeatureFlag
from ccai.agentkit.featureflagregistry import FeatureFlagRegistry
from ccai.agentkit.hotreloadmonitor import HotReloadMonitor
from ccai.agentkit.hotreloadpolicy import HotReloadPolicy
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.pluginmanager import PluginManager


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


class ConcreteAgent(Agent):
    """
        Concrete Agent subclass for configuration integration testing.

        Provides minimal lifecycle implementations that call the
        configuration lifecycle helpers.
    """

    def initialize(self):
        """
            Transitions the agent to INITIALIZED state.
        """
        self._initialize_configuration()
        self._initialize_plugins()
        self._initialize_feature_flags()
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self):
        """
            Transitions the agent to RUNNING state.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self):
        """
            Transitions the agent to PAUSED state.
        """
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self):
        """
            Transitions the agent to RUNNING state from PAUSED.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self):
        """
            Stops configuration resources and transitions to STOPPED state.
        """
        self._stop_configuration()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self):
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def create_agent(name="test-agent", version="1.0"):
    """
        Creates a ConcreteAgent with the given identity parameters.

        :param name: The agent name.
        :param version: The agent version.

        :returns: A ConcreteAgent instance.
    """
    reset_registry()
    identity_data = {"name": name, "version": version}
    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    agent = ConcreteAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# Test: configuration_manager property returns ConfigurationManager
# ---------------------------------------------------------------------------

def test_configuration_manager_property_returns_configuration_manager():
    """
        Tests that the configuration_manager property is accessible and
        returns a ConfigurationManager instance.
    """
    agent = create_agent()

    cm = agent.configuration_manager
    is_correct_type = isinstance(cm, ConfigurationManager)
    assert is_correct_type is True, \
        "Expected ConfigurationManager instance but got {}".format(type(cm).__name__)

    return


# ---------------------------------------------------------------------------
# Test: feature_flags property returns FeatureFlagRegistry
# ---------------------------------------------------------------------------

def test_feature_flags_property_returns_feature_flag_registry():
    """
        Tests that the feature_flags property is accessible and returns
        a FeatureFlagRegistry instance.
    """
    agent = create_agent()

    ff = agent.feature_flags
    is_correct_type = isinstance(ff, FeatureFlagRegistry)
    assert is_correct_type is True, \
        "Expected FeatureFlagRegistry instance but got {}".format(type(ff).__name__)

    return


# ---------------------------------------------------------------------------
# Test: plugin_manager property returns PluginManager
# ---------------------------------------------------------------------------

def test_plugin_manager_property_returns_plugin_manager():
    """
        Tests that the plugin_manager property is accessible and returns
        a PluginManager instance.
    """
    agent = create_agent()

    pm = agent.plugin_manager
    is_correct_type = isinstance(pm, PluginManager)
    assert is_correct_type is True, \
        "Expected PluginManager instance but got {}".format(type(pm).__name__)

    return


# ---------------------------------------------------------------------------
# Test: get_config delegates to ConfigurationManager
# ---------------------------------------------------------------------------

def test_get_config_delegates_to_configuration_manager():
    """
        Tests that get_config delegates to ConfigurationManager.get by
        loading defaults and then retrieving values through get_config.
    """
    agent = create_agent()

    defaults = {
        "logging": {
            "level": "DEBUG",
            "format": "json"
        },
        "timeout": 30
    }
    agent.configuration_manager.load_defaults(defaults)

    level_value = agent.get_config("logging.level")
    assert level_value == "DEBUG", \
        "Expected 'DEBUG' but got '{}'".format(level_value)

    format_value = agent.get_config("logging.format")
    assert format_value == "json", \
        "Expected 'json' but got '{}'".format(format_value)

    timeout_value = agent.get_config("timeout")
    assert timeout_value == 30, \
        "Expected 30 but got {}".format(timeout_value)

    return


# ---------------------------------------------------------------------------
# Test: get_config returns default when path not found
# ---------------------------------------------------------------------------

def test_get_config_returns_default_when_not_found():
    """
        Tests that get_config returns the default value when the field
        path is not found in the configuration.
    """
    agent = create_agent()

    result = agent.get_config("nonexistent.path", default="fallback")
    assert result == "fallback", \
        "Expected 'fallback' but got '{}'".format(result)

    result_none = agent.get_config("nonexistent.path")
    assert result_none is None, \
        "Expected None but got {}".format(result_none)

    return


# ---------------------------------------------------------------------------
# Test: is_feature_enabled delegates to FeatureFlagRegistry
# ---------------------------------------------------------------------------

def test_is_feature_enabled_delegates_to_feature_flag_registry():
    """
        Tests that is_feature_enabled delegates to FeatureFlagRegistry.is_enabled
        by registering a flag and then checking its value through the agent.
    """
    agent = create_agent()

    flag_enabled = FeatureFlag(name="my-feature", default_value=True, description="Test flag")
    agent.feature_flags.register(flag_enabled)

    result_enabled = agent.is_feature_enabled("my-feature")
    assert result_enabled is True, \
        "Expected True but got {}".format(result_enabled)

    flag_disabled = FeatureFlag(name="disabled-feature", default_value=False)
    agent.feature_flags.register(flag_disabled)

    result_disabled = agent.is_feature_enabled("disabled-feature")
    assert result_disabled is False, \
        "Expected False but got {}".format(result_disabled)

    return


# ---------------------------------------------------------------------------
# Test: is_feature_enabled respects runtime overrides
# ---------------------------------------------------------------------------

def test_is_feature_enabled_respects_overrides():
    """
        Tests that is_feature_enabled respects runtime overrides set
        on the FeatureFlagRegistry.
    """
    agent = create_agent()

    flag = FeatureFlag(name="override-flag", default_value=False)
    agent.feature_flags.register(flag)

    before_override = agent.is_feature_enabled("override-flag")
    assert before_override is False, \
        "Expected False before override but got {}".format(before_override)

    agent.feature_flags.set_override("override-flag", True)

    after_override = agent.is_feature_enabled("override-flag")
    assert after_override is True, \
        "Expected True after override but got {}".format(after_override)

    return


# ---------------------------------------------------------------------------
# Test: _initialize_configuration loads config from AgentConfiguration
# ---------------------------------------------------------------------------

def test_initialize_configuration_loads_defaults():
    """
        Tests that _initialize_configuration loads configuration from
        the AgentConfiguration into the ConfigurationManager as defaults.
        After initialize, the agent's configuration should be accessible
        through get_config.
    """
    agent = create_agent(name="config-agent", version="2.0")

    agent.initialize()

    name_value = agent.get_config("identity.name")
    assert name_value == "config-agent", \
        "Expected 'config-agent' but got '{}'".format(name_value)

    version_value = agent.get_config("identity.version")
    assert version_value == "2.0", \
        "Expected '2.0' but got '{}'".format(version_value)

    return


# ---------------------------------------------------------------------------
# Test: _initialize_plugins calls discover on PluginManager
# ---------------------------------------------------------------------------

def test_initialize_plugins_calls_discover():
    """
        Tests that _initialize_plugins calls discover on the PluginManager.
        After initialize, the plugin manager should have been invoked.
        Since discover returns an empty list by default, we verify no
        errors occur and the plugin manager is accessible.
    """
    agent = create_agent()

    agent.initialize()

    pm = agent.plugin_manager
    is_correct_type = isinstance(pm, PluginManager)
    assert is_correct_type is True, \
        "Expected PluginManager instance after initialize"

    plugin_list = pm.list_all()
    plugin_count = len(plugin_list)
    assert plugin_count == 0, \
        "Expected 0 plugins after discover but got {}".format(plugin_count)

    return


# ---------------------------------------------------------------------------
# Test: _start_hot_reload creates and starts a HotReloadMonitor
# ---------------------------------------------------------------------------

def test_start_hot_reload_creates_and_starts_monitor():
    """
        Tests that _start_hot_reload creates a HotReloadMonitor and
        starts it. After calling _start_hot_reload, the monitor should
        be active.
    """
    agent = create_agent()

    policy = HotReloadPolicy(
        polling_interval=1.0,
        monitored_files=[],
        environment_monitoring_enabled=False,
        automatic_reload_enabled=True
    )

    agent._start_hot_reload(policy)

    monitor = agent._hot_reload_monitor
    assert monitor is not None, \
        "Expected _hot_reload_monitor to be set after _start_hot_reload"

    is_monitor_type = isinstance(monitor, HotReloadMonitor)
    assert is_monitor_type is True, \
        "Expected HotReloadMonitor instance but got {}".format(type(monitor).__name__)

    is_active = monitor.is_active
    assert is_active is True, \
        "Expected monitor to be active after _start_hot_reload"

    # Clean up: stop the monitor to release the background thread
    monitor.stop()

    return


# ---------------------------------------------------------------------------
# Test: _stop_configuration stops monitor and unloads plugins
# ---------------------------------------------------------------------------

def test_stop_configuration_stops_monitor():
    """
        Tests that _stop_configuration stops the HotReloadMonitor if
        one is running and sets the reference to None.
    """
    agent = create_agent()

    policy = HotReloadPolicy(
        polling_interval=1.0,
        monitored_files=[],
        environment_monitoring_enabled=False,
        automatic_reload_enabled=True
    )

    agent._start_hot_reload(policy)

    monitor_before = agent._hot_reload_monitor
    assert monitor_before is not None, \
        "Expected monitor to be set before _stop_configuration"

    is_active_before = monitor_before.is_active
    assert is_active_before is True, \
        "Expected monitor to be active before _stop_configuration"

    agent._stop_configuration()

    monitor_after = agent._hot_reload_monitor
    assert monitor_after is None, \
        "Expected _hot_reload_monitor to be None after _stop_configuration"

    is_active_after = monitor_before.is_active
    assert is_active_after is False, \
        "Expected monitor to be inactive after _stop_configuration"

    return


# ---------------------------------------------------------------------------
# Test: _stop_configuration with no monitor does not error
# ---------------------------------------------------------------------------

def test_stop_configuration_without_monitor_does_not_error():
    """
        Tests that _stop_configuration does not raise an error when
        no HotReloadMonitor has been started.
    """
    agent = create_agent()

    monitor_before = agent._hot_reload_monitor
    assert monitor_before is None, \
        "Expected no monitor before _stop_configuration"

    # Should not raise any exception
    agent._stop_configuration()

    monitor_after = agent._hot_reload_monitor
    assert monitor_after is None, \
        "Expected no monitor after _stop_configuration"

    return


# ---------------------------------------------------------------------------
# Test: Full lifecycle with configuration integration
# ---------------------------------------------------------------------------

def test_full_lifecycle_with_configuration():
    """
        Tests the full agent lifecycle with configuration integration:
        create -> initialize (loads config, discovers plugins) ->
        start -> stop (cleans up configuration).
    """
    agent = create_agent(name="lifecycle-config-agent", version="3.0")

    state_created = agent.state
    assert state_created is LifecycleState.CREATED, \
        "Expected CREATED but got {}".format(state_created)

    agent.initialize()

    state_init = agent.state
    assert state_init is LifecycleState.INITIALIZED, \
        "Expected INITIALIZED but got {}".format(state_init)

    # Verify configuration was loaded during initialize
    name_value = agent.get_config("identity.name")
    assert name_value == "lifecycle-config-agent", \
        "Expected 'lifecycle-config-agent' but got '{}'".format(name_value)

    agent.start()

    state_running = agent.state
    assert state_running is LifecycleState.RUNNING, \
        "Expected RUNNING but got {}".format(state_running)

    agent.stop()

    state_stopped = agent.state
    assert state_stopped is LifecycleState.STOPPED, \
        "Expected STOPPED but got {}".format(state_stopped)

    return
