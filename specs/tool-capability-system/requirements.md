# Requirements Document — Tool & Capability System

## Introduction

The Tool & Capability System extends the Core Agent Framework of the `automojo-agent-kit` SDK with a structured mechanism for defining, registering, discovering, validating, executing, chaining, and composing tools that agents use to perform work. A tool is a discrete, reusable unit of functionality with a declared input schema, output schema, and execution logic. The system provides a tool registry for discovery, an executor for validated invocation, a chaining mechanism for composing tool pipelines, a set of built-in tools for common operations (file I/O, HTTP, shell), and a custom tool development API. The system integrates with the Agent base class so agents can register and invoke tools, with `automojo-extension` so tool plugins can be discovered and loaded, and with `automojo-credentials` so tools can securely access credentials when needed.

## Glossary

- **Tool**: A discrete, reusable unit of functionality with a declared name, description, input schema, output schema, and an execute method. A Tool is registered with a ToolRegistry and invoked through a ToolExecutor.
- **ToolDescriptor**: An immutable metadata object that describes a Tool's name, description, version, input schema, output schema, and tags. The ToolDescriptor is used for discovery and documentation without requiring access to the Tool implementation.
- **ToolSchema**: A declarative schema definition that describes the structure, types, and constraints of a Tool's input parameters or output values. ToolSchema is used for validation before execution and after execution.
- **ToolRegistry**: A registry that tracks all Tool instances available to an Agent or runtime, providing lookup by name, tag, and enumeration. Each Agent maintains a ToolRegistry instance.
- **ToolExecutor**: The component responsible for validating inputs against the Tool's input schema, invoking the Tool's execute method, validating outputs against the Tool's output schema, and returning a ToolResult.
- **ToolResult**: An immutable object that encapsulates the outcome of a Tool execution, containing the output value, execution status (success or failure), execution duration, and any error information.
- **ToolChain**: An ordered sequence of Tool references with optional input-output mappings that defines a pipeline where the output of one Tool feeds as input to the next Tool.
- **ToolChainExecutor**: The component responsible for executing a ToolChain by running each Tool in sequence, passing mapped outputs to subsequent inputs, and returning a ToolChainResult.
- **ToolChainResult**: An immutable object that encapsulates the outcome of a ToolChain execution, containing the final output value, the list of individual ToolResult objects for each step, overall execution status, and total execution duration.
- **ToolPlugin**: A tool implementation discovered and loaded through the `automojo-extension` ExtensionPoint mechanism, allowing external packages to contribute tools to an Agent's ToolRegistry.
- **Agent**: The base agent class defined in the Core Agent Framework that owns a ToolRegistry and uses the ToolExecutor to invoke tools.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register Tool implementations with an Agent.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to secrets required by a Tool during execution.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **ToolExecutionError**: An exception raised when a Tool's execute method fails due to a runtime error during execution.
- **ToolValidationError**: An exception raised when input or output validation against a ToolSchema fails.

## Requirements

### Requirement 1: Tool Definition

**User Story:** As a developer, I want a well-defined Tool abstraction with declared input and output schemas, so that I can create reusable, self-describing tools with consistent structure.

#### Acceptance Criteria

1. THE Tool base class SHALL define an abstract interface that includes a name property, a description property, a version property, an input_schema property, an output_schema property, and an execute method.
2. THE Tool base class SHALL require all subclasses to provide an implementation for the execute method.
3. THE Tool base class SHALL expose a read-only descriptor property that returns a ToolDescriptor containing the Tool's name, description, version, input schema, output schema, and tags.
4. THE Tool base class SHALL accept an optional dictionary of tags at construction time for categorization and discovery purposes.
5. THE Tool base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the Tool requires for execution.
6. WHEN a Tool subclass does not provide a name, THEN THE Tool base class SHALL raise a SemanticError indicating that a Tool name is required.
7. THE Tool base class SHALL provide a __repr__ method that includes the class name, tool name, and version.
8. THE Tool base class SHALL provide a __str__ method that returns a human-readable summary including the tool name and description.

### Requirement 2: Tool Descriptor

**User Story:** As a developer, I want an immutable metadata object describing a Tool, so that I can inspect tool capabilities without accessing the tool implementation.

#### Acceptance Criteria

1. THE ToolDescriptor SHALL contain a name string, a description string, a version string, an input ToolSchema, an output ToolSchema, and a dictionary of tags.
2. THE ToolDescriptor SHALL expose all fields as read-only properties.
3. THE ToolDescriptor SHALL provide an as_dict method that returns a dictionary representation of the descriptor fields.
4. THE ToolDescriptor SHALL provide a to_json method that returns a JSON string representation of the descriptor fields.
5. THE ToolDescriptor SHALL provide a class method from_json that deserializes a JSON string into a ToolDescriptor instance.
6. FOR ALL valid ToolDescriptor instances, calling to_json and then from_json SHALL produce an equivalent ToolDescriptor object (round-trip property).

### Requirement 3: Tool Schema

**User Story:** As a developer, I want a declarative schema definition for tool inputs and outputs, so that the framework can validate data before and after tool execution.

#### Acceptance Criteria

1. THE ToolSchema SHALL support defining named parameters with type constraints including string, integer, float, boolean, list, and dictionary types.
2. THE ToolSchema SHALL support marking individual parameters as required or optional.
3. THE ToolSchema SHALL support specifying a default value for optional parameters.
4. THE ToolSchema SHALL support specifying a description for each parameter.
5. THE ToolSchema SHALL provide a validate method that accepts a dictionary of values and returns a list of validation error strings, returning an empty list when all values are valid.
6. WHEN a required parameter is missing from the input dictionary, THE ToolSchema validate method SHALL include an error string identifying the missing parameter name.
7. WHEN a parameter value does not match the declared type constraint, THE ToolSchema validate method SHALL include an error string identifying the parameter name, the expected type, and the actual type.
8. THE ToolSchema SHALL provide an as_dict method that returns a dictionary representation of the schema definition.
9. THE ToolSchema SHALL provide a to_json method that returns a JSON string representation of the schema definition.
10. THE ToolSchema SHALL provide a class method from_dict that constructs a ToolSchema from a dictionary representation.
11. THE ToolSchema SHALL provide a class method from_json that deserializes a JSON string into a ToolSchema instance.
12. FOR ALL valid ToolSchema instances, calling to_json and then from_json SHALL produce an equivalent ToolSchema object (round-trip property).
13. THE ToolSchema SHALL support an empty schema definition to represent tools that accept no input or produce no structured output.

### Requirement 4: Tool Registry

**User Story:** As a developer, I want a registry that tracks available tools, so that I can discover and look up tools by name or tags.

#### Acceptance Criteria

1. THE ToolRegistry SHALL support registration of a Tool instance using the Tool's name as the registration key.
2. IF a Tool with a duplicate name is registered, THEN THE ToolRegistry SHALL raise a SemanticError that includes the duplicate tool name.
3. THE ToolRegistry SHALL support deregistration of a Tool by name.
4. THE ToolRegistry SHALL support lookup of a registered Tool by name, returning the Tool instance or None when the name is not found.
5. THE ToolRegistry SHALL support lookup of registered Tools by tag key-value pairs, returning a list of Tool instances that match all provided tag criteria.
6. THE ToolRegistry SHALL support enumeration of all registered Tool instances as a list.
7. THE ToolRegistry SHALL support enumeration of all registered ToolDescriptor instances as a list, providing discovery without exposing Tool implementations.
8. THE ToolRegistry SHALL expose a read-only property for the count of currently registered tools.
9. THE ToolRegistry SHALL provide a has_tool method that accepts a tool name and returns a boolean indicating whether a Tool with the given name is registered.

### Requirement 5: Tool Execution

**User Story:** As a developer, I want validated tool execution with structured results, so that I can invoke tools with confidence that inputs are checked and outputs are well-formed.

#### Acceptance Criteria

1. WHEN the ToolExecutor receives an execution request, THE ToolExecutor SHALL validate the input dictionary against the Tool's input ToolSchema before invoking the execute method.
2. IF input validation fails, THEN THE ToolExecutor SHALL raise a ToolValidationError that includes the list of validation error strings from the ToolSchema.
3. WHEN input validation succeeds, THE ToolExecutor SHALL invoke the Tool's execute method with the validated input dictionary.
4. WHEN the Tool's execute method completes successfully, THE ToolExecutor SHALL validate the output against the Tool's output ToolSchema.
5. IF output validation fails, THEN THE ToolExecutor SHALL raise a ToolValidationError that includes the list of output validation error strings.
6. WHEN output validation succeeds, THE ToolExecutor SHALL return a ToolResult with a success status, the output value, and the execution duration.
7. IF the Tool's execute method raises an exception, THEN THE ToolExecutor SHALL return a ToolResult with a failure status, the exception information, and the execution duration.
8. THE ToolExecutor SHALL log each tool execution at INFO level, including the tool name, execution status, and execution duration.
9. THE ToolExecutor SHALL resolve any CredentialReference names declared by the Tool through `automojo-credentials` before invoking the execute method, passing resolved credentials as a dictionary to the execute method.
10. IF a CredentialReference declared by the Tool cannot be resolved, THEN THE ToolExecutor SHALL raise a ConfigurationError that identifies the unresolvable credential name and the tool name.

### Requirement 6: Tool Result

**User Story:** As a developer, I want a structured result object from tool execution, so that I can inspect the outcome, timing, and any errors in a consistent way.

#### Acceptance Criteria

1. THE ToolResult SHALL contain the tool name, execution status (success or failure), output value, execution duration as a float in seconds, and optional error information.
2. THE ToolResult SHALL expose all fields as read-only properties.
3. THE ToolResult SHALL provide an is_success read-only property that returns True when the execution status is success.
4. THE ToolResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
5. THE ToolResult SHALL provide a __repr__ method that includes the class name, tool name, and execution status.
6. THE ToolResult SHALL provide a __str__ method that returns a human-readable summary including the tool name, status, and duration.

### Requirement 7: Tool Chaining and Composition

**User Story:** As a developer, I want to compose tools into pipelines where the output of one tool feeds as input to the next, so that I can build complex workflows from simple tool building blocks.

#### Acceptance Criteria

1. THE ToolChain SHALL accept an ordered list of tool names and optional input-output mapping dictionaries that define how the output fields of one step map to the input fields of the next step.
2. THE ToolChain SHALL validate at construction time that all referenced tool names exist in the provided ToolRegistry.
3. IF a referenced tool name does not exist in the ToolRegistry, THEN THE ToolChain SHALL raise a SemanticError identifying the missing tool name.
4. THE ToolChain SHALL validate at construction time that the output schema of each step is compatible with the input schema of the next step according to the provided mappings.
5. IF a schema compatibility check fails, THEN THE ToolChain SHALL raise a ToolValidationError identifying the incompatible step pair and the specific field mismatch.
6. THE ToolChainExecutor SHALL execute each Tool in the ToolChain in sequence, using the ToolExecutor for each individual step.
7. THE ToolChainExecutor SHALL apply the input-output mappings between steps, passing mapped output fields from the previous step as input fields to the next step.
8. WHEN all steps complete successfully, THE ToolChainExecutor SHALL return a ToolChainResult with a success status, the final step output, the list of individual ToolResult objects, and the total execution duration.
9. IF any step fails, THEN THE ToolChainExecutor SHALL stop execution, and return a ToolChainResult with a failure status, the list of ToolResult objects for completed and failed steps, and the error information from the failed step.
10. THE ToolChain SHALL provide a read-only property that returns the ordered list of tool names in the chain.
11. THE ToolChain SHALL provide a read-only property that returns the count of steps in the chain.

### Requirement 8: Tool Chain Result

**User Story:** As a developer, I want a structured result from tool chain execution, so that I can inspect the outcome of each step and the overall pipeline result.

#### Acceptance Criteria

1. THE ToolChainResult SHALL contain the chain name, overall execution status (success or failure), final output value, list of individual ToolResult objects for each step, total execution duration as a float in seconds, and optional error information.
2. THE ToolChainResult SHALL expose all fields as read-only properties.
3. THE ToolChainResult SHALL provide an is_success read-only property that returns True when the overall execution status is success.
4. THE ToolChainResult SHALL provide a step_results read-only property that returns the list of ToolResult objects.
5. THE ToolChainResult SHALL provide an as_dict method that returns a dictionary representation of the chain result fields.
6. THE ToolChainResult SHALL provide a __repr__ method that includes the class name, chain name, and overall execution status.
7. THE ToolChainResult SHALL provide a __str__ method that returns a human-readable summary including the chain name, status, step count, and total duration.

### Requirement 9: Built-in File I/O Tool

**User Story:** As a developer, I want a built-in tool for file read and write operations, so that agents can interact with the local file system without writing custom tool code.

#### Acceptance Criteria

1. THE FileReadTool SHALL accept an input schema with a required file_path string parameter and an optional encoding string parameter with a default value of "utf-8".
2. WHEN the FileReadTool is executed with a valid file path, THE FileReadTool SHALL return the file contents as a string in the output.
3. IF the specified file does not exist, THEN THE FileReadTool SHALL raise a ToolExecutionError that includes the file path in the error message.
4. IF the file cannot be read due to a permission error, THEN THE FileReadTool SHALL raise a ToolExecutionError that includes the file path and the permission error detail.
5. THE FileWriteTool SHALL accept an input schema with a required file_path string parameter, a required content string parameter, and an optional encoding string parameter with a default value of "utf-8".
6. WHEN the FileWriteTool is executed with a valid file path and content, THE FileWriteTool SHALL write the content to the specified file path and return the number of bytes written in the output.
7. IF the file cannot be written due to a permission error, THEN THE FileWriteTool SHALL raise a ToolExecutionError that includes the file path and the permission error detail.

### Requirement 10: Built-in HTTP Tool

**User Story:** As a developer, I want a built-in tool for making HTTP requests, so that agents can interact with web services without writing custom tool code.

#### Acceptance Criteria

1. THE HttpRequestTool SHALL accept an input schema with a required url string parameter, a required method string parameter (GET, POST, PUT, DELETE, PATCH), an optional headers dictionary parameter, an optional body string parameter, and an optional timeout_seconds float parameter with a default value of 30.0.
2. WHEN the HttpRequestTool is executed with a valid URL and method, THE HttpRequestTool SHALL return an output containing the response status code as an integer, the response headers as a dictionary, and the response body as a string.
3. IF the HTTP request times out, THEN THE HttpRequestTool SHALL raise a ToolExecutionError that includes the URL, method, and timeout duration.
4. IF the HTTP request fails due to a connection error, THEN THE HttpRequestTool SHALL raise a ToolExecutionError that includes the URL and the connection error detail.
5. THE HttpRequestTool SHALL support resolving CredentialReference names for authentication headers through `automojo-credentials`.

### Requirement 11: Built-in Shell Tool

**User Story:** As a developer, I want a built-in tool for executing shell commands, so that agents can run system commands without writing custom tool code.

#### Acceptance Criteria

1. THE ShellCommandTool SHALL accept an input schema with a required command string parameter, an optional working_directory string parameter, an optional timeout_seconds float parameter with a default value of 60.0, and an optional environment dictionary parameter for additional environment variables.
2. WHEN the ShellCommandTool is executed with a valid command, THE ShellCommandTool SHALL return an output containing the exit code as an integer, the standard output as a string, and the standard error as a string.
3. IF the shell command exceeds the timeout duration, THEN THE ShellCommandTool SHALL terminate the process and raise a ToolExecutionError that includes the command and timeout duration.
4. IF the working directory does not exist, THEN THE ShellCommandTool SHALL raise a ToolExecutionError that includes the specified working directory path.
5. THE ShellCommandTool SHALL sanitize the command input to prevent shell injection by rejecting commands that contain shell metacharacters when a safe_mode flag is set to True in the input schema.
6. THE ShellCommandTool SHALL default the safe_mode flag to True.

### Requirement 12: Custom Tool Development API

**User Story:** As a developer, I want a simple API for creating custom tools, so that I can extend the tool system with domain-specific functionality using minimal boilerplate.

#### Acceptance Criteria

1. THE Tool base class SHALL allow subclasses to define input and output schemas by declaring class-level INPUT_SCHEMA and OUTPUT_SCHEMA dictionaries that are automatically converted to ToolSchema instances.
2. THE Tool base class SHALL allow subclasses to define the tool name by declaring a class-level TOOL_NAME string.
3. THE Tool base class SHALL allow subclasses to define the tool description by declaring a class-level TOOL_DESCRIPTION string.
4. THE Tool base class SHALL allow subclasses to define the tool version by declaring a class-level TOOL_VERSION string with a default value of "1.0.0".
5. WHEN a subclass declares class-level schema dictionaries, THE Tool base class SHALL validate the schema dictionaries at class construction time and raise a SemanticError if the schema format is invalid.
6. THE framework SHALL provide a create_tool factory function that accepts a name, description, input schema dictionary, output schema dictionary, and an execute callable, and returns a Tool instance without requiring subclassing.

### Requirement 13: Agent Tool Integration

**User Story:** As a developer, I want agents to own a tool registry and execute tools through the agent interface, so that tool usage is scoped to individual agents and integrated with the agent lifecycle.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only tools property that returns the Agent's ToolRegistry instance.
2. THE Agent base class SHALL provide a register_tool method that accepts a Tool instance and registers the Tool with the Agent's ToolRegistry.
3. THE Agent base class SHALL provide an execute_tool method that accepts a tool name and an input dictionary, looks up the Tool in the Agent's ToolRegistry, and executes the Tool through the ToolExecutor, returning a ToolResult.
4. IF the requested tool name is not found in the Agent's ToolRegistry, THEN THE execute_tool method SHALL raise a SemanticError that includes the requested tool name and the agent identity.
5. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all ToolPlugin instances from `automojo-extension` ExtensionPoint entries targeting the Agent.
6. THE Agent base class SHALL provide an execute_chain method that accepts a ToolChain and an initial input dictionary, executes the chain through the ToolChainExecutor, and returns a ToolChainResult.
7. WHEN an Agent transitions to the STOPPED state, THE Agent's ToolRegistry SHALL be cleared of all registered tools.

### Requirement 14: Tool Plugin Integration

**User Story:** As a developer, I want to distribute tools as plugins through `automojo-extension`, so that tool packages can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.tools" through `automojo-extension` for registering ToolPlugin implementations.
2. WHEN an Agent is initialized, THE Agent SHALL query the "automojo.agentkit.tools" ExtensionPoint and register all discovered Tool instances with the Agent's ToolRegistry.
3. IF a ToolPlugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
4. IF a ToolPlugin provides a Tool with a name that conflicts with an already registered Tool, THEN THE Agent SHALL log the conflict at WARNING level including both tool names and skip the conflicting plugin tool.

### Requirement 15: Tool Execution Error Handling

**User Story:** As a developer, I want well-defined error types for tool validation and execution failures, so that I can diagnose and handle tool errors precisely.

#### Acceptance Criteria

1. THE ToolValidationError SHALL inherit from AgentKitError and SHALL be raised when input or output validation against a ToolSchema fails.
2. THE ToolValidationError SHALL contain the tool name, the validation direction (input or output), and the list of validation error strings.
3. THE ToolExecutionError SHALL inherit from AgentKitError and SHALL be raised when a Tool's execute method encounters a runtime error.
4. THE ToolExecutionError SHALL contain the tool name and the original exception as the cause.
5. ALL tool-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name, tool name, and descriptive message.

### Requirement 16: Tool Serialization

**User Story:** As a developer, I want to serialize and deserialize tool descriptors and schemas, so that tool definitions can be stored, transmitted, and reconstructed.

#### Acceptance Criteria

1. THE ToolDescriptor SHALL provide a to_json method that serializes the descriptor to a JSON string.
2. THE ToolDescriptor SHALL provide a class method from_json that deserializes a JSON string into a ToolDescriptor instance.
3. THE ToolSchema SHALL provide a to_json method that serializes the schema to a JSON string.
4. THE ToolSchema SHALL provide a class method from_json that deserializes a JSON string into a ToolSchema instance.
5. FOR ALL valid ToolDescriptor instances, calling to_json and then from_json SHALL produce an equivalent ToolDescriptor object (round-trip property).
6. FOR ALL valid ToolSchema instances, calling to_json and then from_json SHALL produce an equivalent ToolSchema object (round-trip property).

### Requirement 17: Structured Logging for Tools

**User Story:** As a developer, I want tool execution to produce structured log entries, so that I can monitor and debug tool usage using standard Python logging tools.

#### Acceptance Criteria

1. THE ToolExecutor SHALL use the Python standard logging module with a logger hierarchy under `automojo.agentkit.tools`.
2. WHEN a tool execution begins, THE ToolExecutor SHALL log at INFO level including the tool name and the agent identifier.
3. WHEN a tool execution completes successfully, THE ToolExecutor SHALL log at INFO level including the tool name, execution duration, and success status.
4. WHEN a tool execution fails, THE ToolExecutor SHALL log at WARNING level including the tool name, execution duration, and error detail.
5. WHEN input validation fails, THE ToolExecutor SHALL log at WARNING level including the tool name and the list of validation errors.

### Requirement 18: Tool String Representations

**User Story:** As a developer, I want meaningful string representations on tool system classes, so that I can quickly inspect tool state during debugging sessions.

#### Acceptance Criteria

1. THE Tool base class SHALL provide a __repr__ method that includes the class name, tool name, and version.
2. THE Tool base class SHALL provide a __str__ method that returns a human-readable summary including the tool name and description.
3. THE ToolDescriptor SHALL provide a __repr__ method that includes the class name, tool name, and version.
4. THE ToolDescriptor SHALL provide a __str__ method that returns a human-readable summary including the tool name and description.
5. THE ToolSchema SHALL provide a __repr__ method that includes the class name and the count of defined parameters.
6. THE ToolSchema SHALL provide a __str__ method that returns a human-readable summary listing the parameter names and types.
7. THE ToolResult SHALL provide a __repr__ method that includes the class name, tool name, and execution status.
8. THE ToolResult SHALL provide a __str__ method that returns a human-readable summary including the tool name, status, and duration.
9. THE ToolChainResult SHALL provide a __repr__ method that includes the class name, chain name, and overall execution status.
10. THE ToolChainResult SHALL provide a __str__ method that returns a human-readable summary including the chain name, status, step count, and total duration.
11. THE ToolRegistry SHALL provide a __repr__ method that includes the class name and the count of registered tools.
12. THE ToolRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered tool names.
