# Requirements Document — Core Agent Framework

## Introduction

The Core Agent Framework provides the foundational building blocks for the `automojo-agent-kit` Python SDK. It defines the base Agent abstraction, agent identity and metadata, a declarative configuration system, a state machine governing agent lifecycle transitions, lifecycle hooks for extensibility, an agent registry for instance management, and hierarchical agent composition. The framework integrates with existing automojo ecosystem packages: `automojo-credentials` for credential management, `automojo-dataprofiles` for data profile management, `automojo-this-app` for settings and directory-based app presence, `automojo-extension` for plugin extensibility, and `automojo-arcli` for command line interface.

## Glossary

- **Agent**: A configurable, stateful software entity managed by the framework that performs work on behalf of a user or system. An Agent has identity, configuration, lifecycle state, and optional sub-agents.
- **AgentRegistry**: A singleton registry that tracks all Agent instances created within a runtime, providing lookup, enumeration, and lifecycle management across agents.
- **AgentConfiguration**: A declarative configuration object that defines an Agent's identity, behavior, credentials references, data profile references, and sub-agent declarations.
- **AgentStateMachine**: The component that governs valid lifecycle state transitions for an Agent, enforcing the transition rules and emitting state change events.
- **LifecycleState**: One of the well-defined states an Agent can occupy: CREATED, INITIALIZED, RUNNING, PAUSED, STOPPED, or ERROR.
- **LifecycleHook**: A registered callback that the framework invokes at specific lifecycle transition points (e.g., on_initialize, on_start, on_pause, on_resume, on_stop, on_error).
- **SubAgent**: An Agent instance that is owned and managed by a parent Agent, forming a hierarchical composition tree.
- **AgentIdentity**: A metadata object containing the agent's unique identifier, human-readable name, version, and descriptive tags.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register additional capabilities, hooks, or tools with an Agent.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to secrets and credentials required by an Agent.
- **DataProfileReference**: A named reference resolved through `automojo-dataprofiles` that provides data profile configuration to an Agent.
- **AppContext**: The application context provided by `automojo-this-app` that supplies settings, environment variables, and directory-based presence for loading agent configurations.

## Requirements

### Requirement 1: Agent Base Definition

**User Story:** As a developer, I want a well-defined base Agent class with a clear protocol, so that I can create custom agents with consistent structure and behavior.

#### Acceptance Criteria

1. THE Agent base class SHALL define an abstract interface that includes methods for initialize, start, pause, resume, stop, and reset operations.
2. THE Agent base class SHALL require all subclasses to provide an implementation for the initialize, start, pause, resume, stop, and reset methods.
3. THE Agent base class SHALL expose a read-only property for the current LifecycleState of the Agent.
4. THE Agent base class SHALL expose a read-only property for the AgentIdentity of the Agent.
5. THE Agent base class SHALL expose a read-only property for the AgentConfiguration of the Agent.

### Requirement 2: Agent Identity and Metadata

**User Story:** As a developer, I want each agent to have a unique identity with descriptive metadata, so that I can distinguish and manage agents in a multi-agent environment.

#### Acceptance Criteria

1. THE AgentIdentity SHALL contain a unique string identifier, a human-readable name, a version string, and a dictionary of descriptive tags.
2. WHEN an Agent is created without an explicit unique identifier, THE AgentIdentity SHALL generate a UUID-based identifier automatically.
3. THE AgentIdentity SHALL expose all identity fields as read-only properties.
4. THE AgentIdentity SHALL provide an as_dict method that returns a dictionary representation of the identity fields.
5. THE AgentIdentity SHALL provide a to_json method that returns a JSON string representation of the identity fields.
6. FOR ALL valid AgentIdentity instances, converting to JSON and then parsing the JSON back SHALL produce an equivalent AgentIdentity object (round-trip property).

### Requirement 3: Agent Configuration System

**User Story:** As a developer, I want to configure agents declaratively using structured configuration, so that I can define agent behavior without modifying code.

#### Acceptance Criteria

1. THE AgentConfiguration SHALL support loading configuration from a Python dictionary.
2. THE AgentConfiguration SHALL support loading configuration from a JSON file path.
3. THE AgentConfiguration SHALL support loading configuration from a YAML file path.
4. WHEN a configuration file path is provided, THE AgentConfiguration SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
5. THE AgentConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
6. THE AgentConfiguration SHALL support CredentialReference entries that are resolved through `automojo-credentials` at initialization time.
7. THE AgentConfiguration SHALL support DataProfileReference entries that are resolved through `automojo-dataprofiles` at initialization time.
8. IF an invalid configuration value is provided, THEN THE AgentConfiguration SHALL raise a ConfigurationError with a descriptive message identifying the invalid field and the reason for rejection.
9. THE AgentConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration.
10. THE AgentConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration.
11. THE AgentConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration.
12. FOR ALL valid AgentConfiguration instances, converting to JSON and then parsing the JSON back SHALL produce an equivalent AgentConfiguration object (round-trip property).
13. FOR ALL valid AgentConfiguration instances, converting to YAML and then parsing the YAML back SHALL produce an equivalent AgentConfiguration object (round-trip property).

### Requirement 4: Agent Lifecycle State Machine

**User Story:** As a developer, I want a well-defined state machine governing agent lifecycle transitions, so that agents transition between states predictably and invalid transitions are prevented.

#### Acceptance Criteria

1. THE AgentStateMachine SHALL support the following LifecycleState values: CREATED, INITIALIZED, RUNNING, PAUSED, STOPPED, and ERROR.
2. THE AgentStateMachine SHALL enforce the following valid transitions:
   - CREATED to INITIALIZED
   - INITIALIZED to RUNNING
   - INITIALIZED to STOPPED
   - RUNNING to PAUSED
   - RUNNING to STOPPED
   - RUNNING to ERROR
   - PAUSED to RUNNING
   - PAUSED to STOPPED
   - ERROR to STOPPED
   - STOPPED to INITIALIZED (for agent reset and restart)
3. WHEN a valid transition is requested, THE AgentStateMachine SHALL update the current state to the target state.
4. IF an invalid state transition is requested, THEN THE AgentStateMachine SHALL raise a SemanticError that includes the current state, the requested target state, and a list of valid transitions from the current state.
5. WHEN a state transition occurs, THE AgentStateMachine SHALL record the previous state, the new state, and a timestamp for the transition.
6. THE AgentStateMachine SHALL expose a read-only property for the current LifecycleState.
7. THE AgentStateMachine SHALL expose a method that returns the list of valid target states from the current state.
8. THE AgentStateMachine SHALL expose a read-only property for the transition history as a list of transition records.

### Requirement 5: Lifecycle Hooks

**User Story:** As a developer, I want to register callbacks at specific lifecycle transition points, so that I can extend agent behavior without modifying the base agent class.

#### Acceptance Criteria

1. THE Agent base class SHALL support registration of LifecycleHook callbacks for the following transition points: on_initialize, on_start, on_pause, on_resume, on_stop, and on_error.
2. WHEN a lifecycle transition occurs, THE Agent base class SHALL invoke all registered LifecycleHook callbacks for the corresponding transition point in the order they were registered.
3. THE Agent base class SHALL pass the Agent instance and the transition record to each LifecycleHook callback when invoking the callback.
4. IF a LifecycleHook callback raises an exception during invocation, THEN THE Agent base class SHALL log the exception with the agent identity and hook name, and continue invoking the remaining registered hooks.
5. THE Agent base class SHALL support deregistration of a previously registered LifecycleHook callback by reference.
6. THE Agent base class SHALL support registration of LifecycleHook callbacks through the `automojo-extension` ExtensionPoint mechanism, allowing plugins to register hooks without direct access to the Agent instance.

### Requirement 6: Agent Registry

**User Story:** As a developer, I want a central registry that tracks all agent instances, so that I can look up, enumerate, and manage agents across the runtime.

#### Acceptance Criteria

1. THE AgentRegistry SHALL be a singleton instance within a runtime process.
2. WHEN an Agent is created, THE AgentRegistry SHALL automatically register the Agent using the Agent's unique identifier.
3. IF an Agent with a duplicate unique identifier is registered, THEN THE AgentRegistry SHALL raise a SemanticError that includes the duplicate identifier.
4. THE AgentRegistry SHALL support lookup of a registered Agent by unique identifier, returning the Agent instance or None when the identifier is not found.
5. THE AgentRegistry SHALL support lookup of registered Agents by name, returning a list of Agent instances matching the provided name.
6. THE AgentRegistry SHALL support lookup of registered Agents by tag key-value pairs, returning a list of Agent instances that match all provided tag criteria.
7. THE AgentRegistry SHALL support enumeration of all registered Agent instances as a list.
8. WHEN an Agent transitions to the STOPPED state, THE AgentRegistry SHALL support explicit deregistration of the Agent by unique identifier.
9. THE AgentRegistry SHALL expose a read-only property for the count of currently registered agents.

### Requirement 7: Hierarchical Agent Composition

**User Story:** As a developer, I want agents to own and manage sub-agents, so that I can build complex agent hierarchies where parent agents coordinate the work of child agents.

#### Acceptance Criteria

1. THE Agent base class SHALL support adding a SubAgent by providing an Agent instance to be managed as a child.
2. THE Agent base class SHALL support removing a SubAgent by unique identifier.
3. THE Agent base class SHALL expose a read-only property that returns the list of SubAgent instances managed by the Agent.
4. THE Agent base class SHALL expose a read-only property that returns the parent Agent instance, or None when the Agent has no parent.
5. WHEN a parent Agent transitions to the STOPPED state, THE parent Agent SHALL stop all SubAgent instances before completing the parent stop transition.
6. WHEN a parent Agent transitions to the PAUSED state, THE parent Agent SHALL pause all SubAgent instances that are in the RUNNING state before completing the parent pause transition.
7. WHEN a parent Agent transitions to the RUNNING state from PAUSED, THE parent Agent SHALL resume all SubAgent instances that were paused by the parent before completing the parent resume transition.
8. IF a SubAgent transitions to the ERROR state, THEN THE parent Agent SHALL receive notification of the SubAgent error through the on_error LifecycleHook with the SubAgent identity included in the transition record.
9. THE Agent base class SHALL prevent a circular parent-child relationship by validating that an Agent is not added as a SubAgent of itself or any of its descendants.
10. IF a circular parent-child relationship is detected, THEN THE Agent base class SHALL raise a SemanticError that identifies the Agent causing the cycle.

### Requirement 8: App Context Integration

**User Story:** As a developer, I want the agent framework to integrate with `automojo-this-app` for settings and environment configuration, so that agents can load configuration from a well-defined directory-based presence.

#### Acceptance Criteria

1. THE AgentConfiguration SHALL use the AppContext from `automojo-this-app` to resolve the base directory for loading configuration files.
2. THE AgentConfiguration SHALL use the AppContext from `automojo-this-app` to resolve environment variable references found in configuration values.
3. WHEN the AppContext is not available, THE AgentConfiguration SHALL raise a ConfigurationError with a descriptive message indicating that `automojo-this-app` must be initialized before creating agents.

### Requirement 9: Credential Integration

**User Story:** As a developer, I want agents to securely resolve credential references through `automojo-credentials`, so that secrets are managed centrally and not embedded in agent configuration files.

#### Acceptance Criteria

1. WHEN the AgentConfiguration contains CredentialReference entries, THE AgentConfiguration SHALL resolve each CredentialReference through the `automojo-credentials` package during initialization.
2. IF a CredentialReference cannot be resolved, THEN THE AgentConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
3. THE AgentConfiguration SHALL NOT include resolved credential values in the output of the as_dict, to_json, or to_yaml serialization methods.

### Requirement 10: Data Profile Integration

**User Story:** As a developer, I want agents to resolve data profile references through `automojo-dataprofiles`, so that agents can access managed data profiles for their operational context.

#### Acceptance Criteria

1. WHEN the AgentConfiguration contains DataProfileReference entries, THE AgentConfiguration SHALL resolve each DataProfileReference through the `automojo-dataprofiles` package during initialization.
2. IF a DataProfileReference cannot be resolved, THEN THE AgentConfiguration SHALL raise a ConfigurationError that identifies the unresolvable data profile name.

### Requirement 11: Extension Point Integration

**User Story:** As a developer, I want the agent framework to support extensibility through `automojo-extension`, so that plugins can register additional capabilities, hooks, and tools with agents.

#### Acceptance Criteria

1. THE Agent base class SHALL register ExtensionPoint entries with the `automojo-extension` package for each supported LifecycleHook transition point.
2. WHEN an Agent is initialized, THE Agent base class SHALL discover and load all registered extensions from `automojo-extension` that target the Agent's ExtensionPoint entries.
3. THE Agent base class SHALL provide an ExtensionPoint for registering custom tool capabilities with an Agent instance.
4. THE Agent base class SHALL expose a read-only property that returns the list of loaded extensions for the Agent.

### Requirement 12: Agent Serialization

**User Story:** As a developer, I want to serialize and deserialize agent identity and configuration, so that agent definitions can be stored, transmitted, and reconstructed.

#### Acceptance Criteria

1. THE AgentIdentity SHALL provide a to_json method that serializes the identity to a JSON string.
2. THE AgentIdentity SHALL provide a class method from_json that deserializes a JSON string into an AgentIdentity instance.
3. THE AgentConfiguration SHALL provide a to_json method that serializes the configuration to a JSON string.
4. THE AgentConfiguration SHALL provide a class method from_json that deserializes a JSON string into an AgentConfiguration instance.
5. THE AgentConfiguration SHALL provide a to_yaml method that serializes the configuration to a YAML string.
6. THE AgentConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into an AgentConfiguration instance.
7. FOR ALL valid AgentIdentity instances, calling to_json and then from_json SHALL produce an equivalent AgentIdentity object (round-trip property).
8. FOR ALL valid AgentConfiguration instances, calling to_json and then from_json SHALL produce an equivalent AgentConfiguration object (round-trip property).
9. FOR ALL valid AgentConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent AgentConfiguration object (round-trip property).

### Requirement 13: Concurrency Model Support

**User Story:** As a developer, I want the framework to support multiple threading models, so that I can choose the concurrency approach that best fits my agent's workload and integration requirements.

#### Acceptance Criteria

1. THE framework SHALL provide a ConcurrencyModel enum with values ASYNCIO, THREAD, and THREAD_POOL.
2. THE framework SHALL provide an AsyncAgent base class that runs its lifecycle methods as async coroutines on an asyncio event loop.
3. THE framework SHALL provide a ThreadedAgent base class that runs each agent instance on a dedicated thread.
4. THE framework SHALL provide a PooledAgent base class that runs agent instances on a shared thread pool executor.
5. THE AsyncAgent, ThreadedAgent, and PooledAgent base classes SHALL extend the Agent base class and inherit all lifecycle, hook, sub-agent, and registry behaviors.
6. THE AgentStateMachine SHALL be thread-safe, using appropriate synchronization primitives to protect state transitions from concurrent access.
7. THE AgentRegistry SHALL be thread-safe, using appropriate synchronization primitives to protect registration and lookup operations from concurrent access.
8. WHEN a parent agent and child agent use different concurrency models, THE framework SHALL provide a cross-model communication bridge that allows lifecycle operations and hook invocations to cross concurrency model boundaries.

### Requirement 14: Exception Hierarchy

**User Story:** As a developer, I want a well-defined exception hierarchy with descriptive messages, so that I can quickly diagnose and resolve errors in agent code.

#### Acceptance Criteria

1. THE framework SHALL provide an AgentKitError base exception class that all framework-specific exceptions inherit from.
2. THE ConfigurationError SHALL inherit from AgentKitError and SHALL be raised for configuration-related problems.
3. THE SemanticError SHALL inherit from AgentKitError and SHALL be raised for API misuse.
4. THE framework SHALL provide a LifecycleError that inherits from AgentKitError and SHALL be raised for errors that occur during lifecycle transitions.
5. ALL framework exceptions SHALL accept a descriptive message string and an optional cause exception.
6. ALL framework exceptions SHALL provide a meaningful __repr__ that includes the exception class name and the descriptive message.

### Requirement 15: Structured Logging

**User Story:** As a developer, I want the framework to use structured logging with a well-defined logger hierarchy, so that I can monitor and debug agent behavior using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy rooted at `automojo.agentkit`.
2. WHEN a lifecycle state transition occurs, THE framework SHALL log the transition at INFO level, including the agent identifier, the previous state, and the new state.
3. WHEN a LifecycleHook callback raises an exception, THE framework SHALL log the exception at WARNING level, including the agent identifier and the hook name.
4. THE Agent base class SHALL provide a method that returns a logger instance scoped to the agent's identity, using the naming pattern `automojo.agentkit.agent.<agent_identifier>`.

### Requirement 16: Agent String Representation

**User Story:** As a developer, I want meaningful string representations on framework classes, so that I can quickly inspect agent state during debugging sessions.

#### Acceptance Criteria

1. THE Agent base class SHALL provide a __repr__ method that includes the class name, agent identifier, agent name, and current lifecycle state.
2. THE Agent base class SHALL provide a __str__ method that returns a human-readable summary including the agent name and current lifecycle state.
3. THE AgentIdentity SHALL provide a __repr__ method that includes the class name, identifier, name, and version.
4. THE AgentIdentity SHALL provide a __str__ method that returns a human-readable summary including the name and version.
5. THE AgentStateMachine SHALL provide a __repr__ method that includes the class name and current state.
6. THE AgentStateMachine SHALL provide a __str__ method that returns the current state as a human-readable string.
7. THE AgentConfiguration SHALL provide a __repr__ method that includes the class name and identity configuration, and SHALL exclude resolved credential values from the representation.
8. THE AgentConfiguration SHALL provide a __str__ method that returns a human-readable summary of the configuration, excluding resolved credential values.
