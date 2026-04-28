# Implementation Plan: Core Agent Framework

## Overview

Incremental implementation of the Core Agent Framework for the `automojo-agent-kit` SDK. Tasks build bottom-up: foundational types first (enums, errors, records), then value objects (identity, address), then configuration, then state machine, then registry, then the Agent base class with hooks and sub-agents, then AsyncAgent. Each task references specific requirements and design properties. Tests are placed close to the code they validate.

## Tasks

- [x] 1. Implement LifecycleState, ConcurrencyModel, and Exception Hierarchy
  - [x] 1.1 Create `source/packages/automojo/agentkit/lifecyclestate.py` with the LifecycleState enum
    - Implement enum with values: CREATED, INITIALIZED, RUNNING, PAUSED, STOPPED, ERROR
    - _Requirements: 4.1_

  - [x] 1.2 Create `source/packages/automojo/agentkit/concurrencymodel.py` with the ConcurrencyModel enum
    - Implement enum with values: ASYNCIO, THREAD, THREAD_POOL
    - _Requirements: 10.1_

  - [x] 1.3 Create `source/packages/automojo/agentkit/errors.py` with the exception hierarchy
    - AgentKitError base exception with message and optional cause, exception chaining via __cause__
    - ConfigurationError inheriting from AgentKitError
    - SemanticError inheriting from AgentKitError
    - LifecycleError inheriting from AgentKitError
    - All provide __repr__ with class name and message
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x] 1.4 Create `source/packages/automojo/agentkit/configurationerrors.py` with extended configuration exceptions
    - ConfigurationValidationError with schema_name, errors list, optional warnings list
    - PluginLoadError with plugin_name and message
    - Both inherit from AgentKitError
    - Both provide __repr__ with class name and relevant fields
    - _Requirements: 14.1_

  - [x] 1.5 Write property tests for exception hierarchy (Property 24)
    - **Property 24: Exception hierarchy fields and chaining** — for any message and cause, properties match constructor args, __cause__ is set when cause provided, __repr__ contains class name and message
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_errors_properties.py`
    - **Validates: Requirements 14.5, 14.6, 14.7**

  - [x] 1.6 Write unit tests for LifecycleState, ConcurrencyModel, and exceptions
    - Test LifecycleState has all six values
    - Test ConcurrencyModel has all three values
    - Test AgentKitError, ConfigurationError, SemanticError, LifecycleError inheritance chain
    - Test ConfigurationValidationError fields and formatted message
    - Test PluginLoadError fields and formatted message
    - Test exception without cause has None cause
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_lifecyclestate.py`, `test_concurrencymodel.py`, `test_errors.py`, `test_configurationerrors.py`
    - _Requirements: 4.1, 10.1, 14.1, 14.2, 14.3, 14.4_

- [x] 2. Implement TransitionRecord and AgentIdentity
  - [x] 2.1 Create `source/packages/automojo/agentkit/transitionrecord.py` with the TransitionRecord class
    - Implement __init__ with previous_state, new_state, timestamp, optional metadata
    - Implement read-only properties for all fields
    - Implement defensive copy for metadata property
    - Implement __repr__ with class name, previous_state, new_state, timestamp
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 2.2 Create `source/packages/automojo/agentkit/agentidentity.py` with the AgentIdentity class
    - Implement __init__ with name, version, optional tags, optional identifier (auto-generates UUID)
    - Implement read-only properties for identifier, name, version, tags (defensive copy)
    - Implement as_dict(), to_json(), from_json(cls, json_str)
    - Implement __repr__ (class name, identifier, name, version) and __str__ (name, version)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 2.3 Write property tests for AgentIdentity (Properties 1, 2, 11-partial)
    - **Property 1: AgentIdentity JSON round-trip** — for any valid AgentIdentity, from_json(to_json()) produces equivalent fields
    - **Validates: Requirements 2.5, 2.6, 2.7, 2.8**
    - **Property 2: AgentIdentity auto-generates UUID** — for any name and version without explicit identifier, identifier is a non-empty valid UUID
    - **Validates: Requirements 2.2**
    - **Property 11 (partial): Defensive copy for AgentIdentity tags** — modifying returned tags does not affect internal state
    - **Validates: Requirements 2.4**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentidentity_properties.py`

  - [x] 2.4 Write property tests for TransitionRecord (Property 11-partial)
    - **Property 11 (partial): Defensive copy for TransitionRecord metadata** — modifying returned metadata does not affect internal state
    - **Validates: Requirements 5.3**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_transitionrecord_properties.py`

  - [x] 2.5 Write unit tests for TransitionRecord and AgentIdentity
    - Test TransitionRecord read-only properties and __repr__
    - Test TransitionRecord with None metadata defaults to empty dict
    - Test AgentIdentity read-only properties, __repr__, __str__
    - Test AgentIdentity with explicit identifier preserves it
    - Test AgentIdentity with tags and without tags
    - Test files: `source/testroots/automojo/tests/singlehost/agentkit/test_transitionrecord.py`, `test_agentidentity.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.9, 2.10, 5.1, 5.2, 5.4_

- [x] 3. Implement AgentAddress
  - [x] 3.1 Create `source/packages/automojo/agentkit/agentaddress.py` with the AgentAddress class
    - Implement __init__ with agent_identifier, transport_name, optional endpoint dict
    - Implement read-only properties for all fields (endpoint returns defensive copy)
    - Implement as_dict(), to_json(), from_dict(cls, data), from_json(cls, json_str)
    - Implement __eq__ and __hash__ based on (agent_identifier, transport_name)
    - Implement __repr__ (class name, agent_identifier, transport_name) and __str__ (all fields)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11, 9.12_

  - [x] 3.2 Write property tests for AgentAddress (Properties 9, 10, 11-partial)
    - **Property 9: AgentAddress JSON round-trip** — for any valid AgentAddress, from_json(to_json()) produces equivalent fields
    - **Validates: Requirements 9.4, 9.5, 9.6, 9.7, 9.8**
    - **Property 10: AgentAddress equality and hash consistency** — same (agent_identifier, transport_name) implies equal and same hash; different implies not equal
    - **Validates: Requirements 9.9, 9.10**
    - **Property 11 (partial): Defensive copy for AgentAddress endpoint** — modifying returned endpoint does not affect internal state
    - **Validates: Requirements 9.3**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentaddress_properties.py`

  - [x] 3.3 Write unit tests for AgentAddress
    - Test read-only properties and __repr__, __str__
    - Test AgentAddress with None endpoint defaults to empty dict
    - Test AgentAddress as dictionary key and set member
    - Test from_dict with missing endpoint key defaults to empty dict
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentaddress.py`
    - _Requirements: 9.1, 9.2, 9.11, 9.12_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement AgentConfiguration
  - [x] 5.1 Create `source/packages/automojo/agentkit/agentconfiguration.py` with the AgentConfiguration class
    - Implement __init__ with identity, optional settings, credentials, data_profiles, sub_agents, resolved_credentials, resolved_data_profiles
    - Implement read-only properties for all fields (defensive copies)
    - Implement _validate_config_data(cls, config_data) validating required fields
    - Implement _resolve_credentials(cls, credentials_data, app_context) and _resolve_data_profiles(cls, data_profiles_data, app_context)
    - Implement from_dict(cls, config_data, app_context=None), from_json, from_json_file, from_yaml, from_yaml_file
    - Implement as_dict() (excludes resolved credentials), to_json(), to_yaml()
    - Implement __repr__ (class name, identity, excludes resolved credentials) and __str__ (name, version, counts)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15, 11.1, 11.2, 11.3, 12.1, 12.2, 16.1, 16.2, 16.3_

  - [x] 5.2 Write property tests for AgentConfiguration (Properties 3, 4, 5, 6)
    - **Property 3: AgentConfiguration JSON round-trip** — from_json(to_json()) produces equivalent as_dict()
    - **Validates: Requirements 3.1, 3.2, 3.9, 3.10, 3.12**
    - **Property 4: AgentConfiguration YAML round-trip** — from_yaml(to_yaml()) produces equivalent as_dict()
    - **Validates: Requirements 3.4, 3.11, 3.13**
    - **Property 5: AgentConfiguration rejects missing required fields** — missing identity or identity sub-fields raises ConfigurationError
    - **Validates: Requirements 3.6, 3.7**
    - **Property 6: AgentConfiguration excludes resolved credentials from serialization** — as_dict/to_json/to_yaml do not contain resolved credential values
    - **Validates: Requirements 3.14, 3.15, 11.3**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentconfiguration_properties.py`

  - [x] 5.3 Write unit tests for AgentConfiguration
    - Test from_dict with minimal config (identity only)
    - Test from_dict with full config (settings, credentials, data_profiles, sub_agents)
    - Test from_json and from_yaml with valid strings
    - Test from_json_file and from_yaml_file with temp files
    - Test missing identity raises ConfigurationError
    - Test identity not a dict raises ConfigurationError
    - Test missing name or version in identity raises ConfigurationError
    - Test credential resolution with mocked app_context (using automojo.testbase.mocking.Mock)
    - Test unresolvable credential raises ConfigurationError
    - Test data profile resolution with mocked app_context
    - Test unresolvable data profile raises ConfigurationError
    - Test as_dict excludes resolved credentials
    - Test __repr__ and __str__
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentconfiguration.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.14, 3.15, 11.1, 11.2, 11.3, 12.1, 12.2, 16.1, 16.2, 16.3_

- [x] 6. Implement AgentStateMachine
  - [x] 6.1 Create `source/packages/automojo/agentkit/agentstatemachine.py` with the AgentStateMachine class
    - Implement __init__ with initial state CREATED, empty history, threading.Lock
    - Implement VALID_TRANSITIONS class constant with the transition table
    - Implement current_state and transition_history read-only properties
    - Implement get_valid_transitions() returning valid targets from current state
    - Implement transition_to(target_state, metadata=None) with lock, validation, history recording
    - Raise SemanticError for invalid transitions with current state, target state, and valid transitions in message
    - Implement __repr__ (class name, current state) and __str__ (current state value)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11_

  - [x] 6.2 Write property tests for AgentStateMachine (Properties 7, 8)
    - **Property 7: AgentStateMachine enforces valid transitions** — valid transitions succeed and update state; invalid transitions raise SemanticError with correct message content
    - **Validates: Requirements 4.2, 4.3, 4.4**
    - **Property 8: AgentStateMachine records transition history** — N valid transitions produce N TransitionRecords with correct states and non-None timestamps
    - **Validates: Requirements 4.5, 4.7**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentstatemachine_properties.py`

  - [x] 6.3 Write unit tests for AgentStateMachine
    - Test initial state is CREATED
    - Test each valid transition in the table
    - Test invalid transition raises SemanticError with descriptive message
    - Test transition_history grows with each transition
    - Test get_valid_transitions returns correct list for each state
    - Test __repr__ and __str__
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentstatemachine.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.10, 4.11_

- [x] 7. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement AgentRegistry
  - [x] 8.1 Create `source/packages/automojo/agentkit/agentregistry.py` with the AgentRegistry class
    - Implement singleton pattern with _instance, _instance_lock, instance() class method
    - Implement __init__ with _agents dict and threading.Lock
    - Implement register(agent) raising SemanticError on duplicate identifier
    - Implement deregister(identifier) as no-op if not found
    - Implement lookup_by_id(identifier), lookup_by_name(name), lookup_by_tags(**tags)
    - Implement list_all(), count property
    - Implement _reset() and _reset_singleton() for testing
    - Implement __repr__ (class name, count) and __str__ (count summary)
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12_

  - [x] 8.2 Write property tests for AgentRegistry (Properties 17, 18, 19)
    - **Property 17: AgentRegistry registration, lookup, and enumeration** — count, lookup_by_id, lookup_by_name, lookup_by_tags, list_all correctness
    - **Validates: Requirements 7.4, 7.5, 7.6, 7.7, 7.9**
    - **Property 18: AgentRegistry duplicate registration raises SemanticError** — duplicate identifier raises SemanticError
    - **Validates: Requirements 7.3**
    - **Property 19: AgentRegistry deregistration removes agent** — after deregister, lookup returns None, count decreases
    - **Validates: Requirements 7.8**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentregistry_properties.py`

  - [x] 8.3 Write unit tests for AgentRegistry
    - Test singleton pattern (instance() returns same object)
    - Test register and lookup_by_id
    - Test duplicate registration raises SemanticError
    - Test deregister removes agent
    - Test deregister non-existent identifier is no-op
    - Test lookup_by_name with multiple matches
    - Test lookup_by_tags with partial and full matches
    - Test list_all and count
    - Test _reset clears all agents
    - Test _reset_singleton resets singleton
    - Test __repr__ and __str__
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agentregistry.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.11, 7.12_

- [x] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Agent base class with lifecycle, hooks, and sub-agents
  - [x] 10.1 Create `source/packages/automojo/agentkit/agent.py` with the Agent abstract base class
    - Implement __init__(configuration) creating AgentIdentity from config, AgentStateMachine (CREATED), registering with AgentRegistry, initializing hooks dict, creating scoped logger
    - Implement read-only properties: state, identity, configuration, parent, sub_agents, extensions
    - Declare abstract methods: initialize, start, pause, resume, stop, reset
    - Implement _perform_transition(target_state, transition_point, metadata) — transitions state machine, logs at INFO, invokes hooks, propagates ERROR to parent
    - Implement _invoke_hooks(transition_point, record) — invokes hooks in order, logs WARNING on exception, continues
    - Implement register_hook(transition_point, callback) — validates transition point, raises SemanticError for invalid
    - Implement deregister_hook(transition_point, callback) — removes callback by reference
    - Implement add_sub_agent(agent) — cycle detection by walking ancestor chain, self-addition check, sets parent
    - Implement remove_sub_agent(identifier) — clears parent reference
    - Implement get_logger() returning scoped logger
    - Implement __repr__ (class name, identifier, name, state) and __str__ (name, state)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 15.1, 15.2, 15.3, 15.4_

  - [x] 10.2 Write property tests for Agent (Properties 12, 13, 14, 15, 16, 20, 21, 22, 25)
    - **Property 12: Agent construction invariants** — state is CREATED, identity matches config, agent in registry
    - **Validates: Requirements 1.6, 1.7, 1.8**
    - **Property 13: Lifecycle hooks invoked in registration order** — N hooks invoked in order with correct args
    - **Validates: Requirements 6.1, 6.2, 6.3**
    - **Property 14: Lifecycle hook exceptions do not prevent remaining hooks** — remaining hooks still invoked
    - **Validates: Requirements 6.4**
    - **Property 15: Invalid transition point raises SemanticError** — invalid point raises SemanticError with valid points in message
    - **Validates: Requirements 6.6**
    - **Property 16: Hook deregistration prevents invocation** — deregistered hook not invoked
    - **Validates: Requirements 6.5**
    - **Property 20: Sub-agent add sets parent, remove clears parent** — add makes child.parent == parent, remove makes child.parent None
    - **Validates: Requirements 8.1, 8.2, 8.5, 8.6**
    - **Property 21: Circular parent-child relationship detection** — ancestor chain cycle raises SemanticError, self-addition raises SemanticError
    - **Validates: Requirements 8.8, 8.9, 8.10**
    - **Property 22: Sub-agent ERROR notification propagates to parent** — parent on_error hooks invoked with child info in metadata
    - **Validates: Requirements 8.7**
    - **Property 25: Agent logger scoped to identity** — get_logger().name matches automojo.agentkit.agent.<identifier>
    - **Validates: Requirements 15.4**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agent_properties.py`

  - [x] 10.3 Write unit tests for Agent
    - Create a concrete TestAgent subclass for testing
    - Test Agent cannot be instantiated directly (abstract)
    - Test state property returns CREATED after construction
    - Test identity property returns correct AgentIdentity
    - Test configuration property returns correct AgentConfiguration
    - Test parent is None for top-level agent
    - Test sub_agents is empty initially
    - Test extensions is empty initially
    - Test register_hook with valid transition points
    - Test register_hook with invalid transition point raises SemanticError
    - Test deregister_hook removes callback
    - Test _perform_transition logs at INFO level
    - Test _invoke_hooks logs WARNING on hook exception
    - Test add_sub_agent and remove_sub_agent
    - Test add_sub_agent self-addition raises SemanticError
    - Test add_sub_agent circular relationship raises SemanticError
    - Test sub-agent ERROR propagation to parent on_error hooks
    - Test __repr__ and __str__
    - Test get_logger returns correctly named logger
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agent.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 15.1, 15.2, 15.3, 15.4_

- [x] 11. Implement AsyncAgent
  - [x] 11.1 Create `source/packages/automojo/agentkit/asyncagent.py` with the AsyncAgent class
    - Extend Agent, set concurrency_model to ConcurrencyModel.ASYNCIO
    - Implement concurrency_model read-only property
    - Implement synchronous lifecycle methods delegating to async versions via _run_async
    - Declare abstract async methods: async_initialize, async_start, async_pause, async_resume, async_stop, async_reset
    - Implement _run_async(coroutine) — uses asyncio.run() when no loop, ensures_future when loop running
    - Implement _async_perform_transition delegating to _perform_transition
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 11.2 Write property tests for AsyncAgent (Property 23)
    - **Property 23: AsyncAgent sync methods delegate to async methods** — calling initialize() invokes async_initialize() to completion
    - **Validates: Requirements 10.5, 10.7**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_asyncagent_properties.py`

  - [x] 11.3 Write unit tests for AsyncAgent
    - Create a concrete TestAsyncAgent subclass for testing
    - Test AsyncAgent cannot be instantiated directly (abstract)
    - Test concurrency_model returns ConcurrencyModel.ASYNCIO
    - Test synchronous initialize() calls async_initialize()
    - Test synchronous start() calls async_start()
    - Test all six sync-to-async delegations
    - Test _run_async creates event loop when none exists
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_asyncagent.py`
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.7_

- [x] 12. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement string representations property test and integration tests
  - [-] 13.1 Write property test for string representations (Property 26)
    - **Property 26: String representations contain required information** — verify repr/str for Agent, AgentIdentity, AgentStateMachine, AgentAddress, AgentRegistry, TransitionRecord
    - **Validates: Requirements 1.9, 1.10, 2.9, 2.10, 4.10, 4.11, 7.11, 7.12, 5.4, 9.11, 9.12**
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_stringrepresentations_properties.py`

  - [x] 13.2 Write integration tests for extension point and plugin discovery
    - Test Agent._initialize_plugins() with mocked automojo-extension PluginManager (using automojo.testbase.mocking.Mock)
    - Test plugin load failure logging at WARNING level
    - Test extensions property returns loaded extensions
    - Test file: `source/testroots/automojo/tests/singlehost/agentkit/test_agent_integration.py`
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [ ] 14. Wire package exports
  - [x] 14.1 Update `source/packages/automojo/agentkit/__init__.py` to export all core framework classes
    - Export LifecycleState, ConcurrencyModel, TransitionRecord
    - Export AgentKitError, ConfigurationError, SemanticError, LifecycleError
    - Export ConfigurationValidationError, PluginLoadError
    - Export AgentIdentity, AgentAddress, AgentConfiguration
    - Export AgentStateMachine, AgentRegistry
    - Export Agent, AsyncAgent
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 7.1, 9.1, 10.1, 10.2, 14.1_

- [ ] 15. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (26 total across Properties 1–26)
- Unit tests validate specific examples, edge cases, and integration with external packages
- All mocking uses `automojo.testbase.mocking.Mock` per project conventions
- Tests reside under `source/testroots/automojo/tests/singlehost/agentkit/` mirroring the source hierarchy
- Agent tests require a concrete TestAgent subclass since Agent is abstract
- AsyncAgent tests require a concrete TestAsyncAgent subclass since AsyncAgent is abstract
- AgentRegistry tests must call `_reset_singleton()` in teardown to avoid test pollution
