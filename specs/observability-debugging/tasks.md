# Implementation Plan: Observability & Debugging

## Overview

Implement the Observability & Debugging feature for the `automojo-agent-kit` SDK. The implementation follows a bottom-up approach: shared types and error first, then data models (log entries, trace contexts, metric definitions, execution records, breakpoints), then active components (loggers, tracers, collectors, recorders, debug sessions), then exporters, then the coordination layer (ObservabilityPipeline, ObservabilityConfiguration), and finally Agent integration. All source files go under `source/packages/automojo/agentkit/` with lowercase filenames. Tests go under `source/testroots/automojo/tests/singlehost/agentkit/`.

## Tasks

- [x] 1. Implement ObservabilityError and CorrelationContext
  - [x] 1.1 Create `observabilityerror.py` with ObservabilityError class
    - Inherit from AgentKitError with component_name, operation_name, message, and optional cause
    - Provide __repr__ including class name, component name, operation name, and message
    - _Requirements: 29.1, 29.2, 29.3_

  - [x] 1.2 Create `correlationcontext.py` with CorrelationContext class
    - Mutable context with correlation_id (auto-generated UUID if not provided) and optional parent_correlation_id
    - Read-only properties for correlation_id and parent_correlation_id
    - Implement create_child returning new CorrelationContext with current id as parent
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11_

  - [x] 1.3 Write unit tests for ObservabilityError and CorrelationContext
    - Create `test_observabilityerror.py` testing construction, properties, __repr__
    - Create `test_correlationcontext.py` testing auto-generated UUID, read-only properties, create_child, serialization, __repr__, __str__
    - _Requirements: 29.1–29.3, 1.1–1.11_

  - [x] 1.4 Write property test for CorrelationContext JSON round-trip
    - **Property 1: CorrelationContext JSON round-trip**
    - **Validates: Requirements 1.6, 1.8, 1.9**

  - [x] 1.5 Write property test for CorrelationContext auto-generates valid UUID
    - **Property 2: CorrelationContext auto-generates valid UUID**
    - **Validates: Requirements 1.2**

  - [x] 1.6 Write property test for CorrelationContext create_child preserves parent chain
    - **Property 3: CorrelationContext create_child preserves parent chain**
    - **Validates: Requirements 1.4**


- [x] 2. Implement structured logging data models
  - [x] 2.1 Create `structuredlogentry.py` with StructuredLogEntry class
    - Immutable object with timestamp, level, message, logger_name, correlation_id, agent_id, metadata dict
    - Read-only properties for all fields
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 2.2 Create `logformatter.py` with LogFormatter base class and concrete formatters
    - LogFormatter abstract base with format_name property and abstract format method
    - JsonLogFormatter: formats entry as single-line JSON
    - KeyValueLogFormatter: formats entry as space-separated key=value pairs
    - HumanReadableLogFormatter: formats entry as human-readable string with timestamp, level, logger, message, correlation_id
    - All provide __repr__ and __str__
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [x] 2.3 Write unit tests for StructuredLogEntry and LogFormatter
    - Create `test_structuredlogentry.py` testing construction, immutability, serialization, __repr__, __str__
    - Create `test_logformatter.py` testing JsonLogFormatter output is valid JSON, KeyValueLogFormatter format, HumanReadableLogFormatter format, abstract enforcement
    - _Requirements: 2.1–2.9, 4.1–4.8_

  - [x] 2.4 Write property test for StructuredLogEntry JSON round-trip
    - **Property 4: StructuredLogEntry JSON round-trip**
    - **Validates: Requirements 2.4, 2.6, 2.7**

  - [x] 2.5 Write property test for JsonLogFormatter produces valid JSON with all fields
    - **Property 6: JsonLogFormatter produces valid JSON containing all entry fields**
    - **Validates: Requirements 4.3**

- [x] 3. Implement StructuredLogger and LogExporter
  - [x] 3.1 Create `structuredlogger.py` with StructuredLogger class
    - Accept agent_id and CorrelationContext at construction
    - Delegate to Python standard logging under `automojo.agentkit.observability`
    - Provide debug, info, warning, error, critical methods creating StructuredLogEntry with current timestamp, correlation_id, agent_id, and metadata kwargs
    - Provide set_correlation_context method and read-only correlation_context property
    - Implement __repr__ and __str__
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

  - [x] 3.2 Create `logexporter.py` with LogExporter base class and concrete exporters
    - LogExporter abstract base with export, flush, shutdown abstract methods; accepts LogFormatter and optional credential_references
    - ConsoleLogExporter: writes formatted entries to stdout
    - FileLogExporter: writes formatted entries to file path resolved relative to AppContext directory
    - Raise ObservabilityError on export failure
    - All provide __repr__ and __str__
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12_

  - [x] 3.3 Write unit tests for StructuredLogger and LogExporter
    - Create `test_structuredlogger.py` testing log methods produce correct StructuredLogEntry, set_correlation_context, delegation to standard logging
    - Create `test_logexporter.py` testing ConsoleLogExporter output, FileLogExporter file writing, export failure raises ObservabilityError, abstract enforcement
    - _Requirements: 3.1–3.9, 5.1–5.12_

  - [x] 3.4 Write property test for StructuredLogger produces entries with correct fields
    - **Property 5: StructuredLogger produces entries with correct fields**
    - **Validates: Requirements 3.3, 3.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 5. Implement tracing data models
  - [x] 5.1 Create `tracecontext.py` with TraceContext class
    - Immutable object with trace_id (auto-generated 32-char hex), span_id (auto-generated 16-char hex), optional parent_span_id, trace_flags (default 0)
    - Read-only properties for all fields
    - Implement create_child_span_context returning new TraceContext with same trace_id, new span_id, current span_id as parent
    - Implement to_traceparent returning W3C format "00-{trace_id}-{span_id}-{trace_flags:02x}"
    - Implement from_traceparent class method parsing W3C traceparent string, raising SemanticError on malformed input
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 6.14, 6.15, 6.16_

  - [x] 5.2 Create `traceevent.py` with TraceEvent class
    - Immutable object with name, timestamp (auto-generated UTC if not provided), attributes dict
    - Read-only properties for all fields
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_

  - [x] 5.3 Create `tracespan.py` with TraceSpan class
    - Mutable object with name, TraceContext, start_time, optional end_time, status ("unset"/"ok"/"error"), attributes dict, events list
    - set_status validates against VALID_STATUSES, raises SemanticError for invalid values
    - set_attribute adds key-value to attributes
    - add_event appends TraceEvent with current timestamp
    - end sets end_time, raises SemanticError if already ended
    - duration property returns elapsed seconds or None
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13, 7.14, 7.15, 7.16_

  - [x] 5.4 Write unit tests for TraceContext, TraceEvent, and TraceSpan
    - Create `test_tracecontext.py` testing auto-generated ids, create_child_span_context, traceparent round-trip, malformed traceparent error, serialization
    - Create `test_traceevent.py` testing construction, auto-timestamp, immutability, serialization
    - Create `test_tracespan.py` testing set_status valid/invalid, set_attribute, add_event, end/double-end error, duration, serialization
    - _Requirements: 6.1–6.16, 7.1–7.16, 8.1–8.10_

  - [x] 5.5 Write property test for TraceContext auto-generates valid identifiers
    - **Property 7: TraceContext auto-generates valid identifiers**
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [x] 5.6 Write property test for TraceContext JSON round-trip
    - **Property 8: TraceContext JSON round-trip**
    - **Validates: Requirements 6.10, 6.12, 6.13**

  - [x] 5.7 Write property test for TraceContext traceparent round-trip
    - **Property 9: TraceContext traceparent round-trip**
    - **Validates: Requirements 6.6, 6.7, 6.14**

  - [x] 5.8 Write property test for TraceContext create_child_span_context preserves trace_id
    - **Property 10: TraceContext create_child_span_context preserves trace_id**
    - **Validates: Requirements 6.5**

  - [x] 5.9 Write property test for TraceEvent JSON round-trip
    - **Property 11: TraceEvent JSON round-trip**
    - **Validates: Requirements 8.5, 8.7, 8.8**

  - [x] 5.10 Write property test for TraceSpan JSON round-trip for completed spans
    - **Property 12: TraceSpan JSON round-trip for completed spans**
    - **Validates: Requirements 7.11, 7.13, 7.14**

  - [x] 5.11 Write property test for TraceSpan set_attribute accumulates attributes
    - **Property 13: TraceSpan set_attribute accumulates attributes**
    - **Validates: Requirements 7.5**

  - [x] 5.12 Write property test for TraceSpan add_event accumulates events
    - **Property 14: TraceSpan add_event accumulates events**
    - **Validates: Requirements 7.6**

  - [x] 5.13 Write property test for TraceSpan duration equals elapsed time
    - **Property 15: TraceSpan duration equals elapsed time**
    - **Validates: Requirements 7.9**


- [x] 6. Implement Tracer and TraceExporter
  - [x] 6.1 Create `tracer.py` with Tracer class
    - Accept agent_id, optional TraceContext, and sampling_rate (default 1.0)
    - Maintain active span stack; start_span creates root or child span, end_span pops stack and delivers to exporters
    - Provide span context manager that starts span on entry, ends on exit (sets error status on exception)
    - Provide active_span read-only property, sampling_rate property, register_exporter method
    - Implement probabilistic sampling at root span level; non-sampled spans propagate context but don't export
    - Implement __repr__ and __str__
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 30.1, 30.2, 30.3, 30.4, 30.5_

  - [x] 6.2 Create `traceexporter.py` with TraceExporter base class and concrete exporters
    - TraceExporter abstract base with export (accepts list of spans), flush, shutdown abstract methods; optional credential_references
    - ConsoleTraceExporter: writes formatted span text to stdout
    - FileTraceExporter: writes spans as JSON lines to file path resolved relative to AppContext directory
    - Raise ObservabilityError on export failure
    - All provide __repr__ and __str__
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11_

  - [x] 6.3 Write unit tests for Tracer and TraceExporter
    - Create `test_tracer.py` testing start_span/end_span stack behavior, context manager, exporter delivery, sampling at 0.0/1.0/0.5, nested spans share trace_id
    - Create `test_traceexporter.py` testing ConsoleTraceExporter output, FileTraceExporter file writing, export failure raises ObservabilityError, abstract enforcement
    - _Requirements: 9.1–9.10, 10.1–10.11, 30.1–30.5_

  - [x] 6.4 Write property test for Tracer span stack follows LIFO semantics
    - **Property 16: Tracer span stack follows LIFO semantics**
    - **Validates: Requirements 9.2, 9.3, 9.4, 9.5, 9.6**

  - [x] 6.5 Write property test for Tracer child spans share parent trace_id
    - **Property 17: Tracer child spans share parent trace_id**
    - **Validates: Requirements 9.4**

  - [x] 6.6 Write property test for Tracer sampling rate boundaries
    - **Property 34: Tracer sampling rate boundaries**
    - **Validates: Requirements 30.1, 30.2, 30.3, 30.4**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement metrics data models
  - [x] 8.1 Create `metrictype.py` with MetricType enum
    - Define COUNTER, GAUGE, HISTOGRAM values
    - Implement from_string class method raising SemanticError for invalid values
    - _Requirements: 11.8, 11.9, 11.10_

  - [x] 8.2 Create `metricdefinition.py` with MetricDefinition class
    - Immutable object with name, description, unit, metric_type (MetricType)
    - Read-only properties for all fields
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.11, 11.12_

  - [x] 8.3 Create `metricmeasurement.py` with MetricMeasurement class
    - Immutable object with metric_name, value (float), timestamp (auto-generated UTC), labels dict
    - Read-only properties for all fields
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10_

  - [x] 8.4 Create `metricssnapshot.py` with MetricsSnapshot class
    - Immutable object with timestamp and metrics dict (name to current values/labels)
    - get_metric method returning value for a name or None
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10_

  - [x] 8.5 Write unit tests for metrics data models
    - Create `test_metrictype.py` testing enum values and from_string (valid and invalid)
    - Create `test_metricdefinition.py` testing construction, properties, serialization
    - Create `test_metricmeasurement.py` testing construction, auto-timestamp, properties, serialization
    - Create `test_metricssnapshot.py` testing construction, get_metric, serialization
    - _Requirements: 11.1–11.12, 12.1–12.10, 15.1–15.10_

  - [x] 8.6 Write property test for MetricDefinition JSON round-trip
    - **Property 18: MetricDefinition JSON round-trip**
    - **Validates: Requirements 11.4, 11.6, 11.7**

  - [x] 8.7 Write property test for MetricMeasurement JSON round-trip
    - **Property 19: MetricMeasurement JSON round-trip**
    - **Validates: Requirements 12.5, 12.7, 12.8**

  - [x] 8.8 Write property test for MetricsSnapshot JSON round-trip
    - **Property 23: MetricsSnapshot JSON round-trip**
    - **Validates: Requirements 15.5, 15.7, 15.8**


- [x] 9. Implement MetricsRegistry, MetricsCollector, and MetricsExporter
  - [x] 9.1 Create `metricsregistry.py` with MetricsRegistry class
    - Dictionary-based registry with register, deregister, lookup, has_metric, list_all, count
    - Raise SemanticError on duplicate name registration
    - Implement __repr__ and __str__
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9_

  - [x] 9.2 Create `metricscollector.py` with MetricsCollector class
    - Accept MetricsRegistry at construction
    - Implement increment_counter, set_gauge, record_histogram methods with metric type validation (raise SemanticError on type mismatch or unregistered name)
    - Deliver MetricMeasurement to registered exporters
    - Implement snapshot returning MetricsSnapshot, reset clearing values
    - Implement register_exporter, __repr__, __str__
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 13.12, 13.13_

  - [x] 9.3 Create `metricsexporter.py` with MetricsExporter base class and concrete exporters
    - MetricsExporter abstract base with export (accepts list of measurements), flush, shutdown abstract methods; optional credential_references
    - ConsoleMetricsExporter: writes formatted measurements to stdout
    - FileMetricsExporter: writes measurements as JSON lines to file path resolved relative to AppContext directory
    - Raise ObservabilityError on export failure
    - All provide __repr__ and __str__
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10, 16.11_

  - [x] 9.4 Create `builtinagentmetrics.py` with register_builtin_agent_metrics function
    - Register all 13 standard agent metrics (lifecycle transitions, tool duration/errors, LLM duration/tokens/errors, memory ops, messages sent/received, workflow duration/errors, active spans) in the provided MetricsRegistry
    - _Requirements: 17.1_

  - [x] 9.5 Write unit tests for MetricsRegistry, MetricsCollector, MetricsExporter, and built-in metrics
    - Create `test_metricsregistry.py` testing register, deregister, lookup, has_metric, list_all, count, duplicate error
    - Create `test_metricscollector.py` testing increment_counter, set_gauge, record_histogram, type mismatch errors, unregistered name errors, snapshot, reset, exporter delivery
    - Create `test_metricsexporter.py` testing ConsoleMetricsExporter, FileMetricsExporter, export failure, abstract enforcement
    - Create `test_builtinagentmetrics.py` testing all 13 metrics are registered with correct names, types, and units
    - _Requirements: 13.1–13.13, 14.1–14.9, 16.1–16.11, 17.1_

  - [x] 9.6 Write property test for MetricsRegistry registration and lookup correctness
    - **Property 20: MetricsRegistry registration and lookup correctness**
    - **Validates: Requirements 14.1, 14.2, 14.4, 14.5, 14.6, 14.7**

  - [x] 9.7 Write property test for MetricsCollector counter accumulation
    - **Property 21: MetricsCollector counter accumulation**
    - **Validates: Requirements 13.2, 13.10**

  - [x] 9.8 Write property test for MetricsCollector type enforcement
    - **Property 22: MetricsCollector type enforcement**
    - **Validates: Requirements 13.4, 13.6, 13.8**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 11. Implement execution recording and replay
  - [x] 11.1 Create `executionrecord.py` with ExecutionRecord class
    - Immutable object with sequence_number, timestamp, event_type, agent_id, correlation_id, payload dict
    - Read-only properties for all fields
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_

  - [x] 11.2 Create `executionrecording.py` with ExecutionRecording class
    - Immutable object with agent_id, start_time, end_time, records list
    - duration property returning elapsed seconds
    - filter_by_event_type returning new ExecutionRecording with matching records
    - Implement as_dict, to_json, from_dict, from_json, __repr__, __str__
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9, 20.10, 20.11_

  - [x] 11.3 Create `executionrecorder.py` with ExecutionRecorder class
    - Accept agent_id at construction
    - Maintain ordered records list with monotonically increasing sequence numbers starting from 1
    - Provide start, stop, record, get_recording, clear methods
    - is_recording property; record silently discards when not recording
    - Implement count property, __repr__, __str__
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10, 19.11, 19.12_

  - [x] 11.4 Create `executionreplayer.py` with ExecutionReplayer class
    - Accept ExecutionRecording at construction
    - Provide next, previous, reset, seek, filter methods
    - seek raises SemanticError for invalid sequence number
    - filter returns new ExecutionReplayer with filtered recording
    - Provide current, position, total_count read-only properties
    - Implement __repr__, __str__
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8, 21.9, 21.10, 21.11, 21.12_

  - [x] 11.5 Write unit tests for execution recording and replay
    - Create `test_executionrecord.py` testing construction, properties, serialization
    - Create `test_executionrecording.py` testing construction, duration, filter_by_event_type, serialization
    - Create `test_executionrecorder.py` testing start/stop, record while active/inactive, sequence numbers, get_recording, clear
    - Create `test_executionreplayer.py` testing next/previous traversal, boundary conditions, reset, seek valid/invalid, filter
    - _Requirements: 18.1–18.9, 19.1–19.12, 20.1–20.11, 21.1–21.12_

  - [x] 11.6 Write property test for ExecutionRecord JSON round-trip
    - **Property 24: ExecutionRecord JSON round-trip**
    - **Validates: Requirements 18.4, 18.6, 18.7**

  - [x] 11.7 Write property test for ExecutionRecorder assigns monotonically increasing sequence numbers
    - **Property 25: ExecutionRecorder assigns monotonically increasing sequence numbers**
    - **Validates: Requirements 19.3**

  - [x] 11.8 Write property test for ExecutionRecording JSON round-trip
    - **Property 26: ExecutionRecording JSON round-trip**
    - **Validates: Requirements 20.6, 20.8, 20.9**

  - [x] 11.9 Write property test for ExecutionRecording filter_by_event_type correctness
    - **Property 27: ExecutionRecording filter_by_event_type correctness**
    - **Validates: Requirements 20.4**

  - [x] 11.10 Write property test for ExecutionReplayer traversal visits all records in order
    - **Property 28: ExecutionReplayer traversal visits all records in order**
    - **Validates: Requirements 21.2, 21.3**

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 13. Implement debug system
  - [x] 13.1 Create `breakpoint.py` with Breakpoint class
    - Immutable object with breakpoint_type (validated against VALID_TYPES), optional target_name, optional condition
    - Raise SemanticError for invalid breakpoint_type
    - Implement matches method: returns True when type matches event_type and target_name matches (or breakpoint has no target_name)
    - Implement as_dict, __repr__, __str__
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9_

  - [x] 13.2 Create `debuginspector.py` with DebugInspector class
    - Accept Agent instance at construction
    - Read-only properties for lifecycle_state, identity, correlation_context
    - Methods: get_tool_names, get_llm_providers, get_memory_store_names, get_metrics_snapshot, get_active_span, get_execution_recording
    - Implement __repr__, __str__
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 24.9, 24.10, 24.11, 24.12_

  - [x] 13.3 Create `debugsession.py` with DebugSession class
    - Accept Agent instance at construction
    - Manage breakpoints: add_breakpoint, remove_breakpoint, list_breakpoints, clear_breakpoints
    - Provide start, stop, continue_execution, step methods
    - Invoke registered pause_callback with DebugInspector when breakpoint matches
    - Provide is_paused, is_active, inspector read-only properties
    - set_pause_callback method
    - Implement __repr__, __str__
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8, 22.9, 22.10, 22.11, 22.12, 22.13, 22.14, 22.15_

  - [x] 13.4 Write unit tests for debug system
    - Create `test_breakpoint.py` testing construction, invalid type error, matches with/without target_name, as_dict
    - Create `test_debuginspector.py` testing read-only access to agent state using mocked Agent
    - Create `test_debugsession.py` testing add/remove/list/clear breakpoints, start/stop, pause callback invocation, continue_execution, step, is_paused/is_active
    - _Requirements: 22.1–22.15, 23.1–23.9, 24.1–24.12_

  - [x] 13.5 Write property test for Breakpoint matches logic
    - **Property 29: Breakpoint matches logic**
    - **Validates: Requirements 23.4, 23.5, 23.6**

- [x] 14. Implement ObservabilityConfiguration
  - [x] 14.1 Create `observabilityconfiguration.py` with ObservabilityConfiguration class
    - Accept log_level, log_format, tracing_enabled, metrics_enabled, recording_enabled, debug_mode_enabled, sampling_rate, exporter_settings
    - Validate log_level against VALID_LOG_LEVELS, log_format against VALID_LOG_FORMATS, sampling_rate in 0.0–1.0; raise ConfigurationError on invalid values
    - Support CredentialReference entries resolved through automojo-credentials
    - Implement as_dict (excluding credential secrets), to_json, to_yaml, from_dict, from_json, from_yaml, from_json_file, from_yaml_file
    - File paths resolved relative to AppContext directory
    - Implement __repr__, __str__
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7, 25.8, 25.9, 25.10, 25.11, 25.12, 25.13, 25.14, 25.15, 25.16, 25.17, 25.18, 25.19, 25.20, 25.21_

  - [x] 14.2 Write unit tests for ObservabilityConfiguration
    - Create `test_observabilityconfiguration.py` testing construction, defaults, validation errors (invalid log_level, log_format, sampling_rate), serialization (JSON and YAML), credential exclusion from serialization, file loading with mocked AppContext
    - _Requirements: 25.1–25.21_

  - [x] 14.3 Write property test for ObservabilityConfiguration JSON round-trip
    - **Property 30: ObservabilityConfiguration JSON round-trip**
    - **Validates: Requirements 25.13, 25.16, 25.18**

  - [x] 14.4 Write property test for ObservabilityConfiguration YAML round-trip
    - **Property 31: ObservabilityConfiguration YAML round-trip**
    - **Validates: Requirements 25.14, 25.17, 25.19**

  - [x] 14.5 Write property test for ObservabilityConfiguration serialization excludes credentials
    - **Property 32: ObservabilityConfiguration serialization excludes credentials**
    - **Validates: Requirements 25.12, 25.13, 25.14**

  - [x] 14.6 Write property test for ObservabilityConfiguration validation rejects invalid configs
    - **Property 33: ObservabilityConfiguration validation rejects invalid configs**
    - **Validates: Requirements 25.7, 25.8, 25.9**

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 16. Implement ObservabilityPipeline
  - [x] 16.1 Create `observabilitypipeline.py` with ObservabilityPipeline class
    - Accept ObservabilityConfiguration, agent_id, and optional CorrelationContext at construction
    - Construct and own StructuredLogger, Tracer, MetricsCollector, MetricsRegistry, ExecutionRecorder based on configuration
    - When tracing disabled, Tracer operates as no-op (spans not exported)
    - When metrics disabled, MetricsCollector operates as no-op (measurements discarded)
    - When recording disabled, ExecutionRecorder operates as no-op (events discarded)
    - Provide register_log_exporter, register_trace_exporter, register_metrics_exporter methods
    - Provide read-only properties for logger, tracer, metrics_collector, metrics_registry, execution_recorder
    - Implement shutdown flushing and shutting down all exporters
    - Implement __repr__, __str__
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7, 26.8, 26.9, 26.10, 26.11, 26.12, 26.13, 26.14, 26.15, 26.16_

  - [x] 16.2 Write unit tests for ObservabilityPipeline
    - Create `test_observabilitypipeline.py` testing component initialization, no-op behavior when subsystems disabled, exporter registration, shutdown lifecycle, property access
    - _Requirements: 26.1–26.16_

- [x] 17. Implement Agent observability integration
  - [x] 17.1 Extend Agent base class with observability properties and methods
    - Add observability read-only property returning ObservabilityPipeline
    - Add debug_session read-only property returning DebugSession or None
    - Wire ObservabilityPipeline construction into Agent INITIALIZED state transition
    - Wire DebugSession construction when debug_mode_enabled
    - Discover and register ObservabilityExporterPlugin instances from ExtensionPoints during initialization
    - Wire lifecycle transitions to create trace spans, log entries, execution records, and metric updates
    - Wire tool executions to create child spans, log entries, execution records, and metric updates (duration histogram, error counter)
    - Wire LLM requests to create child spans, log entries, execution records, and metric updates (duration, tokens, errors)
    - Wire shutdown to flush and shut down ObservabilityPipeline on STOPPED state
    - Default ObservabilityConfiguration when not provided: log_level="info", log_format="human_readable", tracing/metrics/recording/debug disabled, sampling_rate=1.0
    - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7, 27.8, 27.9, 27.10, 17.2, 17.3, 17.4, 17.5, 17.6_

  - [x] 17.2 Implement exporter plugin discovery integration
    - Define ExtensionPoints: "automojo.agentkit.log_exporters", "automojo.agentkit.trace_exporters", "automojo.agentkit.metrics_exporters"
    - Query ExtensionPoints during Agent initialization and register discovered exporters
    - Log plugin loading failures at WARNING and continue; log conflicts at WARNING and skip
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6_

  - [x] 17.3 Write unit tests for Agent observability integration
    - Test observability property access, debug_session property, lifecycle integration (initialize/start/stop), plugin discovery with mocked ExtensionPoints, plugin failure handling, default configuration
    - _Requirements: 27.1–27.10, 28.1–28.6_

- [x] 18. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and error conditions
- All source files use lowercase filenames with no underscores under `source/packages/automojo/agentkit/`
- All test files go under `source/testroots/automojo/tests/singlehost/agentkit/` mirroring the source hierarchy
- Tests use the `testbase` framework and `automojo.testbase.mocking` for mocks
- Run tests with: `source .venv/bin/activate && testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost.agentkit --output=./.output`
