# Implementation Plan: Core Agent Framework

## Overview

Incremental implementation of the core agent framework for the `automojo-agent-kit` SDK. Each task builds on the previous, starting with foundational types (errors, enums, records), then the state machine, identity, configuration, registry, and finally the Agent base class with hooks, sub-agents, and concurrency models. Tests mirror the source hierarchy under `source/testroots/automojo/tests/singlehost/agentkit/`.

## Tasks

- [x] 1. Implement exception hierarchy and LifecycleState enum
  - [x] 1.1 Create `source/packages/automojo/agentkit/errors.py` with AgentKitError, ConfigurationError, SemanticError, and LifecycleError
    - AgentKitError is the base exception; ConfigurationError, SemanticError, LifecycleError inherit from it
    - All accept a descriptive message string and an optional cause exception
    - All provide a meaningful `__repr__` including class name and message
    - Use multi-line error message formation pattern per coding standards
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

  - [x] 1.2 Create `source/packages/automojo/agentkit/lifecyclestate.py` with LifecycleState enum
    - Define CREATED, INITIALIZED, RUNNING, PAUSED, STOPPED, ERROR values
    - _Requirements: 4.1_

  - [x] 1.3 Create `source/packages/automojo/agentkit/transitionrecord.py` with TransitionRecord
    - Immutable record with previous_state, new_state, timestamp, metadata properties
    - Metadata returns a defensive copy
    - _Requirements: 4.5_

  - [x] 1.4 Write unit tests for errors, LifecycleState, and TransitionRecord
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_errors.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_lifecyclestate.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_transitionrecord.py`
    - Test exception inheritance chain, repr output, cause chaining
    - Test all six LifecycleState enum values exist
    - Test TransitionRecord properties are read-only and metadata is a defensive copy
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 4.1, 4.5_

- [x] 2. Implement AgentStateMachine
  - [x] 2.1 Create `source/packages/automojo/agentkit/agentstatemachine.py` with AgentStateMachine
    - Define VALID_TRANSITIONS class-level dict matching the design transition table
    - Implement current_state read-only property, initial state CREATED
    - Implement transition_to(target_state) that validates and records transitions, raises SemanticError for invalid transitions with current state, target, and valid transitions in message
    - Implement get_valid_transitions() returning valid targets from current state
    - Implement transition_history read-only property returning list of TransitionRecord
    - Implement `__repr__` and `__str__` per Requirement 16
    - Use threading.Lock for thread-safe state transitions
    - _Requirements: 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 13.6, 16.5, 16.6_

  - [x] 2.2 Write property test: State machine accepts valid transitions (Property 8)
    - **Property 8: State machine accepts valid transitions and updates state**
    - **Validates: Requirements 4.2, 4.3**
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_agentstatemachine.py`
    - Use automojo.testbase.properties to generate random valid transition sequences from the transition table
    - Assert current_state equals the last target after each valid transition

  - [x] 2.3 Write property test: State machine rejects invalid transitions (Property 9)
    - **Property 9: State machine rejects invalid transitions**
    - **Validates: Requirements 4.4**
    - Use automojo.testbase.properties to generate (state, invalid_target) pairs not in VALID_TRANSITIONS
    - Assert SemanticError is raised with message containing current state, target, and valid transitions

  - [x] 2.4 Write property test: State machine records transition history (Property 10)
    - **Property 10: State machine records transition history**
    - **Validates: Requirements 4.5**
    - Use automojo.testbase.properties to generate valid transition sequences
    - Assert transition_history length matches number of transitions, each record has correct previous/new state and valid timestamp

  - [x] 2.5 Write property test: get_valid_transitions matches transition table (Property 11)
    - **Property 11: State machine get_valid_transitions matches transition table**
    - **Validates: Requirements 4.7**
    - For each LifecycleState, assert get_valid_transitions() returns exactly VALID_TRANSITIONS[state]

  - [x] 2.6 Write unit tests for AgentStateMachine edge cases
    - Test initial state is CREATED
    - Test thread-safety under concurrent transitions
    - Test __repr__ and __str__ output
    - _Requirements: 4.6, 4.8, 13.6, 16.5, 16.6_

- [x] 3. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement AgentIdentity
  - [x] 4.1 Create `source/packages/automojo/agentkit/agentidentity.py` with AgentIdentity
    - Constructor accepts name, version, tags (optional dict), identifier (optional, auto-generates UUID)
    - Read-only properties: identifier, name, version, tags (defensive copy)
    - Implement as_dict(), to_json(), from_json() class method
    - Implement `__repr__` and `__str__` per Requirement 16
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 12.1, 12.2, 12.7, 16.3, 16.4_

  - [x] 4.2 Write property test: AgentIdentity JSON round-trip (Property 1)
    - **Property 1: AgentIdentity JSON round-trip**
    - **Validates: Requirements 2.6, 12.7**
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_agentidentity.py`
    - Use automojo.testbase.properties to generate random name, version, tags, optional identifier
    - Assert to_json() then from_json() produces equivalent identity

  - [x] 4.3 Write property test: AgentIdentity serialization completeness (Property 2)
    - **Property 2: AgentIdentity serialization completeness**
    - **Validates: Requirements 2.1, 2.4, 2.5, 12.1**
    - Assert as_dict() contains identifier, name, version, tags matching properties
    - Assert to_json() produces valid JSON with same keys and values

  - [x] 4.4 Write property test: AgentIdentity auto-generates UUID (Property 3)
    - **Property 3: AgentIdentity auto-generates UUID**
    - **Validates: Requirements 2.2**
    - Use automojo.testbase.properties to generate identities without explicit identifier
    - Assert identifier is parseable by uuid.UUID

  - [x] 4.5 Write unit tests for AgentIdentity edge cases
    - Test __repr__ and __str__ output format
    - Test empty tags dictionary
    - Test explicit identifier is preserved
    - _Requirements: 2.3, 16.3, 16.4_

- [x] 5. Implement AgentConfiguration
  - [x] 5.1 Create `source/packages/automojo/agentkit/agentconfiguration.py` with AgentConfiguration
    - Implement from_dict(config_data, app_context) class method with validation of required fields
    - Implement from_json(json_str, app_context) and from_json_file(file_path, app_context) class methods
    - Implement from_yaml(yaml_str, app_context) and from_yaml_file(file_path, app_context) class methods
    - Implement as_dict(), to_json(), to_yaml() serialization methods
    - Resolve CredentialReference entries via automojo-credentials during initialization
    - Resolve DataProfileReference entries via automojo-dataprofiles during initialization
    - Resolve file paths relative to AppContext directory from automojo-this-app
    - Resolve environment variable references via AppContext
    - Raise ConfigurationError for missing required fields, invalid values, unresolvable credentials/data profiles, missing AppContext
    - Exclude resolved credential secret values from serialization output
    - Implement `__repr__` and `__str__` excluding credential values per Requirement 16
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 8.1, 8.2, 8.3, 9.1, 9.2, 9.3, 10.1, 10.2, 12.3, 12.4, 12.5, 12.6, 12.8, 12.9, 16.7, 16.8_

  - [x] 5.2 Write property test: AgentConfiguration JSON round-trip (Property 4)
    - **Property 4: AgentConfiguration JSON round-trip**
    - **Validates: Requirements 3.12, 12.8**
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_agentconfiguration.py`
    - Use automojo.testbase.properties to generate valid config dicts (without credential references)
    - Assert to_json() then from_json() produces equivalent as_dict() output

  - [x] 5.3 Write property test: AgentConfiguration YAML round-trip (Property 5)
    - **Property 5: AgentConfiguration YAML round-trip**
    - **Validates: Requirements 3.13, 12.9**
    - Use automojo.testbase.properties to generate valid config dicts (without credential references)
    - Assert to_yaml() then from_yaml() produces equivalent as_dict() output

  - [x] 5.4 Write property test: AgentConfiguration validation rejects invalid configs (Property 6)
    - **Property 6: AgentConfiguration validation rejects invalid configs**
    - **Validates: Requirements 3.5, 3.8**
    - Use automojo.testbase.properties to generate dicts missing required fields or with invalid types
    - Assert ConfigurationError is raised

  - [x] 5.5 Write property test: AgentConfiguration serialization excludes credentials (Property 7)
    - **Property 7: AgentConfiguration serialization excludes credentials**
    - **Validates: Requirements 9.3, 3.9, 3.10, 3.11**
    - Use automojo.testbase.properties to generate configs with CredentialReference entries
    - Assert as_dict(), to_json(), to_yaml() do not contain resolved secret values

  - [x] 5.6 Write property test: AgentConfiguration from_dict produces valid configuration (Property 21)
    - **Property 21: AgentConfiguration from_dict produces valid configuration**
    - **Validates: Requirements 3.1**
    - Use automojo.testbase.properties to generate valid config dicts with all required fields
    - Assert from_dict() produces config whose as_dict() contains same identity, settings, and reference names

  - [x] 5.7 Write unit tests for AgentConfiguration edge cases
    - Test missing AppContext raises ConfigurationError
    - Test unresolvable CredentialReference raises ConfigurationError
    - Test unresolvable DataProfileReference raises ConfigurationError
    - Test file path resolution relative to AppContext directory
    - Test environment variable resolution via AppContext
    - Test __repr__ and __str__ exclude credential values
    - Use testbase.mocking.Mock for automojo-credentials, automojo-dataprofiles, automojo-this-app
    - _Requirements: 8.1, 8.2, 8.3, 9.1, 9.2, 10.1, 10.2, 16.7, 16.8_

- [x] 6. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement AgentRegistry
  - [x] 7.1 Create `source/packages/automojo/agentkit/agentregistry.py` with AgentRegistry
    - Implement singleton pattern via instance() class method
    - Implement register(agent) that stores by identifier, raises SemanticError on duplicate
    - Implement deregister(identifier) to remove agent
    - Implement lookup_by_id(identifier) returning Agent or None
    - Implement lookup_by_name(name) returning list of matching agents
    - Implement lookup_by_tags(**tags) returning agents matching all tag criteria
    - Implement list_all() returning all registered agents
    - Implement count read-only property
    - Use threading.Lock for thread-safe operations
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 13.7_

  - [x] 7.2 Write property test: Registry registration and lookup correctness (Property 15)
    - **Property 15: Registry registration and lookup correctness**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.9**
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_agentregistry.py`
    - Use automojo.testbase.properties to generate sets of agents with unique identifiers
    - Assert count, lookup_by_id, lookup_by_name, lookup_by_tags, list_all correctness
    - Assert duplicate identifier raises SemanticError

  - [x] 7.3 Write property test: Registry deregistration removes agent (Property 16)
    - **Property 16: Registry deregistration removes agent**
    - **Validates: Requirements 6.8**
    - Assert deregister removes agent so lookup_by_id returns None and count decreases

  - [x] 7.4 Write unit tests for AgentRegistry edge cases
    - Test singleton pattern returns same instance
    - Test thread-safety under concurrent registration
    - Test lookup_by_tags with no matches returns empty list
    - _Requirements: 6.1, 13.7_

- [x] 8. Implement Agent base class with lifecycle hooks and structured logging
  - [x] 8.1 Create `source/packages/automojo/agentkit/agent.py` with Agent abstract base class
    - Extend abc.ABC with abstract methods: initialize, start, pause, resume, stop, reset
    - Constructor accepts AgentConfiguration, creates AgentIdentity from config, creates AgentStateMachine, registers with AgentRegistry
    - Read-only properties: state, identity, configuration, parent, sub_agents, extensions
    - Implement register_hook(transition_point, callback) and deregister_hook(transition_point, callback)
    - Hook invocation: call all hooks in registration order, pass Agent and TransitionRecord, log and continue on exception
    - Implement add_sub_agent(agent) with cycle detection via ancestor traversal, sets parent reference
    - Implement remove_sub_agent(identifier) clearing parent reference
    - Lifecycle cascading: stop cascades to sub-agents, pause cascades to RUNNING sub-agents, resume cascades to sub-agents paused by parent
    - Sub-agent error notification: child ERROR triggers parent on_error hooks with child identity in metadata
    - Implement `__repr__` and `__str__` per Requirement 16
    - Use Python logging module with logger hierarchy rooted at `automojo.agentkit`
    - Log transitions at INFO level, hook exceptions at WARNING level
    - Provide method returning logger scoped to `automojo.agentkit.agent.<agent_identifier>`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 11.1, 11.2, 11.3, 11.4, 15.1, 15.2, 15.3, 15.4, 16.1, 16.2_

  - [x] 8.2 Write property test: Hooks invoked in registration order (Property 12)
    - **Property 12: Hooks invoked in registration order with correct arguments**
    - **Validates: Requirements 5.1, 5.2, 5.3**
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_agent.py`
    - Use automojo.testbase.properties to generate lists of N hooks for a transition point
    - Assert all N hooks invoked in order, each receiving Agent and TransitionRecord

  - [x] 8.3 Write property test: Hook exception does not prevent remaining hooks (Property 13)
    - **Property 13: Hook exception does not prevent remaining hooks**
    - **Validates: Requirements 5.4**
    - Use automojo.testbase.properties to generate hook lists where hook K raises an exception
    - Assert hooks K+1 through N-1 are still invoked

  - [x] 8.4 Write property test: Hook deregistration removes hook (Property 14)
    - **Property 14: Hook deregistration removes hook**
    - **Validates: Requirements 5.5**
    - Register a hook, deregister it, trigger transition
    - Assert deregistered hook is not invoked

  - [x] 8.5 Write property test: Sub-agent add and remove correctness (Property 17)
    - **Property 17: Sub-agent add and remove correctness**
    - **Validates: Requirements 7.1, 7.2**
    - Add child as sub-agent, assert in sub_agents and parent set
    - Remove by identifier, assert reversed

  - [x] 8.6 Write property test: Parent lifecycle cascades to sub-agents (Property 18)
    - **Property 18: Parent lifecycle cascades to sub-agents**
    - **Validates: Requirements 7.5, 7.6, 7.7**
    - Create parent with RUNNING sub-agents
    - Assert stop cascades, pause cascades to RUNNING children, resume cascades to parent-paused children

  - [x] 8.7 Write property test: Sub-agent error notifies parent (Property 19)
    - **Property 19: Sub-agent error notifies parent**
    - **Validates: Requirements 7.8**
    - Create parent-child pair, transition child to ERROR
    - Assert parent on_error hooks invoked with child identity in record metadata

  - [x] 8.8 Write property test: Cycle detection prevents circular relationships (Property 20)
    - **Property 20: Cycle detection prevents circular parent-child relationships**
    - **Validates: Requirements 7.9, 7.10**
    - Use automojo.testbase.properties to generate agent hierarchies
    - Assert adding ancestor as sub-agent of descendant (or self) raises SemanticError

  - [x] 8.9 Write unit tests for Agent base class edge cases
    - Test abstract method enforcement (cannot instantiate Agent directly)
    - Test read-only properties
    - Test extension point integration with automojo-extension via testbase.mocking.Mock
    - Test structured logging: transition logged at INFO, hook exception at WARNING
    - Test agent-scoped logger naming pattern
    - Test __repr__ and __str__ output format
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2, 11.3, 11.4, 15.1, 15.2, 15.3, 15.4, 16.1, 16.2_

- [x] 9. Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement concurrency model support
  - [x] 10.1 Create `source/packages/automojo/agentkit/concurrencymodel.py` with ConcurrencyModel enum
    - Define ASYNCIO, THREAD, THREAD_POOL values
    - _Requirements: 13.1_

  - [x] 10.2 Create `source/packages/automojo/agentkit/asyncagent.py` with AsyncAgent base class
    - Extend Agent, lifecycle methods as async coroutines on asyncio event loop
    - Inherit all lifecycle, hook, sub-agent, and registry behaviors
    - _Requirements: 13.2, 13.5_

  - [x] 10.3 Create `source/packages/automojo/agentkit/threadedagent.py` with ThreadedAgent base class
    - Extend Agent, each instance runs on a dedicated thread
    - Inherit all lifecycle, hook, sub-agent, and registry behaviors
    - _Requirements: 13.3, 13.5_

  - [x] 10.4 Create `source/packages/automojo/agentkit/pooledagent.py` with PooledAgent base class
    - Extend Agent, instances run on a shared thread pool executor
    - Inherit all lifecycle, hook, sub-agent, and registry behaviors
    - _Requirements: 13.4, 13.5_

  - [x] 10.5 Implement cross-model communication bridge for parent-child agents with different concurrency models
    - Allow lifecycle operations and hook invocations to cross concurrency model boundaries
    - _Requirements: 13.8_

  - [x] 10.6 Write unit tests for concurrency models
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_concurrencymodel.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_asyncagent.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_threadedagent.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_pooledagent.py`
    - Test ConcurrencyModel enum values
    - Test AsyncAgent, ThreadedAgent, PooledAgent inherit Agent behaviors
    - Test cross-model communication bridge
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.8_

- [x] 11. Wire package together and create `__init__.py`
  - [x] 11.1 Create or update `source/packages/automojo/agentkit/__init__.py`
    - Export all public classes: Agent, AgentIdentity, AgentConfiguration, AgentStateMachine, AgentRegistry, LifecycleState, TransitionRecord, ConcurrencyModel, AsyncAgent, ThreadedAgent, PooledAgent, AgentKitError, ConfigurationError, SemanticError, LifecycleError
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 6.1, 13.1, 14.1_

  - [x] 11.2 Write integration tests for end-to-end agent lifecycle
    - Create `source/testroots/automojo/tests/singlehost/agentkit/test_agent_integration.py`
    - Test creating a concrete agent subclass, configuring it, running full lifecycle (create → initialize → start → pause → resume → stop)
    - Test sub-agent hierarchy with lifecycle cascading
    - Test registry tracks agents through full lifecycle
    - _Requirements: 1.1, 4.2, 5.1, 6.2, 7.1, 7.5_

- [x] 12. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples, edge cases, and external package integration using testbase.mocking.Mock
- All test files go under `source/testroots/automojo/tests/singlehost/agentkit/` mirroring the source hierarchy
- Run tests with: `source .venv/bin/activate && testbase testing run --root source/testroots/automojo --includes=automojo.tests.singlehost.agentkit --output=./.output`
