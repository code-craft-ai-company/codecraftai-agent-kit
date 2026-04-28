# Requirements Document — Core Agent Framework

## Introduction

The Core Agent Framework provides the foundational building blocks for the `automojo-agent-kit` Python SDK. It defines the base Agent abstraction, agent identity and metadata, a declarative configuration system, a state machine governing agent lifecycle transitions, lifecycle hooks for extensibility, an agent registry for instance management, and hierarchical agent composition. The framework integrates with existing automojo ecosystem packages: `automojo-credentials` for credential management, `automojo-dataprofiles` for data profile management, `automojo-this-app` for settings and directory-based app presence, `automojo-extension` for plugin extensibility, and `automojo-arcli` for command line interface.

## Glossary

- **Agent**: A configurable, stateful software entity managed by the framework that performs work on behalf of a user or system. An Agent has identity, configuration, lifecycle state, and optional sub-agents.
- **AgentRegistry**: A singleton registry that tracks all Agent instances created within a runtime, providing lookup, enumeration, and lifecycle management across agents.
- **AgentConfiguration**: A declarative configuration object that defines an Agent's identity, behavior, credentials references, data profile references, and sub-agent declarations.
- **AgentStateMachine**: The component that governs valid lifecycle state transitions for an Agent, enforcing the transition rules and emitting state change events.
- **LifecycleState**: One of the well-defined states an Agent can occupy: CREATED, INITIALIZED, RUNNING, PAUSED, STOPPED, or ERROR.
- **TransitionRecord**: An immutable record capturing the previous state, new state, timestamp, and optional metadata for a lifecycle state transition.
- **LifecycleHook**: A registered callback that the framework invokes at specific lifecycle transition points (e.g., on_initialize, on_start, on_pause, on_resume, on_stop, on_error).
- **SubAgent**: An Agent instance that is owned and managed by a parent Agent, forming a hierarchical composition tree.
- **AgentIdentity**: A metadata object containing the agent's unique identifier, human-readable name, version, and descriptive tags.
- **AgentAddress**: An immutable object representing the network-addressable identity of an Agent, containing the agent identifier, transport name, and protocol-specific endpoint information.
- **ConcurrencyModel**: An enum representing the supported concurrency models for agents: ASYNCIO, THREAD, and THREAD_POOL.
- **AsyncAgent**: An abstract base class extending Agent that runs lifecycle methods as async coroutines on an asyncio event loop.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register additional capabilities, hooks, or tools with an Agent.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to secrets and credentials required by an Agent.
- **DataProfileReference**: A named reference resolved through `automojo-dataprofiles` that provides data profile configuration to an Agent.
- **AppContext**: The application context provided by `automojo-this-app` that supplies settings, environment variables, and directory-based presence for loading agent configurations.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **LifecycleError**: An exception raised for errors that occur during lifecycle transitions, inherited from AgentKitError.

## Requirements

### Requirement 1: Agent Base Definition

**User Story:** As a developer, I want a well-defined base Agent class with a clear protocol, so that I can create custom agents with consistent structure and behavior.

#### Acceptance Criteria

1. THE Agent base class SHALL define an abstract interface that includes methods for initialize, start, pause, resume, stop, and reset operations.
2. THE Agent base class SHALL require all subclasses to provide an implementation for the initialize, start, pause, resume, stop, and reset methods.
3. THE Agent base class SHALL expose a read-only property for the current LifecycleState of the Agent.
4. THE Agent base class SHALL expose a read-only property for the AgentIdentity of the Agent.
5. THE Agent base class SHALL expose a read-only property for the AgentConfiguration of the Agent.
6. WHEN an Agent is constructed, THE Agent base class SHALL create an AgentIdentity from the identity section of the provided AgentConfiguration.
7. WHEN an Agent is constructed, THE Agent base class SHALL create an AgentStateMachine with an initial state of CREATED.
8. WHEN an Agent is constructed, THE Agent base class SHALL register the Agent with the global AgentRegistry singleton.
9. THE Agent base class SHALL provide a __repr__ method that includes the class name, agent identifier, agent name, and current lifecycle state.
10. THE Agent base class SHALL provide a __str__ method that returns a human-readable summary including the agent name and current lifecycle state.

### Requirement 2: Agent Identity and Metadata

**User Story:** As a developer, I want each agent to have a unique identity with descriptive metadata, so that I can distinguish and manage agents in a multi-agent environment.

#### Acceptance Criteria

1. THE AgentIdentity SHALL contain a unique string identifier, a human-readable name, a version string, and a dictionary of descriptive tags.
2. WHEN an Agent is created without an explicit unique identifier, THE AgentIdentity SHALL generate a UUID-based identifier automatically.
3. THE AgentIdentity SHALL expose all identity fields as read-only properties.
4. THE AgentIdentity SHALL return a defensive copy of the tags dictionary from the tags property.
5. THE AgentIdentity SHALL provide an as_dict method that returns a dictionary representation of the identity fields.
6. THE AgentIdentity SHALL provide a to_json method that returns a JSON string representation of the identity fields.
7. THE AgentIdentity SHALL provide a class method from_json that deserializes a JSON string into an AgentIdentity instance.
8. FOR ALL valid AgentIdentity instances, calling to_json and then from_json SHALL produce an equivalent AgentIdentity object (round-trip property).
9. THE AgentIdentity SHALL provide a __repr__ method that includes the class name, identifier, name, and version.
10. THE AgentIdentity SHALL provide a __str__ method that returns a human-readable summary including the name and version.


### Requirement 3: Agent Configuration System

**User Story:** As a developer, I want to configure agents declaratively using structured configuration, so that I can define agent behavior without modifying code.

#### Acceptance Criteria

1. THE AgentConfiguration SHALL support loading configuration from a Python dictionary via a from_dict class method.
2. THE AgentConfiguration SHALL support loading configuration from a JSON string via a from_json class method.
3. THE AgentConfiguration SHALL support loading configuration from a JSON file path via a from_json_file class method.
4. THE AgentConfiguration SHALL support loading configuration from a YAML string via a from_yaml class method.
5. THE AgentConfiguration SHALL support loading configuration from a YAML file path via a from_yaml_file class method.
6. THE AgentConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. IF an invalid configuration value is provided, THEN THE AgentConfiguration SHALL raise a ConfigurationError with a descriptive message identifying the invalid field and the reason for rejection.
8. THE AgentConfiguration SHALL expose read-only properties for identity, settings, credentials, data_profiles, sub_agents, resolved_credentials, and resolved_data_profiles.
9. THE AgentConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration.
10. THE AgentConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration.
11. THE AgentConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration.
12. FOR ALL valid AgentConfiguration instances, calling to_json and then from_json SHALL produce an equivalent AgentConfiguration object (round-trip property).
13. FOR ALL valid AgentConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent AgentConfiguration object (round-trip property).
14. THE AgentConfiguration SHALL provide a __repr__ method that includes the class name and identity configuration, and SHALL exclude resolved credential values from the representation.
15. THE AgentConfiguration SHALL provide a __str__ method that returns a human-readable summary of the configuration, excluding resolved credential values.

### Requirement 4: Agent Lifecycle State Machine

**User Story:** As a developer, I want a well-defined state machine governing agent lifecycle transitions, so that agents transition between states predictably and invalid transitions are prevented.

#### Acceptance Criteria

1. THE AgentStateMachine SHALL support the following LifecycleState values: CREATED, INITIALIZED, RUNNING, PAUSED, STOPPED, and ERROR.
2. THE AgentStateMachine SHALL enforce the following valid transitions: CREATED to INITIALIZED; INITIALIZED to RUNNING or STOPPED; RUNNING to PAUSED, STOPPED, or ERROR; PAUSED to RUNNING or STOPPED; ERROR to STOPPED; STOPPED to INITIALIZED.
3. WHEN a valid transition is requested, THE AgentStateMachine SHALL update the current state to the target state.
4. IF an invalid state transition is requested, THEN THE AgentStateMachine SHALL raise a SemanticError that includes the current state, the requested target state, and a list of valid transitions from the current state.
5. WHEN a state transition occurs, THE AgentStateMachine SHALL record a TransitionRecord containing the previous state, the new state, a UTC timestamp, and optional metadata.
6. THE AgentStateMachine SHALL expose a read-only property for the current LifecycleState.
7. THE AgentStateMachine SHALL expose a method that returns the list of valid target states from the current state.
8. THE AgentStateMachine SHALL expose a read-only property for the transition history as a list of TransitionRecord instances.
9. THE AgentStateMachine SHALL be thread-safe, using a threading lock to protect state transitions from concurrent access.
10. THE AgentStateMachine SHALL provide a __repr__ method that includes the class name and current state.
11. THE AgentStateMachine SHALL provide a __str__ method that returns the current state as a human-readable string.

### Requirement 5: Transition Record

**User Story:** As a developer, I want an immutable record of each lifecycle state transition, so that I can audit and debug the history of agent state changes.

#### Acceptance Criteria

1. THE TransitionRecord SHALL contain the previous LifecycleState, the new LifecycleState, a UTC datetime timestamp, and an optional metadata dictionary.
2. THE TransitionRecord SHALL expose all fields as read-only properties.
3. THE TransitionRecord SHALL return a defensive copy of the metadata dictionary from the metadata property.
4. THE TransitionRecord SHALL provide a __repr__ method that includes the class name, previous state, new state, and timestamp.

### Requirement 6: Lifecycle Hooks

**User Story:** As a developer, I want to register callbacks at specific lifecycle transition points, so that I can extend agent behavior without modifying the base agent class.

#### Acceptance Criteria

1. THE Agent base class SHALL support registration of LifecycleHook callbacks for the following transition points: on_initialize, on_start, on_pause, on_resume, on_stop, and on_error.
2. WHEN a lifecycle transition occurs, THE Agent base class SHALL invoke all registered LifecycleHook callbacks for the corresponding transition point in the order they were registered.
3. THE Agent base class SHALL pass the Agent instance and the TransitionRecord to each LifecycleHook callback when invoking the callback.
4. IF a LifecycleHook callback raises an exception during invocation, THEN THE Agent base class SHALL log the exception at WARNING level including the agent identifier and the transition point, and continue invoking the remaining registered hooks.
5. THE Agent base class SHALL support deregistration of a previously registered LifecycleHook callback by reference.
6. IF an invalid transition point name is provided during hook registration, THEN THE Agent base class SHALL raise a SemanticError that includes the invalid transition point and the list of valid transition points.

### Requirement 7: Agent Registry

**User Story:** As a developer, I want a central registry that tracks all agent instances, so that I can look up, enumerate, and manage agents across the runtime.

#### Acceptance Criteria

1. THE AgentRegistry SHALL be a singleton instance within a runtime process, accessible via an instance() class method.
2. WHEN an Agent is created, THE Agent constructor SHALL automatically register the Agent with the AgentRegistry using the Agent's unique identifier.
3. IF an Agent with a duplicate unique identifier is registered, THEN THE AgentRegistry SHALL raise a SemanticError that includes the duplicate identifier.
4. THE AgentRegistry SHALL support lookup of a registered Agent by unique identifier, returning the Agent instance or None when the identifier is not found.
5. THE AgentRegistry SHALL support lookup of registered Agents by name, returning a list of Agent instances matching the provided name.
6. THE AgentRegistry SHALL support lookup of registered Agents by tag key-value pairs, returning a list of Agent instances that match all provided tag criteria.
7. THE AgentRegistry SHALL support enumeration of all registered Agent instances as a list.
8. THE AgentRegistry SHALL support deregistration of an Agent by unique identifier.
9. THE AgentRegistry SHALL expose a read-only property for the count of currently registered agents.
10. THE AgentRegistry SHALL be thread-safe, using a threading lock to protect registration, deregistration, and lookup operations from concurrent access.
11. THE AgentRegistry SHALL provide a __repr__ method that includes the class name and count of registered agents.
12. THE AgentRegistry SHALL provide a __str__ method that returns a human-readable summary of the registry.

### Requirement 8: Hierarchical Agent Composition

**User Story:** As a developer, I want agents to own and manage sub-agents, so that I can build complex agent hierarchies where parent agents coordinate the work of child agents.

#### Acceptance Criteria

1. THE Agent base class SHALL support adding a SubAgent by providing an Agent instance to be managed as a child.
2. THE Agent base class SHALL support removing a SubAgent by unique identifier.
3. THE Agent base class SHALL expose a read-only property that returns the list of SubAgent instances managed by the Agent.
4. THE Agent base class SHALL expose a read-only property that returns the parent Agent instance, or None when the Agent has no parent.
5. WHEN a SubAgent is added, THE Agent base class SHALL set the parent reference on the child Agent to the parent Agent.
6. WHEN a SubAgent is removed, THE Agent base class SHALL clear the parent reference on the removed child Agent.
7. IF a SubAgent transitions to the ERROR state, THEN THE parent Agent SHALL receive notification of the SubAgent error through the on_error LifecycleHook with the child identifier and child name included in the transition record metadata.
8. THE Agent base class SHALL prevent a circular parent-child relationship by walking up the ancestor chain and validating that the agent being added is not an ancestor of the parent.
9. THE Agent base class SHALL prevent an Agent from being added as a SubAgent of itself.
10. IF a circular parent-child relationship is detected, THEN THE Agent base class SHALL raise a SemanticError that identifies the Agent causing the cycle and the attempted parent.


### Requirement 9: Agent Address

**User Story:** As a developer, I want an immutable address object for agents, so that agents can be located and routed to across different transport mechanisms.

#### Acceptance Criteria

1. THE AgentAddress SHALL contain an agent identifier string, a transport name string, and an optional dictionary of protocol-specific endpoint information.
2. THE AgentAddress SHALL expose all fields as read-only properties.
3. THE AgentAddress SHALL return a defensive copy of the endpoint dictionary from the endpoint property.
4. THE AgentAddress SHALL provide an as_dict method that returns a dictionary representation of the address fields.
5. THE AgentAddress SHALL provide a to_json method that returns a JSON string representation of the address fields.
6. THE AgentAddress SHALL provide a class method from_dict that constructs an AgentAddress from a dictionary.
7. THE AgentAddress SHALL provide a class method from_json that deserializes a JSON string into an AgentAddress instance.
8. FOR ALL valid AgentAddress instances, calling to_json and then from_json SHALL produce an equivalent AgentAddress object (round-trip property).
9. THE AgentAddress SHALL implement equality comparison based on agent_identifier and transport_name fields.
10. THE AgentAddress SHALL implement a hash method based on agent_identifier and transport_name, enabling use as dictionary keys and set members.
11. THE AgentAddress SHALL provide a __repr__ method that includes the class name, agent identifier, and transport name.
12. THE AgentAddress SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, transport name, and endpoint information.

### Requirement 10: Concurrency Model Support

**User Story:** As a developer, I want the framework to support multiple concurrency models, so that I can choose the approach that best fits my agent's workload and integration requirements.

#### Acceptance Criteria

1. THE framework SHALL provide a ConcurrencyModel enum with values ASYNCIO, THREAD, and THREAD_POOL.
2. THE framework SHALL provide an AsyncAgent base class that runs its lifecycle methods as async coroutines on an asyncio event loop.
3. THE AsyncAgent SHALL extend the Agent base class and inherit all lifecycle, hook, sub-agent, and registry behaviors.
4. THE AsyncAgent SHALL define abstract async lifecycle methods: async_initialize, async_start, async_pause, async_resume, async_stop, and async_reset.
5. THE AsyncAgent synchronous lifecycle methods SHALL delegate to the corresponding async lifecycle methods by running them on the event loop.
6. WHEN an asyncio event loop is already running, THE AsyncAgent SHALL schedule the coroutine as a task on the existing loop.
7. WHEN no asyncio event loop is running, THE AsyncAgent SHALL create a new event loop and run the coroutine to completion.

### Requirement 11: Credential Integration

**User Story:** As a developer, I want agents to securely resolve credential references through `automojo-credentials`, so that secrets are managed centrally and not embedded in agent configuration files.

#### Acceptance Criteria

1. WHEN the AgentConfiguration contains CredentialReference entries, THE AgentConfiguration SHALL resolve each CredentialReference through the `automojo-credentials` package during initialization.
2. IF a CredentialReference cannot be resolved, THEN THE AgentConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
3. THE AgentConfiguration SHALL NOT include resolved credential values in the output of the as_dict, to_json, or to_yaml serialization methods.

### Requirement 12: Data Profile Integration

**User Story:** As a developer, I want agents to resolve data profile references through `automojo-dataprofiles`, so that agents can access managed data profiles for their operational context.

#### Acceptance Criteria

1. WHEN the AgentConfiguration contains DataProfileReference entries, THE AgentConfiguration SHALL resolve each DataProfileReference through the `automojo-dataprofiles` package during initialization.
2. IF a DataProfileReference cannot be resolved, THEN THE AgentConfiguration SHALL raise a ConfigurationError that identifies the unresolvable data profile name.

### Requirement 13: Extension Point Integration

**User Story:** As a developer, I want the agent framework to support extensibility through `automojo-extension`, so that plugins can register additional capabilities, hooks, and tools with agents.

#### Acceptance Criteria

1. THE Agent base class SHALL integrate with the `automojo-extension` PluginManager for discovering and loading extensions during initialization.
2. WHEN an Agent is initialized, THE Agent base class SHALL discover and load all registered extensions from `automojo-extension` that target the Agent's ExtensionPoint entries.
3. THE Agent base class SHALL expose a read-only property that returns the list of loaded extensions for the Agent.
4. IF a plugin fails to load during initialization, THEN THE Agent base class SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.

### Requirement 14: Exception Hierarchy

**User Story:** As a developer, I want a well-defined exception hierarchy with descriptive messages, so that I can quickly diagnose and resolve errors in agent code.

#### Acceptance Criteria

1. THE framework SHALL provide an AgentKitError base exception class that all framework-specific exceptions inherit from.
2. THE ConfigurationError SHALL inherit from AgentKitError and SHALL be raised for configuration-related problems.
3. THE SemanticError SHALL inherit from AgentKitError and SHALL be raised for API misuse.
4. THE LifecycleError SHALL inherit from AgentKitError and SHALL be raised for errors that occur during lifecycle transitions.
5. ALL framework exceptions SHALL accept a descriptive message string and an optional cause exception.
6. WHEN a cause exception is provided, THE framework exception SHALL chain the cause using Python's exception chaining mechanism.
7. ALL framework exceptions SHALL provide a meaningful __repr__ that includes the exception class name and the descriptive message.

### Requirement 15: Structured Logging

**User Story:** As a developer, I want the framework to use structured logging with a well-defined logger hierarchy, so that I can monitor and debug agent behavior using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy rooted at `automojo.agentkit`.
2. WHEN a lifecycle state transition occurs, THE framework SHALL log the transition at INFO level, including the agent identifier, the previous state, and the new state.
3. WHEN a LifecycleHook callback raises an exception, THE framework SHALL log the exception at WARNING level, including the agent identifier and the transition point.
4. THE Agent base class SHALL provide a get_logger method that returns a logger instance scoped to the agent's identity, using the naming pattern `automojo.agentkit.agent.<agent_identifier>`.

### Requirement 16: App Context Integration

**User Story:** As a developer, I want the agent framework to integrate with `automojo-this-app` for settings and environment configuration, so that agents can load configuration from a well-defined directory-based presence.

#### Acceptance Criteria

1. THE AgentConfiguration SHALL accept an optional AppContext parameter for resolving file paths and environment variable references during configuration loading.
2. WHEN an AppContext is provided, THE AgentConfiguration SHALL use the AppContext to resolve credential references and data profile references.
3. WHEN an AppContext is not provided, THE AgentConfiguration SHALL proceed without resolving credential and data profile references, leaving them as unresolved entries.
