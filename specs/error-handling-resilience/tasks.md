# Implementation Plan: Error Handling & Resilience

## Overview

Implement the Error Handling & Resilience feature for the `automojo-agent-kit` SDK. The implementation follows a bottom-up approach: data models and enums first, then core components (retry, circuit breaker, degradation, dead letter, health), then the coordination layer (ResiliencePipeline), and finally Agent integration. All source files go under `source/packages/automojo/agentkit/` with lowercase filenames. Tests go under `source/testroots/automojo/tests/singlehost/agentkit/resilience/`.

## Tasks

- [x] 1. Implement resilience error types and enums
  - [x] 1.1 Create `resilienceerrors.py` with CircuitBreakerOpenError and ResilienceError
    - CircuitBreakerOpenError inherits from AgentKitError with circuit_breaker_name, service_name, time_remaining properties
    - ResilienceError inherits from AgentKitError with message and optional cause properties
    - Both provide __repr__ methods
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

  - [x] 1.2 Create `circuitbreakerstate.py` with CircuitBreakerState enum
    - Define CLOSED, OPEN, HALF_OPEN values
    - Implement from_string class method that raises SemanticError for invalid values
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 1.3 Create `degradationlevel.py` with DegradationLevel enum
    - Define NORMAL, DEGRADED, CRITICAL values
    - Implement from_string class method that raises SemanticError for invalid values
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 1.4 Write unit tests for resilience errors and enums
    - Create `test_resilienceerrors.py` testing CircuitBreakerOpenError and ResilienceError construction, properties, __repr__
    - Create `test_circuitbreakerstate.py` testing enum values and from_string (valid and invalid)
    - Create `test_degradationlevel.py` testing enum values and from_string (valid and invalid)
    - _Requirements: 25.1–25.5, 4.1–4.3, 8.1–8.3_

  - [x] 1.5 Write property test for CircuitBreakerState from_string round-trip
    - **Property 14: CircuitBreakerState from_string round-trip**
    - **Validates: Requirements 4.2**

  - [x] 1.6 Write property test for DegradationLevel from_string round-trip
    - **Property 19: DegradationLevel from_string round-trip**
    - **Validates: Requirements 8.2**

- [x] 2. Implement retry data models (RetryAttempt and RetryResult)
  - [x] 2.1 Create `retryattempt.py` with RetryAttempt class
    - Immutable object with attempt_number, delay, exception, timestamp properties
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 2.2 Create `retryresult.py` with RetryResult class
    - Immutable object with success, result, exception, attempts, elapsed_time properties
    - Implement is_success and attempt_count computed properties (attempt_count = len(attempts) + 1)
    - Implement as_dict, to_json, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18, 2.19_

  - [x] 2.3 Write unit tests for RetryAttempt and RetryResult
    - Create `test_retryattempt.py` testing construction, properties, serialization, __repr__, __str__
    - Create `test_retryresult.py` testing construction, properties, is_success, attempt_count, serialization
    - _Requirements: 2.1–2.19_

  - [x] 2.4 Write property test for RetryAttempt JSON round-trip
    - **Property 1: RetryAttempt JSON round-trip**
    - **Validates: Requirements 2.7**

  - [x] 2.5 Write property test for RetryResult JSON round-trip
    - **Property 2: RetryResult JSON round-trip**
    - **Validates: Requirements 2.17**

  - [x] 2.6 Write property test for RetryResult attempt_count consistency
    - **Property 6: RetryResult attempt_count consistency**
    - **Validates: Requirements 2.13**

- [x] 3. Implement RetryExecutor
  - [x] 3.1 Create `retryexecutor.py` with RetryExecutor class
    - Accept RetryPolicy at construction, expose as read-only property
    - Implement execute method: invoke callable, retry on retryable exceptions with delay, raise non-retryable immediately
    - Record RetryAttempt for each failed attempt, return RetryResult with success/failure outcome
    - Log each retry attempt at INFO level under `automojo.agentkit.resilience`
    - Implement __repr__ and __str__ methods
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 27.1, 27.2_

  - [x] 3.2 Write unit tests for RetryExecutor
    - Create `test_retryexecutor.py` testing success path, retryable failure path, non-retryable exception, exhausted retries, logging
    - _Requirements: 1.1–1.11_

  - [x] 3.3 Write property test for RetryExecutor success path
    - **Property 3: RetryExecutor success path**
    - **Validates: Requirements 1.5**

  - [x] 3.4 Write property test for RetryExecutor failure path with exhausted retries
    - **Property 4: RetryExecutor failure path with exhausted retries**
    - **Validates: Requirements 1.6, 1.7**

  - [x] 3.5 Write property test for RetryExecutor non-retryable exception propagation
    - **Property 5: RetryExecutor non-retryable exception propagation**
    - **Validates: Requirements 1.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement circuit breaker data models
  - [x] 5.1 Create `circuitbreakerconfiguration.py` with CircuitBreakerConfiguration class
    - Immutable object with failure_threshold, success_threshold, open_state_timeout, half_open_max_attempts, monitored_exception_types
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12_

  - [x] 5.2 Create `circuitbreakerevent.py` with CircuitBreakerEvent class
    - Immutable object with name, previous_state, new_state, reason, timestamp
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

  - [x] 5.3 Write unit tests for circuit breaker data models
    - Create `test_circuitbreakerconfiguration.py` testing construction, properties, serialization
    - Create `test_circuitbreakerevent.py` testing construction, properties, serialization
    - _Requirements: 4.4–4.12, 5.1–5.9_

  - [x] 5.4 Write property test for CircuitBreakerConfiguration JSON round-trip
    - **Property 7: CircuitBreakerConfiguration JSON round-trip**
    - **Validates: Requirements 4.10**

  - [x] 5.5 Write property test for CircuitBreakerEvent JSON round-trip
    - **Property 8: CircuitBreakerEvent JSON round-trip**
    - **Validates: Requirements 5.7**

- [x] 6. Implement CircuitBreaker and CircuitBreakerRegistry
  - [x] 6.1 Create `circuitbreaker.py` with CircuitBreaker class
    - Thread-safe state machine with CLOSED, OPEN, HALF_OPEN states using threading.Lock
    - Implement execute method: evaluate state, execute or reject, track success/failure, trigger transitions
    - Record CircuitBreakerEvent for each state transition
    - Implement reset method to return to CLOSED and clear counters/events
    - Log state transitions at WARNING level under `automojo.agentkit.resilience`
    - Implement __repr__ and __str__ methods
    - _Requirements: 3.1–3.20, 27.3, 27.4_

  - [x] 6.2 Create `circuitbreakerregistry.py` with CircuitBreakerRegistry class
    - Dictionary-based registry with register, deregister, lookup, list_all, has_circuit_breaker, reset_all
    - Raise SemanticError on duplicate name registration
    - Implement count property, __repr__ and __str__ methods
    - _Requirements: 6.1–6.10_

  - [x] 6.3 Write unit tests for CircuitBreaker
    - Create `test_circuitbreaker.py` testing initial state, CLOSED-to-OPEN transition, OPEN rejection, HALF_OPEN recovery, reset, thread safety, event recording
    - _Requirements: 3.1–3.20_

  - [x] 6.4 Write unit tests for CircuitBreakerRegistry
    - Create `test_circuitbreakerregistry.py` testing register, deregister, lookup, list_all, count, has_circuit_breaker, reset_all, duplicate name error
    - _Requirements: 6.1–6.10_

  - [x] 6.5 Write property test for CircuitBreaker initial state is CLOSED
    - **Property 9: CircuitBreaker initial state is CLOSED**
    - **Validates: Requirements 3.2**

  - [x] 6.6 Write property test for CircuitBreaker CLOSED-to-OPEN transition on failure threshold
    - **Property 10: CircuitBreaker CLOSED-to-OPEN transition on failure threshold**
    - **Validates: Requirements 3.5**

  - [x] 6.7 Write property test for CircuitBreaker OPEN state rejects all requests
    - **Property 11: CircuitBreaker OPEN state rejects all requests**
    - **Validates: Requirements 3.6**

  - [x] 6.8 Write property test for CircuitBreaker reset returns to CLOSED
    - **Property 12: CircuitBreaker reset returns to CLOSED**
    - **Validates: Requirements 3.16**

  - [x] 6.9 Write property test for CircuitBreaker event count matches transition count
    - **Property 13: CircuitBreaker event count matches transition count**
    - **Validates: Requirements 3.11**

  - [x] 6.10 Write property test for CircuitBreakerRegistry register-lookup consistency
    - **Property 15: CircuitBreakerRegistry register-lookup consistency**
    - **Validates: Requirements 6.1, 6.4**

  - [x] 6.11 Write property test for CircuitBreakerRegistry count consistency
    - **Property 16: CircuitBreakerRegistry count consistency**
    - **Validates: Requirements 6.5, 6.6**

  - [x] 6.12 Write property test for CircuitBreakerRegistry has_circuit_breaker consistency
    - **Property 17: CircuitBreakerRegistry has_circuit_breaker consistency**
    - **Validates: Requirements 6.3, 6.7**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement degradation system
  - [x] 8.1 Create `degradationstrategy.py` with DegradationStrategy abstract base class
    - Abstract degrade method accepting dependency_name, exception, optional context dict
    - Read-only strategy_name property, __repr__ and __str__ methods
    - _Requirements: 7.1, 7.2, 7.3, 7.7, 7.8_

  - [x] 8.2 Create `cachedresultstrategy.py` with CachedResultStrategy class
    - Extends DegradationStrategy with cache_result and degrade methods
    - Returns most recently cached successful result for the dependency
    - _Requirements: 7.4_

  - [x] 8.3 Create `defaultvaluestrategy.py` with DefaultValueStrategy class
    - Extends DegradationStrategy, returns configured default_value from degrade method
    - _Requirements: 7.5_

  - [x] 8.4 Create `alternateproviderstrategy.py` with AlternateProviderStrategy class
    - Extends DegradationStrategy, invokes alternate_callable from degrade method
    - _Requirements: 7.6_

  - [x] 8.5 Create `degradationpolicy.py` with DegradationPolicy class
    - Immutable object with dependency_name, strategy, activation_level, fallback_value
    - Implement as_dict, to_json, from_dict (accepting strategy parameter) methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10_

  - [x] 8.6 Create `degradationchangeevent.py` with DegradationChangeEvent class
    - Immutable object with dependency_name, previous_level, new_level, reason, timestamp
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

  - [x] 8.7 Create `degradationmanager.py` with DegradationManager class
    - Accept agent_identifier at construction
    - Implement register_policy, deregister_policy, report_failure, report_recovery methods
    - Track per-dependency DegradationLevel, compute overall_level as maximum across all dependencies
    - Support DegradationChangeListener registration and notification (catch listener exceptions, log at WARNING)
    - Log degradation level changes at WARNING level under `automojo.agentkit.resilience`
    - Implement __repr__ and __str__ methods
    - _Requirements: 9.1–9.13, 27.5, 27.6_

  - [x] 8.8 Write unit tests for degradation strategies
    - Create `test_degradationstrategy.py` testing CachedResultStrategy, DefaultValueStrategy, AlternateProviderStrategy
    - _Requirements: 7.1–7.8_

  - [x] 8.9 Write unit tests for DegradationPolicy and DegradationChangeEvent
    - Create `test_degradationpolicy.py` testing construction, properties, serialization
    - Create `test_degradationchangeevent.py` testing construction, properties, serialization
    - _Requirements: 8.4–8.10, 10.1–10.9_

  - [x] 8.10 Write unit tests for DegradationManager
    - Create `test_degradationmanager.py` testing register/deregister policy, report_failure, report_recovery, listener notification, listener exception handling
    - _Requirements: 9.1–9.13_

  - [x] 8.11 Write property test for DegradationChangeEvent JSON round-trip
    - **Property 18: DegradationChangeEvent JSON round-trip**
    - **Validates: Requirements 10.7**

  - [x] 8.12 Write property test for DegradationManager overall level is maximum
    - **Property 20: DegradationManager overall level is maximum**
    - **Validates: Requirements 9.6**

  - [x] 8.13 Write property test for DefaultValueStrategy returns configured default
    - **Property 21: DefaultValueStrategy returns configured default**
    - **Validates: Requirements 7.5**

  - [x] 8.14 Write property test for CachedResultStrategy returns cached result
    - **Property 22: CachedResultStrategy returns cached result**
    - **Validates: Requirements 7.4**

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement dead letter system
  - [x] 10.1 Create `deadletterentry.py` with DeadLetterEntry class
    - Immutable object with identifier (auto-generated UUID), operation_type, payload, exception_info, retry_attempts, source_component, agent_identifier, timestamp (auto-generated UTC), metadata
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11_

  - [x] 10.2 Create `deadletterquery.py` with DeadLetterQuery and DeadLetterQueryResult classes
    - DeadLetterQuery: optional filters for operation_type, source_component, agent_identifier, start_time, end_time, max_results
    - DeadLetterQueryResult: entries list and total_count
    - Both implement as_dict, __repr__, __str__ methods
    - _Requirements: 14.1–14.13_

  - [x] 10.3 Create `deadletterstore.py` with DeadLetterStore abstract base class
    - Abstract methods: store, retrieve, search, delete, purge, count
    - Read-only store_name property, __repr__ and __str__ methods
    - _Requirements: 13.1, 13.2, 13.3, 13.12, 13.13_

  - [x] 10.4 Create `inmemorydeadletterstore.py` with InMemoryDeadLetterStore class
    - Dictionary-based storage implementing all DeadLetterStore methods
    - Support DeadLetterQuery filtering by operation_type, source_component, agent_identifier, time range, max_results
    - _Requirements: 13.4_

  - [x] 10.5 Create `filedeadletterstore.py` with FileDeadLetterStore class
    - JSON file persistence with one file per entry using entry identifier as filename
    - Create directory at construction if it does not exist
    - Raise ResilienceError on file I/O failures
    - _Requirements: 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11_

  - [x] 10.6 Create `deadletterqueue.py` with DeadLetterQueue class
    - Accept DeadLetterStore at construction
    - Implement enqueue (creates DeadLetterEntry and stores), query, get_entry, replay, purge methods
    - Replay: retrieve entry, invoke callable with payload, remove on success, update metadata on failure
    - Log enqueue at WARNING level under `automojo.agentkit.resilience`
    - Implement entry_count property, __repr__ and __str__ methods
    - _Requirements: 11.1–11.12, 27.7, 27.8_

  - [x] 10.7 Write unit tests for DeadLetterEntry
    - Create `test_deadletterentry.py` testing construction, auto-generated identifier/timestamp, properties, serialization
    - _Requirements: 12.1–12.11_

  - [x] 10.8 Write unit tests for DeadLetterQuery and DeadLetterQueryResult
    - Create `test_deadletterquery.py` testing construction, filtering, as_dict, __repr__, __str__
    - _Requirements: 14.1–14.13_

  - [x] 10.9 Write unit tests for InMemoryDeadLetterStore
    - Create `test_inmemorydeadletterstore.py` testing store, retrieve, search, delete, purge, count
    - _Requirements: 13.4_

  - [x] 10.10 Write unit tests for FileDeadLetterStore
    - Create `test_filedeadletterstore.py` testing file persistence, directory creation, I/O error handling
    - _Requirements: 13.5–13.11_

  - [x] 10.11 Write unit tests for DeadLetterQueue
    - Create `test_deadletterqueue.py` testing enqueue, query, get_entry, replay (success and failure), purge, logging
    - _Requirements: 11.1–11.12_

  - [x] 10.12 Write property test for DeadLetterEntry JSON round-trip
    - **Property 23: DeadLetterEntry JSON round-trip**
    - **Validates: Requirements 12.9**

  - [x] 10.13 Write property test for DeadLetterEntry auto-generates identifier and timestamp
    - **Property 24: DeadLetterEntry auto-generates identifier and timestamp**
    - **Validates: Requirements 12.2, 12.3**

  - [x] 10.14 Write property test for InMemoryDeadLetterStore store-retrieve consistency
    - **Property 25: InMemoryDeadLetterStore store-retrieve consistency**
    - **Validates: Requirements 13.4**

  - [x] 10.15 Write property test for DeadLetterQueue enqueue increases count
    - **Property 26: DeadLetterQueue enqueue increases count**
    - **Validates: Requirements 11.9**

  - [x] 10.16 Write property test for DeadLetterQuery filtering correctness
    - **Property 27: DeadLetterQuery filtering correctness**
    - **Validates: Requirements 14.1**

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement health check system
  - [x] 12.1 Create `healthstatus.py` with HealthStatus class
    - Immutable object with check_name, status (validated against VALID_STATUSES), detail, response_time, timestamp
    - Raise SemanticError for invalid status values
    - Implement is_healthy property, as_dict, to_json, from_dict, from_json methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10, 16.11, 16.12_

  - [x] 12.2 Create `healthcheck.py` with HealthCheck abstract base class
    - Abstract check method returning HealthStatus
    - Read-only name and check_interval properties (default check_interval 30.0)
    - Implement __repr__ and __str__ methods
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.9, 15.10_

  - [x] 12.3 Create `transporthealthcheck.py` with TransportHealthCheck class
    - Extends HealthCheck, checks Transport connection status
    - _Requirements: 15.6_

  - [x] 12.4 Create `memorystorehealthcheck.py` with MemoryStoreHealthCheck class
    - Extends HealthCheck, checks MemoryStore availability via lightweight read
    - _Requirements: 15.7_

  - [x] 12.5 Create `circuitbreakerhealthcheck.py` with CircuitBreakerHealthCheck class
    - Extends HealthCheck, returns "degraded" when CircuitBreaker is OPEN, "healthy" when CLOSED
    - _Requirements: 15.8_

  - [x] 12.6 Create `healthcheckregistry.py` with HealthCheckRegistry class
    - Dictionary-based registry with register, deregister, lookup, list_all, has_health_check
    - Raise SemanticError on duplicate name registration
    - Implement count property, __repr__ and __str__ methods
    - _Requirements: 17.1–17.9_

  - [x] 12.7 Write unit tests for HealthStatus
    - Create `test_healthstatus.py` testing construction, invalid status, is_healthy, serialization
    - _Requirements: 16.1–16.12_

  - [x] 12.8 Write unit tests for health checks
    - Create `test_healthcheck.py` testing TransportHealthCheck, MemoryStoreHealthCheck, CircuitBreakerHealthCheck using mocks
    - _Requirements: 15.1–15.10_

  - [x] 12.9 Write unit tests for HealthCheckRegistry
    - Create `test_healthcheckregistry.py` testing register, deregister, lookup, list_all, count, has_health_check, duplicate name error
    - _Requirements: 17.1–17.9_

  - [x] 12.10 Write property test for HealthStatus JSON round-trip
    - **Property 28: HealthStatus JSON round-trip**
    - **Validates: Requirements 16.10**

  - [x] 12.11 Write property test for HealthStatus is_healthy consistency
    - **Property 29: HealthStatus is_healthy consistency**
    - **Validates: Requirements 16.5**

  - [x] 12.12 Write property test for HealthCheckRegistry register-lookup consistency
    - **Property 30: HealthCheckRegistry register-lookup consistency**
    - **Validates: Requirements 17.1, 17.4**

  - [x] 12.13 Write property test for HealthCheckRegistry count consistency
    - **Property 31: HealthCheckRegistry count consistency**
    - **Validates: Requirements 17.5, 17.6**

- [x] 13. Implement self-healing system
  - [x] 13.1 Create `selfhealingaction.py` with SelfHealingAction abstract base class
    - Abstract heal method accepting check_name and HealthStatus, returning SelfHealingResult
    - Read-only action_name property, __repr__ and __str__ methods
    - _Requirements: 19.1, 19.2, 19.3, 19.7, 19.8_

  - [x] 13.2 Create `reconnecttransportaction.py` with ReconnectTransportAction class
    - Extends SelfHealingAction, disconnects and reconnects a Transport instance
    - _Requirements: 19.4_

  - [x] 13.3 Create `clearcacheaction.py` with ClearCacheAction class
    - Extends SelfHealingAction, invokes cache_clear_callable
    - _Requirements: 19.5_

  - [x] 13.4 Create `resetcircuitbreakeraction.py` with ResetCircuitBreakerAction class
    - Extends SelfHealingAction, resets a CircuitBreaker to CLOSED state
    - _Requirements: 19.6_

  - [x] 13.5 Create `selfhealingpolicy.py` with SelfHealingPolicy class
    - Immutable object with check_name, action, max_attempts, cooldown_interval
    - Implement as_dict, __repr__ and __str__ methods
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

  - [x] 13.6 Create `selfhealingresult.py` with SelfHealingResult class
    - Immutable object with check_name, action_name, success, error_message, attempt_number, timestamp
    - Implement is_success property, as_dict, to_json, from_dict, from_json methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 20.6, 20.7, 20.8, 20.9, 20.10, 20.11, 20.12, 20.13, 20.14, 20.15_

  - [x] 13.7 Write unit tests for self-healing actions
    - Create `test_healthcheck.py` (extend) or separate files testing ReconnectTransportAction, ClearCacheAction, ResetCircuitBreakerAction using mocks
    - _Requirements: 19.1–19.8_

  - [x] 13.8 Write unit tests for SelfHealingPolicy and SelfHealingResult
    - Create `test_selfhealingpolicy.py` testing construction, properties, as_dict
    - Create `test_selfhealingresult.py` testing construction, properties, is_success, serialization
    - _Requirements: 20.1–20.15_

  - [x] 13.9 Write property test for SelfHealingResult JSON round-trip
    - **Property 33: SelfHealingResult JSON round-trip**
    - **Validates: Requirements 20.13**

- [x] 14. Implement HealthMonitor
  - [x] 14.1 Create `healthmonitor.py` with HealthMonitor class
    - Accept HealthCheckRegistry and optional check_interval (default 30.0)
    - Implement start, stop, check_now methods
    - Track latest_results per check, compute overall_status (healthy/degraded/unhealthy)
    - Integrate SelfHealingPolicy: register_healing_policy, execute healing on unhealthy status
    - Enforce max_attempts and cooldown_interval from SelfHealingPolicy
    - Catch HealthCheck.check() exceptions as unhealthy HealthStatus, catch SelfHealingAction.heal() exceptions as failed SelfHealingResult
    - Log health check results at DEBUG (healthy) / WARNING (degraded/unhealthy), self-healing at INFO, healing exceptions at WARNING
    - Implement is_active property, __repr__ and __str__ methods
    - _Requirements: 18.1–18.11, 20.16–20.20, 26.6, 26.7, 27.9, 27.10_

  - [x] 14.2 Write unit tests for HealthMonitor
    - Create `test_healthmonitor.py` testing check_now, overall_status computation, self-healing trigger, max_attempts/cooldown, exception handling
    - _Requirements: 18.1–18.11, 20.16–20.20_

  - [x] 14.3 Write property test for HealthMonitor overall status computation
    - **Property 32: HealthMonitor overall status computation**
    - **Validates: Requirements 18.6**

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement ResilienceConfiguration
  - [x] 16.1 Create `resilienceconfiguration.py` with ResilienceConfiguration class
    - Accept default_retry_policy and enablement flags with defaults (all True, health_check_interval 30.0)
    - Implement as_dict, to_json, to_yaml, from_dict, from_json, from_yaml methods
    - Validate required fields during loading, raise ConfigurationError on missing fields
    - Implement __repr__ and __str__ methods
    - _Requirements: 21.1–21.16_

  - [x] 16.2 Write unit tests for ResilienceConfiguration
    - Create `test_resilienceconfiguration.py` testing construction, defaults, serialization (JSON and YAML), validation errors
    - _Requirements: 21.1–21.16_

  - [x] 16.3 Write property test for ResilienceConfiguration JSON round-trip
    - **Property 34: ResilienceConfiguration JSON round-trip**
    - **Validates: Requirements 21.13**

  - [x] 16.4 Write property test for ResilienceConfiguration YAML round-trip
    - **Property 35: ResilienceConfiguration YAML round-trip**
    - **Validates: Requirements 21.14**

- [x] 17. Implement ResiliencePipeline
  - [x] 17.1 Create `resiliencepipeline.py` with ResiliencePipeline class
    - Accept ResilienceConfiguration and agent_identifier at construction
    - Initialize RetryExecutor, CircuitBreakerRegistry, DegradationManager, DeadLetterQueue, HealthMonitor based on configuration enablement flags
    - Implement execute_with_resilience method coordinating circuit breaker check, retry execution, degradation fallback, and dead letter enqueue
    - Expose read-only properties for all managed components
    - Implement __repr__ and __str__ methods
    - _Requirements: 22.1–22.12, 27.11, 27.12_

  - [x] 17.2 Write unit tests for ResiliencePipeline
    - Create `test_resiliencepipeline.py` testing component initialization based on config flags, execute_with_resilience success/failure/circuit-breaker/degradation/dead-letter paths
    - _Requirements: 22.1–22.12_

- [x] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Implement Agent resilience integration
  - [x] 19.1 Extend Agent base class with resilience properties and methods
    - Add resilience, health_monitor, circuit_breakers, dead_letter_queue read-only properties
    - Add execute_resilient method delegating to ResiliencePipeline.execute_with_resilience
    - Wire ResiliencePipeline initialization into Agent.initialize() (INITIALIZED state transition)
    - Wire HealthMonitor start into Agent.start() (RUNNING state transition)
    - Wire HealthMonitor stop and resource release into Agent.stop() (STOPPED state transition)
    - Discover and register ResiliencePlugin instances from ExtensionPoint "automojo.agentkit.resilience" during initialization
    - _Requirements: 23.1–23.9, 24.1–24.4_

  - [x] 19.2 Write unit tests for Agent resilience integration
    - Test resilience property access, execute_resilient delegation, lifecycle integration (initialize/start/stop), plugin discovery
    - _Requirements: 23.1–23.9, 24.1–24.4_

- [x] 20. Implement resilience observability integration
  - [x] 20.1 Add logging and metrics integration across all resilience components
    - Ensure RetryExecutor logs at INFO for retry attempts (operation name, attempt number, delay, exception type)
    - Ensure CircuitBreaker logs at WARNING for state transitions
    - Ensure DegradationManager logs at WARNING for level changes
    - Ensure DeadLetterQueue logs at WARNING for enqueue operations
    - Ensure HealthMonitor logs at DEBUG/WARNING for check results and INFO for self-healing
    - Add MetricsCollector integration when observability is available (retry count, CB state changes, DLQ depth, health check counts, self-healing counts)
    - _Requirements: 26.1–26.8_

  - [x] 20.2 Write unit tests for resilience observability
    - Verify logging output at correct levels for each component
    - _Requirements: 26.1–26.8_

- [x] 21. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and error conditions
- All source files use lowercase filenames with no underscores under `source/packages/automojo/agentkit/`
- All test files go under `source/testroots/automojo/tests/singlehost/agentkit/resilience/`
- Tests use the `testbase` framework and `automojo.testbase.mocking` for mocks
- Run tests with: `source .venv/bin/activate && testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost.agentkit.resilience --output=./.output`
