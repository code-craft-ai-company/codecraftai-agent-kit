"""
    Unit tests for Agent resilience integration.

    Tests that the Agent base class correctly initializes the
    ResiliencePipeline, exposes resilience properties (resilience,
    health_monitor, circuit_breakers, dead_letter_queue), delegates
    execute_resilient to the pipeline, manages lifecycle (initialize,
    start, stop), and discovers resilience plugins from extensions.

    Feature: error-handling-resilience
    Requirements: 23.1-23.9, 24.1-24.4
"""

import logging

from ccai.agentkit.agent import Agent
from ccai.agentkit.agentconfiguration import AgentConfiguration
from ccai.agentkit.agentregistry import AgentRegistry
from ccai.agentkit.circuitbreakerregistry import CircuitBreakerRegistry
from ccai.agentkit.deadletterqueue import DeadLetterQueue
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.healthcheck import HealthCheck
from ccai.agentkit.healthmonitor import HealthMonitor
from ccai.agentkit.healthstatus import HealthStatus
from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.resilienceconfiguration import ResilienceConfiguration
from ccai.agentkit.resiliencepipeline import ResiliencePipeline
from ccai.agentkit.retrypolicy import RetryPolicy


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_registry():
    """
        Resets the AgentRegistry singleton.
    """
    registry = AgentRegistry.instance()
    registry._reset()
    return


class ResilientTestAgent(Agent):
    """
        Concrete Agent subclass that wires resilience into lifecycle.
    """

    def initialize(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        self._initialize_resilience()
        return

    def start(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        self._start_resilience()
        return

    def pause(self) -> None:
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        self._stop_resilience()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


class ResilientTestAgentWithConfig(Agent):
    """
        Concrete Agent subclass that accepts a ResilienceConfiguration.
    """

    def __init__(self, configuration, resilience_config):
        super().__init__(configuration)
        self._resilience_config = resilience_config
        return

    def initialize(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        self._initialize_resilience(self._resilience_config)
        return

    def start(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        self._start_resilience()
        return

    def pause(self) -> None:
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        self._stop_resilience()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def _create_config(name="resilient-agent"):
    """
        Creates an AgentConfiguration with the given name.

        :param name: The agent name.

        :returns: An AgentConfiguration instance.
    """
    identity_data = {"name": name, "version": "1.0"}
    config_data = {"identity": identity_data}
    config = AgentConfiguration.from_dict(config_data)
    return config


class StubHealthCheck(HealthCheck):
    """
        A concrete HealthCheck subclass for testing plugin discovery.
    """

    def __init__(self, name, extension_point=None):
        super().__init__(name)
        self.extension_point = extension_point
        return

    def check(self) -> HealthStatus:
        return HealthStatus(
            check_name=self._name,
            status="healthy",
            detail="stub check"
        )


# ---------------------------------------------------------------------------
# Requirement 23.1: resilience property returns ResiliencePipeline
# ---------------------------------------------------------------------------

def test_resilience_property_none_before_init():
    """
        Verify resilience is None before initialization.
    """
    _reset_registry()
    config = _create_config("agent-none")
    agent = ResilientTestAgent(config)

    assert agent.resilience is None, "resilience should be None before init"
    assert agent.health_monitor is None, "health_monitor should be None"
    assert agent.circuit_breakers is None, "circuit_breakers should be None"
    assert agent.dead_letter_queue is None, "dead_letter_queue should be None"
    return


def test_resilience_initialized_after_init():
    """
        Verify resilience pipeline is created after initialize.
    """
    _reset_registry()
    config = _create_config("agent-init")
    agent = ResilientTestAgent(config)
    agent.initialize()

    assert agent.resilience is not None, "resilience should be initialized"
    assert isinstance(agent.resilience, ResiliencePipeline), \
        "resilience should be a ResiliencePipeline"
    return


# ---------------------------------------------------------------------------
# Requirement 23.2: health_monitor property
# ---------------------------------------------------------------------------

def test_health_monitor_property_returns_health_monitor():
    """
        Verify health_monitor returns the HealthMonitor from the pipeline.
    """
    _reset_registry()
    config = _create_config("agent-hm-prop")
    agent = ResilientTestAgent(config)
    agent.initialize()

    monitor = agent.health_monitor
    assert monitor is not None, "health_monitor should be available"
    assert isinstance(monitor, HealthMonitor), \
        "health_monitor should be a HealthMonitor instance"
    return


# ---------------------------------------------------------------------------
# Requirement 23.3: circuit_breakers property
# ---------------------------------------------------------------------------

def test_circuit_breakers_property_returns_registry():
    """
        Verify circuit_breakers returns the CircuitBreakerRegistry from the pipeline.
    """
    _reset_registry()
    config = _create_config("agent-cb-prop")
    agent = ResilientTestAgent(config)
    agent.initialize()

    cb_registry = agent.circuit_breakers
    assert cb_registry is not None, "circuit_breakers should be available"
    assert isinstance(cb_registry, CircuitBreakerRegistry), \
        "circuit_breakers should be a CircuitBreakerRegistry instance"
    return


# ---------------------------------------------------------------------------
# Requirement 23.4: dead_letter_queue property
# ---------------------------------------------------------------------------

def test_dead_letter_queue_property_returns_queue():
    """
        Verify dead_letter_queue returns the DeadLetterQueue from the pipeline.
    """
    _reset_registry()
    config = _create_config("agent-dlq-prop")
    agent = ResilientTestAgent(config)
    agent.initialize()

    dlq = agent.dead_letter_queue
    assert dlq is not None, "dead_letter_queue should be available"
    assert isinstance(dlq, DeadLetterQueue), \
        "dead_letter_queue should be a DeadLetterQueue instance"
    return


# ---------------------------------------------------------------------------
# Requirement 23.5: INITIALIZED state sets up resilience
# ---------------------------------------------------------------------------

def test_initialize_creates_resilience_pipeline():
    """
        Verify that transitioning to INITIALIZED creates the ResiliencePipeline.
    """
    _reset_registry()
    config = _create_config("agent-init-pipeline")
    agent = ResilientTestAgent(config)

    assert agent.resilience is None, "pipeline should be None before init"

    agent.initialize()

    assert agent.resilience is not None, "pipeline should exist after init"
    assert agent.state == LifecycleState.INITIALIZED, \
        "agent should be in INITIALIZED state"
    return


def test_initialize_with_custom_config():
    """
        Verify that initialize uses the provided ResilienceConfiguration.
    """
    _reset_registry()
    policy = RetryPolicy(max_retries=5, backoff_strategy="exponential",
                         base_delay=0.1, max_delay=1.0)
    resilience_config = ResilienceConfiguration(
        default_retry_policy=policy,
        circuit_breaker_enabled=True,
        health_monitoring_enabled=True
    )
    agent_config = _create_config("agent-custom-cfg")
    agent = ResilientTestAgentWithConfig(agent_config, resilience_config)
    agent.initialize()

    pipeline = agent.resilience
    assert pipeline is not None, "pipeline should exist"
    assert pipeline.retry_executor is not None, "retry_executor should exist"
    assert pipeline.circuit_breaker_registry is not None, \
        "circuit_breaker_registry should exist"
    assert pipeline.health_monitor is not None, \
        "health_monitor should exist"
    return


# ---------------------------------------------------------------------------
# Requirement 23.6: RUNNING state starts HealthMonitor
# ---------------------------------------------------------------------------

def test_health_monitor_started_after_start():
    """
        Verify health monitor is active after start.
    """
    _reset_registry()
    config = _create_config("agent-start")
    agent = ResilientTestAgent(config)
    agent.initialize()
    agent.start()

    assert agent.health_monitor.is_active is True, \
        "health_monitor should be active after start"
    return


def test_health_monitor_not_started_when_disabled():
    """
        Verify health monitor is not started when health monitoring is disabled.
    """
    _reset_registry()
    resilience_config = ResilienceConfiguration(
        health_monitoring_enabled=False
    )
    agent_config = _create_config("agent-hm-disabled")
    agent = ResilientTestAgentWithConfig(agent_config, resilience_config)
    agent.initialize()
    agent.start()

    assert agent.health_monitor is None, \
        "health_monitor should be None when disabled"
    return


# ---------------------------------------------------------------------------
# Requirement 23.7: STOPPED state stops HealthMonitor
# ---------------------------------------------------------------------------

def test_health_monitor_stopped_after_stop():
    """
        Verify health monitor is inactive after stop.
    """
    _reset_registry()
    config = _create_config("agent-stop")
    agent = ResilientTestAgent(config)
    agent.initialize()
    agent.start()
    agent.stop()

    assert agent.health_monitor.is_active is False, \
        "health_monitor should be inactive after stop"
    return


def test_stop_without_start_does_not_error():
    """
        Verify stopping an initialized agent without starting does not raise.
    """
    _reset_registry()
    config = _create_config("agent-stop-no-start")
    agent = ResilientTestAgent(config)
    agent.initialize()

    # Health monitor exists but is not active
    assert agent.health_monitor.is_active is False, \
        "health_monitor should not be active before start"

    agent.stop()

    assert agent.health_monitor.is_active is False, \
        "health_monitor should remain inactive"
    return


# ---------------------------------------------------------------------------
# Requirement 23.9: execute_resilient delegates to pipeline
# ---------------------------------------------------------------------------

def test_execute_resilient_success():
    """
        Verify execute_resilient returns callable result.
    """
    _reset_registry()
    policy = RetryPolicy(max_retries=2, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    resilience_config = ResilienceConfiguration(default_retry_policy=policy)
    agent_config = _create_config("agent-exec")
    agent = ResilientTestAgentWithConfig(agent_config, resilience_config)
    agent.initialize()

    result = agent.execute_resilient(lambda: 42, operation_name="test")

    assert result == 42, "should return callable result"
    return


def test_execute_resilient_raises_without_init():
    """
        Verify execute_resilient raises SemanticError when not initialized.
    """
    _reset_registry()
    config = _create_config("agent-no-init")
    agent = ResilientTestAgent(config)

    raised = False
    try:
        agent.execute_resilient(lambda: 42)
    except SemanticError:
        raised = True

    assert raised is True, "should raise SemanticError without resilience init"
    return


def test_execute_resilient_with_operation_name():
    """
        Verify execute_resilient passes operation_name to the pipeline.
    """
    _reset_registry()
    policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                         base_delay=0.01, max_delay=0.1)
    resilience_config = ResilienceConfiguration(default_retry_policy=policy)
    agent_config = _create_config("agent-exec-name")
    agent = ResilientTestAgentWithConfig(agent_config, resilience_config)
    agent.initialize()

    result = agent.execute_resilient(
        lambda: "hello",
        operation_name="greeting-op"
    )

    assert result == "hello", "should return callable result"
    return


def test_execute_resilient_with_retry_policy_override():
    """
        Verify execute_resilient accepts a retry_policy override.
    """
    _reset_registry()
    default_policy = RetryPolicy(max_retries=1, backoff_strategy="fixed",
                                 base_delay=0.01, max_delay=0.1)
    override_policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                                  base_delay=0.01, max_delay=0.1)
    resilience_config = ResilienceConfiguration(default_retry_policy=default_policy)
    agent_config = _create_config("agent-exec-override")
    agent = ResilientTestAgentWithConfig(agent_config, resilience_config)
    agent.initialize()

    result = agent.execute_resilient(
        lambda: 99,
        operation_name="override-op",
        retry_policy=override_policy
    )

    assert result == 99, "should return callable result with override policy"
    return


# ---------------------------------------------------------------------------
# Requirement 23.1-23.4: disabled components return None
# ---------------------------------------------------------------------------

def test_resilience_with_disabled_components():
    """
        Verify resilience works with all components disabled.
    """
    _reset_registry()
    resilience_config = ResilienceConfiguration(
        circuit_breaker_enabled=False,
        degradation_enabled=False,
        dead_letter_enabled=False,
        health_monitoring_enabled=False,
        self_healing_enabled=False
    )
    agent_config = _create_config("agent-disabled")
    agent = ResilientTestAgentWithConfig(agent_config, resilience_config)
    agent.initialize()

    assert agent.resilience is not None, "pipeline should exist"
    assert agent.health_monitor is None, "health_monitor should be None"
    assert agent.circuit_breakers is None, "circuit_breakers should be None"
    assert agent.dead_letter_queue is None, "dead_letter_queue should be None"
    return


# ---------------------------------------------------------------------------
# Requirement 23.5: default ResilienceConfiguration when none provided
# ---------------------------------------------------------------------------

def test_initialize_with_default_config():
    """
        Verify that _initialize_resilience uses a default config when
        none is provided.
    """
    _reset_registry()
    config = _create_config("agent-default-cfg")
    agent = ResilientTestAgent(config)
    agent.initialize()

    pipeline = agent.resilience
    assert pipeline is not None, "pipeline should exist with default config"

    # Default config enables all components
    assert pipeline.health_monitor is not None, \
        "health_monitor should be enabled by default"
    assert pipeline.circuit_breaker_registry is not None, \
        "circuit_breaker_registry should be enabled by default"
    assert pipeline.dead_letter_queue is not None, \
        "dead_letter_queue should be enabled by default"
    return


# ---------------------------------------------------------------------------
# Requirement 23.6-23.7: full lifecycle integration
# ---------------------------------------------------------------------------

def test_full_lifecycle_resilience():
    """
        Verify resilience through the full agent lifecycle:
        initialize -> start -> stop.
    """
    _reset_registry()
    config = _create_config("agent-lifecycle")
    agent = ResilientTestAgent(config)

    # Before init
    assert agent.resilience is None, "no pipeline before init"

    # Initialize
    agent.initialize()
    assert agent.resilience is not None, "pipeline after init"
    assert agent.health_monitor.is_active is False, \
        "monitor not active after init"

    # Start
    agent.start()
    assert agent.health_monitor.is_active is True, \
        "monitor active after start"

    # Stop
    agent.stop()
    assert agent.health_monitor.is_active is False, \
        "monitor inactive after stop"
    return


# ---------------------------------------------------------------------------
# Requirement 23.8, 24.1-24.2: Plugin discovery
# ---------------------------------------------------------------------------

def test_plugin_discovery_registers_health_check():
    """
        Verify that a HealthCheck extension with extension_point
        "ccai.agentkit.resilience" is registered with the
        HealthMonitor's registry during initialization.
    """
    _reset_registry()
    config = _create_config("agent-plugin-hc")
    agent = ResilientTestAgent(config)

    # Add a stub health check extension before initialization
    stub_check = StubHealthCheck(
        "plugin-check",
        extension_point="ccai.agentkit.resilience"
    )
    agent._extensions.append(stub_check)

    agent.initialize()

    # The health check should be registered in the monitor's registry
    monitor = agent.health_monitor
    assert monitor is not None, "health_monitor should exist"
    registry = monitor._health_check_registry
    found = registry.has_health_check("plugin-check")
    assert found is True, \
        "plugin health check should be registered in the registry"
    return


def test_plugin_discovery_skips_non_matching_extension_point():
    """
        Verify that extensions with a different extension_point are
        not registered as resilience plugins.
    """
    _reset_registry()
    config = _create_config("agent-plugin-skip")
    agent = ResilientTestAgent(config)

    # Add a health check with a non-matching extension point
    stub_check = StubHealthCheck(
        "other-check",
        extension_point="ccai.agentkit.other"
    )
    agent._extensions.append(stub_check)

    agent.initialize()

    monitor = agent.health_monitor
    registry = monitor._health_check_registry
    found = registry.has_health_check("other-check")
    assert found is False, \
        "non-matching extension should not be registered"
    return


# ---------------------------------------------------------------------------
# Requirement 24.3: Plugin load failure logged at WARNING
# ---------------------------------------------------------------------------

def test_plugin_discovery_handles_load_failure():
    """
        Verify that when a resilience plugin fails to load, the failure
        is logged at WARNING and the agent continues without error.
    """
    _reset_registry()
    log_records = []

    config = _create_config("agent-plugin-fail")
    agent = ResilientTestAgent(config)

    logger = agent.get_logger()

    class WarningCapture(logging.Handler):
        """
            Captures log records for assertion.
        """

        def emit(self, record):
            """
                Stores the log record.

                :param record: The log record.
            """
            log_records.append(record)
            return

    handler = WarningCapture()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        # Create a HealthCheck subclass whose name property raises
        class FailingHealthCheck(HealthCheck):
            """
                A HealthCheck that raises when name is accessed.
            """

            def __init__(self):
                # Bypass parent __init__ to avoid setting _name
                self.extension_point = "ccai.agentkit.resilience"
                self._check_interval = 30.0
                return

            @property
            def name(self):
                """
                    Raises an error when name is accessed.
                """
                raise RuntimeError("Simulated plugin load failure")

            def check(self):
                """
                    Stub check method.
                """
                return HealthStatus(
                    check_name="failing",
                    status="healthy",
                    detail="stub"
                )

        broken_check = FailingHealthCheck()
        agent._extensions.append(broken_check)

        agent.initialize()

        # Agent should still be initialized successfully
        assert agent.resilience is not None, \
            "pipeline should exist despite plugin failure"

        # Check that a warning was logged
        warning_records = [
            r for r in log_records if r.levelno == logging.WARNING
        ]
        warning_count = len(warning_records)
        assert warning_count >= 1, \
            "at least one WARNING should be logged for plugin failure, got {}".format(
                warning_count
            )

    finally:
        logger.removeHandler(handler)

    return


# ---------------------------------------------------------------------------
# Requirement 24.4: Plugin name conflict logged at WARNING
# ---------------------------------------------------------------------------

def test_plugin_discovery_handles_name_conflict():
    """
        Verify that when a resilience plugin has a name that conflicts
        with an already registered component, the conflict is logged
        at WARNING and the duplicate is skipped.
    """
    _reset_registry()
    log_records = []

    config = _create_config("agent-plugin-conflict")
    agent = ResilientTestAgent(config)

    logger = agent.get_logger()

    class WarningCapture(logging.Handler):
        """
            Captures log records for assertion.
        """

        def emit(self, record):
            """
                Stores the log record.

                :param record: The log record.
            """
            log_records.append(record)
            return

    handler = WarningCapture()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        # Add two health checks with the same name
        check_a = StubHealthCheck(
            "duplicate-check",
            extension_point="ccai.agentkit.resilience"
        )
        check_b = StubHealthCheck(
            "duplicate-check",
            extension_point="ccai.agentkit.resilience"
        )
        agent._extensions.append(check_a)
        agent._extensions.append(check_b)

        agent.initialize()

        # Only the first should be registered
        monitor = agent.health_monitor
        registry = monitor._health_check_registry
        found = registry.has_health_check("duplicate-check")
        assert found is True, "first check should be registered"

        # Check that a warning was logged for the conflict
        warning_records = [
            r for r in log_records if r.levelno == logging.WARNING
        ]
        conflict_warnings = [
            r for r in warning_records
            if "conflict" in r.getMessage().lower()
            or "already registered" in r.getMessage().lower()
        ]
        conflict_count = len(conflict_warnings)
        assert conflict_count >= 1, \
            "at least one WARNING about name conflict should be logged, got {}".format(
                conflict_count
            )

    finally:
        logger.removeHandler(handler)

    return


# ---------------------------------------------------------------------------
# Requirement 24.2: Multiple plugin types discovered
# ---------------------------------------------------------------------------

def test_plugin_discovery_with_no_extensions():
    """
        Verify that plugin discovery completes without error when
        the agent has no extensions.
    """
    _reset_registry()
    config = _create_config("agent-no-ext")
    agent = ResilientTestAgent(config)

    # Ensure no extensions
    agent._extensions = []

    agent.initialize()

    assert agent.resilience is not None, \
        "pipeline should be created even with no extensions"
    return


def test_plugin_discovery_with_multiple_health_checks():
    """
        Verify that multiple HealthCheck plugins with unique names
        are all registered.
    """
    _reset_registry()
    config = _create_config("agent-multi-hc")
    agent = ResilientTestAgent(config)

    check_a = StubHealthCheck(
        "check-alpha",
        extension_point="ccai.agentkit.resilience"
    )
    check_b = StubHealthCheck(
        "check-beta",
        extension_point="ccai.agentkit.resilience"
    )
    agent._extensions.append(check_a)
    agent._extensions.append(check_b)

    agent.initialize()

    monitor = agent.health_monitor
    registry = monitor._health_check_registry
    assert registry.has_health_check("check-alpha") is True, \
        "check-alpha should be registered"
    assert registry.has_health_check("check-beta") is True, \
        "check-beta should be registered"
    assert registry.count >= 2, \
        "at least 2 health checks should be registered"
    return
