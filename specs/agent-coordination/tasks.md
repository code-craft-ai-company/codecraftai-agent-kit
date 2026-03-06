# Implementation Plan: Agent Coordination

## Overview

Bottom-up implementation of the Agent Coordination feature for the `automojo-agent-kit` SDK. Starts with foundational data objects (enums, immutable DTOs), then builds registries and trackers, then coordination protocols, and finally wires everything into the Agent base class. All source files go under `source/packages/automojo/agentkit/coordination/` and tests under `source/testroots/automojo/tests/singlehost/agentkit/coordination/`.

## Tasks

- [ ] 1. Create package structure and exception hierarchy
  - [ ] 1.1 Create coordination package directories and `__init__.py` files
    - Create `source/packages/automojo/agentkit/coordination/__init__.py`
    - Create `source/packages/automojo/agentkit/coordination/protocols/__init__.py`
    - Create `source/packages/automojo/agentkit/coordination/handlers/__init__.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/coordination/__init__.py`
    - Create `source/testroots/automojo/tests/singlehost/agentkit/coordination/protocols/__init__.py`
    - _Requirements: Design file layout table_

  - [ ] 1.2 Implement coordination exception hierarchy in `coordination/errors.py`
    - Implement `TaskDelegationError` inheriting from `AgentKitError` with optional `cause`, `target_agent_id`, `task_request_id` properties and `__repr__`
    - Implement `TaskTimeoutError` inheriting from `AgentKitError` with optional `cause`, `task_request_id`, `timeout_duration` properties and `__repr__`
    - Implement `CapabilityNotFoundError` inheriting from `AgentKitError` with optional `cause`, `capability_name`, `task_type` properties and `__repr__`
    - Implement `TaskQueueFullError` inheriting from `AgentKitError` with optional `cause` property and `__repr__`
    - Use multi-line error message formation pattern per coding standards
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9_

  - [ ] 1.3 Write unit tests for exception hierarchy in `coordination/test_errors.py`
    - Test correct inheritance from `AgentKitError`
    - Test diagnostic context field access (`target_agent_id`, `task_request_id`, `timeout_duration`, `capability_name`, `task_type`, `cause`)
    - Test `__repr__` includes class name, message, and diagnostic fields
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9_

- [ ] 2. Implement TaskStatus enumeration
  - [ ] 2.1 Implement `TaskStatus` enum in `coordination/taskstatus.py`
    - Define enum members: PENDING, ACCEPTED, RUNNING, COMPLETED, FAILED, TIMED_OUT, CANCELLED
    - Implement `is_terminal` read-only property returning True for COMPLETED, FAILED, TIMED_OUT, CANCELLED
    - Implement `from_string` class method with case-insensitive matching, raising `SemanticError` for invalid values
    - Implement `__str__` returning the status value as lowercase string
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 19.5_

  - [ ] 2.2 Write unit tests for `TaskStatus` in `coordination/test_taskstatus.py`
    - Test all seven enum members exist with correct string values
    - Test `is_terminal` returns True for COMPLETED, FAILED, TIMED_OUT, CANCELLED and False for PENDING, ACCEPTED, RUNNING
    - Test `from_string` with valid lowercase, uppercase, and mixed-case inputs
    - Test `from_string` raises `SemanticError` for invalid string values
    - Test `__str__` returns lowercase value for each member
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 19.5_

- [ ] 3. Implement TaskRequest data object
  - [ ] 3.1 Implement `TaskRequest` in `coordination/taskrequest.py`
    - Implement `__init__` with `task_type`, `parameters`, `requester_agent_id`, `priority` (default 0), `deadline` (default None), `metadata` (default None), `identifier` (auto-generated UUID if None)
    - Implement read-only properties: `identifier`, `task_type`, `parameters`, `priority`, `deadline`, `requester_agent_id`, `metadata`
    - Implement `as_dict`, `to_json`, `from_dict`, `from_json` methods with ISO 8601 deadline handling
    - Implement `__repr__` and `__str__` per design
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.10, 1.11, 18.1, 19.1, 19.2_

  - [ ] 3.2 Write unit tests for `TaskRequest` in `coordination/test_taskrequest.py`
    - Test construction with all fields, with defaults, and with auto-generated identifier
    - Test read-only properties return correct values
    - Test `as_dict` returns correct dictionary representation
    - Test `to_json` / `from_json` round-trip produces equivalent object
    - Test `from_dict` with and without optional fields
    - Test `__repr__` includes class name, identifier, task_type, priority
    - Test `__str__` includes task_type, priority, requester_agent_id
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 18.1, 18.6, 19.1, 19.2_

- [ ] 4. Implement TaskResponse data object
  - [ ] 4.1 Implement `TaskResponse` in `coordination/taskresponse.py`
    - Implement `__init__` with `task_request_id`, `status` (TaskStatus), `responder_agent_id`, `result` (default None), `error_info` (default None), `completion_timestamp` (default UTC now)
    - Implement read-only properties: `task_request_id`, `status`, `result`, `error_info`, `responder_agent_id`, `completion_timestamp`, `is_success`
    - Implement `as_dict`, `to_json`, `from_dict`, `from_json` methods
    - Implement `__repr__` and `__str__` per design
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.10, 2.11, 18.2, 19.3, 19.4_

  - [ ] 4.2 Write unit tests for `TaskResponse` in `coordination/test_taskresponse.py`
    - Test construction with all fields and with auto-generated timestamp
    - Test `is_success` returns True only for COMPLETED status
    - Test `to_json` / `from_json` round-trip produces equivalent object
    - Test `__repr__` and `__str__` content
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 18.2, 18.7, 19.3, 19.4_

- [ ] 5. Checkpoint - Verify foundational data objects
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 6. Implement AgentCapability data object
  - [ ] 6.1 Implement `AgentCapability` in `coordination/agentcapability.py`
    - Implement `__init__` with `capability_name`, `description`, `supported_task_types` (stored as frozenset), `input_schema` (default {}), `output_schema` (default {}), `metadata` (default {})
    - Implement read-only properties: `capability_name`, `description`, `supported_task_types`, `input_schema`, `output_schema`, `metadata`
    - Implement `supports_task_type` method
    - Implement `as_dict`, `to_json`, `from_dict`, `from_json` methods
    - Implement `__repr__` and `__str__` per design
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9, 4.10, 18.3, 19.6, 19.7_

  - [ ] 6.2 Write unit tests for `AgentCapability` in `coordination/test_agentcapability.py`
    - Test construction with all fields and defaults
    - Test `supports_task_type` with matching and non-matching types
    - Test `to_json` / `from_json` round-trip produces equivalent object
    - Test `__repr__` includes class name, capability_name, task type count
    - Test `__str__` includes capability_name, description, supported task types
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 18.3, 18.8, 19.6, 19.7_

- [ ] 7. Implement CapabilityAdvertisement data object
  - [ ] 7.1 Implement `CapabilityAdvertisement` in `coordination/capabilityadvertisement.py`
    - Implement `__init__` with `agent_id`, `capabilities` (list of AgentCapability), `timestamp` (default UTC now)
    - Implement read-only properties: `agent_id`, `capabilities`, `timestamp`
    - Implement `as_dict`, `to_json`, `from_dict`, `from_json` methods (nested AgentCapability serialization)
    - Implement `__repr__` and `__str__` per design
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.9, 5.10, 18.4, 19.8, 19.9_

  - [ ] 7.2 Write unit tests for `CapabilityAdvertisement` in `coordination/test_capabilityadvertisement.py`
    - Test construction with explicit timestamp and auto-generated timestamp
    - Test `capabilities` property returns a copy of the list
    - Test `to_json` / `from_json` round-trip with nested AgentCapability objects
    - Test `__repr__` and `__str__` content
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 18.4, 18.9, 19.8, 19.9_

- [ ] 8. Implement CoordinationConfiguration
  - [ ] 8.1 Implement `CoordinationConfiguration` in `coordination/coordinationconfiguration.py`
    - Implement `__init__` with `default_timeout` (60.0), `default_priority` (0), `max_concurrent_delegations` (10), `task_queue_capacity` (100), `retry_policy` (None)
    - Implement validation: timeout > 0, max_concurrent >= 1, queue_capacity >= 1, raising `ConfigurationError`
    - Implement read-only properties for all fields
    - Implement `as_dict`, `to_json`, `to_yaml`, `from_dict`, `from_json`, `from_yaml`, `from_json_file`, `from_yaml_file` methods
    - Implement `__repr__` and `__str__` per design
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10, 14.11, 14.12, 14.13, 14.14, 14.15, 14.18, 14.19, 18.5, 19.16, 19.17_

  - [ ] 8.2 Write unit tests for `CoordinationConfiguration` in `coordination/test_coordinationconfiguration.py`
    - Test construction with defaults and custom values
    - Test validation raises `ConfigurationError` for timeout <= 0, max_concurrent < 1, queue_capacity < 1
    - Test `from_dict`, `from_json`, `from_yaml` loading
    - Test `to_json` / `from_json` round-trip
    - Test `to_yaml` / `from_yaml` round-trip
    - Test `__repr__` and `__str__` content
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.6, 14.7, 14.8, 14.9, 14.10, 14.11, 14.12, 14.13, 14.14, 14.15, 14.16, 14.17, 14.18, 14.19, 18.5, 18.10, 19.16, 19.17_

- [ ] 9. Checkpoint - Verify all data objects and configuration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement CapabilityRegistry
  - [ ] 10.1 Implement `CapabilityRegistry` in `coordination/capabilityregistry.py`
    - Implement thread-safe `register`, `deregister`, `find_by_capability_name`, `find_by_task_type`, `get_advertisement`, `list_all` methods using `threading.Lock`
    - Implement `agent_count` read-only property
    - Implement `has_capability` and `has_task_type` convenience methods
    - Implement `__repr__` and `__str__` per design
    - Add structured logging at INFO level for registration/deregistration
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 17.1, 19.10, 19.11, 21.1_

  - [ ] 10.2 Write unit tests for `CapabilityRegistry` in `coordination/test_capabilityregistry.py`
    - Test register and retrieve advertisement
    - Test re-registration replaces previous advertisement
    - Test deregister removes agent capabilities
    - Test `find_by_capability_name` returns correct agent IDs
    - Test `find_by_task_type` returns correct agent IDs
    - Test `get_advertisement` returns None for unknown agent
    - Test `list_all` returns all advertisements
    - Test `has_capability` and `has_task_type` boolean results
    - Test `agent_count` property
    - Test `__repr__` and `__str__` content
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 6.11, 6.12, 6.13, 19.10, 19.11, 21.1_

- [ ] 11. Implement TaskTracker
  - [ ] 11.1 Implement `TaskTracker` in `coordination/tasktracker.py`
    - Implement thread-safe `register`, `update_status`, `get_status`, `get_task`, `get_active_tasks`, `get_completed_tasks` methods using `threading.Lock`
    - Implement `cancel_task` raising `SemanticError` for unknown task IDs
    - Implement `check_timeouts` updating status to TIMED_OUT and raising `TaskTimeoutError`
    - Implement `active_count` and `total_count` read-only properties
    - Implement `__repr__` and `__str__` per design
    - Add structured logging at INFO/WARNING levels
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 8.13, 8.14, 8.15, 8.16, 17.1, 17.4, 19.12, 19.13, 21.2_

  - [ ] 11.2 Write unit tests for `TaskTracker` in `coordination/test_tasktracker.py`
    - Test register sets initial status to PENDING
    - Test update_status changes tracked status
    - Test get_status returns None for unknown task
    - Test get_active_tasks and get_completed_tasks filtering
    - Test cancel_task updates status to CANCELLED
    - Test cancel_task raises `SemanticError` for unknown task ID
    - Test check_timeouts detects expired deadlines and raises `TaskTimeoutError`
    - Test `active_count` and `total_count` properties
    - Test `__repr__` and `__str__` content
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 8.13, 8.14, 8.15, 8.16, 19.12, 19.13, 21.2_

- [ ] 12. Implement TaskQueue
  - [ ] 12.1 Implement `TaskQueue` in `coordination/taskqueue.py`
    - Implement thread-safe `enqueue`, `dequeue`, `peek`, `remove` methods using `threading.Lock` and `heapq`
    - Implement priority ordering with higher priority values dispatched first (negate for min-heap)
    - Implement capacity enforcement raising `TaskQueueFullError`
    - Implement `size`, `max_capacity`, `is_empty` read-only properties
    - Implement `__repr__` and `__str__` per design
    - Add structured logging at DEBUG level for enqueue/dequeue
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 13.12, 13.13, 17.1, 17.6, 19.14, 19.15, 21.3_

  - [ ] 12.2 Write unit tests for `TaskQueue` in `coordination/test_taskqueue.py`
    - Test enqueue and dequeue returns highest priority first
    - Test peek returns highest priority without removing
    - Test remove by task request identifier
    - Test capacity enforcement raises `TaskQueueFullError`
    - Test `size`, `max_capacity`, `is_empty` properties
    - Test dequeue and peek return None on empty queue
    - Test `__repr__` and `__str__` content
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 13.12, 13.13, 19.14, 19.15, 21.3_

- [ ] 13. Checkpoint - Verify registries, tracker, and queue
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 14. Implement DelegationHandler and CoordinationProtocol base class
  - [ ] 14.1 Implement `DelegationHandler` type alias in `coordination/handlers/delegationhandler.py`
    - Define `DelegationHandler` as a `Callable[[TaskRequest], TaskResponse]` type alias
    - _Requirements: 15.1_

  - [ ] 14.2 Implement `CoordinationProtocol` abstract base class in `coordination/protocols/coordinationprotocol.py`
    - Implement `__init__` accepting `protocol_name`, raising `SemanticError` for empty/None name
    - Implement `protocol_name` read-only property
    - Define abstract `coordinate` method accepting `TaskRequest` and `CoordinationConfiguration`
    - Implement `__repr__` and `__str__` per design
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 19.18, 19.19_

  - [ ] 14.3 Write unit tests for `CoordinationProtocol` in `coordination/protocols/test_coordinationprotocol.py`
    - Test that `CoordinationProtocol` cannot be instantiated directly (abstract)
    - Test concrete subclass can be instantiated with valid protocol name
    - Test `SemanticError` raised for empty or None protocol name
    - Test `protocol_name` property, `__repr__`, and `__str__`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 19.18, 19.19_

- [ ] 15. Implement DirectDelegationProtocol
  - [ ] 15.1 Implement `DirectDelegationProtocol` in `coordination/protocols/directdelegationprotocol.py`
    - Implement `__init__` accepting `address_resolver`, `transport`, optional `agent_registry`
    - Set protocol name to "direct"
    - Implement `coordinate` method: extract `target_agent_id` from metadata, check local registry first, fall back to remote via transport
    - Implement `_delegate_local` delivering TaskRequest to target agent's DelegationHandler
    - Implement `_delegate_remote` serializing TaskRequest into Message and sending via Transport
    - Raise `TaskDelegationError` for missing target_agent_id or unreachable agent
    - Add structured logging at INFO level
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 17.1, 17.2_

  - [ ] 15.2 Write unit tests for `DirectDelegationProtocol` in `coordination/protocols/test_directdelegationprotocol.py`
    - Test local delegation via mocked AgentRegistry (agent found locally)
    - Test remote delegation via mocked Transport and AddressResolver (agent not local)
    - Test `TaskDelegationError` raised when `target_agent_id` missing from metadata
    - Test `TaskDelegationError` raised when remote agent unreachable
    - Use `automojo.testbase.mocking.Mock` for all external dependencies
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 16. Implement CapabilityRoutingProtocol
  - [ ] 16.1 Implement `CapabilityRoutingProtocol` in `coordination/protocols/capabilityroutingprotocol.py`
    - Implement `__init__` accepting `capability_registry`, `task_tracker`, `address_resolver`, `transport`, optional `agent_registry`
    - Set protocol name to "capability_routing"
    - Implement `coordinate` method: query CapabilityRegistry by task type, select least-loaded agent via TaskTracker, delegate via DirectDelegationProtocol
    - Implement `_sort_by_load` sorting agents by active task count ascending
    - Implement fallback: try next agent if selected agent fails
    - Raise `CapabilityNotFoundError` when no agent supports the task type
    - Raise `TaskDelegationError` when all capable agents fail
    - Add structured logging at INFO/WARNING levels
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 17.1, 17.5_

  - [ ] 16.2 Write unit tests for `CapabilityRoutingProtocol` in `coordination/protocols/test_capabilityroutingprotocol.py`
    - Test routing to single capable agent
    - Test load balancing selects agent with fewest active tasks
    - Test fallback to next agent when first agent fails
    - Test `CapabilityNotFoundError` raised when no agent supports task type
    - Test `TaskDelegationError` raised when all agents fail
    - Use `automojo.testbase.mocking.Mock` for external dependencies
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ] 17. Implement FanOutFanInProtocol
  - [ ] 17.1 Implement `FanOutFanInProtocol` in `coordination/protocols/fanoutfaninprotocol.py`
    - Implement `__init__` accepting `address_resolver`, `transport`, optional `agent_registry`
    - Set protocol name to "fan_out_fan_in"
    - Implement `coordinate` method: extract `target_agent_ids` from metadata, delegate concurrently using `concurrent.futures.ThreadPoolExecutor`
    - Collect all TaskResponse objects, include TIMED_OUT responses for unresponsive agents
    - Support optional `aggregator` callable from metadata
    - Raise `TaskDelegationError` when `target_agent_ids` missing or empty
    - Add structured logging at INFO level
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 17.1_

  - [ ] 17.2 Write unit tests for `FanOutFanInProtocol` in `coordination/protocols/test_fanoutfaninprotocol.py`
    - Test fan-out to multiple agents collects all responses
    - Test TIMED_OUT response included for unresponsive agents
    - Test aggregator callable applied to responses
    - Test `TaskDelegationError` raised when `target_agent_ids` missing
    - Use `automojo.testbase.mocking.Mock` for external dependencies
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8_

- [ ] 18. Checkpoint - Verify all coordination protocols
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Integrate coordination into Agent base class
  - [ ] 19.1 Extend Agent base class with coordination support
    - Add `_task_tracker`, `_capability_registry`, `_delegation_handler`, `_coordination_configuration`, `_coordination_protocols` attributes to `Agent.__init__`
    - Load `CoordinationConfiguration` from `AgentConfiguration.options["coordination"]` if present, otherwise use defaults
    - Implement `task_tracker` and `capability_registry` read-only properties
    - Implement `coordination_protocols` read-only property
    - Implement `delegate_task` method: register in tracker, check local AgentRegistry, fall back to remote transport, update tracker with response
    - Implement `delegate_task_by_capability` method: query CapabilityRegistry, delegate to discovered agent
    - Implement `register_delegation_handler` and `deregister_delegation_handler` methods
    - Implement `handle_incoming_task` method: invoke handler, catch exceptions, return FAILED response if no handler or handler raises
    - Implement `get_coordination_logger` returning logger scoped to `automojo.agentkit.coordination.<agent_id>`
    - Implement `_delegate_local` and `_delegate_remote` private methods
    - Implement `_load_coordination_extensions` for automojo-extension integration
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 15.2, 15.3, 15.4, 15.5, 17.2, 17.3, 17.7, 17.8, 20.1, 20.2, 20.3, 20.4, 21.4_

  - [ ] 19.2 Write unit tests for Agent coordination integration in `coordination/test_agent_coordination.py`
    - Test `delegate_task` with local agent (mocked AgentRegistry returns target)
    - Test `delegate_task` with remote agent (mocked Transport)
    - Test `delegate_task_by_capability` discovers and delegates to capable agent
    - Test `delegate_task_by_capability` raises `CapabilityNotFoundError` when no agent found
    - Test `register_delegation_handler` and `deregister_delegation_handler`
    - Test `handle_incoming_task` invokes registered handler
    - Test `handle_incoming_task` returns FAILED when no handler registered
    - Test `handle_incoming_task` returns FAILED with error info when handler raises exception
    - Test `task_tracker` and `capability_registry` properties
    - Use `automojo.testbase.mocking.Mock` for Agent, AgentRegistry, Transport, AddressResolver
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 15.2, 15.3, 15.4, 15.5, 17.2, 17.3, 17.7, 17.8, 21.4_

- [ ] 20. Wire up package exports in `__init__.py` files
  - Update `coordination/__init__.py` to export all public classes: `TaskStatus`, `TaskRequest`, `TaskResponse`, `AgentCapability`, `CapabilityAdvertisement`, `CapabilityRegistry`, `TaskTracker`, `TaskQueue`, `CoordinationConfiguration`, `TaskDelegationError`, `TaskTimeoutError`, `CapabilityNotFoundError`, `TaskQueueFullError`
  - Update `coordination/protocols/__init__.py` to export: `CoordinationProtocol`, `DirectDelegationProtocol`, `CapabilityRoutingProtocol`, `FanOutFanInProtocol`
  - Update `coordination/handlers/__init__.py` to export: `DelegationHandler`
  - _Requirements: Design file layout table_

- [ ] 21. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- All source files use lowercase filenames with no underscores per project naming conventions
- Tests use `testbase` framework and `automojo.testbase.mocking` for mocks
- Implementation follows bottom-up order: data objects → registries → protocols → agent integration → exports
