# Requirements Document — Error Handling & Resilience

## Introduction

The Error Handling & Resilience feature extends the `codecraftai-agent-kit` SDK with a cross-cutting system for handling failures, recovering from transient errors, and maintaining system health across all agent subsystems. It defines a unified retry executor that leverages the existing RetryPolicy from the LLM Integration feature and applies it across all agent operations (tool execution, transport communication, memory backend access, workflow steps), a circuit breaker pattern for protecting agents from cascading failures when external services are degraded, graceful degradation strategies that allow agents to continue operating with reduced functionality when dependencies are unavailable, a dead letter queue for capturing and managing messages and operations that have permanently failed after exhausting retry and fallback options, and a health check and self-healing system for monitoring agent component health and triggering automated recovery actions. The system integrates with the Agent base class so agents own and manage resilience components throughout their lifecycle, with the Tool & Capability System so tool executions are protected by circuit breakers and retries, with the LLM Integration system so LLM requests leverage the existing RetryPolicy and FallbackChain with circuit breaker protection, with the Memory & Context Management system so memory backend operations are resilient to transient failures, with the Communication & Messaging system so message delivery failures are captured in the dead letter queue, with the Workflow & Orchestration system so workflow step failures trigger retry and degradation strategies, with the Observability & Debugging system so resilience events are traced, logged, and metered, with the Security & Access Control system so resilience operations are audited, with the Configuration & Extensibility system so resilience policies are configurable and hot-reloadable, with `codecraftai-extension` so resilience plugins can be discovered and loaded, with `codecraftai-credentials` for credential management, with `codecraftai-dataprofiles` for data profile management, and with `codecraftai-this-app` for settings and environment configuration.

## Glossary

- **RetryPolicy**: The retry configuration object defined in the LLM Integration feature, containing maximum retry count, backoff strategy (fixed, exponential, exponential_with_jitter), base delay, maximum delay, and retryable exception types. The Error Handling & Resilience feature reuses this class as the unified retry configuration across all agent subsystems.
- **RetryExecutor**: A component that executes a callable with retry logic governed by a RetryPolicy. The RetryExecutor handles delay calculation, attempt tracking, and retryable exception filtering. The RetryExecutor is the cross-cutting retry mechanism used by all agent subsystems.
- **RetryAttempt**: An immutable object representing a single retry attempt, containing the attempt number, the delay before the attempt in seconds, the exception that triggered the retry, and a timestamp.
- **RetryResult**: An immutable object encapsulating the outcome of a retried operation, containing the operation result value on success, the final exception on failure, the list of RetryAttempt objects, the total elapsed time in seconds, and a success flag.
- **CircuitBreaker**: A component that monitors the success and failure rate of operations directed at an external service and transitions between closed (allowing requests), open (blocking requests), and half-open (testing recovery) states. The CircuitBreaker prevents cascading failures by fast-failing requests to degraded services.
- **CircuitBreakerState**: An enumeration defining the state of a CircuitBreaker: CLOSED (normal operation, requests pass through), OPEN (service is degraded, requests are rejected immediately), and HALF_OPEN (recovery testing, a limited number of requests are allowed through to test if the service has recovered).
- **CircuitBreakerConfiguration**: An immutable configuration object defining the thresholds and timing for a CircuitBreaker, containing the failure threshold count, the success threshold count for recovery, the open state timeout in seconds, the half-open max attempts count, and an optional list of monitored exception types.
- **CircuitBreakerEvent**: An immutable object representing a state transition or significant event in a CircuitBreaker, containing the circuit breaker name, the previous state, the new state, the event reason string, and a timestamp.
- **CircuitBreakerRegistry**: A registry that tracks all CircuitBreaker instances for an Agent, providing lookup by name and enumeration.
- **CircuitBreakerOpenError**: An exception raised when a request is rejected because the CircuitBreaker is in the OPEN state, inherited from AgentKitError. The exception includes the circuit breaker name, the service name, and the time remaining until the next half-open test.
- **DegradationStrategy**: An abstract base class representing a strategy for graceful degradation when a dependency is unavailable. Concrete implementations define fallback behavior such as returning cached results, using default values, or switching to alternative providers.
- **DegradationLevel**: An enumeration defining the severity of degradation: NORMAL (all dependencies available), DEGRADED (some dependencies unavailable, fallback behavior active), and CRITICAL (essential dependencies unavailable, minimal operation only).
- **DegradationPolicy**: An immutable configuration object defining the degradation behavior for a specific dependency, containing the dependency name, the DegradationStrategy to apply, the DegradationLevel at which the strategy activates, and an optional fallback value.
- **DegradationManager**: A component that monitors dependency availability and applies DegradationPolicy rules to maintain agent operation when dependencies fail. The DegradationManager tracks the current DegradationLevel and notifies registered listeners of degradation changes.
- **DegradationChangeEvent**: An immutable object representing a change in degradation level, containing the dependency name, the previous DegradationLevel, the new DegradationLevel, the reason string, and a timestamp.
- **DegradationChangeListener**: A callback interface invoked when a DegradationChangeEvent is detected by the DegradationManager.
- **DeadLetterQueue**: A component that stores operations and messages that have permanently failed after exhausting all retry attempts and fallback options. The DeadLetterQueue provides inspection, replay, and purge capabilities for failed items.
- **DeadLetterEntry**: An immutable object representing a failed operation or message stored in the DeadLetterQueue, containing a unique identifier, the original operation type string, the original payload as a dictionary, the final exception information, the list of RetryAttempt objects from the failed retry sequence, the source component name, the agent identifier, a creation timestamp, and a metadata dictionary.
- **DeadLetterStore**: An abstract base class for persisting DeadLetterEntry objects. Concrete implementations handle specific storage backends (in-memory, file-based). The DeadLetterStore provides append-only write semantics with support for replay and purge operations.
- **InMemoryDeadLetterStore**: A built-in DeadLetterStore implementation that stores DeadLetterEntry objects in process memory. Suitable for development, testing, and short-lived agents.
- **FileDeadLetterStore**: A built-in DeadLetterStore implementation that persists DeadLetterEntry objects to JSON files on the local file system. Suitable for single-agent local deployments.
- **DeadLetterQuery**: An immutable object representing a search request against a DeadLetterStore, containing optional filter criteria (operation type, source component, agent identifier, time range).
- **DeadLetterQueryResult**: An immutable object encapsulating the result of a DeadLetterQuery, containing the list of matching DeadLetterEntry objects and the total count of matches.
- **HealthCheck**: An abstract base class representing a health check for a specific agent component or external dependency. A HealthCheck has a name, a check method that returns a HealthStatus, and a configurable check interval.
- **HealthStatus**: An immutable object representing the result of a health check, containing the check name, a status string (one of "healthy", "degraded", "unhealthy"), an optional detail message, a response time in seconds as a float, and a timestamp.
- **HealthCheckRegistry**: A registry that tracks all HealthCheck instances for an Agent, providing lookup by name and enumeration.
- **HealthMonitor**: A component that periodically executes registered HealthCheck instances and aggregates the results into an overall agent health status. The HealthMonitor triggers self-healing actions when unhealthy components are detected.
- **SelfHealingAction**: An abstract base class representing an automated recovery action triggered when a HealthCheck reports an unhealthy status. Concrete implementations define specific recovery behaviors such as reconnecting transports, restarting sub-agents, or clearing caches.
- **SelfHealingPolicy**: An immutable configuration object defining the self-healing behavior for a specific health check, containing the health check name, the SelfHealingAction to execute, the maximum consecutive healing attempts, and a cooldown interval in seconds between healing attempts.
- **SelfHealingResult**: An immutable object representing the outcome of a self-healing action, containing the health check name, the action name, a success flag, an optional error message, the attempt number, and a timestamp.
- **ResilienceConfiguration**: A configuration object that defines the resilience settings for an Agent, including default RetryPolicy, circuit breaker enablement, degradation management enablement, dead letter queue enablement, health monitoring enablement, health check interval, and self-healing enablement.
- **ResiliencePipeline**: A component that coordinates the RetryExecutor, CircuitBreakerRegistry, DegradationManager, DeadLetterQueue, and HealthMonitor for an Agent, providing a unified resilience surface.
- **ResiliencePlugin**: A resilience component implementation (DegradationStrategy, HealthCheck, SelfHealingAction, or DeadLetterStore) discovered and loaded through the `codecraftai-extension` ExtensionPoint mechanism, allowing external packages to contribute resilience components.
- **Agent**: The base agent class defined in the Core Agent Framework that owns a ResiliencePipeline and applies resilience policies throughout its lifecycle.
- **ToolExecutor**: The tool executor defined in the Tool & Capability System, wrapped by the RetryExecutor and CircuitBreaker for resilient tool execution.
- **LlmProvider**: The LLM provider abstraction defined in the LLM Integration feature, protected by CircuitBreaker instances for resilient LLM requests.
- **FallbackChain**: The fallback chain defined in the LLM Integration feature, used in conjunction with CircuitBreaker state to skip degraded providers.
- **MemoryStore**: The memory store abstraction defined in the Memory & Context Management feature, protected by RetryExecutor for resilient memory operations.
- **Transport**: The transport abstraction defined in the Communication & Messaging feature, protected by CircuitBreaker and RetryExecutor for resilient message delivery.
- **Message**: The message object defined in the Communication & Messaging feature, stored in the DeadLetterQueue when delivery permanently fails.
- **MessageEnvelope**: The message envelope defined in the Communication & Messaging feature, used for tracking delivery attempts before dead-lettering.
- **WorkflowExecutor**: The workflow executor defined in the Workflow & Orchestration feature, using RetryPolicy and CircuitBreaker for resilient step execution.
- **CorrelationContext**: The correlation context defined in the Observability & Debugging feature, used for correlating resilience events with trace spans.
- **StructuredLogger**: The structured logger defined in the Observability & Debugging feature, used for logging resilience events.
- **MetricsCollector**: The metrics collector defined in the Observability & Debugging feature, used for recording resilience metrics (retry counts, circuit breaker state changes, dead letter counts).
- **Tracer**: The tracer defined in the Observability & Debugging feature, used for tracing retry attempts and circuit breaker decisions.
- **AuditLogger**: The audit logger defined in the Security & Access Control feature, used for auditing resilience events.
- **ConfigurationManager**: The configuration manager defined in the Configuration & Extensibility feature, used for loading and hot-reloading resilience configuration.
- **FeatureFlagRegistry**: The feature flag registry defined in the Configuration & Extensibility feature, used for toggling resilience features.
- **ExtensionPoint**: An integration surface provided by `codecraftai-extension` that allows external plugins to register resilience component implementations with an Agent.
- **CredentialReference**: A named reference resolved through `codecraftai-credentials` that provides secure access to secrets required by resilience components.
- **AppContext**: The application context provided by `codecraftai-this-app` that supplies settings, environment variables, and directory-based presence for loading resilience configuration files.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **ResilienceError**: An exception raised when a resilience operation fails due to a configuration or execution error, inherited from AgentKitError.

## Requirements

### Requirement 1: Retry Executor

**User Story:** As a developer, I want a cross-cutting retry executor that applies RetryPolicy-based retry logic to any callable operation, so that transient failures across all agent subsystems are handled consistently without duplicating retry logic in each subsystem.

#### Acceptance Criteria

1. THE RetryExecutor SHALL accept a RetryPolicy instance at construction time, defining the retry behavior for all operations executed through the RetryExecutor.
2. THE RetryExecutor SHALL provide an execute method that accepts a callable and optional arguments, invokes the callable, and returns a RetryResult containing the operation outcome.
3. WHEN the callable raises an exception that matches one of the retryable exception types in the RetryPolicy, THE RetryExecutor SHALL wait for the delay calculated by the RetryPolicy get_delay method and retry the callable.
4. WHEN the callable raises an exception that does not match any retryable exception type in the RetryPolicy, THE RetryExecutor SHALL raise the exception immediately without retrying.
5. WHEN the callable succeeds, THE RetryExecutor SHALL return a RetryResult with a success flag of True, the operation result value, and the list of RetryAttempt objects from any preceding failed attempts.
6. WHEN all retry attempts are exhausted, THE RetryExecutor SHALL return a RetryResult with a success flag of False, the final exception, and the complete list of RetryAttempt objects.
7. THE RetryExecutor SHALL record a RetryAttempt object for each failed attempt, containing the attempt number, the delay before the attempt, the exception, and a timestamp.
8. THE RetryExecutor SHALL log each retry attempt at INFO level including the operation name, attempt number, delay, and exception type, using the logger hierarchy under `ccai.agentkit.resilience`.
9. THE RetryExecutor SHALL provide a read-only property for the configured RetryPolicy.
10. THE RetryExecutor SHALL provide a __repr__ method that includes the class name, maximum retry count, and backoff strategy from the configured RetryPolicy.
11. THE RetryExecutor SHALL provide a __str__ method that returns a human-readable summary of the retry configuration.

### Requirement 2: Retry Attempt and Retry Result

**User Story:** As a developer, I want structured objects representing individual retry attempts and the overall retry outcome, so that I can inspect retry behavior during debugging and post-mortem analysis.

#### Acceptance Criteria

1. THE RetryAttempt SHALL contain the attempt number as an integer, the delay before the attempt in seconds as a float, the exception that triggered the retry, and a timestamp.
2. THE RetryAttempt SHALL expose all fields as read-only properties.
3. THE RetryAttempt SHALL provide an as_dict method that returns a dictionary representation of the attempt fields, with the exception represented as a string containing the exception type and message.
4. THE RetryAttempt SHALL provide a to_json method that returns a JSON string representation of the attempt fields.
5. THE RetryAttempt SHALL provide a class method from_dict that constructs a RetryAttempt from a dictionary.
6. THE RetryAttempt SHALL provide a class method from_json that deserializes a JSON string into a RetryAttempt instance.
7. FOR ALL valid RetryAttempt instances, calling to_json and then from_json SHALL produce a RetryAttempt with equivalent attempt number, delay, exception string representation, and timestamp values (round-trip property).
8. THE RetryAttempt SHALL provide a __repr__ method that includes the class name, attempt number, and exception type.
9. THE RetryAttempt SHALL provide a __str__ method that returns a human-readable summary including the attempt number, delay, and exception message.
10. THE RetryResult SHALL contain the operation result value on success, the final exception on failure, the list of RetryAttempt objects, the total elapsed time in seconds as a float, and a success flag as a boolean.
11. THE RetryResult SHALL expose all fields as read-only properties.
12. THE RetryResult SHALL provide an is_success read-only property that returns True when the success flag is True.
13. THE RetryResult SHALL provide an attempt_count read-only property that returns the total number of attempts including the initial attempt and all retries.
14. THE RetryResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
15. THE RetryResult SHALL provide a to_json method that returns a JSON string representation of the result fields.
16. THE RetryResult SHALL provide a class method from_json that deserializes a JSON string into a RetryResult instance.
17. FOR ALL valid RetryResult instances, calling to_json and then from_json SHALL produce a RetryResult with equivalent success flag, attempt list, and elapsed time values (round-trip property).
18. THE RetryResult SHALL provide a __repr__ method that includes the class name, success flag, and attempt count.
19. THE RetryResult SHALL provide a __str__ method that returns a human-readable summary including the success flag, attempt count, and elapsed time.

### Requirement 3: Circuit Breaker

**User Story:** As a developer, I want a circuit breaker that monitors failure rates for external services and fast-fails requests when a service is degraded, so that agents do not waste resources on requests that are likely to fail and cascading failures are prevented.

#### Acceptance Criteria

1. THE CircuitBreaker SHALL accept a name string and a CircuitBreakerConfiguration at construction time.
2. THE CircuitBreaker SHALL maintain a current CircuitBreakerState, starting in the CLOSED state.
3. THE CircuitBreaker SHALL provide an execute method that accepts a callable and optional arguments, evaluates the current state, and either executes the callable or rejects the request.
4. WHILE the CircuitBreaker is in the CLOSED state, THE CircuitBreaker SHALL execute the callable and track the outcome (success or failure).
5. WHEN the failure count in the CLOSED state reaches the failure threshold defined in the CircuitBreakerConfiguration, THE CircuitBreaker SHALL transition to the OPEN state.
6. WHILE the CircuitBreaker is in the OPEN state, THE CircuitBreaker SHALL reject all requests by raising a CircuitBreakerOpenError without executing the callable.
7. WHEN the open state timeout defined in the CircuitBreakerConfiguration elapses while in the OPEN state, THE CircuitBreaker SHALL transition to the HALF_OPEN state.
8. WHILE the CircuitBreaker is in the HALF_OPEN state, THE CircuitBreaker SHALL allow a limited number of requests through (up to the half-open max attempts defined in the CircuitBreakerConfiguration) to test if the service has recovered.
9. WHEN the success count in the HALF_OPEN state reaches the success threshold defined in the CircuitBreakerConfiguration, THE CircuitBreaker SHALL transition to the CLOSED state and reset the failure count.
10. WHEN a request fails in the HALF_OPEN state, THE CircuitBreaker SHALL transition back to the OPEN state and reset the open state timeout.
11. THE CircuitBreaker SHALL record a CircuitBreakerEvent for each state transition, containing the circuit breaker name, previous state, new state, reason, and timestamp.
12. THE CircuitBreaker SHALL expose a read-only property for the current CircuitBreakerState.
13. THE CircuitBreaker SHALL expose a read-only property for the current failure count.
14. THE CircuitBreaker SHALL expose a read-only property for the current success count.
15. THE CircuitBreaker SHALL expose a read-only property for the list of recorded CircuitBreakerEvent objects.
16. THE CircuitBreaker SHALL provide a reset method that transitions the CircuitBreaker to the CLOSED state and clears all counters and event history.
17. THE CircuitBreaker SHALL log each state transition at WARNING level including the circuit breaker name, previous state, new state, and reason, using the logger hierarchy under `ccai.agentkit.resilience`.
18. THE CircuitBreaker SHALL be thread-safe, using appropriate synchronization primitives to protect state transitions and counter updates from concurrent access.
19. THE CircuitBreaker SHALL provide a __repr__ method that includes the class name, circuit breaker name, and current state.
20. THE CircuitBreaker SHALL provide a __str__ method that returns a human-readable summary including the circuit breaker name, current state, failure count, and success count.

### Requirement 4: Circuit Breaker State and Configuration

**User Story:** As a developer, I want well-defined circuit breaker states and declarative configuration, so that I can tune circuit breaker behavior for different services and inspect the current state during debugging.

#### Acceptance Criteria

1. THE CircuitBreakerState enumeration SHALL define the values CLOSED, OPEN, and HALF_OPEN.
2. THE CircuitBreakerState enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding CircuitBreakerState member.
3. IF an invalid string value is provided to the from_string method, THEN THE CircuitBreakerState SHALL raise a SemanticError identifying the invalid value and listing the valid state values.
4. THE CircuitBreakerConfiguration SHALL contain a failure threshold count as an integer, a success threshold count as an integer, an open state timeout in seconds as a float, a half-open max attempts count as an integer, and an optional list of monitored exception types.
5. THE CircuitBreakerConfiguration SHALL expose all fields as read-only properties.
6. THE CircuitBreakerConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration fields.
7. THE CircuitBreakerConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration fields.
8. THE CircuitBreakerConfiguration SHALL provide a class method from_dict that constructs a CircuitBreakerConfiguration from a dictionary.
9. THE CircuitBreakerConfiguration SHALL provide a class method from_json that deserializes a JSON string into a CircuitBreakerConfiguration instance.
10. FOR ALL valid CircuitBreakerConfiguration instances (excluding the monitored exception types list), calling to_json and then from_dict on the parsed JSON SHALL produce a CircuitBreakerConfiguration with equivalent failure threshold, success threshold, open state timeout, and half-open max attempts values.
11. THE CircuitBreakerConfiguration SHALL provide a __repr__ method that includes the class name, failure threshold, and open state timeout.
12. THE CircuitBreakerConfiguration SHALL provide a __str__ method that returns a human-readable summary of the circuit breaker configuration.

### Requirement 5: Circuit Breaker Event

**User Story:** As a developer, I want structured event objects for circuit breaker state transitions, so that I can trace and audit circuit breaker behavior across agent operations.

#### Acceptance Criteria

1. THE CircuitBreakerEvent SHALL contain the circuit breaker name as a string, the previous CircuitBreakerState, the new CircuitBreakerState, the event reason as a string, and a timestamp.
2. THE CircuitBreakerEvent SHALL expose all fields as read-only properties.
3. THE CircuitBreakerEvent SHALL provide an as_dict method that returns a dictionary representation of the event fields.
4. THE CircuitBreakerEvent SHALL provide a to_json method that returns a JSON string representation of the event fields.
5. THE CircuitBreakerEvent SHALL provide a class method from_dict that constructs a CircuitBreakerEvent from a dictionary.
6. THE CircuitBreakerEvent SHALL provide a class method from_json that deserializes a JSON string into a CircuitBreakerEvent instance.
7. FOR ALL valid CircuitBreakerEvent instances, calling to_json and then from_json SHALL produce an equivalent CircuitBreakerEvent object (round-trip property).
8. THE CircuitBreakerEvent SHALL provide a __repr__ method that includes the class name, circuit breaker name, previous state, and new state.
9. THE CircuitBreakerEvent SHALL provide a __str__ method that returns a human-readable summary including the circuit breaker name, state transition, and reason.

### Requirement 6: Circuit Breaker Registry

**User Story:** As a developer, I want a registry that tracks all circuit breakers for an agent, so that I can discover, inspect, and manage circuit breakers by name.

#### Acceptance Criteria

1. THE CircuitBreakerRegistry SHALL support registration of a CircuitBreaker instance using the circuit breaker name as the registration key.
2. IF a CircuitBreaker with a duplicate name is registered, THEN THE CircuitBreakerRegistry SHALL raise a SemanticError that includes the duplicate circuit breaker name.
3. THE CircuitBreakerRegistry SHALL support deregistration of a CircuitBreaker by name.
4. THE CircuitBreakerRegistry SHALL support lookup of a registered CircuitBreaker by name, returning the CircuitBreaker instance or None when the name is not found.
5. THE CircuitBreakerRegistry SHALL support enumeration of all registered CircuitBreaker instances as a list.
6. THE CircuitBreakerRegistry SHALL expose a read-only property for the count of currently registered circuit breakers.
7. THE CircuitBreakerRegistry SHALL provide a has_circuit_breaker method that accepts a name and returns a boolean indicating whether a CircuitBreaker with the given name is registered.
8. THE CircuitBreakerRegistry SHALL provide a reset_all method that calls the reset method on all registered CircuitBreaker instances.
9. THE CircuitBreakerRegistry SHALL provide a __repr__ method that includes the class name and the count of registered circuit breakers.
10. THE CircuitBreakerRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered circuit breaker names and their current states.

### Requirement 7: Graceful Degradation Strategy

**User Story:** As a developer, I want pluggable degradation strategies that define fallback behavior when dependencies are unavailable, so that agents can continue operating with reduced functionality rather than failing completely.

#### Acceptance Criteria

1. THE DegradationStrategy base class SHALL define an abstract interface with a degrade method that accepts the dependency name, the original exception, and an optional context dictionary, and returns a fallback result value.
2. THE DegradationStrategy base class SHALL require all subclasses to provide an implementation for the degrade method.
3. THE DegradationStrategy base class SHALL expose a read-only property for the strategy name as a string.
4. THE framework SHALL provide a CachedResultStrategy that returns the most recently cached successful result for the dependency when the dependency is unavailable.
5. THE framework SHALL provide a DefaultValueStrategy that returns a configured default value when the dependency is unavailable.
6. THE framework SHALL provide a AlternateProviderStrategy that routes the operation to an alternative provider or backend when the primary dependency is unavailable.
7. THE DegradationStrategy base class SHALL provide a __repr__ method that includes the class name and strategy name.
8. THE DegradationStrategy base class SHALL provide a __str__ method that returns a human-readable summary including the strategy name.

### Requirement 8: Degradation Level and Policy

**User Story:** As a developer, I want to classify degradation severity and configure degradation policies per dependency, so that agents respond appropriately to different levels of service disruption.

#### Acceptance Criteria

1. THE DegradationLevel enumeration SHALL define the values NORMAL, DEGRADED, and CRITICAL.
2. THE DegradationLevel enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding DegradationLevel member.
3. IF an invalid string value is provided to the from_string method, THEN THE DegradationLevel SHALL raise a SemanticError identifying the invalid value and listing the valid level values.
4. THE DegradationPolicy SHALL contain a dependency name string, a DegradationStrategy instance, a DegradationLevel at which the strategy activates, and an optional fallback value.
5. THE DegradationPolicy SHALL expose all fields as read-only properties.
6. THE DegradationPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields, with the DegradationStrategy represented by its strategy name.
7. THE DegradationPolicy SHALL provide a to_json method that returns a JSON string representation of the policy fields.
8. THE DegradationPolicy SHALL provide a class method from_dict that constructs a DegradationPolicy from a dictionary, accepting a DegradationStrategy instance as a separate parameter.
9. THE DegradationPolicy SHALL provide a __repr__ method that includes the class name, dependency name, and activation level.
10. THE DegradationPolicy SHALL provide a __str__ method that returns a human-readable summary including the dependency name, strategy name, and activation level.

### Requirement 9: Degradation Manager

**User Story:** As a developer, I want a degradation manager that monitors dependency availability and applies degradation policies, so that agents automatically switch to fallback behavior when dependencies fail and recover when dependencies are restored.

#### Acceptance Criteria

1. THE DegradationManager SHALL accept an agent identifier string at construction time.
2. THE DegradationManager SHALL provide a register_policy method that accepts a DegradationPolicy and stores the policy for the specified dependency.
3. THE DegradationManager SHALL provide a deregister_policy method that accepts a dependency name and removes the policy.
4. THE DegradationManager SHALL provide a report_failure method that accepts a dependency name and an exception, evaluates the registered DegradationPolicy for the dependency, and applies the DegradationStrategy when the activation level is reached.
5. THE DegradationManager SHALL provide a report_recovery method that accepts a dependency name and transitions the dependency back to NORMAL DegradationLevel.
6. THE DegradationManager SHALL expose a read-only property for the current overall DegradationLevel, computed as the highest DegradationLevel across all tracked dependencies.
7. THE DegradationManager SHALL expose a method that returns a dictionary of dependency names to their current DegradationLevel values.
8. THE DegradationManager SHALL support registration of DegradationChangeListener callbacks that are invoked when a dependency DegradationLevel changes.
9. WHEN a dependency DegradationLevel changes, THE DegradationManager SHALL create a DegradationChangeEvent and invoke all registered DegradationChangeListener callbacks with the event.
10. IF a DegradationChangeListener callback raises an exception during invocation, THEN THE DegradationManager SHALL log the exception at WARNING level including the agent identifier and dependency name, and continue invoking the remaining registered listeners.
11. THE DegradationManager SHALL log each degradation level change at WARNING level including the agent identifier, dependency name, previous level, new level, and reason, using the logger hierarchy under `ccai.agentkit.resilience`.
12. THE DegradationManager SHALL provide a __repr__ method that includes the class name, agent identifier, and current overall degradation level.
13. THE DegradationManager SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, overall degradation level, and count of tracked dependencies.

### Requirement 10: Degradation Change Event

**User Story:** As a developer, I want structured event objects for degradation level changes, so that I can trace and react to dependency availability changes across agent operations.

#### Acceptance Criteria

1. THE DegradationChangeEvent SHALL contain the dependency name as a string, the previous DegradationLevel, the new DegradationLevel, the reason as a string, and a timestamp.
2. THE DegradationChangeEvent SHALL expose all fields as read-only properties.
3. THE DegradationChangeEvent SHALL provide an as_dict method that returns a dictionary representation of the event fields.
4. THE DegradationChangeEvent SHALL provide a to_json method that returns a JSON string representation of the event fields.
5. THE DegradationChangeEvent SHALL provide a class method from_dict that constructs a DegradationChangeEvent from a dictionary.
6. THE DegradationChangeEvent SHALL provide a class method from_json that deserializes a JSON string into a DegradationChangeEvent instance.
7. FOR ALL valid DegradationChangeEvent instances, calling to_json and then from_json SHALL produce an equivalent DegradationChangeEvent object (round-trip property).
8. THE DegradationChangeEvent SHALL provide a __repr__ method that includes the class name, dependency name, and new degradation level.
9. THE DegradationChangeEvent SHALL provide a __str__ method that returns a human-readable summary including the dependency name, level transition, and reason.

### Requirement 11: Dead Letter Queue

**User Story:** As a developer, I want a dead letter queue that captures permanently failed operations and messages, so that I can inspect, diagnose, and optionally replay failed items without losing them.

#### Acceptance Criteria

1. THE DeadLetterQueue SHALL accept a DeadLetterStore instance at construction time for persisting DeadLetterEntry objects.
2. THE DeadLetterQueue SHALL provide an enqueue method that accepts an operation type string, a payload dictionary, the final exception, the list of RetryAttempt objects, the source component name, the agent identifier, and optional metadata, creates a DeadLetterEntry, and stores the entry in the DeadLetterStore.
3. THE DeadLetterQueue SHALL provide a query method that accepts a DeadLetterQuery and returns a DeadLetterQueryResult containing matching entries.
4. THE DeadLetterQueue SHALL provide a get_entry method that accepts a DeadLetterEntry identifier and returns the DeadLetterEntry or None when the identifier is not found.
5. THE DeadLetterQueue SHALL provide a replay method that accepts a DeadLetterEntry identifier and a callable, retrieves the entry, invokes the callable with the entry payload, and returns the callable result on success.
6. WHEN the replay method succeeds, THE DeadLetterQueue SHALL remove the replayed entry from the DeadLetterStore.
7. IF the replay method fails, THEN THE DeadLetterQueue SHALL update the entry metadata with the replay failure information and retain the entry in the DeadLetterStore.
8. THE DeadLetterQueue SHALL provide a purge method that accepts an optional age threshold in seconds and removes all entries older than the threshold, or all entries when no threshold is provided.
9. THE DeadLetterQueue SHALL expose a read-only property for the count of entries in the DeadLetterStore.
10. THE DeadLetterQueue SHALL log each enqueue operation at WARNING level including the operation type, source component, agent identifier, and exception type, using the logger hierarchy under `ccai.agentkit.resilience`.
11. THE DeadLetterQueue SHALL provide a __repr__ method that includes the class name and entry count.
12. THE DeadLetterQueue SHALL provide a __str__ method that returns a human-readable summary including the entry count and store type.

### Requirement 12: Dead Letter Entry

**User Story:** As a developer, I want a structured dead letter entry with full context about the failed operation, so that I can diagnose failures and decide whether to replay or discard the entry.

#### Acceptance Criteria

1. THE DeadLetterEntry SHALL contain a unique string identifier, an operation type string, a payload dictionary, the final exception information as a string containing the exception type and message, the list of RetryAttempt objects, the source component name as a string, the agent identifier as a string, a creation timestamp, and a metadata dictionary.
2. WHEN a DeadLetterEntry is created without an explicit unique identifier, THE DeadLetterEntry SHALL generate a UUID-based identifier automatically.
3. WHEN a DeadLetterEntry is created without an explicit creation timestamp, THE DeadLetterEntry SHALL set the creation timestamp to the current UTC time.
4. THE DeadLetterEntry SHALL expose all fields as read-only properties.
5. THE DeadLetterEntry SHALL provide an as_dict method that returns a dictionary representation of the entry fields.
6. THE DeadLetterEntry SHALL provide a to_json method that returns a JSON string representation of the entry fields.
7. THE DeadLetterEntry SHALL provide a class method from_dict that constructs a DeadLetterEntry from a dictionary.
8. THE DeadLetterEntry SHALL provide a class method from_json that deserializes a JSON string into a DeadLetterEntry instance.
9. FOR ALL valid DeadLetterEntry instances, calling to_json and then from_json SHALL produce an equivalent DeadLetterEntry object (round-trip property).
10. THE DeadLetterEntry SHALL provide a __repr__ method that includes the class name, identifier, operation type, and source component.
11. THE DeadLetterEntry SHALL provide a __str__ method that returns a human-readable summary including the identifier, operation type, source component, and exception information.

### Requirement 13: Dead Letter Store

**User Story:** As a developer, I want pluggable dead letter storage backends with built-in in-memory and file-based implementations, so that I can choose the persistence strategy that fits my deployment environment.

#### Acceptance Criteria

1. THE DeadLetterStore base class SHALL define an abstract interface that includes methods for store (add a DeadLetterEntry), retrieve (get a DeadLetterEntry by identifier), search (execute a DeadLetterQuery), delete (remove a DeadLetterEntry by identifier), purge (remove entries by age threshold), and count (return the number of stored entries).
2. THE DeadLetterStore base class SHALL require all subclasses to provide an implementation for the store, retrieve, search, delete, purge, and count methods.
3. THE DeadLetterStore base class SHALL expose a read-only property for the store name as a string.
4. THE InMemoryDeadLetterStore SHALL implement the DeadLetterStore interface using in-process dictionary-based storage.
5. THE FileDeadLetterStore SHALL implement the DeadLetterStore interface using JSON file persistence on the local file system.
6. THE FileDeadLetterStore SHALL accept a directory path at construction time specifying where dead letter files are stored.
7. WHEN a DeadLetterEntry is stored in the FileDeadLetterStore, THE FileDeadLetterStore SHALL persist the entry as a JSON file within the configured directory, using the entry identifier as the file name.
8. IF the configured directory does not exist, THEN THE FileDeadLetterStore SHALL create the directory at construction time.
9. THE FileDeadLetterStore SHALL resolve the directory path relative to the AppContext directory provided by `codecraftai-this-app`.
10. IF a file read or write operation fails, THEN THE FileDeadLetterStore SHALL raise a ResilienceError that includes the file path and the underlying I/O error detail.
11. FOR ALL DeadLetterEntry objects stored in the FileDeadLetterStore, writing the entry to a JSON file and then reading the JSON file back SHALL produce an equivalent DeadLetterEntry object (round-trip property).
12. THE DeadLetterStore base class SHALL provide a __repr__ method that includes the class name and store name.
13. THE DeadLetterStore base class SHALL provide a __str__ method that returns a human-readable summary including the store name and entry count.

### Requirement 14: Dead Letter Query

**User Story:** As a developer, I want to search dead letter entries by operation type, source component, agent identifier, and time range, so that I can find and diagnose specific categories of failures.

#### Acceptance Criteria

1. THE DeadLetterQuery SHALL support filtering by operation type string.
2. THE DeadLetterQuery SHALL support filtering by source component name string.
3. THE DeadLetterQuery SHALL support filtering by agent identifier string.
4. THE DeadLetterQuery SHALL support filtering by a time range defined by an optional start timestamp and an optional end timestamp, matching entries whose creation timestamp falls within the range.
5. THE DeadLetterQuery SHALL support an optional max_results integer to limit the number of returned entries.
6. THE DeadLetterQuery SHALL provide an as_dict method that returns a dictionary representation of the query fields.
7. THE DeadLetterQuery SHALL provide a __repr__ method that includes the class name and a summary of active filter criteria.
8. THE DeadLetterQuery SHALL provide a __str__ method that returns a human-readable summary of the query criteria.
9. THE DeadLetterQueryResult SHALL contain the list of matching DeadLetterEntry objects and the total count of matches.
10. THE DeadLetterQueryResult SHALL expose all fields as read-only properties.
11. THE DeadLetterQueryResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
12. THE DeadLetterQueryResult SHALL provide a __repr__ method that includes the class name and the count of matching entries.
13. THE DeadLetterQueryResult SHALL provide a __str__ method that returns a human-readable summary including the match count.

### Requirement 15: Health Check Abstraction

**User Story:** As a developer, I want a pluggable health check abstraction for monitoring agent component and dependency health, so that I can define custom health checks for any component and receive structured health status results.

#### Acceptance Criteria

1. THE HealthCheck base class SHALL define an abstract interface with a check method that returns a HealthStatus object.
2. THE HealthCheck base class SHALL require all subclasses to provide an implementation for the check method.
3. THE HealthCheck base class SHALL expose a read-only property for the health check name as a string.
4. THE HealthCheck base class SHALL expose a read-only property for the check interval in seconds as a float.
5. THE HealthCheck base class SHALL accept a check interval in seconds as a float at construction time, with a default value of 30.0.
6. THE framework SHALL provide a TransportHealthCheck that checks the connection status of a Transport instance and returns a HealthStatus reflecting the transport connectivity.
7. THE framework SHALL provide a MemoryStoreHealthCheck that checks the availability of a MemoryStore instance by performing a lightweight read operation and returns a HealthStatus reflecting the store availability.
8. THE framework SHALL provide a CircuitBreakerHealthCheck that checks the state of a CircuitBreaker instance and returns a HealthStatus of "degraded" when the circuit breaker is in the OPEN state and "healthy" when in the CLOSED state.
9. THE HealthCheck base class SHALL provide a __repr__ method that includes the class name and health check name.
10. THE HealthCheck base class SHALL provide a __str__ method that returns a human-readable summary including the health check name and check interval.

### Requirement 16: Health Status

**User Story:** As a developer, I want a structured health status object with status classification, detail message, and response time, so that I can inspect component health during debugging and monitoring.

#### Acceptance Criteria

1. THE HealthStatus SHALL contain the check name as a string, a status string (one of "healthy", "degraded", "unhealthy"), an optional detail message string, a response time in seconds as a float, and a timestamp.
2. WHEN a HealthStatus is created without an explicit timestamp, THE HealthStatus SHALL set the timestamp to the current UTC time.
3. THE HealthStatus SHALL expose all fields as read-only properties.
4. WHEN a HealthStatus is created with a status value not in the set of valid status values, THEN THE HealthStatus SHALL raise a SemanticError identifying the invalid status and listing the valid status values.
5. THE HealthStatus SHALL provide an is_healthy read-only property that returns True when the status is "healthy".
6. THE HealthStatus SHALL provide an as_dict method that returns a dictionary representation of the status fields.
7. THE HealthStatus SHALL provide a to_json method that returns a JSON string representation of the status fields.
8. THE HealthStatus SHALL provide a class method from_dict that constructs a HealthStatus from a dictionary.
9. THE HealthStatus SHALL provide a class method from_json that deserializes a JSON string into a HealthStatus instance.
10. FOR ALL valid HealthStatus instances, calling to_json and then from_json SHALL produce an equivalent HealthStatus object (round-trip property).
11. THE HealthStatus SHALL provide a __repr__ method that includes the class name, check name, and status.
12. THE HealthStatus SHALL provide a __str__ method that returns a human-readable summary including the check name, status, detail message, and response time.

### Requirement 17: Health Check Registry

**User Story:** As a developer, I want a registry that tracks all health checks for an agent, so that I can discover, inspect, and manage health checks by name.

#### Acceptance Criteria

1. THE HealthCheckRegistry SHALL support registration of a HealthCheck instance using the health check name as the registration key.
2. IF a HealthCheck with a duplicate name is registered, THEN THE HealthCheckRegistry SHALL raise a SemanticError that includes the duplicate health check name.
3. THE HealthCheckRegistry SHALL support deregistration of a HealthCheck by name.
4. THE HealthCheckRegistry SHALL support lookup of a registered HealthCheck by name, returning the HealthCheck instance or None when the name is not found.
5. THE HealthCheckRegistry SHALL support enumeration of all registered HealthCheck instances as a list.
6. THE HealthCheckRegistry SHALL expose a read-only property for the count of currently registered health checks.
7. THE HealthCheckRegistry SHALL provide a has_health_check method that accepts a name and returns a boolean indicating whether a HealthCheck with the given name is registered.
8. THE HealthCheckRegistry SHALL provide a __repr__ method that includes the class name and the count of registered health checks.
9. THE HealthCheckRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered health check names.

### Requirement 18: Health Monitor

**User Story:** As a developer, I want a health monitor that periodically executes registered health checks and aggregates results into an overall agent health status, so that I can detect and respond to component failures automatically.

#### Acceptance Criteria

1. THE HealthMonitor SHALL accept a HealthCheckRegistry instance and an optional check interval in seconds as a float at construction time, with a default check interval of 30.0.
2. THE HealthMonitor SHALL provide a start method that begins periodic execution of all registered health checks at the configured check interval.
3. THE HealthMonitor SHALL provide a stop method that stops periodic health check execution and releases resources.
4. THE HealthMonitor SHALL provide a check_now method that immediately executes all registered health checks and returns a dictionary of health check names to HealthStatus objects.
5. THE HealthMonitor SHALL expose a read-only property for the most recent HealthStatus result for each registered health check as a dictionary keyed by health check name.
6. THE HealthMonitor SHALL expose a read-only property for the overall agent health status as a string, computed as "healthy" when all checks are healthy, "degraded" when any check is degraded but none are unhealthy, and "unhealthy" when any check is unhealthy.
7. THE HealthMonitor SHALL expose a read-only property for the monitoring status as a boolean indicating whether the monitor is currently active.
8. WHEN a HealthCheck execution raises an exception, THE HealthMonitor SHALL record a HealthStatus with status "unhealthy" and the exception detail as the detail message, and continue executing the remaining health checks.
9. THE HealthMonitor SHALL log each health check result at DEBUG level when the status is "healthy" and at WARNING level when the status is "degraded" or "unhealthy", including the check name, status, and response time, using the logger hierarchy under `ccai.agentkit.resilience`.
10. THE HealthMonitor SHALL provide a __repr__ method that includes the class name, overall health status, and monitoring status.
11. THE HealthMonitor SHALL provide a __str__ method that returns a human-readable summary including the overall health status, check count, and monitoring status.

### Requirement 19: Self-Healing Actions

**User Story:** As a developer, I want pluggable self-healing actions that are triggered when health checks report unhealthy status, so that agents can automatically attempt recovery without manual intervention.

#### Acceptance Criteria

1. THE SelfHealingAction base class SHALL define an abstract interface with a heal method that accepts the health check name and the HealthStatus that triggered the action, and returns a SelfHealingResult.
2. THE SelfHealingAction base class SHALL require all subclasses to provide an implementation for the heal method.
3. THE SelfHealingAction base class SHALL expose a read-only property for the action name as a string.
4. THE framework SHALL provide a ReconnectTransportAction that attempts to disconnect and reconnect a Transport instance when the transport health check reports unhealthy.
5. THE framework SHALL provide a ClearCacheAction that clears cached data in a specified component (such as CredentialManager cache or MemoryStore index) when the corresponding health check reports unhealthy.
6. THE framework SHALL provide a ResetCircuitBreakerAction that resets a CircuitBreaker to the CLOSED state when triggered by a health check indicating the protected service has recovered.
7. THE SelfHealingAction base class SHALL provide a __repr__ method that includes the class name and action name.
8. THE SelfHealingAction base class SHALL provide a __str__ method that returns a human-readable summary including the action name.

### Requirement 20: Self-Healing Policy and Result

**User Story:** As a developer, I want to configure self-healing policies with attempt limits and cooldown intervals, and receive structured results from healing actions, so that self-healing is controlled and observable.

#### Acceptance Criteria

1. THE SelfHealingPolicy SHALL contain the health check name as a string, the SelfHealingAction instance, the maximum consecutive healing attempts as an integer, and the cooldown interval in seconds as a float.
2. THE SelfHealingPolicy SHALL expose all fields as read-only properties.
3. THE SelfHealingPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields, with the SelfHealingAction represented by its action name.
4. THE SelfHealingPolicy SHALL provide a __repr__ method that includes the class name, health check name, and maximum attempts.
5. THE SelfHealingPolicy SHALL provide a __str__ method that returns a human-readable summary including the health check name, action name, maximum attempts, and cooldown interval.
6. THE SelfHealingResult SHALL contain the health check name as a string, the action name as a string, a success flag as a boolean, an optional error message string, the attempt number as an integer, and a timestamp.
7. THE SelfHealingResult SHALL expose all fields as read-only properties.
8. THE SelfHealingResult SHALL provide an is_success read-only property that returns True when the success flag is True.
9. THE SelfHealingResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
10. THE SelfHealingResult SHALL provide a to_json method that returns a JSON string representation of the result fields.
11. THE SelfHealingResult SHALL provide a class method from_dict that constructs a SelfHealingResult from a dictionary.
12. THE SelfHealingResult SHALL provide a class method from_json that deserializes a JSON string into a SelfHealingResult instance.
13. FOR ALL valid SelfHealingResult instances, calling to_json and then from_json SHALL produce an equivalent SelfHealingResult object (round-trip property).
14. THE SelfHealingResult SHALL provide a __repr__ method that includes the class name, health check name, action name, and success flag.
15. THE SelfHealingResult SHALL provide a __str__ method that returns a human-readable summary including the health check name, action name, success flag, and attempt number.
16. WHEN the HealthMonitor detects an unhealthy HealthStatus and a SelfHealingPolicy is registered for the health check, THE HealthMonitor SHALL execute the SelfHealingAction from the policy.
17. WHEN the consecutive healing attempt count for a health check reaches the maximum defined in the SelfHealingPolicy, THE HealthMonitor SHALL stop executing the SelfHealingAction for that health check until the cooldown interval elapses.
18. WHEN the cooldown interval elapses, THE HealthMonitor SHALL reset the consecutive healing attempt count and allow healing attempts to resume.
19. THE HealthMonitor SHALL log each self-healing attempt at INFO level including the health check name, action name, attempt number, and result, using the logger hierarchy under `ccai.agentkit.resilience`.
20. IF a SelfHealingAction raises an exception during execution, THEN THE HealthMonitor SHALL log the exception at WARNING level including the health check name and action name, record a SelfHealingResult with a success flag of False, and continue monitoring.

### Requirement 21: Resilience Configuration

**User Story:** As a developer, I want to configure resilience settings declaratively, so that I can define retry policies, circuit breaker thresholds, degradation behavior, dead letter queue settings, and health monitoring parameters without modifying code.

#### Acceptance Criteria

1. THE ResilienceConfiguration SHALL contain a default RetryPolicy, a circuit breaker enablement flag as a boolean with a default value of True, a degradation management enablement flag as a boolean with a default value of True, a dead letter queue enablement flag as a boolean with a default value of True, a health monitoring enablement flag as a boolean with a default value of True, a health check interval in seconds as a float with a default value of 30.0, and a self-healing enablement flag as a boolean with a default value of True.
2. THE ResilienceConfiguration SHALL support loading configuration from a Python dictionary.
3. THE ResilienceConfiguration SHALL support loading configuration from a JSON file path.
4. THE ResilienceConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE ResilienceConfiguration SHALL resolve the file path relative to the AppContext directory provided by `codecraftai-this-app`.
6. THE ResilienceConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. THE ResilienceConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration.
8. THE ResilienceConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration.
9. THE ResilienceConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration.
10. THE ResilienceConfiguration SHALL provide a class method from_dict that constructs a ResilienceConfiguration from a dictionary.
11. THE ResilienceConfiguration SHALL provide a class method from_json that deserializes a JSON string into a ResilienceConfiguration instance.
12. THE ResilienceConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into a ResilienceConfiguration instance.
13. FOR ALL valid ResilienceConfiguration instances, calling to_json and then from_json SHALL produce an equivalent ResilienceConfiguration object (round-trip property).
14. FOR ALL valid ResilienceConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent ResilienceConfiguration object (round-trip property).
15. THE ResilienceConfiguration SHALL provide a __repr__ method that includes the class name and enablement flags.
16. THE ResilienceConfiguration SHALL provide a __str__ method that returns a human-readable summary of the resilience configuration settings.

### Requirement 22: Resilience Pipeline

**User Story:** As a developer, I want a unified resilience pipeline that coordinates retry, circuit breaker, degradation, dead letter, and health monitoring components, so that all resilience capabilities are managed through a single consistent interface.

#### Acceptance Criteria

1. THE ResiliencePipeline SHALL accept a ResilienceConfiguration at construction time.
2. THE ResiliencePipeline SHALL own and manage a RetryExecutor instance configured with the default RetryPolicy from the ResilienceConfiguration.
3. THE ResiliencePipeline SHALL own and manage a CircuitBreakerRegistry instance when circuit breaker is enabled in the ResilienceConfiguration.
4. THE ResiliencePipeline SHALL own and manage a DegradationManager instance when degradation management is enabled in the ResilienceConfiguration.
5. THE ResiliencePipeline SHALL own and manage a DeadLetterQueue instance when dead letter queue is enabled in the ResilienceConfiguration.
6. THE ResiliencePipeline SHALL own and manage a HealthMonitor instance when health monitoring is enabled in the ResilienceConfiguration.
7. THE ResiliencePipeline SHALL provide an execute_with_resilience method that accepts a callable, an optional operation name, an optional RetryPolicy override, and an optional circuit breaker name, and executes the callable with retry logic and circuit breaker protection, returning the operation result.
8. WHEN the execute_with_resilience method exhausts all retry attempts and the operation permanently fails, THE ResiliencePipeline SHALL enqueue the failed operation in the DeadLetterQueue when dead letter queue is enabled.
9. WHEN the execute_with_resilience method encounters a failure and a DegradationPolicy is registered for the operation, THE ResiliencePipeline SHALL apply the DegradationStrategy and return the fallback result.
10. THE ResiliencePipeline SHALL expose read-only properties for the RetryExecutor, CircuitBreakerRegistry, DegradationManager, DeadLetterQueue, and HealthMonitor instances.
11. THE ResiliencePipeline SHALL provide a __repr__ method that includes the class name and the enablement status of each component.
12. THE ResiliencePipeline SHALL provide a __str__ method that returns a human-readable summary of the pipeline configuration and component status.

### Requirement 23: Agent Resilience Integration

**User Story:** As a developer, I want agents to own a resilience pipeline and apply resilience policies throughout their lifecycle, so that all agent operations benefit from retry, circuit breaker, degradation, dead letter, and health monitoring capabilities.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only resilience property that returns the Agent's ResiliencePipeline instance.
2. THE Agent base class SHALL expose a read-only health_monitor property that returns the Agent's HealthMonitor instance from the ResiliencePipeline.
3. THE Agent base class SHALL expose a read-only circuit_breakers property that returns the Agent's CircuitBreakerRegistry instance from the ResiliencePipeline.
4. THE Agent base class SHALL expose a read-only dead_letter_queue property that returns the Agent's DeadLetterQueue instance from the ResiliencePipeline.
5. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL initialize the ResiliencePipeline using the ResilienceConfiguration from the Agent's configuration.
6. WHEN an Agent transitions to the RUNNING state, THE Agent SHALL start the HealthMonitor if health monitoring is enabled.
7. WHEN an Agent transitions to the STOPPED state, THE Agent SHALL stop the HealthMonitor and release resilience resources.
8. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all ResiliencePlugin instances from `codecraftai-extension` ExtensionPoint entries targeting the Agent.
9. THE Agent base class SHALL provide an execute_resilient method that accepts a callable, an optional operation name, an optional RetryPolicy, and an optional circuit breaker name, and delegates to the ResiliencePipeline execute_with_resilience method.

### Requirement 24: Resilience Plugin Integration

**User Story:** As a developer, I want to distribute resilience components as plugins through `codecraftai-extension`, so that custom degradation strategies, health checks, self-healing actions, and dead letter stores can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "ccai.agentkit.resilience" through `codecraftai-extension` for registering ResiliencePlugin implementations.
2. WHEN an Agent is initialized, THE Agent SHALL query the "ccai.agentkit.resilience" ExtensionPoint and register all discovered HealthCheck, DegradationStrategy, SelfHealingAction, and DeadLetterStore instances with the appropriate registries in the ResiliencePipeline.
3. IF a ResiliencePlugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
4. IF a ResiliencePlugin provides a component with a name that conflicts with an already registered component, THEN THE Agent SHALL log the conflict at WARNING level including both component names and skip the conflicting plugin component.

### Requirement 25: Resilience Exception Hierarchy

**User Story:** As a developer, I want well-defined exception types for resilience failures, so that I can diagnose and handle circuit breaker rejections and resilience errors precisely.

#### Acceptance Criteria

1. THE CircuitBreakerOpenError SHALL inherit from AgentKitError and SHALL be raised when a request is rejected because the CircuitBreaker is in the OPEN state.
2. THE CircuitBreakerOpenError SHALL contain the circuit breaker name, the service name, and the time remaining in seconds until the next half-open test.
3. THE ResilienceError SHALL inherit from AgentKitError and SHALL be raised when a resilience operation fails due to a configuration or execution error.
4. THE ResilienceError SHALL contain a descriptive message and an optional cause exception.
5. ALL resilience-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name and descriptive message.

### Requirement 26: Resilience Observability Integration

**User Story:** As a developer, I want resilience events to be traced, logged, and metered through the observability system, so that I can monitor retry rates, circuit breaker state changes, degradation events, dead letter queue depth, and health check results.

#### Acceptance Criteria

1. THE ResiliencePipeline SHALL use the Python standard logging module with a logger hierarchy under `ccai.agentkit.resilience`.
2. WHEN a retry attempt occurs, THE RetryExecutor SHALL log at INFO level including the operation name, attempt number, delay, and exception type.
3. WHEN a circuit breaker state transition occurs, THE CircuitBreaker SHALL log at WARNING level including the circuit breaker name, previous state, new state, and reason.
4. WHEN a degradation level change occurs, THE DegradationManager SHALL log at WARNING level including the dependency name, previous level, new level, and reason.
5. WHEN an operation is enqueued in the dead letter queue, THE DeadLetterQueue SHALL log at WARNING level including the operation type, source component, and exception type.
6. WHEN a health check reports a non-healthy status, THE HealthMonitor SHALL log at WARNING level including the check name, status, and detail message.
7. WHEN a self-healing action is executed, THE HealthMonitor SHALL log at INFO level including the health check name, action name, and result.
8. THE ResiliencePipeline SHALL record the following metrics through the MetricsCollector when observability is available: retry attempt count (counter), circuit breaker state change count (counter), dead letter queue depth (gauge), health check result count by status (counter), and self-healing attempt count (counter).

### Requirement 27: Resilience String Representations

**User Story:** As a developer, I want meaningful string representations on all resilience system classes, so that I can quickly inspect resilience state during debugging sessions.

#### Acceptance Criteria

1. THE RetryExecutor SHALL provide a __repr__ method that includes the class name, maximum retry count, and backoff strategy.
2. THE RetryExecutor SHALL provide a __str__ method that returns a human-readable summary of the retry configuration.
3. THE CircuitBreaker SHALL provide a __repr__ method that includes the class name, circuit breaker name, and current state.
4. THE CircuitBreaker SHALL provide a __str__ method that returns a human-readable summary including the circuit breaker name, current state, failure count, and success count.
5. THE DegradationManager SHALL provide a __repr__ method that includes the class name, agent identifier, and current overall degradation level.
6. THE DegradationManager SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, overall degradation level, and count of tracked dependencies.
7. THE DeadLetterQueue SHALL provide a __repr__ method that includes the class name and entry count.
8. THE DeadLetterQueue SHALL provide a __str__ method that returns a human-readable summary including the entry count and store type.
9. THE HealthMonitor SHALL provide a __repr__ method that includes the class name, overall health status, and monitoring status.
10. THE HealthMonitor SHALL provide a __str__ method that returns a human-readable summary including the overall health status, check count, and monitoring status.
11. THE ResiliencePipeline SHALL provide a __repr__ method that includes the class name and the enablement status of each component.
12. THE ResiliencePipeline SHALL provide a __str__ method that returns a human-readable summary of the pipeline configuration and component status.
