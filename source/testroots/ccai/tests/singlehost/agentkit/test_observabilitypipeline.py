"""
    Unit tests for the ccai.agentkit.observabilitypipeline module.

    Tests the ObservabilityPipeline class: component initialization,
    no-op behavior when subsystems are disabled, exporter registration,
    shutdown lifecycle, and property access.
"""

from ccai.agentkit.correlationcontext import CorrelationContext
from ccai.agentkit.executionrecorder import ExecutionRecorder
from ccai.agentkit.metricscollector import MetricsCollector
from ccai.agentkit.metricsregistry import MetricsRegistry
from ccai.agentkit.observabilityconfiguration import ObservabilityConfiguration
from ccai.agentkit.observabilitypipeline import ObservabilityPipeline
from ccai.agentkit.structuredlogger import StructuredLogger
from ccai.agentkit.tracer import Tracer
from ccai.testbase.mocking import Mock


def test_construction_creates_all_components():
    """
        Verify that constructing an ObservabilityPipeline creates all
        subsystem components: logger, tracer, metrics_collector,
        metrics_registry, and execution_recorder.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-001"
    )

    assert isinstance(pipeline.logger, StructuredLogger), \
        "logger should be a StructuredLogger instance"
    assert isinstance(pipeline.tracer, Tracer), \
        "tracer should be a Tracer instance"
    assert isinstance(pipeline.metrics_collector, MetricsCollector), \
        "metrics_collector should be a MetricsCollector instance"
    assert isinstance(pipeline.metrics_registry, MetricsRegistry), \
        "metrics_registry should be a MetricsRegistry instance"
    assert isinstance(pipeline.execution_recorder, ExecutionRecorder), \
        "execution_recorder should be an ExecutionRecorder instance"
    return


def test_construction_auto_creates_correlation_context():
    """
        Verify that when no CorrelationContext is provided, the pipeline
        auto-creates one and passes it to the StructuredLogger.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-002"
    )

    correlation_context = pipeline.logger.correlation_context
    assert correlation_context is not None, \
        "CorrelationContext should be auto-created"
    assert isinstance(correlation_context, CorrelationContext), \
        "Auto-created context should be a CorrelationContext instance"
    return


def test_construction_uses_provided_correlation_context():
    """
        Verify that when a CorrelationContext is provided, the pipeline
        passes it to the StructuredLogger.
    """
    context = CorrelationContext(correlation_id="custom-corr-id")
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-003",
        correlation_context=context
    )

    logger_context = pipeline.logger.correlation_context
    assert logger_context.correlation_id == "custom-corr-id", \
        "Logger should use the provided CorrelationContext"
    return


def test_tracing_disabled_sets_sampling_rate_zero():
    """
        Verify that when tracing_enabled is False, the Tracer is created
        with sampling_rate=0.0 so spans are not exported.
    """
    config = ObservabilityConfiguration(tracing_enabled=False)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-004"
    )

    assert pipeline.tracer.sampling_rate == 0.0, \
        "Tracer sampling_rate should be 0.0 when tracing is disabled"
    return


def test_tracing_enabled_uses_configured_sampling_rate():
    """
        Verify that when tracing_enabled is True, the Tracer uses the
        configured sampling_rate from the ObservabilityConfiguration.
    """
    config = ObservabilityConfiguration(
        tracing_enabled=True,
        sampling_rate=0.75
    )
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-005"
    )

    assert pipeline.tracer.sampling_rate == 0.75, \
        "Tracer sampling_rate should match the configured value"
    return


def test_metrics_enabled_registers_builtin_metrics():
    """
        Verify that when metrics_enabled is True, the built-in agent
        metrics are automatically registered in the MetricsRegistry.
    """
    config = ObservabilityConfiguration(metrics_enabled=True)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-006"
    )

    registry = pipeline.metrics_registry
    assert registry.count == 13, \
        "MetricsRegistry should have 13 built-in metrics when metrics enabled"
    assert registry.has_metric("agent.lifecycle.transitions"), \
        "Built-in metric 'agent.lifecycle.transitions' should be registered"
    assert registry.has_metric("agent.active.spans"), \
        "Built-in metric 'agent.active.spans' should be registered"
    return


def test_metrics_disabled_does_not_register_builtin_metrics():
    """
        Verify that when metrics_enabled is False, no built-in metrics
        are registered in the MetricsRegistry.
    """
    config = ObservabilityConfiguration(metrics_enabled=False)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-007"
    )

    registry = pipeline.metrics_registry
    assert registry.count == 0, \
        "MetricsRegistry should be empty when metrics disabled"
    return


def test_recording_enabled_starts_recorder():
    """
        Verify that when recording_enabled is True, the ExecutionRecorder
        is started and is_recording returns True.
    """
    config = ObservabilityConfiguration(recording_enabled=True)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-008"
    )

    assert pipeline.execution_recorder.is_recording is True, \
        "ExecutionRecorder should be recording when recording is enabled"
    return


def test_recording_disabled_does_not_start_recorder():
    """
        Verify that when recording_enabled is False, the ExecutionRecorder
        is not started and is_recording returns False.
    """
    config = ObservabilityConfiguration(recording_enabled=False)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-009"
    )

    assert pipeline.execution_recorder.is_recording is False, \
        "ExecutionRecorder should not be recording when recording is disabled"
    return


def test_recording_disabled_discards_events():
    """
        Verify that when recording is disabled, calling record on the
        ExecutionRecorder silently discards events.
    """
    config = ObservabilityConfiguration(recording_enabled=False)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-010"
    )

    recorder = pipeline.execution_recorder
    recorder.record(
        event_type="lifecycle",
        correlation_id="corr-001",
        payload={"state": "initialized"}
    )

    assert recorder.count == 0, \
        "ExecutionRecorder should discard events when not recording"
    return


def test_register_log_exporter():
    """
        Verify that register_log_exporter adds the exporter to the
        pipeline's log exporter list.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-011"
    )

    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    pipeline.register_log_exporter(mock_exporter)

    # Verify the exporter is tracked by checking repr includes count
    repr_str = repr(pipeline)
    assert "log_exporters=1" in repr_str, \
        "Pipeline repr should show 1 log exporter after registration"
    return


def test_register_trace_exporter():
    """
        Verify that register_trace_exporter adds the exporter to the
        pipeline and registers it with the Tracer.
    """
    config = ObservabilityConfiguration(tracing_enabled=True)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-012"
    )

    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    pipeline.register_trace_exporter(mock_exporter)

    repr_str = repr(pipeline)
    assert "trace_exporters=1" in repr_str, \
        "Pipeline repr should show 1 trace exporter after registration"
    return


def test_register_metrics_exporter():
    """
        Verify that register_metrics_exporter adds the exporter to the
        pipeline and registers it with the MetricsCollector.
    """
    config = ObservabilityConfiguration(metrics_enabled=True)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-013"
    )

    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    pipeline.register_metrics_exporter(mock_exporter)

    repr_str = repr(pipeline)
    assert "metrics_exporters=1" in repr_str, \
        "Pipeline repr should show 1 metrics exporter after registration"
    return


def test_shutdown_flushes_and_shuts_down_log_exporters():
    """
        Verify that shutdown calls flush and shutdown on all registered
        log exporters.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-014"
    )

    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    flush_ctx = mock_exporter.mock_context().mock_method('flush')
    shutdown_ctx = mock_exporter.mock_context().mock_method('shutdown')

    pipeline.register_log_exporter(mock_exporter)
    pipeline.shutdown()

    flush_ctx.assert_called_once()
    shutdown_ctx.assert_called_once()
    return


def test_shutdown_flushes_and_shuts_down_trace_exporters():
    """
        Verify that shutdown calls flush and shutdown on all registered
        trace exporters.
    """
    config = ObservabilityConfiguration(tracing_enabled=True)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-015"
    )

    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    flush_ctx = mock_exporter.mock_context().mock_method('flush')
    shutdown_ctx = mock_exporter.mock_context().mock_method('shutdown')

    pipeline.register_trace_exporter(mock_exporter)
    pipeline.shutdown()

    flush_ctx.assert_called_once()
    shutdown_ctx.assert_called_once()
    return


def test_shutdown_flushes_and_shuts_down_metrics_exporters():
    """
        Verify that shutdown calls flush and shutdown on all registered
        metrics exporters.
    """
    config = ObservabilityConfiguration(metrics_enabled=True)
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-016"
    )

    mock_exporter = Mock()
    mock_exporter.configure(recursive=True)
    flush_ctx = mock_exporter.mock_context().mock_method('flush')
    shutdown_ctx = mock_exporter.mock_context().mock_method('shutdown')

    pipeline.register_metrics_exporter(mock_exporter)
    pipeline.shutdown()

    flush_ctx.assert_called_once()
    shutdown_ctx.assert_called_once()
    return


def test_shutdown_with_multiple_exporters():
    """
        Verify that shutdown flushes and shuts down all exporters across
        all exporter types.
    """
    config = ObservabilityConfiguration(
        tracing_enabled=True,
        metrics_enabled=True
    )
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-017"
    )

    log_exporter = Mock()
    log_exporter.configure(recursive=True)
    log_flush = log_exporter.mock_context().mock_method('flush')
    log_shutdown = log_exporter.mock_context().mock_method('shutdown')

    trace_exporter = Mock()
    trace_exporter.configure(recursive=True)
    trace_flush = trace_exporter.mock_context().mock_method('flush')
    trace_shutdown = trace_exporter.mock_context().mock_method('shutdown')

    metrics_exporter = Mock()
    metrics_exporter.configure(recursive=True)
    metrics_flush = metrics_exporter.mock_context().mock_method('flush')
    metrics_shutdown = metrics_exporter.mock_context().mock_method('shutdown')

    pipeline.register_log_exporter(log_exporter)
    pipeline.register_trace_exporter(trace_exporter)
    pipeline.register_metrics_exporter(metrics_exporter)

    pipeline.shutdown()

    log_flush.assert_called_once()
    log_shutdown.assert_called_once()
    trace_flush.assert_called_once()
    trace_shutdown.assert_called_once()
    metrics_flush.assert_called_once()
    metrics_shutdown.assert_called_once()
    return


def test_shutdown_with_no_exporters():
    """
        Verify that shutdown completes without error when no exporters
        are registered.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-018"
    )

    pipeline.shutdown()
    # No exception means success
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-019"
    )

    repr_str = repr(pipeline)
    assert "ObservabilityPipeline" in repr_str, \
        "__repr__ should contain the class name"
    return


def test_repr_contains_exporter_counts():
    """
        Verify that __repr__ includes the count of log, trace, and
        metrics exporters.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-020"
    )

    repr_str = repr(pipeline)
    assert "log_exporters=0" in repr_str, \
        "__repr__ should show log_exporters count"
    assert "trace_exporters=0" in repr_str, \
        "__repr__ should show trace_exporters count"
    assert "metrics_exporters=0" in repr_str, \
        "__repr__ should show metrics_exporters count"
    return


def test_str_contains_log_level():
    """
        Verify that __str__ includes the log level from configuration.
    """
    config = ObservabilityConfiguration(log_level="debug")
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-021"
    )

    str_val = str(pipeline)
    assert "log_level=debug" in str_val, \
        "__str__ should contain the log level"
    return


def test_str_contains_enabled_statuses():
    """
        Verify that __str__ includes the tracing, metrics, and recording
        enabled statuses.
    """
    config = ObservabilityConfiguration(
        tracing_enabled=True,
        metrics_enabled=True,
        recording_enabled=False
    )
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-022"
    )

    str_val = str(pipeline)
    assert "tracing_enabled=True" in str_val, \
        "__str__ should contain tracing_enabled status"
    assert "metrics_enabled=True" in str_val, \
        "__str__ should contain metrics_enabled status"
    assert "recording_enabled=False" in str_val, \
        "__str__ should contain recording_enabled status"
    return


def test_all_subsystems_enabled():
    """
        Verify that when all subsystems are enabled, the pipeline
        constructs all components in their active state.
    """
    config = ObservabilityConfiguration(
        tracing_enabled=True,
        metrics_enabled=True,
        recording_enabled=True,
        sampling_rate=0.5
    )
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-023"
    )

    assert pipeline.tracer.sampling_rate == 0.5, \
        "Tracer should use configured sampling rate when tracing enabled"
    assert pipeline.metrics_registry.count == 13, \
        "MetricsRegistry should have 13 built-in metrics"
    assert pipeline.execution_recorder.is_recording is True, \
        "ExecutionRecorder should be recording"
    return


def test_property_logger_returns_same_instance():
    """
        Verify that the logger property returns the same instance
        on repeated access.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-024"
    )

    logger1 = pipeline.logger
    logger2 = pipeline.logger
    assert logger1 is logger2, \
        "logger property should return the same instance"
    return


def test_property_tracer_returns_same_instance():
    """
        Verify that the tracer property returns the same instance
        on repeated access.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-025"
    )

    tracer1 = pipeline.tracer
    tracer2 = pipeline.tracer
    assert tracer1 is tracer2, \
        "tracer property should return the same instance"
    return


def test_property_metrics_collector_returns_same_instance():
    """
        Verify that the metrics_collector property returns the same
        instance on repeated access.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-026"
    )

    collector1 = pipeline.metrics_collector
    collector2 = pipeline.metrics_collector
    assert collector1 is collector2, \
        "metrics_collector property should return the same instance"
    return


def test_property_metrics_registry_returns_same_instance():
    """
        Verify that the metrics_registry property returns the same
        instance on repeated access.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-027"
    )

    registry1 = pipeline.metrics_registry
    registry2 = pipeline.metrics_registry
    assert registry1 is registry2, \
        "metrics_registry property should return the same instance"
    return


def test_property_execution_recorder_returns_same_instance():
    """
        Verify that the execution_recorder property returns the same
        instance on repeated access.
    """
    config = ObservabilityConfiguration()
    pipeline = ObservabilityPipeline(
        configuration=config,
        agent_id="agent-028"
    )

    recorder1 = pipeline.execution_recorder
    recorder2 = pipeline.execution_recorder
    assert recorder1 is recorder2, \
        "execution_recorder property should return the same instance"
    return
