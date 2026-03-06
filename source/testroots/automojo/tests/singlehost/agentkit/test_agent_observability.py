"""
    Unit tests for Agent observability integration in the
    automojo-agent-kit framework.

    Tests that the Agent base class correctly initializes the
    ObservabilityPipeline and DebugSession, exposes the observability
    and debug_session properties, applies default configuration when
    no observability settings are provided, and handles exporter
    plugin discovery with mocked extensions.

    Feature: observability-debugging
"""

import logging

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.debugsession import DebugSession
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.observabilityconfiguration import ObservabilityConfiguration
from automojo.agentkit.observabilitypipeline import ObservabilityPipeline
from automojo.agentkit.structuredlogger import StructuredLogger
from automojo.agentkit.tracer import Tracer
from automojo.agentkit.metricscollector import MetricsCollector
from automojo.agentkit.metricsregistry import MetricsRegistry
from automojo.agentkit.executionrecorder import ExecutionRecorder
from automojo.testbase.mocking import Mock


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


class ObservabilityTestAgent(Agent):
    """
        Concrete Agent subclass for observability integration testing.
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


def create_observability_agent(name="obs-agent", version="1.0",
                               settings=None):
    """
        Creates an ObservabilityTestAgent with optional settings.

        :param name: The agent name.
        :param version: The agent version.
        :param settings: Optional settings dictionary.

        :returns: An ObservabilityTestAgent instance.
    """
    config_data = {
        "identity": {"name": name, "version": version}
    }

    if settings is not None:
        config_data["settings"] = settings

    config = AgentConfiguration.from_dict(config_data)
    agent = ObservabilityTestAgent(configuration=config)
    return agent


# ---------------------------------------------------------------------------
# Test: observability property returns ObservabilityPipeline
# ---------------------------------------------------------------------------

def test_observability_property_returns_pipeline():
    """
        Verify that the observability property returns an
        ObservabilityPipeline instance after agent construction.
    """
    reset_registry()

    agent = create_observability_agent()
    pipeline = agent.observability

    assert isinstance(pipeline, ObservabilityPipeline), \
        "observability should return an ObservabilityPipeline, got {}".format(
            type(pipeline).__name__
        )

    return


# ---------------------------------------------------------------------------
# Test: observability pipeline has all subsystem components
# ---------------------------------------------------------------------------

def test_observability_pipeline_has_all_components():
    """
        Verify that the ObservabilityPipeline created by the Agent
        contains all expected subsystem components.
    """
    reset_registry()

    agent = create_observability_agent()
    pipeline = agent.observability

    assert isinstance(pipeline.logger, StructuredLogger), \
        "pipeline.logger should be a StructuredLogger"
    assert isinstance(pipeline.tracer, Tracer), \
        "pipeline.tracer should be a Tracer"
    assert isinstance(pipeline.metrics_collector, MetricsCollector), \
        "pipeline.metrics_collector should be a MetricsCollector"
    assert isinstance(pipeline.metrics_registry, MetricsRegistry), \
        "pipeline.metrics_registry should be a MetricsRegistry"
    assert isinstance(pipeline.execution_recorder, ExecutionRecorder), \
        "pipeline.execution_recorder should be an ExecutionRecorder"

    return


# ---------------------------------------------------------------------------
# Test: debug_session is None when debug mode not enabled
# ---------------------------------------------------------------------------

def test_debug_session_none_when_not_enabled():
    """
        Verify that the debug_session property returns None when
        debug_mode_enabled is not set in the configuration.
    """
    reset_registry()

    agent = create_observability_agent()
    session = agent.debug_session

    assert session is None, \
        "debug_session should be None when debug mode is not enabled, got {}".format(
            type(session).__name__ if session is not None else "None"
        )

    return


# ---------------------------------------------------------------------------
# Test: debug_session is created when debug mode enabled
# ---------------------------------------------------------------------------

def test_debug_session_created_when_enabled():
    """
        Verify that the debug_session property returns a DebugSession
        instance when debug_mode_enabled is True in the observability
        configuration.
    """
    reset_registry()

    settings = {
        "observability": {
            "debug_mode_enabled": True
        }
    }
    agent = create_observability_agent(settings=settings)
    session = agent.debug_session

    assert isinstance(session, DebugSession), \
        "debug_session should be a DebugSession when debug mode is enabled, got {}".format(
            type(session).__name__ if session is not None else "None"
        )

    return


# ---------------------------------------------------------------------------
# Test: default configuration when no observability settings provided
# ---------------------------------------------------------------------------

def test_default_observability_configuration():
    """
        Verify that when no observability settings are provided in the
        AgentConfiguration, the ObservabilityPipeline is created with
        default values: log_level="info", log_format="human_readable",
        tracing/metrics/recording/debug disabled, sampling_rate=1.0.
    """
    reset_registry()

    agent = create_observability_agent()
    pipeline = agent.observability

    # The tracer should have sampling_rate=0.0 (tracing disabled by default)
    tracer = pipeline.tracer
    tracer_sampling_rate = tracer.sampling_rate
    assert tracer_sampling_rate == 0.0, \
        "Tracer sampling rate should be 0.0 when tracing disabled, got {}".format(
            tracer_sampling_rate
        )

    # The execution recorder should not be recording (recording disabled by default)
    recorder = pipeline.execution_recorder
    is_recording = recorder.is_recording
    assert is_recording is False, \
        "ExecutionRecorder should not be recording when recording disabled"

    return


# ---------------------------------------------------------------------------
# Test: custom observability configuration from settings
# ---------------------------------------------------------------------------

def test_custom_observability_configuration():
    """
        Verify that observability settings from the AgentConfiguration
        are correctly applied to the ObservabilityPipeline.
    """
    reset_registry()

    settings = {
        "observability": {
            "log_level": "debug",
            "log_format": "json",
            "tracing_enabled": True,
            "metrics_enabled": True,
            "recording_enabled": True,
            "sampling_rate": 0.5
        }
    }
    agent = create_observability_agent(settings=settings)
    pipeline = agent.observability

    # Tracer should have sampling_rate=0.5 (tracing enabled)
    tracer = pipeline.tracer
    tracer_sampling_rate = tracer.sampling_rate
    assert tracer_sampling_rate == 0.5, \
        "Tracer sampling rate should be 0.5, got {}".format(tracer_sampling_rate)

    # Execution recorder should be recording (recording enabled)
    recorder = pipeline.execution_recorder
    is_recording = recorder.is_recording
    assert is_recording is True, \
        "ExecutionRecorder should be recording when recording enabled"

    # Metrics registry should have built-in metrics registered
    registry = pipeline.metrics_registry
    metric_count = registry.count
    assert metric_count > 0, \
        "MetricsRegistry should have built-in metrics when metrics enabled, got count={}".format(
            metric_count
        )

    return


# ---------------------------------------------------------------------------
# Test: plugin discovery with no extensions does not error
# ---------------------------------------------------------------------------

def test_plugin_discovery_with_no_extensions():
    """
        Verify that plugin discovery completes without error when
        the agent has no extensions registered.
    """
    reset_registry()

    agent = create_observability_agent()

    # Agent should have been created successfully with empty extensions
    extensions = agent.extensions
    ext_count = len(extensions)
    assert ext_count == 0, \
        "Agent should have no extensions initially, got {}".format(ext_count)

    # Pipeline should still be valid
    pipeline = agent.observability
    assert pipeline is not None, \
        "ObservabilityPipeline should be created even with no extensions"

    return


# ---------------------------------------------------------------------------
# Test: plugin discovery with mocked extension that has matching point
# ---------------------------------------------------------------------------

def test_plugin_discovery_registers_matching_exporter():
    """
        Verify that when an extension has a matching extension_point,
        it is registered with the pipeline.
    """
    reset_registry()

    agent = create_observability_agent()

    # Create a mock log exporter with the correct extension_point
    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    ctx = mock_exporter.mock_context()
    ctx.set_attribute("extension_point", "automojo.agentkit.log_exporters")

    # Add the mock exporter to the agent's extensions list
    agent._extensions.append(mock_exporter)

    # Re-run plugin discovery
    agent._discover_exporter_plugins()

    # The pipeline should have the exporter registered
    # We verify by checking the pipeline's internal log exporters list
    pipeline = agent.observability
    log_exporter_count = len(pipeline._log_exporters)
    assert log_exporter_count >= 1, \
        "Pipeline should have at least 1 log exporter after discovery, got {}".format(
            log_exporter_count
        )

    return


# ---------------------------------------------------------------------------
# Test: plugin discovery handles exporter registration failure gracefully
# ---------------------------------------------------------------------------

def test_plugin_discovery_handles_registration_failure():
    """
        Verify that when an exporter plugin raises an exception during
        registration, the failure is logged at WARNING and the agent
        continues without error.
    """
    reset_registry()

    log_records = []

    agent = create_observability_agent()
    logger = agent.get_logger()

    class WarningHandler(logging.Handler):
        """
            A logging handler that captures warning log records.
        """

        def emit(self, record):
            """
                Captures a log record.

                :param record: The log record to capture.
            """
            log_records.append(record)
            return

    handler = WarningHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        # Create a mock exporter that will cause registration to fail
        mock_exporter = Mock()
        mock_exporter.configure(recursive=True)
        ctx = mock_exporter.mock_context()
        ctx.set_attribute("extension_point", "automojo.agentkit.log_exporters")

        # Make the pipeline's register_log_exporter raise an exception
        # by replacing it with a failing function
        original_register = agent.observability.register_log_exporter

        def failing_register(exporter):
            """
                A register function that always raises an exception.

                :param exporter: The exporter to register.
            """
            raise RuntimeError("Simulated registration failure")

        agent.observability.register_log_exporter = failing_register

        # Add the mock exporter and re-run discovery
        agent._extensions.append(mock_exporter)
        agent._discover_exporter_plugins()

        # Verify a warning was logged
        warning_records = [r for r in log_records if r.levelno == logging.WARNING]
        warning_count = len(warning_records)
        assert warning_count >= 1, \
            "At least one WARNING should be logged for registration failure, got {}".format(
                warning_count
            )

    finally:
        logger.removeHandler(handler)

    return


# ---------------------------------------------------------------------------
# Test: plugin discovery skips extensions without matching extension_point
# ---------------------------------------------------------------------------

def test_plugin_discovery_skips_non_matching_extensions():
    """
        Verify that extensions without a matching extension_point
        attribute are not registered as exporters.
    """
    reset_registry()

    agent = create_observability_agent()

    # Create a mock extension with a non-matching extension_point
    mock_ext = Mock()
    mock_ext.configure(recursive=True)
    ctx = mock_ext.mock_context()
    ctx.set_attribute("extension_point", "automojo.agentkit.some_other_point")

    agent._extensions.append(mock_ext)
    agent._discover_exporter_plugins()

    pipeline = agent.observability
    log_exporter_count = len(pipeline._log_exporters)
    trace_exporter_count = len(pipeline._trace_exporters)
    metrics_exporter_count = len(pipeline._metrics_exporters)

    total = log_exporter_count + trace_exporter_count + metrics_exporter_count
    assert total == 0, \
        "No exporters should be registered for non-matching extension points, got {}".format(
            total
        )

    return
