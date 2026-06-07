"""
    Defines the ObservabilityPipeline class that coordinates the
    StructuredLogger, Tracer, MetricsCollector, MetricsRegistry, and
    ExecutionRecorder for an Agent.

    The pipeline constructs all subsystem components during initialization
    based on the provided ObservabilityConfiguration. When tracing is
    disabled, the Tracer operates with a sampling rate of 0.0 so that
    spans are not exported. When metrics are disabled, the MetricsCollector
    exists but measurements are not delivered to exporters. When recording
    is disabled, the ExecutionRecorder exists but is never started, so
    calls to record silently discard events.

    The pipeline provides methods for registering log, trace, and metrics
    exporters, and a shutdown method that flushes and shuts down all
    registered exporters.
"""

from typing import Optional

from ccai.agentkit.builtinagentmetrics import register_builtin_agent_metrics
from ccai.agentkit.correlationcontext import CorrelationContext
from ccai.agentkit.executionrecorder import ExecutionRecorder
from ccai.agentkit.logexporter import LogExporter
from ccai.agentkit.metricscollector import MetricsCollector
from ccai.agentkit.metricsexporter import MetricsExporter
from ccai.agentkit.metricsregistry import MetricsRegistry
from ccai.agentkit.observabilityconfiguration import ObservabilityConfiguration
from ccai.agentkit.observabilityerror import ObservabilityError
from ccai.agentkit.structuredlogger import StructuredLogger
from ccai.agentkit.tracer import Tracer
from ccai.agentkit.traceexporter import TraceExporter


class ObservabilityPipeline:
    """
        A component that coordinates the StructuredLogger, Tracer,
        MetricsCollector, MetricsRegistry, and ExecutionRecorder for
        an Agent, routing observability data to configured exporters.

        The pipeline constructs all subsystem components during
        initialization. The StructuredLogger is always created. When
        tracing is disabled, the Tracer is created with a sampling
        rate of 0.0 so spans are not exported. When metrics are
        disabled, the MetricsCollector exists but does not deliver
        measurements to exporters. When recording is disabled, the
        ExecutionRecorder exists but is never started, so calls to
        record silently discard events.

        When metrics are enabled, the built-in agent metrics are
        automatically registered in the MetricsRegistry.

        :param configuration: The ObservabilityConfiguration defining
            the pipeline behavior.
        :param agent_id: The agent identifier string for the agent
            that owns this pipeline.
        :param correlation_context: Optional CorrelationContext for
            the pipeline. Auto-created if not provided.
    """

    def __init__(self, configuration: ObservabilityConfiguration, agent_id: str,
                 correlation_context: CorrelationContext = None) -> None:

        self._configuration = configuration
        self._agent_id = agent_id

        if correlation_context is not None:
            self._correlation_context = correlation_context
        else:
            self._correlation_context = CorrelationContext()

        self._log_exporters = []
        self._trace_exporters = []
        self._metrics_exporters = []

        # StructuredLogger is always created
        self._logger = StructuredLogger(
            agent_id=agent_id,
            correlation_context=self._correlation_context
        )

        # Tracer: when tracing disabled, use sampling_rate=0.0 (no-op)
        if configuration.tracing_enabled:
            tracer_sampling_rate = configuration.sampling_rate
        else:
            tracer_sampling_rate = 0.0

        self._tracer = Tracer(
            agent_id=agent_id,
            sampling_rate=tracer_sampling_rate
        )

        # MetricsRegistry and MetricsCollector
        self._metrics_registry = MetricsRegistry()
        self._metrics_collector = MetricsCollector(
            registry=self._metrics_registry
        )

        # Register built-in agent metrics when metrics are enabled
        if configuration.metrics_enabled:
            register_builtin_agent_metrics(self._metrics_registry)

        # ExecutionRecorder: when recording disabled, never start it
        self._execution_recorder = ExecutionRecorder(
            agent_id=agent_id
        )

        if configuration.recording_enabled:
            self._execution_recorder.start()

        return

    @property
    def logger(self) -> StructuredLogger:
        """
            The StructuredLogger instance owned by this pipeline.

            :returns: The StructuredLogger instance.
        """
        return self._logger

    @property
    def tracer(self) -> Tracer:
        """
            The Tracer instance owned by this pipeline.

            :returns: The Tracer instance.
        """
        return self._tracer

    @property
    def metrics_collector(self) -> MetricsCollector:
        """
            The MetricsCollector instance owned by this pipeline.

            :returns: The MetricsCollector instance.
        """
        return self._metrics_collector

    @property
    def metrics_registry(self) -> MetricsRegistry:
        """
            The MetricsRegistry instance owned by this pipeline.

            :returns: The MetricsRegistry instance.
        """
        return self._metrics_registry

    @property
    def execution_recorder(self) -> ExecutionRecorder:
        """
            The ExecutionRecorder instance owned by this pipeline.

            :returns: The ExecutionRecorder instance.
        """
        return self._execution_recorder

    def register_log_exporter(self, exporter: LogExporter) -> None:
        """
            Registers a LogExporter instance with the pipeline.

            :param exporter: The LogExporter instance to register.
        """
        self._log_exporters.append(exporter)

        return

    def register_trace_exporter(self, exporter: TraceExporter) -> None:
        """
            Registers a TraceExporter instance with the pipeline and
            adds it to the Tracer's exporter list.

            :param exporter: The TraceExporter instance to register.
        """
        self._trace_exporters.append(exporter)
        self._tracer.register_exporter(exporter)

        return

    def register_metrics_exporter(self, exporter: MetricsExporter) -> None:
        """
            Registers a MetricsExporter instance with the pipeline and
            adds it to the MetricsCollector's exporter list.

            :param exporter: The MetricsExporter instance to register.
        """
        self._metrics_exporters.append(exporter)
        self._metrics_collector.register_exporter(exporter)

        return

    def shutdown(self) -> None:
        """
            Flushes and shuts down all registered exporters.

            Iterates through all log, trace, and metrics exporters,
            calling flush and then shutdown on each. If an exporter
            raises an exception during flush or shutdown, an
            ObservabilityError is raised with the exporter details.
        """
        for exporter in self._log_exporters:
            exporter.flush()
            exporter.shutdown()

        for exporter in self._trace_exporters:
            exporter.flush()
            exporter.shutdown()

        for exporter in self._metrics_exporters:
            exporter.flush()
            exporter.shutdown()

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of log, trace, and metrics
            exporters.

            :returns: A repr string for debugging.
        """
        repr_str = (
            "ObservabilityPipeline("
            "log_exporters={}, "
            "trace_exporters={}, "
            "metrics_exporters={})"
        ).format(
            len(self._log_exporters),
            len(self._trace_exporters),
            len(self._metrics_exporters)
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the log level,
            tracing enabled status, metrics enabled status, and
            recording enabled status.

            :returns: A human-readable string.
        """
        str_val = (
            "ObservabilityPipeline: "
            "log_level={}, "
            "tracing_enabled={}, "
            "metrics_enabled={}, "
            "recording_enabled={}"
        ).format(
            self._configuration.log_level,
            self._configuration.tracing_enabled,
            self._configuration.metrics_enabled,
            self._configuration.recording_enabled
        )
        return str_val
