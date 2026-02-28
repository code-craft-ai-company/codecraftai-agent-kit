# Requirements Document — Observability & Debugging

## Introduction

The Observability & Debugging feature extends the `automojo-agent-kit` SDK with a comprehensive system for monitoring, tracing, measuring, recording, and debugging agent execution. It defines a structured logging system with correlation identifiers for tracing log entries across agent operations, a distributed tracing layer compatible with OpenTelemetry for tracking execution across agent boundaries, a metrics collection system for capturing latency, token usage, error rates, and custom counters, an execution recording and replay system for inspecting agent behavior after the fact, and a debug mode with step-through execution for interactive development and troubleshooting. The system integrates with the Agent base class so agents produce observability data throughout their lifecycle, with the Tool system so tool executions are traced and metered, with the LLM Integration system so LLM requests are traced with token usage metrics, with the Memory & Context Management system so memory operations are observable, with the Communication & Messaging system so message exchanges are traced across agents, with the Workflow & Orchestration system so workflow step executions are traced and metered, with `automojo-extension` so observability backends and exporters can be discovered and loaded as plugins, with `automojo-credentials` for exporter authentication, with `automojo-dataprofiles` for data profile management, and with `automojo-this-app` for settings and environment configuration.

## Glossary

- **CorrelationContext**: A mutable context object that carries a correlation identifier and optional parent correlation identifier across agent operations. The CorrelationContext is propagated through log entries, trace spans, and metric labels to enable end-to-end tracing of a logical operation.
- **StructuredLogEntry**: An immutable object representing a single structured log record, containing a timestamp, log level, message, logger name, correlation identifier, agent identifier, and a metadata dictionary of additional key-value fields.
- **StructuredLogger**: A logger wrapper that enriches standard Python log records with correlation identifiers, agent identity, and structured metadata fields. The StructuredLogger produces StructuredLogEntry objects and delegates to the Python standard logging module.
- **LogFormatter**: An abstract base class for formatting StructuredLogEntry objects into output strings. Concrete implementations produce specific formats (JSON, key-value, human-readable).
- **LogExporter**: An abstract base class for exporting StructuredLogEntry objects to external systems (file, console, remote log aggregator). Concrete implementations handle specific destinations.
- **TraceContext**: An immutable object representing the distributed tracing context for a single operation, containing a trace identifier, a span identifier, an optional parent span identifier, and trace flags. The TraceContext is compatible with the W3C Trace Context specification.
- **TraceSpan**: A mutable object representing a single unit of work within a distributed trace. A TraceSpan has a name, a TraceContext, a start timestamp, an optional end timestamp, a status, attributes dictionary, and a list of TraceEvent objects. TraceSpan follows the OpenTelemetry span model.
- **TraceEvent**: An immutable object representing a timestamped annotation within a TraceSpan, containing a name, a timestamp, and an attributes dictionary.
- **Tracer**: A component that creates and manages TraceSpan objects for an Agent. The Tracer maintains the current active span and supports nested span creation for hierarchical tracing.
- **TraceExporter**: An abstract base class for exporting completed TraceSpan objects to external tracing backends (console, OTLP endpoint, file). Concrete implementations handle specific export protocols.
- **MetricDefinition**: An immutable object describing a metric, containing a name, a description, a unit string, and a metric type (counter, gauge, histogram).
- **MetricType**: An enumeration defining the type of a metric: COUNTER (monotonically increasing value), GAUGE (value that can increase or decrease), and HISTOGRAM (distribution of values).
- **MetricMeasurement**: An immutable object representing a single metric data point, containing the metric name, the value as a float, a timestamp, and a labels dictionary of key-value pairs.
- **MetricsCollector**: A component that records MetricMeasurement objects for defined metrics. The MetricsCollector supports incrementing counters, setting gauges, and recording histogram values.
- **MetricsRegistry**: A registry that tracks all MetricDefinition instances available to an Agent, providing lookup by name and enumeration.
- **MetricsExporter**: An abstract base class for exporting MetricMeasurement objects to external metrics backends (console, Prometheus endpoint, OTLP endpoint, file). Concrete implementations handle specific export protocols.
- **MetricsSnapshot**: An immutable object representing a point-in-time snapshot of all metric values, containing the snapshot timestamp and a dictionary of metric names to their current values and labels.
- **ExecutionRecord**: An immutable object representing a recorded event during agent execution, containing a sequence number, a timestamp, an event type string, the agent identifier, a correlation identifier, and a payload dictionary with event-specific data.
- **ExecutionRecorder**: A component that captures ExecutionRecord objects during agent execution, storing them in an ordered sequence for later replay and inspection.
- **ExecutionRecording**: An immutable object representing a complete recording of agent execution, containing the agent identifier, a start timestamp, an end timestamp, and the ordered list of ExecutionRecord objects.
- **ExecutionReplayer**: A component that reads an ExecutionRecording and allows step-by-step inspection of the recorded events, supporting forward traversal, backward traversal, and filtering by event type.
- **DebugSession**: A component that enables step-through execution of agent operations. The DebugSession pauses execution at configurable breakpoints and allows inspection of agent state, tool inputs/outputs, LLM requests/responses, and workflow context before continuing.
- **Breakpoint**: An immutable object representing a condition at which the DebugSession pauses execution, containing a breakpoint type (lifecycle, tool, llm, workflow_step, message, memory, custom), an optional target name, and an optional condition expression.
- **DebugInspector**: A component that provides read-only access to the current agent state during a DebugSession pause, including lifecycle state, tool registry contents, LLM provider registry contents, memory store contents, workflow context, and the current correlation context.
- **ObservabilityConfiguration**: A configuration object that defines the logging format, log level, tracing enablement, metrics enablement, recording enablement, debug mode enablement, exporter settings, and sampling rates for an Agent's observability system.
- **ObservabilityPipeline**: A component that coordinates the StructuredLogger, Tracer, MetricsCollector, and ExecutionRecorder for an Agent, routing observability data to configured exporters.
- **ObservabilityExporterPlugin**: An exporter implementation (LogExporter, TraceExporter, or MetricsExporter) discovered and loaded through the `automojo-extension` ExtensionPoint mechanism, allowing external packages to contribute observability backends.
- **Agent**: The base agent class defined in the Core Agent Framework that owns an ObservabilityPipeline and produces observability data throughout its lifecycle.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register exporter implementations with an Agent.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to secrets required by exporters (API keys, authentication tokens for remote backends).
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **ObservabilityError**: An exception raised when an observability operation fails due to an exporter error, recording error, or pipeline configuration error.

## Requirements

### Requirement 1: Correlation Context

**User Story:** As a developer, I want a correlation context that propagates a unique identifier across all agent operations, so that I can trace log entries, spans, and metrics belonging to the same logical operation.

#### Acceptance Criteria

1. THE CorrelationContext SHALL contain a correlation identifier as a string and an optional parent correlation identifier as a string.
2. WHEN a CorrelationContext is created without an explicit correlation identifier, THE CorrelationContext SHALL generate a UUID-based identifier automatically.
3. THE CorrelationContext SHALL expose all fields as read-only properties.
4. THE CorrelationContext SHALL provide a create_child method that returns a new CorrelationContext with a new correlation identifier and the current correlation identifier set as the parent.
5. THE CorrelationContext SHALL provide an as_dict method that returns a dictionary representation of the context fields.
6. THE CorrelationContext SHALL provide a to_json method that returns a JSON string representation of the context fields.
7. THE CorrelationContext SHALL provide a class method from_dict that constructs a CorrelationContext from a dictionary.
8. THE CorrelationContext SHALL provide a class method from_json that deserializes a JSON string into a CorrelationContext instance.
9. FOR ALL valid CorrelationContext instances, calling to_json and then from_json SHALL produce an equivalent CorrelationContext object (round-trip property).
10. THE CorrelationContext SHALL provide a __repr__ method that includes the class name, correlation identifier, and parent correlation identifier.
11. THE CorrelationContext SHALL provide a __str__ method that returns a human-readable summary including the correlation identifier and parent correlation identifier.

### Requirement 2: Structured Log Entry

**User Story:** As a developer, I want structured log entries with correlation identifiers and agent metadata, so that I can search, filter, and correlate log output across agent operations.

#### Acceptance Criteria

1. THE StructuredLogEntry SHALL contain a timestamp, a log level string, a message string, a logger name string, a correlation identifier string, an agent identifier string, and a metadata dictionary of additional key-value fields.
2. THE StructuredLogEntry SHALL expose all fields as read-only properties.
3. THE StructuredLogEntry SHALL provide an as_dict method that returns a dictionary representation of the log entry fields.
4. THE StructuredLogEntry SHALL provide a to_json method that returns a JSON string representation of the log entry fields.
5. THE StructuredLogEntry SHALL provide a class method from_dict that constructs a StructuredLogEntry from a dictionary.
6. THE StructuredLogEntry SHALL provide a class method from_json that deserializes a JSON string into a StructuredLogEntry instance.
7. FOR ALL valid StructuredLogEntry instances, calling to_json and then from_json SHALL produce an equivalent StructuredLogEntry object (round-trip property).
8. THE StructuredLogEntry SHALL provide a __repr__ method that includes the class name, log level, logger name, and correlation identifier.
9. THE StructuredLogEntry SHALL provide a __str__ method that returns a human-readable summary including the timestamp, log level, logger name, message, and correlation identifier.

### Requirement 3: Structured Logger

**User Story:** As a developer, I want a logger that automatically enriches log records with correlation identifiers and agent identity, so that I can produce structured log output without manually adding context to every log call.

#### Acceptance Criteria

1. THE StructuredLogger SHALL wrap the Python standard logging module and delegate log output to a standard Python logger.
2. THE StructuredLogger SHALL accept an agent identifier string and a CorrelationContext at construction time.
3. THE StructuredLogger SHALL provide log methods for each standard log level: debug, info, warning, error, and critical.
4. WHEN a log method is called, THE StructuredLogger SHALL create a StructuredLogEntry containing the current timestamp, the log level, the message, the logger name, the correlation identifier from the CorrelationContext, the agent identifier, and any additional metadata key-value pairs passed as keyword arguments.
5. THE StructuredLogger SHALL provide a set_correlation_context method that accepts a CorrelationContext and updates the active correlation context for subsequent log entries.
6. THE StructuredLogger SHALL provide a read-only property for the current CorrelationContext.
7. THE StructuredLogger SHALL use the logger hierarchy rooted at `automojo.agentkit.observability` for delegating log output.
8. THE StructuredLogger SHALL provide a __repr__ method that includes the class name, agent identifier, and logger name.
9. THE StructuredLogger SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and logger name.

### Requirement 4: Log Formatter

**User Story:** As a developer, I want pluggable log formatters that produce output in different formats, so that I can choose the log format that best fits my monitoring infrastructure.

#### Acceptance Criteria

1. THE LogFormatter base class SHALL define an abstract interface with a format method that accepts a StructuredLogEntry and returns a formatted string.
2. THE LogFormatter base class SHALL require all subclasses to provide an implementation for the format method.
3. THE framework SHALL provide a JsonLogFormatter that formats a StructuredLogEntry as a single-line JSON string.
4. THE framework SHALL provide a KeyValueLogFormatter that formats a StructuredLogEntry as a key=value pair string with space-separated fields.
5. THE framework SHALL provide a HumanReadableLogFormatter that formats a StructuredLogEntry as a human-readable string with timestamp, level, logger name, message, and correlation identifier.
6. THE LogFormatter base class SHALL expose a read-only property for the format name as a string.
7. THE LogFormatter base class SHALL provide a __repr__ method that includes the class name and format name.
8. THE LogFormatter base class SHALL provide a __str__ method that returns a human-readable summary including the format name.

### Requirement 5: Log Exporter

**User Story:** As a developer, I want pluggable log exporters that send structured log entries to different destinations, so that I can route log output to files, consoles, or remote aggregators.

#### Acceptance Criteria

1. THE LogExporter base class SHALL define an abstract interface with an export method that accepts a StructuredLogEntry and delivers the entry to the configured destination.
2. THE LogExporter base class SHALL define an abstract method flush that ensures all buffered entries are delivered.
3. THE LogExporter base class SHALL define an abstract method shutdown that releases resources held by the exporter.
4. THE LogExporter base class SHALL require all subclasses to provide an implementation for the export, flush, and shutdown methods.
5. THE LogExporter base class SHALL accept a LogFormatter at construction time for formatting entries before export.
6. THE LogExporter base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the exporter requires.
7. THE framework SHALL provide a ConsoleLogExporter that writes formatted log entries to standard output.
8. THE framework SHALL provide a FileLogExporter that writes formatted log entries to a specified file path.
9. WHEN the FileLogExporter is constructed with a file path, THE FileLogExporter SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
10. IF a LogExporter export operation fails, THEN THE LogExporter SHALL raise an ObservabilityError that includes the exporter class name and the underlying error detail.
11. THE LogExporter base class SHALL provide a __repr__ method that includes the class name and the LogFormatter format name.
12. THE LogExporter base class SHALL provide a __str__ method that returns a human-readable summary including the exporter class name and format name.

### Requirement 6: Trace Context

**User Story:** As a developer, I want a trace context compatible with the W3C Trace Context specification, so that I can propagate tracing information across agent boundaries and integrate with OpenTelemetry-compatible systems.

#### Acceptance Criteria

1. THE TraceContext SHALL contain a trace identifier as a 32-character lowercase hexadecimal string, a span identifier as a 16-character lowercase hexadecimal string, an optional parent span identifier as a 16-character lowercase hexadecimal string, and trace flags as an integer.
2. WHEN a TraceContext is created without an explicit trace identifier, THE TraceContext SHALL generate a random 32-character lowercase hexadecimal string automatically.
3. WHEN a TraceContext is created without an explicit span identifier, THE TraceContext SHALL generate a random 16-character lowercase hexadecimal string automatically.
4. THE TraceContext SHALL expose all fields as read-only properties.
5. THE TraceContext SHALL provide a create_child_span_context method that returns a new TraceContext with the same trace identifier, a new span identifier, and the current span identifier set as the parent span identifier.
6. THE TraceContext SHALL provide a to_traceparent method that returns a W3C traceparent header string in the format "00-{trace_id}-{span_id}-{trace_flags:02x}".
7. THE TraceContext SHALL provide a class method from_traceparent that parses a W3C traceparent header string and returns a TraceContext instance.
8. IF the traceparent string is malformed, THEN THE from_traceparent method SHALL raise a SemanticError identifying the invalid traceparent string and the parsing error detail.
9. THE TraceContext SHALL provide an as_dict method that returns a dictionary representation of the context fields.
10. THE TraceContext SHALL provide a to_json method that returns a JSON string representation of the context fields.
11. THE TraceContext SHALL provide a class method from_dict that constructs a TraceContext from a dictionary.
12. THE TraceContext SHALL provide a class method from_json that deserializes a JSON string into a TraceContext instance.
13. FOR ALL valid TraceContext instances, calling to_json and then from_json SHALL produce an equivalent TraceContext object (round-trip property).
14. FOR ALL valid TraceContext instances, calling to_traceparent and then from_traceparent SHALL produce a TraceContext with equivalent trace identifier, span identifier, and trace flags (round-trip property).
15. THE TraceContext SHALL provide a __repr__ method that includes the class name, trace identifier, and span identifier.
16. THE TraceContext SHALL provide a __str__ method that returns a human-readable summary including the trace identifier, span identifier, and parent span identifier.


### Requirement 7: Trace Span

**User Story:** As a developer, I want trace spans that represent units of work within a distributed trace, so that I can visualize and analyze the execution flow and timing of agent operations.

#### Acceptance Criteria

1. THE TraceSpan SHALL contain a name string, a TraceContext, a start timestamp, an optional end timestamp, a status string (one of "unset", "ok", "error"), an attributes dictionary of key-value pairs, and a list of TraceEvent objects.
2. THE TraceSpan SHALL expose all fields as read-only properties except status and attributes which support mutation during the span's lifetime.
3. THE TraceSpan SHALL provide a set_status method that accepts a status string and an optional description string and updates the span status.
4. WHEN a set_status call provides a status value not in the set of valid status values, THEN THE TraceSpan SHALL raise a SemanticError identifying the invalid status value and listing the valid values.
5. THE TraceSpan SHALL provide a set_attribute method that accepts a key string and a value and adds the key-value pair to the span attributes dictionary.
6. THE TraceSpan SHALL provide an add_event method that accepts a name string and an optional attributes dictionary and appends a TraceEvent with the current timestamp to the span's event list.
7. THE TraceSpan SHALL provide an end method that sets the end timestamp to the current UTC time and marks the span as completed.
8. IF the end method is called on a span that has already been ended, THEN THE TraceSpan SHALL raise a SemanticError indicating that the span has already been completed.
9. THE TraceSpan SHALL provide a duration read-only property that returns the elapsed time in seconds as a float between the start and end timestamps, or None when the span has not been ended.
10. THE TraceSpan SHALL provide an as_dict method that returns a dictionary representation of the span fields including events.
11. THE TraceSpan SHALL provide a to_json method that returns a JSON string representation of the span fields.
12. THE TraceSpan SHALL provide a class method from_dict that constructs a TraceSpan from a dictionary.
13. THE TraceSpan SHALL provide a class method from_json that deserializes a JSON string into a TraceSpan instance.
14. FOR ALL valid completed TraceSpan instances, calling to_json and then from_json SHALL produce an equivalent TraceSpan object (round-trip property).
15. THE TraceSpan SHALL provide a __repr__ method that includes the class name, name, trace identifier, span identifier, and status.
16. THE TraceSpan SHALL provide a __str__ method that returns a human-readable summary including the name, status, and duration.

### Requirement 8: Trace Event

**User Story:** As a developer, I want timestamped annotations within trace spans, so that I can record significant moments during a span's lifetime for debugging and analysis.

#### Acceptance Criteria

1. THE TraceEvent SHALL contain a name string, a timestamp, and an attributes dictionary of key-value pairs.
2. WHEN a TraceEvent is created without an explicit timestamp, THE TraceEvent SHALL set the timestamp to the current UTC time.
3. THE TraceEvent SHALL expose all fields as read-only properties.
4. THE TraceEvent SHALL provide an as_dict method that returns a dictionary representation of the event fields.
5. THE TraceEvent SHALL provide a to_json method that returns a JSON string representation of the event fields.
6. THE TraceEvent SHALL provide a class method from_dict that constructs a TraceEvent from a dictionary.
7. THE TraceEvent SHALL provide a class method from_json that deserializes a JSON string into a TraceEvent instance.
8. FOR ALL valid TraceEvent instances, calling to_json and then from_json SHALL produce an equivalent TraceEvent object (round-trip property).
9. THE TraceEvent SHALL provide a __repr__ method that includes the class name, name, and timestamp.
10. THE TraceEvent SHALL provide a __str__ method that returns a human-readable summary including the name and timestamp.

### Requirement 9: Tracer

**User Story:** As a developer, I want a tracer that creates and manages trace spans for an agent, so that I can instrument agent operations with distributed tracing without manually managing span lifecycle.

#### Acceptance Criteria

1. THE Tracer SHALL accept an agent identifier string and an optional TraceContext at construction time for establishing the root trace context.
2. THE Tracer SHALL provide a start_span method that accepts a span name string and an optional attributes dictionary and returns a new TraceSpan as a child of the current active span.
3. WHEN start_span is called and no active span exists, THE Tracer SHALL create a root TraceSpan with a new TraceContext.
4. WHEN start_span is called and an active span exists, THE Tracer SHALL create a child TraceSpan using the active span's TraceContext create_child_span_context method.
5. THE Tracer SHALL provide an end_span method that ends the current active span and restores the previous span as the active span.
6. THE Tracer SHALL provide a read-only property for the current active TraceSpan, returning None when no span is active.
7. THE Tracer SHALL provide a context manager interface (span method) that accepts a span name and attributes, starts a span on entry, and ends the span on exit, setting error status if an exception occurs.
8. WHEN a span is ended, THE Tracer SHALL deliver the completed TraceSpan to all registered TraceExporter instances.
9. THE Tracer SHALL provide a __repr__ method that includes the class name, agent identifier, and whether an active span exists.
10. THE Tracer SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and active span name.

### Requirement 10: Trace Exporter

**User Story:** As a developer, I want pluggable trace exporters that send completed spans to different tracing backends, so that I can route trace data to consoles, files, or OpenTelemetry-compatible collectors.

#### Acceptance Criteria

1. THE TraceExporter base class SHALL define an abstract interface with an export method that accepts a list of completed TraceSpan objects and delivers the spans to the configured destination.
2. THE TraceExporter base class SHALL define an abstract method flush that ensures all buffered spans are delivered.
3. THE TraceExporter base class SHALL define an abstract method shutdown that releases resources held by the exporter.
4. THE TraceExporter base class SHALL require all subclasses to provide an implementation for the export, flush, and shutdown methods.
5. THE TraceExporter base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the exporter requires.
6. THE framework SHALL provide a ConsoleTraceExporter that writes completed TraceSpan objects as formatted text to standard output.
7. THE framework SHALL provide a FileTraceExporter that writes completed TraceSpan objects as JSON lines to a specified file path.
8. WHEN the FileTraceExporter is constructed with a file path, THE FileTraceExporter SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
9. IF a TraceExporter export operation fails, THEN THE TraceExporter SHALL raise an ObservabilityError that includes the exporter class name and the underlying error detail.
10. THE TraceExporter base class SHALL provide a __repr__ method that includes the class name.
11. THE TraceExporter base class SHALL provide a __str__ method that returns a human-readable summary including the exporter class name.

### Requirement 11: Metric Definition and Metric Type

**User Story:** As a developer, I want to define metrics with a name, description, unit, and type, so that the metrics system can validate and organize metric data consistently.

#### Acceptance Criteria

1. THE MetricDefinition SHALL contain a name string, a description string, a unit string, and a MetricType value.
2. THE MetricDefinition SHALL expose all fields as read-only properties.
3. THE MetricDefinition SHALL provide an as_dict method that returns a dictionary representation of the definition fields.
4. THE MetricDefinition SHALL provide a to_json method that returns a JSON string representation of the definition fields.
5. THE MetricDefinition SHALL provide a class method from_dict that constructs a MetricDefinition from a dictionary.
6. THE MetricDefinition SHALL provide a class method from_json that deserializes a JSON string into a MetricDefinition instance.
7. FOR ALL valid MetricDefinition instances, calling to_json and then from_json SHALL produce an equivalent MetricDefinition object (round-trip property).
8. THE MetricType enumeration SHALL define the values COUNTER, GAUGE, and HISTOGRAM.
9. THE MetricType enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding MetricType member.
10. IF an invalid string value is provided to the MetricType from_string method, THEN THE MetricType SHALL raise a SemanticError identifying the invalid value and listing the valid metric type values.
11. THE MetricDefinition SHALL provide a __repr__ method that includes the class name, metric name, and metric type.
12. THE MetricDefinition SHALL provide a __str__ method that returns a human-readable summary including the metric name, type, and unit.

### Requirement 12: Metric Measurement

**User Story:** As a developer, I want structured metric data points with labels, so that I can record and query metric values with dimensional context.

#### Acceptance Criteria

1. THE MetricMeasurement SHALL contain the metric name as a string, the value as a float, a timestamp, and a labels dictionary of string key-value pairs.
2. WHEN a MetricMeasurement is created without an explicit timestamp, THE MetricMeasurement SHALL set the timestamp to the current UTC time.
3. THE MetricMeasurement SHALL expose all fields as read-only properties.
4. THE MetricMeasurement SHALL provide an as_dict method that returns a dictionary representation of the measurement fields.
5. THE MetricMeasurement SHALL provide a to_json method that returns a JSON string representation of the measurement fields.
6. THE MetricMeasurement SHALL provide a class method from_dict that constructs a MetricMeasurement from a dictionary.
7. THE MetricMeasurement SHALL provide a class method from_json that deserializes a JSON string into a MetricMeasurement instance.
8. FOR ALL valid MetricMeasurement instances, calling to_json and then from_json SHALL produce an equivalent MetricMeasurement object (round-trip property).
9. THE MetricMeasurement SHALL provide a __repr__ method that includes the class name, metric name, and value.
10. THE MetricMeasurement SHALL provide a __str__ method that returns a human-readable summary including the metric name, value, unit, and labels.

### Requirement 13: Metrics Collector

**User Story:** As a developer, I want a metrics collector that records counter increments, gauge values, and histogram observations, so that I can capture quantitative data about agent operations.

#### Acceptance Criteria

1. THE MetricsCollector SHALL accept a MetricsRegistry at construction time for validating metric names against registered definitions.
2. THE MetricsCollector SHALL provide an increment_counter method that accepts a metric name, an optional increment value as a float with a default of 1.0, and an optional labels dictionary, and records a counter increment.
3. WHEN increment_counter is called with a metric name not registered in the MetricsRegistry, THEN THE MetricsCollector SHALL raise a SemanticError identifying the unregistered metric name.
4. WHEN increment_counter is called with a metric name whose MetricType is not COUNTER, THEN THE MetricsCollector SHALL raise a SemanticError identifying the metric name and the expected type.
5. THE MetricsCollector SHALL provide a set_gauge method that accepts a metric name, a value as a float, and an optional labels dictionary, and records a gauge value.
6. WHEN set_gauge is called with a metric name whose MetricType is not GAUGE, THEN THE MetricsCollector SHALL raise a SemanticError identifying the metric name and the expected type.
7. THE MetricsCollector SHALL provide a record_histogram method that accepts a metric name, a value as a float, and an optional labels dictionary, and records a histogram observation.
8. WHEN record_histogram is called with a metric name whose MetricType is not HISTOGRAM, THEN THE MetricsCollector SHALL raise a SemanticError identifying the metric name and the expected type.
9. THE MetricsCollector SHALL deliver each MetricMeasurement to all registered MetricsExporter instances.
10. THE MetricsCollector SHALL provide a snapshot method that returns a MetricsSnapshot containing the current values of all recorded metrics.
11. THE MetricsCollector SHALL provide a reset method that clears all accumulated metric values.
12. THE MetricsCollector SHALL provide a __repr__ method that includes the class name and the count of registered metrics.
13. THE MetricsCollector SHALL provide a __str__ method that returns a human-readable summary including the count of registered metrics and the count of recorded measurements.

### Requirement 14: Metrics Registry

**User Story:** As a developer, I want a registry that tracks metric definitions, so that I can discover and validate metrics by name.

#### Acceptance Criteria

1. THE MetricsRegistry SHALL support registration of a MetricDefinition instance using the metric name as the registration key.
2. IF a MetricDefinition with a duplicate name is registered, THEN THE MetricsRegistry SHALL raise a SemanticError that includes the duplicate metric name.
3. THE MetricsRegistry SHALL support deregistration of a MetricDefinition by name.
4. THE MetricsRegistry SHALL support lookup of a registered MetricDefinition by name, returning the MetricDefinition instance or None when the name is not found.
5. THE MetricsRegistry SHALL support enumeration of all registered MetricDefinition instances as a list.
6. THE MetricsRegistry SHALL expose a read-only property for the count of currently registered metrics.
7. THE MetricsRegistry SHALL provide a has_metric method that accepts a metric name and returns a boolean indicating whether a MetricDefinition with the given name is registered.
8. THE MetricsRegistry SHALL provide a __repr__ method that includes the class name and the count of registered metrics.
9. THE MetricsRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered metric names and types.

### Requirement 15: Metrics Snapshot

**User Story:** As a developer, I want a point-in-time snapshot of all metric values, so that I can inspect the current state of metrics for monitoring and debugging.

#### Acceptance Criteria

1. THE MetricsSnapshot SHALL contain a snapshot timestamp and a dictionary of metric names to their current aggregated values and labels.
2. THE MetricsSnapshot SHALL expose all fields as read-only properties.
3. THE MetricsSnapshot SHALL provide a get_metric method that accepts a metric name and returns the current value and labels for the metric, or None when the metric has no recorded values.
4. THE MetricsSnapshot SHALL provide an as_dict method that returns a dictionary representation of the snapshot fields.
5. THE MetricsSnapshot SHALL provide a to_json method that returns a JSON string representation of the snapshot fields.
6. THE MetricsSnapshot SHALL provide a class method from_dict that constructs a MetricsSnapshot from a dictionary.
7. THE MetricsSnapshot SHALL provide a class method from_json that deserializes a JSON string into a MetricsSnapshot instance.
8. FOR ALL valid MetricsSnapshot instances, calling to_json and then from_json SHALL produce an equivalent MetricsSnapshot object (round-trip property).
9. THE MetricsSnapshot SHALL provide a __repr__ method that includes the class name, snapshot timestamp, and the count of metrics.
10. THE MetricsSnapshot SHALL provide a __str__ method that returns a human-readable summary including the snapshot timestamp and the list of metric names.

### Requirement 16: Metrics Exporter

**User Story:** As a developer, I want pluggable metrics exporters that send metric data to different backends, so that I can route metrics to consoles, files, or monitoring systems.

#### Acceptance Criteria

1. THE MetricsExporter base class SHALL define an abstract interface with an export method that accepts a list of MetricMeasurement objects and delivers the measurements to the configured destination.
2. THE MetricsExporter base class SHALL define an abstract method flush that ensures all buffered measurements are delivered.
3. THE MetricsExporter base class SHALL define an abstract method shutdown that releases resources held by the exporter.
4. THE MetricsExporter base class SHALL require all subclasses to provide an implementation for the export, flush, and shutdown methods.
5. THE MetricsExporter base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the exporter requires.
6. THE framework SHALL provide a ConsoleMetricsExporter that writes MetricMeasurement objects as formatted text to standard output.
7. THE framework SHALL provide a FileMetricsExporter that writes MetricMeasurement objects as JSON lines to a specified file path.
8. WHEN the FileMetricsExporter is constructed with a file path, THE FileMetricsExporter SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
9. IF a MetricsExporter export operation fails, THEN THE MetricsExporter SHALL raise an ObservabilityError that includes the exporter class name and the underlying error detail.
10. THE MetricsExporter base class SHALL provide a __repr__ method that includes the class name.
11. THE MetricsExporter base class SHALL provide a __str__ method that returns a human-readable summary including the exporter class name.

### Requirement 17: Built-in Agent Metrics

**User Story:** As a developer, I want the framework to automatically register and collect standard agent metrics for latency, token usage, and error rates, so that I get useful operational metrics without manual instrumentation.

#### Acceptance Criteria

1. WHEN an Agent is initialized with observability enabled, THE framework SHALL register the following MetricDefinition instances in the Agent's MetricsRegistry:
   - "agent.lifecycle.transitions" as a COUNTER with unit "count" and description "Count of agent lifecycle state transitions"
   - "agent.tool.execution.duration" as a HISTOGRAM with unit "seconds" and description "Duration of tool executions"
   - "agent.tool.execution.errors" as a COUNTER with unit "count" and description "Count of tool execution errors"
   - "agent.llm.request.duration" as a HISTOGRAM with unit "seconds" and description "Duration of LLM completion requests"
   - "agent.llm.token.usage.prompt" as a COUNTER with unit "tokens" and description "Count of prompt tokens consumed"
   - "agent.llm.token.usage.completion" as a COUNTER with unit "tokens" and description "Count of completion tokens consumed"
   - "agent.llm.request.errors" as a COUNTER with unit "count" and description "Count of LLM request errors"
   - "agent.memory.operations" as a COUNTER with unit "count" and description "Count of memory store operations"
   - "agent.message.sent" as a COUNTER with unit "count" and description "Count of messages sent"
   - "agent.message.received" as a COUNTER with unit "count" and description "Count of messages received"
   - "agent.workflow.step.duration" as a HISTOGRAM with unit "seconds" and description "Duration of workflow step executions"
   - "agent.workflow.step.errors" as a COUNTER with unit "count" and description "Count of workflow step execution errors"
   - "agent.active.spans" as a GAUGE with unit "count" and description "Count of currently active trace spans"
2. WHEN a lifecycle state transition occurs, THE framework SHALL increment the "agent.lifecycle.transitions" counter with labels including the agent identifier, the previous state, and the new state.
3. WHEN a tool execution completes, THE framework SHALL record the execution duration in the "agent.tool.execution.duration" histogram with labels including the agent identifier and tool name.
4. WHEN a tool execution fails, THE framework SHALL increment the "agent.tool.execution.errors" counter with labels including the agent identifier and tool name.
5. WHEN an LLM completion request completes, THE framework SHALL record the request duration in the "agent.llm.request.duration" histogram and increment the token usage counters with labels including the agent identifier, provider name, and model name.
6. WHEN an LLM completion request fails, THE framework SHALL increment the "agent.llm.request.errors" counter with labels including the agent identifier, provider name, and model name.

### Requirement 18: Execution Record

**User Story:** As a developer, I want structured execution records that capture agent events with sequence numbers and payloads, so that I can replay and inspect agent behavior after execution.

#### Acceptance Criteria

1. THE ExecutionRecord SHALL contain a sequence number as an integer, a timestamp, an event type string, an agent identifier string, a correlation identifier string, and a payload dictionary with event-specific data.
2. THE ExecutionRecord SHALL expose all fields as read-only properties.
3. THE ExecutionRecord SHALL provide an as_dict method that returns a dictionary representation of the record fields.
4. THE ExecutionRecord SHALL provide a to_json method that returns a JSON string representation of the record fields.
5. THE ExecutionRecord SHALL provide a class method from_dict that constructs an ExecutionRecord from a dictionary.
6. THE ExecutionRecord SHALL provide a class method from_json that deserializes a JSON string into an ExecutionRecord instance.
7. FOR ALL valid ExecutionRecord instances, calling to_json and then from_json SHALL produce an equivalent ExecutionRecord object (round-trip property).
8. THE ExecutionRecord SHALL provide a __repr__ method that includes the class name, sequence number, event type, and agent identifier.
9. THE ExecutionRecord SHALL provide a __str__ method that returns a human-readable summary including the sequence number, timestamp, event type, and agent identifier.

### Requirement 19: Execution Recorder

**User Story:** As a developer, I want a recorder that captures execution events during agent operation, so that I can build a complete recording for later replay and analysis.

#### Acceptance Criteria

1. THE ExecutionRecorder SHALL accept an agent identifier string at construction time.
2. THE ExecutionRecorder SHALL provide a record method that accepts an event type string, a correlation identifier string, and a payload dictionary, assigns the next sequence number, and stores an ExecutionRecord.
3. THE ExecutionRecorder SHALL assign monotonically increasing sequence numbers starting from 1 to each recorded ExecutionRecord.
4. THE ExecutionRecorder SHALL provide a read-only property for the count of recorded events.
5. THE ExecutionRecorder SHALL provide a get_recording method that returns an ExecutionRecording containing all recorded ExecutionRecord objects.
6. THE ExecutionRecorder SHALL provide a clear method that removes all recorded events and resets the sequence counter.
7. THE ExecutionRecorder SHALL provide a is_recording read-only property that returns True when the recorder is actively capturing events.
8. THE ExecutionRecorder SHALL provide a start method that enables event capture.
9. THE ExecutionRecorder SHALL provide a stop method that disables event capture.
10. WHEN the recorder is not actively capturing events, THE record method SHALL silently discard the event without storing an ExecutionRecord.
11. THE ExecutionRecorder SHALL provide a __repr__ method that includes the class name, agent identifier, and event count.
12. THE ExecutionRecorder SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, event count, and recording status.

### Requirement 20: Execution Recording

**User Story:** As a developer, I want a complete execution recording object that I can serialize, store, and load, so that I can share and analyze agent execution traces offline.

#### Acceptance Criteria

1. THE ExecutionRecording SHALL contain the agent identifier as a string, a start timestamp, an end timestamp, and the ordered list of ExecutionRecord objects.
2. THE ExecutionRecording SHALL expose all fields as read-only properties.
3. THE ExecutionRecording SHALL provide a duration read-only property that returns the elapsed time in seconds as a float between the start and end timestamps.
4. THE ExecutionRecording SHALL provide a filter_by_event_type method that accepts an event type string and returns a new ExecutionRecording containing only the ExecutionRecord objects matching the event type.
5. THE ExecutionRecording SHALL provide an as_dict method that returns a dictionary representation of the recording fields including all records.
6. THE ExecutionRecording SHALL provide a to_json method that returns a JSON string representation of the recording fields.
7. THE ExecutionRecording SHALL provide a class method from_dict that constructs an ExecutionRecording from a dictionary.
8. THE ExecutionRecording SHALL provide a class method from_json that deserializes a JSON string into an ExecutionRecording instance.
9. FOR ALL valid ExecutionRecording instances, calling to_json and then from_json SHALL produce an equivalent ExecutionRecording object (round-trip property).
10. THE ExecutionRecording SHALL provide a __repr__ method that includes the class name, agent identifier, and event count.
11. THE ExecutionRecording SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, event count, and duration.

### Requirement 21: Execution Replayer

**User Story:** As a developer, I want to step through a recorded execution forward and backward, so that I can inspect agent behavior at each recorded event for debugging.

#### Acceptance Criteria

1. THE ExecutionReplayer SHALL accept an ExecutionRecording at construction time.
2. THE ExecutionReplayer SHALL provide a current read-only property that returns the ExecutionRecord at the current position, or None when the replayer is at the beginning or end boundary.
3. THE ExecutionReplayer SHALL provide a next method that advances the position to the next ExecutionRecord and returns the record, or None when the end of the recording is reached.
4. THE ExecutionReplayer SHALL provide a previous method that moves the position to the previous ExecutionRecord and returns the record, or None when the beginning of the recording is reached.
5. THE ExecutionReplayer SHALL provide a reset method that moves the position back to the beginning of the recording.
6. THE ExecutionReplayer SHALL provide a seek method that accepts a sequence number and moves the position to the ExecutionRecord with the matching sequence number.
7. IF the seek method receives a sequence number that does not exist in the recording, THEN THE ExecutionReplayer SHALL raise a SemanticError identifying the invalid sequence number.
8. THE ExecutionReplayer SHALL provide a filter method that accepts an event type string and returns a new ExecutionReplayer containing only the ExecutionRecord objects matching the event type.
9. THE ExecutionReplayer SHALL provide a read-only property for the total count of records in the recording.
10. THE ExecutionReplayer SHALL provide a read-only property for the current position index as an integer.
11. THE ExecutionReplayer SHALL provide a __repr__ method that includes the class name, agent identifier, current position, and total record count.
12. THE ExecutionReplayer SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, current position, total record count, and current event type.

### Requirement 22: Debug Session

**User Story:** As a developer, I want a debug mode that pauses agent execution at configurable breakpoints, so that I can interactively inspect agent state and step through operations during development.

#### Acceptance Criteria

1. THE DebugSession SHALL accept an Agent instance at construction time.
2. THE DebugSession SHALL provide an add_breakpoint method that accepts a Breakpoint and registers the breakpoint with the session.
3. THE DebugSession SHALL provide a remove_breakpoint method that accepts a Breakpoint and deregisters the breakpoint from the session.
4. THE DebugSession SHALL provide a list_breakpoints method that returns the list of registered Breakpoint objects.
5. THE DebugSession SHALL provide a clear_breakpoints method that removes all registered breakpoints.
6. WHEN agent execution reaches a point matching a registered Breakpoint, THE DebugSession SHALL pause execution and invoke a registered pause callback with a DebugInspector instance.
7. THE DebugSession SHALL provide a continue_execution method that resumes execution after a pause.
8. THE DebugSession SHALL provide a step method that resumes execution until the next breakpoint-eligible point is reached, regardless of whether a breakpoint is registered at that point.
9. THE DebugSession SHALL provide a read-only property for the current pause state as a boolean indicating whether execution is currently paused.
10. THE DebugSession SHALL provide a read-only property for the DebugInspector, returning None when execution is not paused.
11. THE DebugSession SHALL provide an is_active read-only property that returns True when the debug session is enabled.
12. THE DebugSession SHALL provide a start method that enables the debug session.
13. THE DebugSession SHALL provide a stop method that disables the debug session and resumes any paused execution.
14. THE DebugSession SHALL provide a __repr__ method that includes the class name, agent identifier, breakpoint count, and pause state.
15. THE DebugSession SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, breakpoint count, and whether execution is paused.

### Requirement 23: Breakpoint

**User Story:** As a developer, I want to define breakpoints by type and optional target name, so that I can pause execution at specific agent operations during debugging.

#### Acceptance Criteria

1. THE Breakpoint SHALL contain a breakpoint type string (one of "lifecycle", "tool", "llm", "workflow_step", "message", "memory", "custom"), an optional target name string, and an optional condition expression string.
2. THE Breakpoint SHALL expose all fields as read-only properties.
3. WHEN a Breakpoint is created with a breakpoint type not in the set of valid types, THEN THE Breakpoint SHALL raise a SemanticError identifying the invalid type and listing the valid breakpoint types.
4. THE Breakpoint SHALL provide a matches method that accepts an event type string and an optional target name string and returns a boolean indicating whether the breakpoint matches the event.
5. WHEN a Breakpoint has a target name, THE matches method SHALL return True only when both the breakpoint type matches the event type and the target name matches the provided target name.
6. WHEN a Breakpoint has no target name, THE matches method SHALL return True when the breakpoint type matches the event type.
7. THE Breakpoint SHALL provide an as_dict method that returns a dictionary representation of the breakpoint fields.
8. THE Breakpoint SHALL provide a __repr__ method that includes the class name, breakpoint type, and target name.
9. THE Breakpoint SHALL provide a __str__ method that returns a human-readable summary including the breakpoint type, target name, and condition expression.

### Requirement 24: Debug Inspector

**User Story:** As a developer, I want read-only access to agent state during a debug pause, so that I can inspect lifecycle state, registries, memory, and context without modifying agent behavior.

#### Acceptance Criteria

1. THE DebugInspector SHALL accept an Agent instance at construction time and provide read-only access to the agent's internal state.
2. THE DebugInspector SHALL provide a read-only property for the agent's current LifecycleState.
3. THE DebugInspector SHALL provide a read-only property for the agent's AgentIdentity.
4. THE DebugInspector SHALL provide a read-only property for the agent's current CorrelationContext.
5. THE DebugInspector SHALL provide a method that returns the list of registered tool names from the agent's ToolRegistry.
6. THE DebugInspector SHALL provide a method that returns the list of registered LLM provider name-model pairs from the agent's LlmProviderRegistry.
7. THE DebugInspector SHALL provide a method that returns the list of registered memory store names from the agent's MemoryStoreRegistry.
8. THE DebugInspector SHALL provide a method that returns the current MetricsSnapshot from the agent's MetricsCollector.
9. THE DebugInspector SHALL provide a method that returns the current active TraceSpan from the agent's Tracer, or None when no span is active.
10. THE DebugInspector SHALL provide a method that returns the current ExecutionRecording from the agent's ExecutionRecorder.
11. THE DebugInspector SHALL provide a __repr__ method that includes the class name and agent identifier.
12. THE DebugInspector SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and current lifecycle state.

### Requirement 25: Observability Configuration

**User Story:** As a developer, I want to configure the observability system declaratively, so that I can define logging format, log level, tracing enablement, metrics enablement, recording enablement, debug mode, and exporter settings without modifying code.

#### Acceptance Criteria

1. THE ObservabilityConfiguration SHALL contain the log level as a string (one of "debug", "info", "warning", "error", "critical"), the log format as a string (one of "json", "key_value", "human_readable"), tracing enabled as a boolean, metrics enabled as a boolean, recording enabled as a boolean, debug mode enabled as a boolean, a sampling rate as a float between 0.0 and 1.0 inclusive, and exporter settings as a dictionary.
2. THE ObservabilityConfiguration SHALL support loading configuration from a Python dictionary.
3. THE ObservabilityConfiguration SHALL support loading configuration from a JSON file path.
4. THE ObservabilityConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE ObservabilityConfiguration SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
6. THE ObservabilityConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. IF an invalid log level is provided, THEN THE ObservabilityConfiguration SHALL raise a ConfigurationError identifying the invalid log level and listing the valid log levels.
8. IF an invalid log format is provided, THEN THE ObservabilityConfiguration SHALL raise a ConfigurationError identifying the invalid log format and listing the valid log formats.
9. IF the sampling rate is outside the range 0.0 to 1.0, THEN THE ObservabilityConfiguration SHALL raise a ConfigurationError indicating that the sampling rate must be between 0.0 and 1.0 inclusive.
10. THE ObservabilityConfiguration SHALL support CredentialReference entries for exporter authentication that are resolved through `automojo-credentials` at initialization time.
11. IF a CredentialReference cannot be resolved, THEN THE ObservabilityConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
12. THE ObservabilityConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration, excluding resolved credential values.
13. THE ObservabilityConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration, excluding resolved credential values.
14. THE ObservabilityConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration, excluding resolved credential values.
15. THE ObservabilityConfiguration SHALL provide a class method from_dict that constructs an ObservabilityConfiguration from a dictionary.
16. THE ObservabilityConfiguration SHALL provide a class method from_json that deserializes a JSON string into an ObservabilityConfiguration instance.
17. THE ObservabilityConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into an ObservabilityConfiguration instance.
18. FOR ALL valid ObservabilityConfiguration instances, calling to_json and then from_json SHALL produce an equivalent ObservabilityConfiguration object (round-trip property).
19. FOR ALL valid ObservabilityConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent ObservabilityConfiguration object (round-trip property).
20. THE ObservabilityConfiguration SHALL provide a __repr__ method that includes the class name, log level, log format, and tracing enabled status.
21. THE ObservabilityConfiguration SHALL provide a __str__ method that returns a human-readable summary including the log level, log format, tracing enabled, metrics enabled, recording enabled, debug mode, and sampling rate.

### Requirement 26: Observability Pipeline

**User Story:** As a developer, I want a coordinating component that routes observability data from the structured logger, tracer, metrics collector, and execution recorder to configured exporters, so that all observability subsystems work together through a single integration point.

#### Acceptance Criteria

1. THE ObservabilityPipeline SHALL accept an ObservabilityConfiguration at construction time for configuring the pipeline behavior.
2. THE ObservabilityPipeline SHALL construct and own the StructuredLogger, Tracer, MetricsCollector, MetricsRegistry, and ExecutionRecorder instances based on the ObservabilityConfiguration.
3. THE ObservabilityPipeline SHALL provide a read-only property for the StructuredLogger instance.
4. THE ObservabilityPipeline SHALL provide a read-only property for the Tracer instance.
5. THE ObservabilityPipeline SHALL provide a read-only property for the MetricsCollector instance.
6. THE ObservabilityPipeline SHALL provide a read-only property for the MetricsRegistry instance.
7. THE ObservabilityPipeline SHALL provide a read-only property for the ExecutionRecorder instance.
8. THE ObservabilityPipeline SHALL provide a register_log_exporter method that accepts a LogExporter and adds the exporter to the pipeline.
9. THE ObservabilityPipeline SHALL provide a register_trace_exporter method that accepts a TraceExporter and adds the exporter to the pipeline.
10. THE ObservabilityPipeline SHALL provide a register_metrics_exporter method that accepts a MetricsExporter and adds the exporter to the pipeline.
11. WHEN tracing is disabled in the ObservabilityConfiguration, THE Tracer SHALL operate as a no-op, creating spans that are not exported.
12. WHEN metrics are disabled in the ObservabilityConfiguration, THE MetricsCollector SHALL operate as a no-op, discarding measurements without exporting.
13. WHEN recording is disabled in the ObservabilityConfiguration, THE ExecutionRecorder SHALL operate as a no-op, discarding events without storing.
14. THE ObservabilityPipeline SHALL provide a shutdown method that flushes and shuts down all registered exporters.
15. THE ObservabilityPipeline SHALL provide a __repr__ method that includes the class name, the count of log exporters, trace exporters, and metrics exporters.
16. THE ObservabilityPipeline SHALL provide a __str__ method that returns a human-readable summary including the log level, tracing enabled status, metrics enabled status, and recording enabled status.

### Requirement 27: Agent Observability Integration

**User Story:** As a developer, I want agents to own an observability pipeline and produce observability data throughout their lifecycle, so that all agent operations are automatically instrumented for monitoring and debugging.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only observability property that returns the Agent's ObservabilityPipeline instance.
2. THE Agent base class SHALL expose a read-only debug_session property that returns the Agent's DebugSession instance, or None when debug mode is not enabled.
3. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL construct the ObservabilityPipeline from the Agent's ObservabilityConfiguration.
4. WHEN an Agent transitions to the INITIALIZED state and debug mode is enabled in the ObservabilityConfiguration, THE Agent SHALL construct a DebugSession.
5. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all ObservabilityExporterPlugin instances from `automojo-extension` ExtensionPoint entries targeting the Agent.
6. WHEN a lifecycle state transition occurs, THE ObservabilityPipeline SHALL create a trace span for the transition, log the transition through the StructuredLogger, record the transition through the ExecutionRecorder, and update the lifecycle transition counter metric.
7. WHEN a tool execution occurs, THE ObservabilityPipeline SHALL create a child trace span for the execution, log the execution through the StructuredLogger, record the execution through the ExecutionRecorder, and update the tool execution duration histogram and error counter metrics.
8. WHEN an LLM completion request occurs, THE ObservabilityPipeline SHALL create a child trace span for the request, log the request through the StructuredLogger, record the request through the ExecutionRecorder, and update the LLM request duration histogram, token usage counters, and error counter metrics.
9. WHEN an Agent transitions to the STOPPED state, THE Agent SHALL flush and shut down the ObservabilityPipeline.
10. IF the Agent's ObservabilityConfiguration is not provided, THEN THE Agent SHALL default to an ObservabilityConfiguration with log level "info", log format "human_readable", tracing disabled, metrics disabled, recording disabled, debug mode disabled, and sampling rate 1.0.

### Requirement 28: Observability Exporter Plugin Integration

**User Story:** As a developer, I want to distribute observability exporters as plugins through `automojo-extension`, so that exporter packages can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.log_exporters" through `automojo-extension` for registering LogExporter plugin implementations.
2. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.trace_exporters" through `automojo-extension` for registering TraceExporter plugin implementations.
3. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.metrics_exporters" through `automojo-extension` for registering MetricsExporter plugin implementations.
4. WHEN an Agent is initialized, THE Agent SHALL query the observability exporter ExtensionPoints and register all discovered exporter instances with the Agent's ObservabilityPipeline.
5. IF an ObservabilityExporterPlugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
6. IF an ObservabilityExporterPlugin provides an exporter that conflicts with an already registered exporter of the same type and name, THEN THE Agent SHALL log the conflict at WARNING level and skip the conflicting plugin exporter.

### Requirement 29: Observability Error Handling

**User Story:** As a developer, I want a well-defined error type for observability operation failures, so that I can diagnose and handle observability errors precisely.

#### Acceptance Criteria

1. THE ObservabilityError SHALL inherit from AgentKitError and SHALL be raised when an observability operation fails due to an exporter error, recording error, or pipeline configuration error.
2. THE ObservabilityError SHALL contain the component name string (e.g., exporter class name, recorder name), the operation name string, and the original exception as the cause.
3. THE ObservabilityError SHALL provide a meaningful __repr__ that includes the exception class name, component name, operation name, and descriptive message.

### Requirement 30: Trace Span Sampling

**User Story:** As a developer, I want to control the sampling rate of trace spans, so that I can reduce the volume of trace data in high-throughput scenarios while still capturing representative samples.

#### Acceptance Criteria

1. THE Tracer SHALL accept a sampling rate as a float between 0.0 and 1.0 inclusive at construction time, defaulting to 1.0 (sample all spans).
2. WHEN the sampling rate is less than 1.0, THE Tracer SHALL probabilistically decide whether to record each new root span based on the sampling rate.
3. WHEN a root span is not sampled, THE Tracer SHALL create a non-recording span that propagates the TraceContext but does not export span data.
4. WHEN a root span is sampled, THE Tracer SHALL record and export the span and all child spans within the same trace.
5. THE Tracer SHALL expose a read-only property for the configured sampling rate.
