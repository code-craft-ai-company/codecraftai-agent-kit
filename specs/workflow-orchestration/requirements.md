# Requirements Document — Workflow & Orchestration

## Introduction

The Workflow & Orchestration feature extends the `codecraftai-agent-kit` SDK with a system for defining, executing, checkpointing, and resuming multi-step workflows composed as directed acyclic graphs (DAGs). It provides a workflow definition abstraction with typed steps and edges, conditional branching and looping constructs, parallel task execution, workflow checkpointing and resumption for fault tolerance, and human-in-the-loop approval gates for supervised automation. The system integrates with the Agent base class so agents can define and execute workflows, with the Tool system so workflow steps can invoke tools, with the LLM Integration system so workflow steps can make LLM completion requests, with the Memory & Context Management system so workflow state can be persisted, with the Communication & Messaging system so workflows can coordinate across agents, with `codecraftai-extension` so workflow step plugins can be discovered and loaded, with `codecraftai-credentials` for credential management within workflow steps, with `codecraftai-dataprofiles` for data profile management, and with `codecraftai-this-app` for settings and environment configuration.

## Glossary

- **WorkflowDefinition**: An immutable object representing a complete workflow as a directed acyclic graph (DAG) of WorkflowStep nodes connected by WorkflowEdge edges. The WorkflowDefinition contains a name, version, description, the set of steps, the set of edges, and a designated start step identifier.
- **WorkflowStep**: An abstract base class representing a single unit of work within a workflow. A WorkflowStep has a unique identifier, a name, a step type, an input schema, an output schema, and an execute method. Concrete implementations include ToolStep, LlmStep, AgentStep, ApprovalStep, SubWorkflowStep, and custom steps.
- **WorkflowEdge**: An immutable object representing a directed connection between two WorkflowStep nodes in a WorkflowDefinition, containing a source step identifier, a target step identifier, an optional condition expression, and an optional priority integer for ordering when multiple edges leave a step.
- **WorkflowExecutor**: The component responsible for executing a WorkflowDefinition by traversing the DAG, evaluating edge conditions, executing steps, managing parallel branches, and producing a WorkflowResult. The WorkflowExecutor coordinates with the CheckpointManager for fault tolerance.
- **WorkflowResult**: An immutable object encapsulating the outcome of a workflow execution, containing the workflow name, overall execution status (completed, failed, paused, cancelled), the list of individual StepResult objects, the final output dictionary, total execution duration, and any error information.
- **StepResult**: An immutable object encapsulating the outcome of a single WorkflowStep execution, containing the step identifier, step name, execution status (completed, failed, skipped, pending_approval, cancelled), the output value, execution duration, and any error information.
- **WorkflowContext**: A mutable object that carries shared state across workflow steps during execution, containing the workflow input dictionary, accumulated step outputs keyed by step identifier, workflow-level metadata, and a reference to the executing Agent.
- **ConditionExpression**: A string expression evaluated against the WorkflowContext to determine whether a WorkflowEdge should be traversed. The expression supports referencing step outputs by step identifier and comparing values using standard comparison operators.
- **ConditionEvaluator**: A component that parses and evaluates ConditionExpression strings against a WorkflowContext, returning a boolean result. The ConditionEvaluator supports a safe subset of Python expressions.
- **CheckpointManager**: A component responsible for persisting and restoring WorkflowExecution state at configurable checkpoint boundaries, enabling workflow resumption after failures or process restarts.
- **WorkflowCheckpoint**: An immutable object representing a snapshot of workflow execution state at a specific point, containing the workflow name, execution identifier, the set of completed step identifiers, the WorkflowContext state, the current step identifier, and a timestamp.
- **ApprovalGate**: A component that pauses workflow execution at a designated ApprovalStep and waits for an external approval or rejection signal before allowing the workflow to continue or abort.
- **ApprovalRequest**: An immutable object representing a pending approval, containing a unique identifier, the workflow execution identifier, the step identifier, a description of what is being approved, the requesting agent identifier, the approval status (pending, approved, rejected, expired), and a timestamp.
- **ApprovalHandler**: A callback interface invoked when an ApprovalRequest is created, allowing external systems or users to be notified of pending approvals.
- **ToolStep**: A concrete WorkflowStep that executes a named Tool from the Agent's ToolRegistry during workflow execution.
- **LlmStep**: A concrete WorkflowStep that executes an LLM completion request through the Agent's LlmProviderRegistry during workflow execution.
- **AgentStep**: A concrete WorkflowStep that delegates execution to another Agent, sending a message through the Communication & Messaging system and awaiting a response.
- **ApprovalStep**: A concrete WorkflowStep that creates an ApprovalRequest and pauses workflow execution until the approval is resolved.
- **SubWorkflowStep**: A concrete WorkflowStep that executes a nested WorkflowDefinition as a sub-workflow within the parent workflow execution.
- **ParallelBranch**: A grouping construct within a WorkflowDefinition that identifies a set of WorkflowStep nodes that can be executed concurrently. A ParallelBranch has a fork step identifier where parallel execution begins and a join step identifier where parallel branches converge.
- **WorkflowConfiguration**: A configuration object that defines default execution settings including maximum parallel workers, checkpoint interval, default approval timeout, and retry policies for workflow steps.
- **WorkflowRegistry**: A registry that tracks all WorkflowDefinition instances available to an Agent, providing lookup by name, version, and enumeration.
- **WorkflowExecutionStatus**: An enumeration defining the overall status of a workflow execution: RUNNING, COMPLETED, FAILED, PAUSED, CANCELLED.
- **StepExecutionStatus**: An enumeration defining the status of a single step execution: PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, PENDING_APPROVAL, CANCELLED.
- **Agent**: The base agent class defined in the Core Agent Framework that owns a WorkflowRegistry and uses the WorkflowExecutor to run workflows.
- **ToolRegistry**: The tool registry defined in the Tool & Capability System, used by ToolStep to look up and execute tools.
- **ToolResult**: The tool result object defined in the Tool & Capability System, returned by tool execution within a ToolStep.
- **LlmProviderRegistry**: The LLM provider registry defined in the LLM Integration feature, used by LlmStep to execute completion requests.
- **LlmResponse**: The LLM response object defined in the LLM Integration feature, returned by LLM completion within an LlmStep.
- **MemoryStore**: The memory store abstraction defined in the Memory & Context Management feature, used by the CheckpointManager for persisting workflow checkpoints.
- **Transport**: The transport abstraction defined in the Communication & Messaging feature, used by AgentStep for cross-agent communication.
- **ExtensionPoint**: An integration surface provided by `codecraftai-extension` that allows external plugins to register WorkflowStep implementations with an Agent.
- **CredentialReference**: A named reference resolved through `codecraftai-credentials` that provides secure access to secrets required by workflow steps.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **WorkflowDefinitionError**: An exception raised when a WorkflowDefinition is structurally invalid (contains cycles, missing start step, disconnected nodes).
- **WorkflowExecutionError**: An exception raised when a workflow execution fails due to a runtime error during step execution.
- **WorkflowCheckpointError**: An exception raised when a checkpoint save or restore operation fails.
- **ApprovalTimeoutError**: An exception raised when an ApprovalRequest exceeds the configured approval timeout duration.

## Requirements

### Requirement 1: Workflow Definition

**User Story:** As a developer, I want to define workflows as directed acyclic graphs of steps with typed edges, so that I can model complex multi-step processes with clear dependencies and execution order.

#### Acceptance Criteria

1. THE WorkflowDefinition SHALL contain a name string, a version string, an optional description string, a dictionary of WorkflowStep objects keyed by step identifier, a list of WorkflowEdge objects, and a start step identifier.
2. THE WorkflowDefinition SHALL validate at construction time that the start step identifier references a step present in the steps dictionary.
3. IF the start step identifier does not reference a valid step, THEN THE WorkflowDefinition SHALL raise a WorkflowDefinitionError identifying the invalid start step identifier.
4. THE WorkflowDefinition SHALL validate at construction time that all WorkflowEdge source and target step identifiers reference steps present in the steps dictionary.
5. IF a WorkflowEdge references a step identifier not present in the steps dictionary, THEN THE WorkflowDefinition SHALL raise a WorkflowDefinitionError identifying the invalid edge and the missing step identifier.
6. THE WorkflowDefinition SHALL validate at construction time that the graph formed by the steps and edges contains no cycles.
7. IF a cycle is detected in the workflow graph, THEN THE WorkflowDefinition SHALL raise a WorkflowDefinitionError identifying the step identifiers involved in the cycle.
8. THE WorkflowDefinition SHALL validate at construction time that all steps are reachable from the start step.
9. IF unreachable steps are detected, THEN THE WorkflowDefinition SHALL raise a WorkflowDefinitionError identifying the unreachable step identifiers.
10. THE WorkflowDefinition SHALL expose all fields as read-only properties.
11. THE WorkflowDefinition SHALL provide a get_step method that accepts a step identifier and returns the WorkflowStep or None when the identifier is not found.
12. THE WorkflowDefinition SHALL provide a get_outgoing_edges method that accepts a step identifier and returns the list of WorkflowEdge objects originating from the step, ordered by edge priority.
13. THE WorkflowDefinition SHALL provide a get_incoming_edges method that accepts a step identifier and returns the list of WorkflowEdge objects targeting the step.
14. THE WorkflowDefinition SHALL provide a get_terminal_steps method that returns the list of step identifiers that have no outgoing edges.

### Requirement 2: Workflow Step Abstraction

**User Story:** As a developer, I want a well-defined step base class with input and output schemas, so that I can create reusable workflow steps with consistent structure and validated data flow.

#### Acceptance Criteria

1. THE WorkflowStep base class SHALL define an abstract interface that includes a step_id property, a name property, a step_type property, an input_schema property, an output_schema property, and an execute method.
2. THE WorkflowStep base class SHALL require all subclasses to provide an implementation for the execute method.
3. THE WorkflowStep execute method SHALL accept a WorkflowContext and return a StepResult.
4. THE WorkflowStep base class SHALL expose all identity fields (step_id, name, step_type) as read-only properties.
5. WHEN a WorkflowStep subclass does not provide a step_id, THEN THE WorkflowStep base class SHALL raise a SemanticError indicating that a step identifier is required.
6. WHEN a WorkflowStep subclass does not provide a name, THEN THE WorkflowStep base class SHALL raise a SemanticError indicating that a step name is required.
7. THE WorkflowStep base class SHALL accept an optional dictionary of tags at construction time for categorization and discovery purposes.
8. THE WorkflowStep base class SHALL accept an optional RetryPolicy at construction time for configuring step-level retry behavior.
9. THE WorkflowStep base class SHALL provide a __repr__ method that includes the class name, step identifier, step name, and step type.
10. THE WorkflowStep base class SHALL provide a __str__ method that returns a human-readable summary including the step name and step type.

### Requirement 3: Workflow Edge and Condition Expression

**User Story:** As a developer, I want directed edges between steps with optional condition expressions, so that I can define conditional branching logic within workflows.

#### Acceptance Criteria

1. THE WorkflowEdge SHALL contain a source step identifier string, a target step identifier string, an optional ConditionExpression string, and an optional priority integer with a default value of 0.
2. THE WorkflowEdge SHALL expose all fields as read-only properties.
3. WHEN a WorkflowEdge has no ConditionExpression, THE WorkflowEdge SHALL be treated as an unconditional edge that is always traversed.
4. WHEN multiple outgoing edges from a step have ConditionExpression values, THE WorkflowExecutor SHALL evaluate the edges in ascending priority order and traverse the first edge whose condition evaluates to True.
5. THE ConditionEvaluator SHALL support referencing step outputs using the syntax "steps.<step_id>.<output_field>".
6. THE ConditionEvaluator SHALL support referencing workflow input values using the syntax "inputs.<field_name>".
7. THE ConditionEvaluator SHALL support comparison operators: ==, !=, <, >, <=, >=.
8. THE ConditionEvaluator SHALL support logical operators: and, or, not.
9. THE ConditionEvaluator SHALL support the "in" operator for membership testing.
10. THE ConditionEvaluator SHALL restrict evaluation to a safe subset of Python expressions, preventing execution of arbitrary code, function calls, or attribute access beyond the allowed patterns.
11. IF a ConditionExpression references a step identifier that has not been executed, THEN THE ConditionEvaluator SHALL raise a WorkflowExecutionError identifying the unresolved step reference.
12. IF a ConditionExpression contains invalid syntax, THEN THE ConditionEvaluator SHALL raise a WorkflowDefinitionError identifying the expression and the syntax error detail.
13. THE WorkflowEdge SHALL provide an as_dict method that returns a dictionary representation of the edge fields.
14. THE WorkflowEdge SHALL provide a __repr__ method that includes the class name, source step identifier, target step identifier, and whether a condition is present.
15. THE WorkflowEdge SHALL provide a __str__ method that returns a human-readable summary including the source, target, and condition expression.


### Requirement 4: Workflow Executor

**User Story:** As a developer, I want an executor that traverses the workflow DAG, evaluates conditions, and runs steps in the correct order, so that workflows execute predictably with proper dependency resolution.

#### Acceptance Criteria

1. THE WorkflowExecutor SHALL accept a WorkflowDefinition and an initial input dictionary and execute the workflow by traversing the DAG starting from the designated start step.
2. THE WorkflowExecutor SHALL execute steps in topological order, ensuring that a step is executed only after all steps connected by incoming edges have completed.
3. WHEN a step completes, THE WorkflowExecutor SHALL store the StepResult output in the WorkflowContext keyed by the step identifier.
4. WHEN a step has multiple outgoing edges with ConditionExpression values, THE WorkflowExecutor SHALL evaluate the conditions in ascending edge priority order and traverse the first edge whose condition evaluates to True.
5. WHEN a step has multiple outgoing unconditional edges, THE WorkflowExecutor SHALL traverse all unconditional edges, enabling parallel branch execution.
6. WHEN all terminal steps have completed, THE WorkflowExecutor SHALL return a WorkflowResult with a COMPLETED status, the final outputs from terminal steps, and the list of all StepResult objects.
7. IF a step execution fails and no RetryPolicy is configured for the step, THEN THE WorkflowExecutor SHALL return a WorkflowResult with a FAILED status, the error information from the failed step, and the list of StepResult objects for completed and failed steps.
8. IF a step execution fails and a RetryPolicy is configured for the step, THEN THE WorkflowExecutor SHALL retry the step according to the RetryPolicy before marking the step as failed.
9. THE WorkflowExecutor SHALL accept an optional WorkflowConfiguration at construction time for configuring execution behavior.
10. THE WorkflowExecutor SHALL log each step execution start at INFO level including the workflow name, step identifier, and step name.
11. THE WorkflowExecutor SHALL log each step execution completion at INFO level including the workflow name, step identifier, execution status, and duration.
12. THE WorkflowExecutor SHALL provide a __repr__ method that includes the class name and the workflow name being executed.
13. THE WorkflowExecutor SHALL provide a __str__ method that returns a human-readable summary including the workflow name and execution status.

### Requirement 5: Workflow Context

**User Story:** As a developer, I want a shared context object that carries workflow inputs, step outputs, and metadata across steps, so that steps can access data produced by earlier steps in the workflow.

#### Acceptance Criteria

1. THE WorkflowContext SHALL contain the workflow input dictionary, a dictionary of step outputs keyed by step identifier, a workflow metadata dictionary, and a reference to the executing Agent.
2. THE WorkflowContext SHALL provide a get_step_output method that accepts a step identifier and returns the output dictionary for the completed step, or None when the step has not completed.
3. THE WorkflowContext SHALL provide a set_step_output method that accepts a step identifier and an output dictionary and stores the output in the context.
4. THE WorkflowContext SHALL provide a get_input method that accepts a field name and returns the value from the workflow input dictionary, or None when the field is not present.
5. THE WorkflowContext SHALL provide a get_metadata method that accepts a key string and returns the metadata value, or None when the key is not present.
6. THE WorkflowContext SHALL provide a set_metadata method that accepts a key string and a value and stores the metadata in the context.
7. THE WorkflowContext SHALL expose a read-only property for the executing Agent instance.
8. THE WorkflowContext SHALL expose a read-only property for the workflow input dictionary.
9. THE WorkflowContext SHALL expose a read-only property for the dictionary of completed step outputs.
10. THE WorkflowContext SHALL provide an as_dict method that returns a dictionary representation of the context state including inputs, step outputs, and metadata.
11. THE WorkflowContext SHALL provide a to_json method that returns a JSON string representation of the context state.
12. THE WorkflowContext SHALL provide a class method from_dict that constructs a WorkflowContext from a dictionary representation, accepting an Agent reference as a separate parameter.
13. FOR ALL valid WorkflowContext instances with JSON-serializable content, calling to_json and then parsing the JSON and calling from_dict SHALL produce a WorkflowContext with equivalent inputs, step outputs, and metadata (round-trip property).
14. THE WorkflowContext SHALL provide a __repr__ method that includes the class name, the count of completed steps, and the count of input fields.
15. THE WorkflowContext SHALL provide a __str__ method that returns a human-readable summary including the count of completed steps and input field names.

### Requirement 6: Workflow Result and Step Result

**User Story:** As a developer, I want structured result objects from workflow and step execution, so that I can inspect the outcome of each step and the overall workflow in a consistent way.

#### Acceptance Criteria

1. THE WorkflowResult SHALL contain the workflow name, the WorkflowExecutionStatus, the list of StepResult objects, the final output dictionary from terminal steps, the total execution duration as a float in seconds, and optional error information.
2. THE WorkflowResult SHALL expose all fields as read-only properties.
3. THE WorkflowResult SHALL provide an is_success read-only property that returns True when the execution status is COMPLETED.
4. THE WorkflowResult SHALL provide a get_step_result method that accepts a step identifier and returns the StepResult for the step, or None when the step was not executed.
5. THE WorkflowResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
6. THE WorkflowResult SHALL provide a to_json method that returns a JSON string representation of the result fields.
7. THE WorkflowResult SHALL provide a class method from_json that deserializes a JSON string into a WorkflowResult instance.
8. FOR ALL valid WorkflowResult instances, calling to_json and then from_json SHALL produce an equivalent WorkflowResult object (round-trip property).
9. THE StepResult SHALL contain the step identifier, step name, the StepExecutionStatus, the output value as a dictionary, the execution duration as a float in seconds, and optional error information.
10. THE StepResult SHALL expose all fields as read-only properties.
11. THE StepResult SHALL provide an is_success read-only property that returns True when the execution status is COMPLETED.
12. THE StepResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
13. THE StepResult SHALL provide a to_json method that returns a JSON string representation of the result fields.
14. THE StepResult SHALL provide a class method from_json that deserializes a JSON string into a StepResult instance.
15. FOR ALL valid StepResult instances, calling to_json and then from_json SHALL produce an equivalent StepResult object (round-trip property).

### Requirement 7: Workflow Execution Status Enumerations

**User Story:** As a developer, I want well-defined status enumerations for workflow and step execution, so that I can programmatically inspect and react to execution state.

#### Acceptance Criteria

1. THE WorkflowExecutionStatus enumeration SHALL define the values RUNNING, COMPLETED, FAILED, PAUSED, and CANCELLED.
2. THE WorkflowExecutionStatus enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding WorkflowExecutionStatus member.
3. IF an invalid string value is provided to the WorkflowExecutionStatus from_string method, THEN THE WorkflowExecutionStatus SHALL raise a SemanticError identifying the invalid value and listing the valid status values.
4. THE StepExecutionStatus enumeration SHALL define the values PENDING, RUNNING, COMPLETED, FAILED, SKIPPED, PENDING_APPROVAL, and CANCELLED.
5. THE StepExecutionStatus enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding StepExecutionStatus member.
6. IF an invalid string value is provided to the StepExecutionStatus from_string method, THEN THE StepExecutionStatus SHALL raise a SemanticError identifying the invalid value and listing the valid status values.


### Requirement 8: Parallel Task Execution

**User Story:** As a developer, I want to execute independent workflow branches in parallel, so that workflows complete faster when steps have no data dependencies on each other.

#### Acceptance Criteria

1. THE WorkflowDefinition SHALL support ParallelBranch declarations that identify a fork step identifier and a join step identifier, defining the boundaries of parallel execution.
2. THE WorkflowDefinition SHALL validate at construction time that each ParallelBranch fork step and join step reference valid steps in the steps dictionary.
3. IF a ParallelBranch references an invalid fork or join step identifier, THEN THE WorkflowDefinition SHALL raise a WorkflowDefinitionError identifying the invalid ParallelBranch and the missing step identifier.
4. THE WorkflowDefinition SHALL validate at construction time that all paths from a fork step converge at the corresponding join step.
5. IF parallel paths do not converge at the declared join step, THEN THE WorkflowDefinition SHALL raise a WorkflowDefinitionError identifying the non-converging paths.
6. WHEN the WorkflowExecutor reaches a fork step, THE WorkflowExecutor SHALL execute all outgoing branches concurrently up to the configured maximum parallel workers.
7. WHEN all branches of a ParallelBranch have completed, THE WorkflowExecutor SHALL merge the branch outputs into the WorkflowContext and proceed to the join step.
8. IF any branch of a ParallelBranch fails, THEN THE WorkflowExecutor SHALL cancel the remaining running branches and mark the ParallelBranch as failed.
9. THE WorkflowConfiguration SHALL contain a maximum parallel workers integer with a default value of 4, controlling the maximum number of concurrently executing branches.
10. THE ParallelBranch SHALL expose the fork step identifier and join step identifier as read-only properties.
11. THE ParallelBranch SHALL provide an as_dict method that returns a dictionary representation of the branch fields.
12. THE ParallelBranch SHALL provide a __repr__ method that includes the class name, fork step identifier, and join step identifier.
13. THE ParallelBranch SHALL provide a __str__ method that returns a human-readable summary including the fork and join step identifiers.

### Requirement 9: Workflow Checkpointing

**User Story:** As a developer, I want to checkpoint workflow execution state at configurable boundaries, so that workflows can be resumed after failures or process restarts without re-executing completed steps.

#### Acceptance Criteria

1. THE CheckpointManager SHALL accept a MemoryStore instance at construction time for persisting WorkflowCheckpoint objects.
2. THE CheckpointManager SHALL provide a save_checkpoint method that accepts a workflow execution identifier, the current WorkflowContext, the set of completed step identifiers, and the current step identifier, and persists a WorkflowCheckpoint to the MemoryStore.
3. THE CheckpointManager SHALL provide a load_checkpoint method that accepts a workflow execution identifier and returns the most recent WorkflowCheckpoint for the execution, or None when no checkpoint exists.
4. THE CheckpointManager SHALL provide a list_checkpoints method that accepts a workflow name and returns the list of WorkflowCheckpoint objects for the workflow, ordered by timestamp descending.
5. THE CheckpointManager SHALL provide a delete_checkpoint method that accepts a workflow execution identifier and removes all checkpoints for the execution from the MemoryStore.
6. WHEN the WorkflowExecutor completes a step and the checkpoint interval has elapsed since the last checkpoint, THE WorkflowExecutor SHALL invoke the CheckpointManager to save a checkpoint.
7. THE WorkflowConfiguration SHALL contain a checkpoint interval as an optional integer representing the number of steps between automatic checkpoints, with a default value of 1 (checkpoint after every step).
8. IF a checkpoint save operation fails, THEN THE CheckpointManager SHALL raise a WorkflowCheckpointError that includes the workflow execution identifier and the underlying error detail.
9. IF a checkpoint load operation fails, THEN THE CheckpointManager SHALL raise a WorkflowCheckpointError that includes the workflow execution identifier and the underlying error detail.
10. THE WorkflowCheckpoint SHALL contain the workflow name, execution identifier, the set of completed step identifiers, the serialized WorkflowContext state, the current step identifier, and a timestamp.
11. THE WorkflowCheckpoint SHALL expose all fields as read-only properties.
12. THE WorkflowCheckpoint SHALL provide an as_dict method that returns a dictionary representation of the checkpoint fields.
13. THE WorkflowCheckpoint SHALL provide a to_json method that returns a JSON string representation of the checkpoint fields.
14. THE WorkflowCheckpoint SHALL provide a class method from_json that deserializes a JSON string into a WorkflowCheckpoint instance.
15. FOR ALL valid WorkflowCheckpoint instances, calling to_json and then from_json SHALL produce an equivalent WorkflowCheckpoint object (round-trip property).

### Requirement 10: Workflow Resumption

**User Story:** As a developer, I want to resume a workflow from the last checkpoint, so that long-running workflows can recover from failures without losing progress.

#### Acceptance Criteria

1. THE WorkflowExecutor SHALL provide a resume method that accepts a workflow execution identifier and a WorkflowDefinition, loads the most recent WorkflowCheckpoint, restores the WorkflowContext, and continues execution from the step following the last completed step.
2. WHEN resuming a workflow, THE WorkflowExecutor SHALL skip all steps whose identifiers are in the checkpoint's completed step set.
3. WHEN resuming a workflow, THE WorkflowExecutor SHALL restore the WorkflowContext from the checkpoint state, including all previously completed step outputs.
4. IF no checkpoint exists for the provided execution identifier, THEN THE WorkflowExecutor SHALL raise a WorkflowCheckpointError indicating that no checkpoint was found for the execution identifier.
5. THE WorkflowExecutor SHALL log workflow resumption at INFO level including the workflow name, execution identifier, and the count of previously completed steps.
6. WHEN a resumed workflow completes, THE WorkflowExecutor SHALL return a WorkflowResult that includes StepResult objects for both previously completed steps (from the checkpoint) and newly executed steps.

### Requirement 11: Human-in-the-Loop Approval Gates

**User Story:** As a developer, I want to pause workflow execution at designated approval points and wait for external approval, so that critical workflow decisions can be reviewed by a human before proceeding.

#### Acceptance Criteria

1. THE ApprovalStep SHALL be a concrete WorkflowStep that creates an ApprovalRequest and pauses workflow execution until the approval is resolved.
2. THE ApprovalStep SHALL accept a description string at construction time describing what is being approved.
3. THE ApprovalStep SHALL accept an optional timeout in seconds as a float at construction time, defaulting to the value configured in the WorkflowConfiguration.
4. WHEN the ApprovalStep is executed, THE ApprovalStep SHALL create an ApprovalRequest with status "pending" and invoke all registered ApprovalHandler callbacks.
5. WHEN an ApprovalRequest is approved, THE ApprovalStep SHALL return a StepResult with COMPLETED status and the approval metadata in the output.
6. WHEN an ApprovalRequest is rejected, THE ApprovalStep SHALL return a StepResult with FAILED status and the rejection reason in the error information.
7. IF an ApprovalRequest exceeds the configured timeout duration without a response, THEN THE ApprovalStep SHALL raise an ApprovalTimeoutError that includes the approval request identifier, the step identifier, and the timeout duration.
8. THE ApprovalGate SHALL provide an approve method that accepts an approval request identifier and an optional metadata dictionary and resolves the pending approval.
9. THE ApprovalGate SHALL provide a reject method that accepts an approval request identifier and a reason string and resolves the pending approval as rejected.
10. THE ApprovalGate SHALL provide a list_pending method that returns the list of ApprovalRequest objects with status "pending".
11. THE ApprovalGate SHALL support registration of ApprovalHandler callbacks that are invoked when a new ApprovalRequest is created.
12. THE ApprovalGate SHALL support deregistration of a previously registered ApprovalHandler callback.
13. THE ApprovalRequest SHALL contain a unique string identifier, the workflow execution identifier, the step identifier, a description string, the requesting agent identifier, the approval status string (one of "pending", "approved", "rejected", "expired"), an optional metadata dictionary, an optional rejection reason string, and a timestamp.
14. THE ApprovalRequest SHALL expose all fields as read-only properties.
15. THE ApprovalRequest SHALL provide an as_dict method that returns a dictionary representation of the request fields.
16. THE ApprovalRequest SHALL provide a to_json method that returns a JSON string representation of the request fields.
17. THE ApprovalRequest SHALL provide a class method from_json that deserializes a JSON string into an ApprovalRequest instance.
18. FOR ALL valid ApprovalRequest instances, calling to_json and then from_json SHALL produce an equivalent ApprovalRequest object (round-trip property).


### Requirement 12: Built-in Tool Step

**User Story:** As a developer, I want a built-in workflow step that executes a tool from the agent's tool registry, so that I can incorporate tool invocations into workflows without writing custom step code.

#### Acceptance Criteria

1. THE ToolStep SHALL accept a tool name string at construction time identifying the Tool to execute from the Agent's ToolRegistry.
2. THE ToolStep SHALL accept an optional input mapping dictionary at construction time that maps WorkflowContext fields to tool input fields.
3. WHEN the ToolStep is executed, THE ToolStep SHALL resolve the input mapping against the WorkflowContext, look up the Tool by name in the Agent's ToolRegistry, execute the Tool through the Agent's ToolExecutor, and return a StepResult containing the ToolResult output.
4. IF the tool name is not found in the Agent's ToolRegistry, THEN THE ToolStep SHALL return a StepResult with FAILED status and an error message identifying the missing tool name.
5. IF the tool execution fails, THEN THE ToolStep SHALL return a StepResult with FAILED status and the ToolExecutionError information.

### Requirement 13: Built-in LLM Step

**User Story:** As a developer, I want a built-in workflow step that executes an LLM completion request, so that I can incorporate LLM interactions into workflows without writing custom step code.

#### Acceptance Criteria

1. THE LlmStep SHALL accept a provider name string and a model name string at construction time identifying the LlmProvider to use.
2. THE LlmStep SHALL accept a PromptTemplate or a static prompt string at construction time for constructing the LLM request.
3. THE LlmStep SHALL accept an optional OutputParser at construction time for parsing the LLM response into structured output.
4. WHEN the LlmStep is executed, THE LlmStep SHALL render the prompt using the WorkflowContext, construct an LlmConversation, execute the completion request through the Agent, and return a StepResult containing the LlmResponse content or parsed output.
5. IF the LLM completion request fails, THEN THE LlmStep SHALL return a StepResult with FAILED status and the LlmRequestError information.
6. IF the OutputParser fails to parse the response, THEN THE LlmStep SHALL return a StepResult with FAILED status and the LlmResponseParsingError information.

### Requirement 14: Built-in Agent Step

**User Story:** As a developer, I want a built-in workflow step that delegates execution to another agent, so that workflows can coordinate work across multiple agents.

#### Acceptance Criteria

1. THE AgentStep SHALL accept a target agent identifier string at construction time identifying the Agent to delegate to.
2. THE AgentStep SHALL accept an optional transport name string at construction time for specifying the communication transport.
3. THE AgentStep SHALL accept an optional timeout in seconds as a float at construction time for the request/response exchange.
4. WHEN the AgentStep is executed, THE AgentStep SHALL construct a request message from the WorkflowContext, send the message to the target agent through the Communication & Messaging system, and await a response.
5. WHEN a response is received, THE AgentStep SHALL return a StepResult with COMPLETED status and the response payload in the output.
6. IF the target agent does not respond within the timeout duration, THEN THE AgentStep SHALL return a StepResult with FAILED status and a MessageTimeoutError.
7. IF the message send fails, THEN THE AgentStep SHALL return a StepResult with FAILED status and the TransportError information.

### Requirement 15: Built-in Sub-Workflow Step

**User Story:** As a developer, I want a built-in workflow step that executes a nested workflow, so that I can compose complex workflows from smaller reusable workflow definitions.

#### Acceptance Criteria

1. THE SubWorkflowStep SHALL accept a WorkflowDefinition at construction time representing the sub-workflow to execute.
2. THE SubWorkflowStep SHALL accept an optional input mapping dictionary at construction time that maps parent WorkflowContext fields to sub-workflow input fields.
3. WHEN the SubWorkflowStep is executed, THE SubWorkflowStep SHALL create a new WorkflowExecutor, resolve the input mapping against the parent WorkflowContext, execute the sub-workflow, and return a StepResult containing the sub-workflow's final output.
4. IF the sub-workflow execution fails, THEN THE SubWorkflowStep SHALL return a StepResult with FAILED status and the sub-workflow's WorkflowResult error information.
5. THE SubWorkflowStep SHALL support checkpointing of the sub-workflow execution independently from the parent workflow.

### Requirement 16: Workflow Registry

**User Story:** As a developer, I want a registry that tracks available workflow definitions, so that I can discover and look up workflows by name or version.

#### Acceptance Criteria

1. THE WorkflowRegistry SHALL support registration of a WorkflowDefinition instance using a composite key of workflow name and version.
2. IF a WorkflowDefinition with a duplicate name and version is registered, THEN THE WorkflowRegistry SHALL raise a SemanticError that includes the duplicate workflow name and version.
3. THE WorkflowRegistry SHALL support deregistration of a WorkflowDefinition by name and version.
4. THE WorkflowRegistry SHALL support lookup of a registered WorkflowDefinition by name and optional version, returning the latest version when no version is specified.
5. THE WorkflowRegistry SHALL support enumeration of all registered WorkflowDefinition instances as a list.
6. THE WorkflowRegistry SHALL expose a read-only property for the count of currently registered workflows.
7. THE WorkflowRegistry SHALL provide a has_workflow method that accepts a workflow name and optional version and returns a boolean indicating whether a matching WorkflowDefinition is registered.
8. THE WorkflowRegistry SHALL provide a __repr__ method that includes the class name and the count of registered workflows.
9. THE WorkflowRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered workflow names and versions.

### Requirement 17: Workflow Configuration

**User Story:** As a developer, I want to configure workflow execution behavior declaratively, so that I can define default settings for parallel workers, checkpointing, approval timeouts, and retry policies without modifying code.

#### Acceptance Criteria

1. THE WorkflowConfiguration SHALL contain the maximum parallel workers as an integer with a default value of 4, the checkpoint interval as an optional integer with a default value of 1, the default approval timeout in seconds as a float with a default value of 3600.0, and an optional default RetryPolicy for workflow steps.
2. THE WorkflowConfiguration SHALL support loading configuration from a Python dictionary.
3. THE WorkflowConfiguration SHALL support loading configuration from a JSON file path.
4. THE WorkflowConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE WorkflowConfiguration SHALL resolve the file path relative to the AppContext directory provided by `codecraftai-this-app`.
6. THE WorkflowConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. IF the maximum parallel workers value is less than 1, THEN THE WorkflowConfiguration SHALL raise a ConfigurationError indicating that the maximum parallel workers must be at least 1.
8. IF the default approval timeout value is less than or equal to 0, THEN THE WorkflowConfiguration SHALL raise a ConfigurationError indicating that the approval timeout must be a positive value.
9. THE WorkflowConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration.
10. THE WorkflowConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration.
11. THE WorkflowConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration.
12. THE WorkflowConfiguration SHALL provide a class method from_dict that constructs a WorkflowConfiguration from a dictionary.
13. THE WorkflowConfiguration SHALL provide a class method from_json that deserializes a JSON string into a WorkflowConfiguration instance.
14. THE WorkflowConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into a WorkflowConfiguration instance.
15. FOR ALL valid WorkflowConfiguration instances, calling to_json and then from_json SHALL produce an equivalent WorkflowConfiguration object (round-trip property).
16. FOR ALL valid WorkflowConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent WorkflowConfiguration object (round-trip property).


### Requirement 18: Agent Workflow Integration

**User Story:** As a developer, I want agents to own a workflow registry and execute workflows through the agent interface, so that workflow usage is scoped to individual agents and integrated with the agent lifecycle.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only workflows property that returns the Agent's WorkflowRegistry instance.
2. THE Agent base class SHALL expose a read-only approval_gate property that returns the Agent's ApprovalGate instance.
3. THE Agent base class SHALL provide a register_workflow method that accepts a WorkflowDefinition instance and registers the WorkflowDefinition with the Agent's WorkflowRegistry.
4. THE Agent base class SHALL provide an execute_workflow method that accepts a workflow name, an optional version, and an input dictionary, looks up the WorkflowDefinition in the Agent's WorkflowRegistry, and executes the workflow through the WorkflowExecutor, returning a WorkflowResult.
5. IF the requested workflow name and version combination is not found in the Agent's WorkflowRegistry, THEN THE execute_workflow method SHALL raise a SemanticError that includes the requested workflow name, version, and the agent identity.
6. THE Agent base class SHALL provide a resume_workflow method that accepts a workflow execution identifier and an optional workflow name, loads the checkpoint, and resumes execution, returning a WorkflowResult.
7. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL construct the WorkflowRegistry, WorkflowExecutor, CheckpointManager, and ApprovalGate from the Agent's WorkflowConfiguration.
8. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all WorkflowStep plugins from `codecraftai-extension` ExtensionPoint entries targeting the Agent.
9. WHEN an Agent transitions to the STOPPED state, THE Agent's WorkflowRegistry SHALL be cleared of all registered workflows.
10. WHEN an Agent transitions to the STOPPED state, THE Agent SHALL cancel all pending ApprovalRequest objects in the ApprovalGate.
11. IF the Agent's WorkflowConfiguration is not provided, THEN THE Agent SHALL default to a WorkflowConfiguration with default values.

### Requirement 19: Workflow Step Plugin Integration

**User Story:** As a developer, I want to distribute custom workflow steps as plugins through `codecraftai-extension`, so that step packages can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "ccai.agentkit.workflow_steps" through `codecraftai-extension` for registering WorkflowStep plugin implementations.
2. WHEN an Agent is initialized, THE Agent SHALL query the "ccai.agentkit.workflow_steps" ExtensionPoint and register all discovered WorkflowStep types as available step types for workflow construction.
3. IF a WorkflowStep plugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
4. IF a WorkflowStep plugin provides a step type that conflicts with an already registered step type, THEN THE Agent SHALL log the conflict at WARNING level including both step type names and skip the conflicting plugin step.

### Requirement 20: Workflow Error Handling

**User Story:** As a developer, I want well-defined error types for workflow definition, execution, checkpoint, and approval failures, so that I can diagnose and handle workflow errors precisely.

#### Acceptance Criteria

1. THE WorkflowDefinitionError SHALL inherit from AgentKitError and SHALL be raised when a WorkflowDefinition is structurally invalid.
2. THE WorkflowDefinitionError SHALL contain the workflow name and a descriptive error message identifying the structural problem (cycle detected, missing start step, unreachable steps, invalid edge references).
3. THE WorkflowExecutionError SHALL inherit from AgentKitError and SHALL be raised when a workflow execution fails due to a runtime error during step execution.
4. THE WorkflowExecutionError SHALL contain the workflow name, the step identifier where the error occurred, and the original exception as the cause.
5. THE WorkflowCheckpointError SHALL inherit from AgentKitError and SHALL be raised when a checkpoint save or restore operation fails.
6. THE WorkflowCheckpointError SHALL contain the workflow execution identifier, the operation name (save or load), and the original exception as the cause.
7. THE ApprovalTimeoutError SHALL inherit from AgentKitError and SHALL be raised when an ApprovalRequest exceeds the configured timeout duration.
8. THE ApprovalTimeoutError SHALL contain the approval request identifier, the step identifier, and the timeout duration in seconds.
9. ALL workflow-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name and descriptive message.

### Requirement 21: Workflow Serialization

**User Story:** As a developer, I want to serialize and deserialize workflow definitions, results, checkpoints, and approval requests, so that workflow data can be stored, transmitted, and reconstructed.

#### Acceptance Criteria

1. THE WorkflowDefinition SHALL provide an as_dict method that returns a dictionary representation of the workflow including steps, edges, and parallel branches.
2. THE WorkflowDefinition SHALL provide a to_json method that serializes the workflow definition to a JSON string.
3. THE WorkflowDefinition SHALL provide a to_yaml method that serializes the workflow definition to a YAML string.
4. THE WorkflowDefinition SHALL provide a class method from_dict that constructs a WorkflowDefinition from a dictionary representation, accepting a step type registry for resolving step types.
5. THE WorkflowDefinition SHALL provide a class method from_json that deserializes a JSON string into a WorkflowDefinition instance.
6. THE WorkflowDefinition SHALL provide a class method from_yaml that deserializes a YAML string into a WorkflowDefinition instance.
7. FOR ALL valid WorkflowDefinition instances, calling to_json and then from_json SHALL produce an equivalent WorkflowDefinition object (round-trip property).
8. FOR ALL valid WorkflowDefinition instances, calling to_yaml and then from_yaml SHALL produce an equivalent WorkflowDefinition object (round-trip property).
9. THE WorkflowResult SHALL provide a to_json method that serializes the result to a JSON string.
10. THE WorkflowResult SHALL provide a class method from_json that deserializes a JSON string into a WorkflowResult instance.
11. FOR ALL valid WorkflowResult instances, calling to_json and then from_json SHALL produce an equivalent WorkflowResult object (round-trip property).
12. THE WorkflowCheckpoint SHALL provide a to_json method that serializes the checkpoint to a JSON string.
13. THE WorkflowCheckpoint SHALL provide a class method from_json that deserializes a JSON string into a WorkflowCheckpoint instance.
14. FOR ALL valid WorkflowCheckpoint instances, calling to_json and then from_json SHALL produce an equivalent WorkflowCheckpoint object (round-trip property).
15. THE ApprovalRequest SHALL provide a to_json method that serializes the request to a JSON string.
16. THE ApprovalRequest SHALL provide a class method from_json that deserializes a JSON string into an ApprovalRequest instance.
17. FOR ALL valid ApprovalRequest instances, calling to_json and then from_json SHALL produce an equivalent ApprovalRequest object (round-trip property).

### Requirement 22: Structured Logging for Workflow Operations

**User Story:** As a developer, I want workflow operations to produce structured log entries, so that I can monitor and debug workflow execution using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy under `ccai.agentkit.workflow`.
2. WHEN a workflow execution begins, THE WorkflowExecutor SHALL log at INFO level including the workflow name, execution identifier, and agent identifier.
3. WHEN a workflow execution completes, THE WorkflowExecutor SHALL log at INFO level including the workflow name, execution identifier, execution status, and total duration.
4. WHEN a workflow execution fails, THE WorkflowExecutor SHALL log at WARNING level including the workflow name, execution identifier, the failed step identifier, and error detail.
5. WHEN a step execution begins, THE WorkflowExecutor SHALL log at INFO level including the workflow name, step identifier, and step name.
6. WHEN a step execution completes, THE WorkflowExecutor SHALL log at INFO level including the workflow name, step identifier, execution status, and duration.
7. WHEN a step execution fails, THE WorkflowExecutor SHALL log at WARNING level including the workflow name, step identifier, and error detail.
8. WHEN a checkpoint is saved, THE CheckpointManager SHALL log at INFO level including the workflow name, execution identifier, and the count of completed steps.
9. WHEN a workflow is resumed from a checkpoint, THE WorkflowExecutor SHALL log at INFO level including the workflow name, execution identifier, and the count of previously completed steps.
10. WHEN an ApprovalRequest is created, THE ApprovalGate SHALL log at INFO level including the approval request identifier, workflow name, step identifier, and description.
11. WHEN an ApprovalRequest is approved, THE ApprovalGate SHALL log at INFO level including the approval request identifier and the approver metadata.
12. WHEN an ApprovalRequest is rejected, THE ApprovalGate SHALL log at WARNING level including the approval request identifier and the rejection reason.
13. WHEN an ApprovalRequest times out, THE ApprovalGate SHALL log at WARNING level including the approval request identifier and the timeout duration.
14. WHEN parallel branches are forked, THE WorkflowExecutor SHALL log at INFO level including the workflow name, fork step identifier, and the count of parallel branches.
15. WHEN parallel branches are joined, THE WorkflowExecutor SHALL log at INFO level including the workflow name, join step identifier, and the count of completed branches.

### Requirement 23: Workflow String Representations

**User Story:** As a developer, I want meaningful string representations on workflow system classes, so that I can quickly inspect workflow state during debugging sessions.

#### Acceptance Criteria

1. THE WorkflowDefinition SHALL provide a __repr__ method that includes the class name, workflow name, version, and step count.
2. THE WorkflowDefinition SHALL provide a __str__ method that returns a human-readable summary including the workflow name, version, step count, and edge count.
3. THE WorkflowStep base class SHALL provide a __repr__ method that includes the class name, step identifier, step name, and step type.
4. THE WorkflowStep base class SHALL provide a __str__ method that returns a human-readable summary including the step name and step type.
5. THE WorkflowEdge SHALL provide a __repr__ method that includes the class name, source step identifier, target step identifier, and whether a condition is present.
6. THE WorkflowEdge SHALL provide a __str__ method that returns a human-readable summary including the source, target, and condition expression.
7. THE WorkflowResult SHALL provide a __repr__ method that includes the class name, workflow name, and execution status.
8. THE WorkflowResult SHALL provide a __str__ method that returns a human-readable summary including the workflow name, status, step count, and total duration.
9. THE StepResult SHALL provide a __repr__ method that includes the class name, step identifier, and execution status.
10. THE StepResult SHALL provide a __str__ method that returns a human-readable summary including the step name, status, and duration.
11. THE WorkflowContext SHALL provide a __repr__ method that includes the class name, the count of completed steps, and the count of input fields.
12. THE WorkflowContext SHALL provide a __str__ method that returns a human-readable summary including the count of completed steps and input field names.
13. THE WorkflowCheckpoint SHALL provide a __repr__ method that includes the class name, workflow name, execution identifier, and the count of completed steps.
14. THE WorkflowCheckpoint SHALL provide a __str__ method that returns a human-readable summary including the workflow name, execution identifier, and timestamp.
15. THE ApprovalRequest SHALL provide a __repr__ method that includes the class name, identifier, step identifier, and approval status.
16. THE ApprovalRequest SHALL provide a __str__ method that returns a human-readable summary including the identifier, description, and approval status.
17. THE ApprovalGate SHALL provide a __repr__ method that includes the class name and the count of pending approvals.
18. THE ApprovalGate SHALL provide a __str__ method that returns a human-readable summary including the count of pending approvals.
19. THE WorkflowRegistry SHALL provide a __repr__ method that includes the class name and the count of registered workflows.
20. THE WorkflowRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered workflow names and versions.
21. THE WorkflowExecutor SHALL provide a __repr__ method that includes the class name and the workflow name being executed.
22. THE WorkflowExecutor SHALL provide a __str__ method that returns a human-readable summary including the workflow name and execution status.
23. THE WorkflowConfiguration SHALL provide a __repr__ method that includes the class name, maximum parallel workers, and checkpoint interval.
24. THE WorkflowConfiguration SHALL provide a __str__ method that returns a human-readable summary including the maximum parallel workers, checkpoint interval, and default approval timeout.
25. THE ParallelBranch SHALL provide a __repr__ method that includes the class name, fork step identifier, and join step identifier.
26. THE ParallelBranch SHALL provide a __str__ method that returns a human-readable summary including the fork and join step identifiers.
27. THE CheckpointManager SHALL provide a __repr__ method that includes the class name and the MemoryStore name.
28. THE CheckpointManager SHALL provide a __str__ method that returns a human-readable summary including the MemoryStore name.
