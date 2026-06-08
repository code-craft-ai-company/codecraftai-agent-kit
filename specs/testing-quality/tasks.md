# Implementation Plan: Testing & Quality

## Overview

Implement the Testing & Quality feature for the `codecraftai-agent-kit` SDK. The implementation follows a bottom-up approach: error types and configuration first, then mock providers, then core test fixtures and assertions, then execution trace recording and replay, then invariant system, and finally platform test harnesses. All source files go under `source/packages/ccai/agentkit/testing/` with lowercase filenames (no underscores). Tests go under `source/testroots/ccai/tests/singlehost/agentkit/testing/`, mirroring the source hierarchy.

## Tasks

- [ ] 1. Implement testing error hierarchy and testing configuration
  - [ ] 1.1 Create `testing/errors.py` with TestingError, ReplayMismatchError, and InvariantViolationError
    - TestingError inherits from AgentKitError with message and optional cause properties
    - ReplayMismatchError inherits from TestingError with expected_event_type, actual_event_type, sequence_number properties
    - InvariantViolationError inherits from TestingError with invariant_name and counterexample properties
    - All provide __repr__ methods per coding standards
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7_

  - [ ] 1.2 Create `testing/testingconfiguration.py` with TestingConfiguration class
    - Immutable object with default_mock_latency, default_replay_strict_ordering, default_invariant_max_examples, default_platform_harness_type
    - Implement as_dict, to_json, from_dict, from_json, from_json_file methods
    - Raise ConfigurationError on invalid field values
    - Implement __repr__ and __str__ methods
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 24.9, 24.10, 24.11, 24.12_

  - [ ] 1.3 Create `testing/__init__.py` package init exporting public API
    - _Requirements: N/A (infrastructure)_

  - [ ]* 1.4 Write unit tests for testing error hierarchy
    - Create `testing/test_errors.py` testing TestingError construction, cause chaining, __repr__
    - Test ReplayMismatchError construction, properties, error message format
    - Test InvariantViolationError construction, properties, error message format
    - _Requirements: 23.1–23.7_

  - [ ]* 1.5 Write unit tests for TestingConfiguration
    - Create `testing/test_testingconfiguration.py` testing construction, defaults, read-only properties
    - Test as_dict, to_json, from_dict, from_json round-trip serialization
    - Test from_json_file loading
    - Test ConfigurationError on invalid values
    - Test __repr__ and __str__ output
    - _Requirements: 24.1–24.12_

- [ ] 2. Implement mock credential, data profile, and embedding providers
  - [ ] 2.1 Create `testing/mocks/__init__.py` package init
    - _Requirements: N/A (infrastructure)_

  - [ ] 2.2 Create `testing/mocks/mockcredentialprovider.py` with MockCredentialProvider class
    - Accept credentials dictionary at construction
    - Implement resolve, add_credential, remove_credential methods
    - Raise ConfigurationError on unresolvable credential name
    - Record all resolve calls, expose resolved_names property
    - Implement __repr__ and __str__ methods
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9_

  - [ ] 2.3 Create `testing/mocks/mockdataprofileprovider.py` with MockDataProfileProvider class
    - Accept profiles dictionary at construction
    - Implement resolve, add_profile, remove_profile methods
    - Raise ConfigurationError on unresolvable data profile name
    - Record all resolve calls, expose resolved_names property
    - Implement __repr__ and __str__ methods
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_

  - [ ] 2.4 Create `testing/mocks/mockembeddingprovider.py` with MockEmbeddingProvider class
    - Accept optional dimension (default 128) and explicit text-to-embedding mappings
    - Implement embed method returning deterministic vectors based on text hash
    - Record all embed calls, expose embed_count property
    - Implement reset, __repr__, __str__ methods
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9_

  - [ ]* 2.5 Write unit tests for MockCredentialProvider
    - Create `testing/mocks/test_mockcredentialprovider.py` testing resolve, add_credential, remove_credential
    - Test ConfigurationError on missing credential name
    - Test resolve call recording and resolved_names property
    - Test __repr__ and __str__ output
    - _Requirements: 8.1–8.9_

  - [ ]* 2.6 Write unit tests for MockDataProfileProvider
    - Create `testing/mocks/test_mockdataprofileprovider.py` testing resolve, add_profile, remove_profile
    - Test ConfigurationError on missing data profile name
    - Test resolve call recording and resolved_names property
    - Test __repr__ and __str__ output
    - _Requirements: 9.1–9.9_

  - [ ]* 2.7 Write unit tests for MockEmbeddingProvider
    - Create `testing/mocks/test_mockembeddingprovider.py` testing deterministic vectors (same input same output)
    - Test explicit mappings override hash-based generation
    - Test dimension configuration, embed_count, reset
    - Test __repr__ and __str__ output
    - _Requirements: 10.1–10.9_

- [ ] 3. Implement core mock providers (LLM, Tool, Transport, Memory)
  - [ ] 3.1 Create `testing/mocks/mockllmprovider.py` with MockLlmProvider class
    - Implement LlmProvider interface with complete and complete_stream methods
    - Accept response list at construction, return in sequence for successive requests
    - Raise TestingError when response sequence exhausted
    - Support conditional responses matching on message content patterns
    - Support latency simulation delay and error injection at specific indices
    - Record all completion requests, expose recorded_requests and request_count properties
    - Return TokenUsage with configurable token counts (default zero)
    - Implement reset, __repr__, __str__ methods
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13, 27.3_

  - [ ] 3.2 Create `testing/mocks/mocktoolexecutor.py` with MockToolExecutor class
    - Implement ToolExecutor interface with execute method
    - Accept tool_results dictionary mapping tool names to ToolResult lists
    - Raise TestingError when result sequence exhausted for a tool
    - Support conditional results matching on input patterns and error injection
    - Record all execution requests, expose recorded_requests, request_count, get_calls_for_tool
    - Implement reset, __repr__, __str__ methods
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 27.4_

  - [ ] 3.3 Create `testing/mocks/mocktransport.py` with MockTransport class
    - Implement Transport interface with connect, disconnect, send, receive, is_connected methods
    - Capture all sent messages in ordered list, support incoming message sequence
    - Track connection state, support send failure injection at specific indices
    - Expose sent_messages, sent_count, get_sent_messages_to properties/methods
    - Implement reset, __repr__, __str__ methods
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 27.5_

  - [ ] 3.4 Create `testing/mocks/mockmemorystore.py` with MockMemoryStore class
    - Implement MemoryStore interface with store, retrieve, search, update, delete, clear methods
    - Dictionary-based indexing by entry identifier
    - Support MemoryQuery filtering by tags, metadata, MemoryScope, time range
    - Support cosine similarity search with embedding vectors
    - Accept optional MockEmbeddingProvider for generating embeddings during store
    - Record all operations in ordered operation log
    - Implement reset, __repr__, __str__ methods
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 27.6_

  - [ ]* 3.5 Write unit tests for MockLlmProvider
    - Create `testing/mocks/test_mockllmprovider.py` testing response sequencing, conditional responses
    - Test TestingError on exhausted sequence, error injection at indices
    - Test call recording, request_count, latency simulation, reset
    - Test TokenUsage defaults and configuration
    - Test __repr__ and __str__ output
    - _Requirements: 4.1–4.13_

  - [ ]* 3.6 Write unit tests for MockToolExecutor
    - Create `testing/mocks/test_mocktoolexecutor.py` testing result sequencing per tool
    - Test TestingError on exhausted sequence, conditional results, error injection
    - Test call recording, request_count, get_calls_for_tool, reset
    - Test __repr__ and __str__ output
    - _Requirements: 5.1–5.12_

  - [ ]* 3.7 Write unit tests for MockTransport
    - Create `testing/mocks/test_mocktransport.py` testing message capture, incoming message sequence
    - Test connection state tracking, send failure injection
    - Test sent_messages, sent_count, get_sent_messages_to, reset
    - Test __repr__ and __str__ output
    - _Requirements: 6.1–6.11_

  - [ ]* 3.8 Write unit tests for MockMemoryStore
    - Create `testing/mocks/test_mockmemorystore.py` testing store, retrieve, search, update, delete, clear
    - Test tag/metadata/scope/time filtering via MemoryQuery
    - Test cosine similarity search with embedding vectors
    - Test operation log recording, reset
    - Test __repr__ and __str__ output
    - _Requirements: 7.1–7.10_

- [ ] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement TestConfigurationBuilder, AgentTestContext, and AgentAssertions
  - [ ] 5.1 Create `testing/testconfigurationbuilder.py` with TestConfigurationBuilder class
    - Fluent API with method chaining: with_identity, with_llm_provider, with_tool, with_memory_store, with_credential, with_data_profile
    - Build method returns AgentConfiguration with sensible defaults (UUID identifier, "test-agent" name, "1.0.0" version)
    - Implement __repr__ and __str__ methods
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8, 22.9, 22.10, 22.11, 27.13_

  - [ ] 5.2 Create `testing/agenttestcontext.py` with AgentTestContext class
    - Mutable context with read-only properties for Agent, MockLlmProvider, MockToolExecutor, MockTransport, MockMemoryStore, MockCredentialProvider, MockDataProfileProvider
    - Implement get_captured_events returning list of event dictionaries
    - Implement reset clearing all captured events and resetting all mock providers
    - Implement __repr__ and __str__ methods
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 27.2_

  - [ ] 5.3 Create `testing/agentassertions.py` with AgentAssertions class
    - Static methods: assert_lifecycle_state, assert_tool_called, assert_tool_called_with, assert_tool_call_count
    - Static methods: assert_llm_called, assert_llm_called_with_messages, assert_message_sent
    - Static methods: assert_memory_contains, assert_workflow_completed, assert_workflow_step_completed
    - All assertion methods include descriptive error messages with expected value, actual value, and agent identifier
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11_

  - [ ]* 5.4 Write unit tests for TestConfigurationBuilder
    - Create `testing/test_testconfigurationbuilder.py` testing fluent API chaining
    - Test defaults (UUID identifier, "test-agent" name, "1.0.0" version, empty collections)
    - Test build produces valid AgentConfiguration
    - Test __repr__ and __str__ output
    - _Requirements: 22.1–22.11_

  - [ ]* 5.5 Write unit tests for AgentTestContext
    - Create `testing/test_agenttestcontext.py` testing read-only properties return correct mock instances
    - Test get_captured_events returns event list
    - Test reset clears events and resets all mocks
    - Test __repr__ and __str__ output
    - _Requirements: 2.1–2.11_

  - [ ]* 5.6 Write unit tests for AgentAssertions
    - Create `testing/test_agentassertions.py` testing each assertion method raises AssertionError with descriptive message on failure
    - Test each assertion passes on valid state
    - _Requirements: 3.1–3.11_

- [ ] 6. Implement AgentTestFixture resource factory
  - [ ] 6.1 Create `testing/agenttestfixture.py` with create_agent_test_fixture resource factory
    - Implement as `testbase` resource factory function decorated with @testbase.register.resource_factory()
    - Create temporary directory for AppContext isolation
    - Instantiate all mock providers: MockLlmProvider, MockToolExecutor, MockTransport, MockMemoryStore, MockCredentialProvider, MockDataProfileProvider
    - Build AgentConfiguration via TestConfigurationBuilder with defaults and optional overrides
    - Create Agent, register optional tools, configure optional LLM responses
    - Yield AgentTestContext with Agent in INITIALIZED state
    - Cleanup: stop Agent, remove temporary directory
    - Implement __repr__ and __str__ on the factory (via docstring metadata)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 27.1_

  - [ ]* 6.2 Write unit tests for AgentTestFixture
    - Create `testing/test_agenttestfixture.py` testing Agent is in INITIALIZED state after yield
    - Test cleanup stops Agent and removes temporary directory
    - Test mock providers are registered and accessible via AgentTestContext
    - Test AppContext uses temporary directory for isolation
    - Test optional configuration, tools, and llm_responses parameters
    - _Requirements: 1.1–1.10_

- [ ] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implement execution trace data objects
  - [ ] 8.1 Create `testing/replay/__init__.py` package init
    - _Requirements: N/A (infrastructure)_

  - [ ] 8.2 Create `testing/replay/executiontraceevent.py` with ExecutionTraceEvent class
    - Immutable object with sequence_number, timestamp, event_type, agent_id, payload
    - Validate event_type against VALID_EVENT_TYPES
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 12.12, 12.13, 12.14, 12.15, 12.16, 12.17, 12.18, 12.19, 12.20, 27.8_

  - [ ] 8.3 Create `testing/replay/executiontrace.py` with ExecutionTrace class
    - Immutable object with agent_id, start_timestamp, end_timestamp, events list
    - Implement event_count property and get_events_by_type method
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11, 27.7_

  - [ ] 8.4 Create `testing/replay/replayconfiguration.py` with ReplayConfiguration class
    - Immutable object with strict_ordering (default True), fail_on_unexpected (default True), timing_tolerance (default 0.0)
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 27.14_

  - [ ]* 8.5 Write unit tests for ExecutionTraceEvent
    - Create `testing/replay/test_executiontraceevent.py` testing construction, read-only properties
    - Test event_type validation against VALID_EVENT_TYPES
    - Test as_dict, to_json, from_dict, from_json round-trip serialization
    - Test __repr__ and __str__ output
    - _Requirements: 12.12–12.20_

  - [ ]* 8.6 Write unit tests for ExecutionTrace
    - Create `testing/replay/test_executiontrace.py` testing construction, read-only properties
    - Test event_count property and get_events_by_type filtering
    - Test as_dict, to_json, from_dict, from_json round-trip serialization
    - Test __repr__ and __str__ output
    - _Requirements: 12.1–12.11_

  - [ ]* 8.7 Write unit tests for ReplayConfiguration
    - Create `testing/replay/test_replayconfiguration.py` testing construction, defaults
    - Test as_dict, to_json, from_dict, from_json round-trip serialization
    - Test __repr__ and __str__ output
    - _Requirements: 14.1–14.9_

- [ ] 9. Implement execution trace recorder and replayer
  - [ ] 9.1 Create `testing/replay/executiontracerecorder.py` with ExecutionTraceRecorder class
    - Accept Agent at construction, register callbacks for lifecycle, tool, LLM, memory, messaging, workflow events
    - Implement start method to begin recording with callback registration
    - Capture ExecutionTraceEvent for each event type with monotonically increasing sequence numbers
    - Implement stop method returning finalized ExecutionTrace
    - Expose event_count property
    - Log captured events at DEBUG level under `ccai.agentkit.testing`
    - Implement __repr__ and __str__ methods
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 11.12, 11.13, 25.3_

  - [ ] 9.2 Create `testing/replay/executiontracereplayer.py` with ExecutionTraceReplayer class
    - Accept ExecutionTrace and ReplayConfiguration at construction
    - Implement replay method: configure MockLlmProvider and MockToolExecutor from recorded events, trigger agent operations
    - Implement step method for single-event replay with inspection
    - Raise ReplayMismatchError when strict ordering is enabled and event types don't match
    - Expose current_position and is_complete properties
    - Log replayed events at INFO level, mismatches at WARNING level
    - Implement __repr__ and __str__ methods
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 25.4, 25.5, 27.9_

  - [ ]* 9.3 Write unit tests for ExecutionTraceRecorder
    - Create `testing/replay/test_executiontracerecorder.py` testing event capture for each event type
    - Test monotonically increasing sequence numbers
    - Test stop returns complete ExecutionTrace with all captured events
    - Test event_count property
    - Test __repr__ and __str__ output
    - _Requirements: 11.1–11.13_

  - [ ]* 9.4 Write unit tests for ExecutionTraceReplayer
    - Create `testing/replay/test_executiontracereplayer.py` testing replay configures mock providers from trace
    - Test strict ordering raises ReplayMismatchError on mismatch
    - Test step-by-step replay with current_position and is_complete
    - Test __repr__ and __str__ output
    - _Requirements: 13.1–13.10_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 11. Implement invariant system
  - [ ] 11.1 Create `testing/invariants/__init__.py` package init
    - _Requirements: N/A (infrastructure)_

  - [ ] 11.2 Create `testing/invariants/agentinvariant.py` with AgentInvariant abstract base class
    - Abstract properties: name, description
    - Abstract methods: strategy (returns Strategy from ccai.testbase.properties.strategies), verify (accepts generated input, raises InvariantViolationError)
    - Implement __repr__ and __str__ methods
    - _Requirements: 15.1, 15.2, 15.9, 15.10_

  - [ ] 11.3 Create `testing/invariants/invariantresult.py` with InvariantResult class
    - Immutable object with invariant_name, passed, test_case_count, optional counterexample, duration
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 27.10_

  - [ ] 11.4 Create `testing/invariants/invariantstrategy.py` with InvariantStrategy class
    - Static methods providing testbase property strategies: agent_configurations, agent_identities, lifecycle_state_sequences
    - Static methods: tool_schemas, llm_messages, llm_conversations, memory_entries, messages
    - All strategies constrain generated values to valid ranges and formats
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9_

  - [ ] 11.5 Create `testing/invariants/statemachineinvariant.py` with StateMachineTransitionInvariant class
    - Extends AgentInvariant, verifies valid transitions produce expected target state
    - Verifies invalid transitions raise SemanticError
    - _Requirements: 15.3_

  - [ ] 11.6 Create `testing/invariants/roundtripinvariants.py` with round-trip invariant classes
    - ConfigurationRoundTripInvariant: AgentConfiguration JSON round-trip
    - IdentityRoundTripInvariant: AgentIdentity JSON round-trip
    - ToolSchemaRoundTripInvariant: ToolSchema JSON round-trip
    - MemoryEntryRoundTripInvariant: MemoryEntry JSON round-trip
    - MessageRoundTripInvariant: Message JSON round-trip
    - _Requirements: 15.4, 15.5, 15.6, 15.7, 15.8_

  - [ ] 11.7 Create `testing/invariants/invarianttestrunner.py` with InvariantTestRunner class
    - Accept list of AgentInvariant instances and optional max_examples (default 100)
    - Implement run method executing all invariants via ccai.testbase.properties, returning list of InvariantResult
    - Implement run_single method for individual invariant execution
    - Discover additional invariants from "ccai.agentkit.testing.invariants" ExtensionPoint
    - Log invariant execution at INFO level, failures at WARNING level
    - Implement __repr__ and __str__ methods
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 25.6, 25.7, 26.2, 26.3_

  - [ ]* 11.8 Write unit tests for AgentInvariant and InvariantResult
    - Create `testing/invariants/test_agentinvariant.py` testing abstract interface enforcement
    - Create `testing/invariants/test_invariantresult.py` testing construction, read-only properties, serialization round-trip
    - Test __repr__ and __str__ output
    - _Requirements: 15.1–15.2, 18.1–18.9_

  - [ ]* 11.9 Write unit tests for InvariantStrategy
    - Create `testing/invariants/test_invariantstrategy.py` testing each strategy generates valid data
    - Test agent_configurations, agent_identities, lifecycle_state_sequences produce valid objects
    - Test tool_schemas, llm_messages, llm_conversations, memory_entries, messages produce valid objects
    - _Requirements: 16.1–16.9_

  - [ ]* 11.10 Write unit tests for StateMachineTransitionInvariant and round-trip invariants
    - Create `testing/invariants/test_statemachineinvariant.py` testing valid and invalid transitions
    - Create `testing/invariants/test_roundtripinvariants.py` testing each round-trip invariant verify method
    - _Requirements: 15.3–15.8_

  - [ ]* 11.11 Write unit tests for InvariantTestRunner
    - Create `testing/invariants/test_invarianttestrunner.py` testing run executes all invariants
    - Test run_single returns InvariantResult with correct pass/fail
    - Test extension point discovery of additional invariants
    - Test __repr__ and __str__ output
    - _Requirements: 17.1–17.9_

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement platform test harness system
  - [ ] 13.1 Create `testing/platform/__init__.py` package init
    - _Requirements: N/A (infrastructure)_

  - [ ] 13.2 Create `testing/platform/simulatedplatformservice.py` with SimulatedPlatformService abstract base class
    - Abstract properties: service_name, service_type (one of "compute", "storage", "messaging")
    - Abstract methods: start, stop
    - Implement is_running property, interaction_log property, reset method
    - Support configuring error responses for specific operations
    - Implement __repr__ and __str__ methods
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 27.12_

  - [ ] 13.3 Create `testing/platform/platformtestharness.py` with PlatformTestHarness abstract base class
    - Abstract properties: platform_name
    - Abstract methods: setup, teardown, get_service
    - Implement `testbase` resource factory function yielding PlatformTestContext
    - Implement __repr__ and __str__ methods
    - _Requirements: 19.1, 19.2, 19.7, 19.8, 19.9, 27.11_

  - [ ] 13.4 Create `testing/platform/platformtestcontext.py` with PlatformTestContext class
    - Expose read-only harness and platform_name properties
    - Implement get_service, get_interactions (with optional service_name filter), reset_all methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7_

  - [ ] 13.5 Create concrete platform harnesses
    - Create `testing/platform/awstestharness.py` with AwsTestHarness (simulated Lambda, S3, SQS)
    - Create `testing/platform/azuretestharness.py` with AzureTestHarness (simulated Functions, Blob, Service Bus)
    - Create `testing/platform/gcptestharness.py` with GcpTestHarness (simulated Cloud Functions, Cloud Storage, Pub/Sub)
    - Create `testing/platform/localtestharness.py` with LocalTestHarness (file system, process, in-memory queue)
    - Each implements setup, teardown, get_service with simulated compute, storage, messaging services
    - _Requirements: 19.3, 19.4, 19.5, 19.6_

  - [ ]* 13.6 Write unit tests for SimulatedPlatformService
    - Create `testing/platform/test_simulatedplatformservice.py` testing abstract interface enforcement
    - Test interaction log recording, reset, error injection
    - Test __repr__ and __str__ output
    - _Requirements: 20.1–20.8_

  - [ ]* 13.7 Write unit tests for PlatformTestHarness and PlatformTestContext
    - Create `testing/platform/test_platformtestharness.py` testing abstract interface enforcement
    - Create `testing/platform/test_platformtestcontext.py` testing delegation to harness, get_interactions filtering, reset_all
    - Test __repr__ and __str__ output
    - _Requirements: 19.1–19.2, 21.1–21.7_

  - [ ]* 13.8 Write unit tests for concrete platform harnesses
    - Create `testing/platform/test_awstestharness.py` testing setup/teardown lifecycle, get_service, interaction logging
    - Create `testing/platform/test_azuretestharness.py` testing setup/teardown lifecycle, get_service, interaction logging
    - Create `testing/platform/test_gcptestharness.py` testing setup/teardown lifecycle, get_service, interaction logging
    - Create `testing/platform/test_localtestharness.py` testing setup/teardown lifecycle, get_service, interaction logging
    - _Requirements: 19.3–19.6_

- [ ] 14. Implement extension point integration and structured logging
  - [ ] 14.1 Register ExtensionPoints for testing harnesses and invariants
    - Define ExtensionPoint "ccai.agentkit.testing.harnesses" for PlatformTestHarness implementations
    - Define ExtensionPoint "ccai.agentkit.testing.invariants" for AgentInvariant implementations
    - Handle plugin load failures: log at WARNING, continue loading remaining plugins
    - _Requirements: 26.1, 26.2, 26.3, 26.4_

  - [ ] 14.2 Verify structured logging across all testing components
    - Ensure AgentTestFixture logs at INFO on Agent creation
    - Ensure ExecutionTraceRecorder logs at DEBUG on event capture
    - Ensure ExecutionTraceReplayer logs at INFO on replay, WARNING on mismatch
    - Ensure InvariantTestRunner logs at INFO on completion, WARNING on failure
    - Ensure PlatformTestHarness logs at INFO on setup/teardown
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7, 25.8_

  - [ ]* 14.3 Write unit tests for extension point integration and logging
    - Test InvariantTestRunner discovers invariants from ExtensionPoint
    - Test plugin load failure is logged at WARNING and does not propagate
    - Verify logging output at correct levels for each component
    - _Requirements: 26.1–26.4, 25.1–25.8_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Unit tests validate specific examples, edge cases, and error conditions
- All source files use lowercase filenames with no underscores under `source/packages/ccai/agentkit/testing/`
- All test files go under `source/testroots/ccai/tests/singlehost/agentkit/testing/`, mirroring the source hierarchy
- Tests use the `testbase` framework and `ccai.testbase.mocking` for mocks
- Run tests with: `source .venv/bin/activate && testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost.agentkit.testing --output=./.output`
