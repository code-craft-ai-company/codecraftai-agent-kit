# Implementation Plan: Tool & Capability System

## Overview

Incremental implementation of the Tool & Capability System for the `automojo-agent-kit` SDK. Tasks build bottom-up: foundational types first (schema, errors, result), then core abstractions (tool, registry, executor), then composition (chain), then built-in tools, then agent integration and plugin support. Each task references specific requirements and design properties. Tests are placed close to the code they validate.

## Tasks

- [ ] 1. Implement ToolSchema and ToolErrors
  - [ ] 1.1 Create `source/packages/automojo/agentkit/toolschema.py` with the ToolSchema class
    - Implement `__init__` accepting a list of parameter definitions
    - Implement `parameters` and `parameter_count` read-only properties
    - Implement `validate(values)` returning a list of error strings: check required params, type constraints, apply defaults for optional params
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, schema_data)`, `from_json(cls, json_str)` for serialization
    - Implement `__repr__` (class name + parameter count) and `__str__` (parameter names and types)
    - Support empty schema (no parameters) for tools with no input/output
    - Use `SUPPORTED_TYPES` and `TYPE_MAP` class constants as defined in design
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 16.3, 16.4, 16.6, 18.5, 18.6_

  - [ ] 1.2 Create `source/packages/automojo/agentkit/toolerrors.py` with ToolValidationError and ToolExecutionError
    - ToolValidationError inherits from AgentKitError, stores tool_name, direction ("input"/"output"), errors list
    - ToolExecutionError inherits from AgentKitError, stores tool_name, cause exception
    - Both provide `__repr__` with class name, tool name, and descriptive message
    - Use multi-line error message formation pattern per coding standards
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [ ] 1.3 Write property tests for ToolSchema (Properties 1–4)
    - **Property 1: ToolSchema JSON round-trip** — for any valid ToolSchema, `from_json(to_json())` produces equivalent `as_dict()` output
    - **Validates: Requirements 3.8, 3.9, 3.10, 3.11, 3.12, 16.3, 16.4, 16.6**
    - **Property 2: ToolSchema validates correct inputs as valid** — valid inputs produce empty error list
    - **Validates: Requirements 3.1, 3.2, 3.5**
    - **Property 3: ToolSchema reports missing required parameters** — missing required param yields error containing param name
    - **Validates: Requirements 3.6**
    - **Property 4: ToolSchema reports type mismatches** — wrong type yields error with param name, expected type, actual type
    - **Validates: Requirements 3.7**

  - [ ] 1.4 Write unit tests for ToolSchema and ToolErrors
    - Test empty schema validates any input
    - Test default values applied for optional parameters
    - Test parameter description storage
    - Test ToolValidationError fields (tool_name, direction, errors) and repr
    - Test ToolExecutionError fields (tool_name, cause) and repr
    - Test ToolSchema __repr__ and __str__ output
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_toolschema.py` and `test_toolerrors.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.13, 15.1, 15.2, 15.3, 15.4, 15.5, 18.5, 18.6_

- [ ] 2. Implement ToolDescriptor and ToolResult
  - [ ] 2.1 Create `source/packages/automojo/agentkit/tooldescriptor.py` with the ToolDescriptor class
    - Implement `__init__` with name, description, version, input_schema, output_schema, tags
    - Implement all read-only properties
    - Implement `as_dict()`, `to_json()`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, tool name, version) and `__str__` (tool name, description)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 16.1, 16.2, 16.5, 18.3, 18.4_

  - [ ] 2.2 Create `source/packages/automojo/agentkit/toolresult.py` with the ToolResult class
    - Implement `__init__` with tool_name, status, output, duration, error
    - Implement all read-only properties including `is_success`
    - Implement `as_dict()`, `__repr__`, `__str__`
    - Use STATUS_SUCCESS and STATUS_FAILURE class constants
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 18.7, 18.8_

  - [ ] 2.3 Write property tests for ToolDescriptor and ToolResult (Properties 5, 15, 16)
    - **Property 5: ToolDescriptor JSON round-trip** — `from_json(to_json())` produces equivalent ToolDescriptor
    - **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 16.1, 16.2, 16.5**
    - **Property 15: ToolResult is_success reflects status** — True for "success", False for "failure"
    - **Validates: Requirements 6.3**
    - **Property 16: ToolResult fields and as_dict correctness** — all fields accessible, as_dict matches
    - **Validates: Requirements 6.1, 6.2, 6.4**

  - [ ] 2.4 Write unit tests for ToolDescriptor and ToolResult
    - Test ToolDescriptor read-only properties
    - Test ToolDescriptor __repr__ and __str__
    - Test ToolResult with None output, failure status with error
    - Test ToolResult __repr__ and __str__
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_tooldescriptor.py` and `test_toolresult.py`
    - _Requirements: 2.1, 2.2, 6.1, 6.2, 6.5, 6.6, 18.3, 18.4, 18.7, 18.8_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement Tool base class and create_tool factory
  - [ ] 4.1 Create `source/packages/automojo/agentkit/tool.py` with the Tool abstract base class
    - Implement `__init__` accepting optional tags dict and credential_names list
    - Support class-level TOOL_NAME, TOOL_DESCRIPTION, TOOL_VERSION, INPUT_SCHEMA, OUTPUT_SCHEMA declarations
    - Validate class-level schema dicts at construction, raise SemanticError if invalid
    - Raise SemanticError if name is None
    - Implement read-only properties: name, description, version, input_schema, output_schema, tags, credential_names
    - Implement `descriptor` property returning a ToolDescriptor
    - Declare abstract `execute(self, inputs, credentials=None)` method
    - Implement `__repr__` (class name, tool name, version) and `__str__` (tool name, description)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 12.1, 12.2, 12.3, 12.4, 12.5, 18.1, 18.2_

  - [ ] 4.2 Create `source/packages/automojo/agentkit/toolfactory.py` with the create_tool function
    - Implement `create_tool(name, description, input_schema, output_schema, execute_fn, version, tags)` returning a Tool instance
    - Internally create a dynamic Tool subclass that delegates execute to the provided callable
    - _Requirements: 12.6_

  - [ ] 4.3 Write property tests for Tool and create_tool (Properties 6, 7, 8, 26)
    - **Property 6: Tool descriptor property reflects tool metadata** — descriptor fields match tool properties
    - **Validates: Requirements 1.3, 12.2, 12.3**
    - **Property 7: Tool construction preserves tags and credential names** — tags and credential_names match provided values
    - **Validates: Requirements 1.4, 1.5**
    - **Property 8: Tool class-level schema declarations validated and converted** — valid schemas produce ToolSchema instances, invalid raise SemanticError
    - **Validates: Requirements 12.1, 12.5**
    - **Property 26: create_tool factory produces working Tool** — returned Tool has correct name, description, schemas, and delegates execute
    - **Validates: Requirements 12.6**

  - [ ] 4.4 Write unit tests for Tool and create_tool
    - Test Tool without name raises SemanticError
    - Test abstract execute method enforcement
    - Test Tool __repr__ and __str__
    - Test create_tool with various schema configurations
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_tool.py` and `test_toolfactory.py`
    - _Requirements: 1.1, 1.2, 1.6, 1.7, 1.8, 12.6, 18.1, 18.2_

- [ ] 5. Implement ToolRegistry
  - [ ] 5.1 Create `source/packages/automojo/agentkit/toolregistry.py` with the ToolRegistry class
    - Implement `__init__` with internal `_tools` dict
    - Implement `register(tool)` raising SemanticError on duplicate name
    - Implement `deregister(tool_name)`, `lookup(tool_name)` returning Tool or None
    - Implement `lookup_by_tags(**tags)` returning list of matching Tools
    - Implement `list_all()`, `list_descriptors()`, `has_tool(tool_name)`, `clear()`
    - Implement `count` read-only property
    - Implement `__repr__` (class name, count) and `__str__` (registered tool names)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 18.11, 18.12_

  - [ ] 5.2 Write property tests for ToolRegistry (Properties 9, 10, 11)
    - **Property 9: ToolRegistry registration, lookup, and enumeration correctness** — count, lookup, has_tool, list_all, list_descriptors, duplicate raises SemanticError
    - **Validates: Requirements 4.1, 4.2, 4.4, 4.6, 4.7, 4.8, 4.9**
    - **Property 10: ToolRegistry deregistration removes tool** — after deregister, lookup returns None, has_tool False, count decreases
    - **Validates: Requirements 4.3**
    - **Property 11: ToolRegistry lookup by tags returns matching tools** — returns exactly tools matching all tag criteria
    - **Validates: Requirements 4.5**

  - [ ] 5.3 Write unit tests for ToolRegistry
    - Test empty registry count is 0
    - Test deregister non-existent tool behavior
    - Test lookup_by_tags with no matches
    - Test __repr__ and __str__
    - Create test file at `source/testroots/automojo/tests/singlehost/agentkit/test_toolregistry.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 18.11, 18.12_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement ToolExecutor with credential resolution and logging
  - [ ] 7.1 Create `source/packages/automojo/agentkit/toolexecutor.py` with the ToolExecutor class
    - Implement `__init__` accepting optional credential_resolver
    - Use `logging.getLogger("automojo.agentkit.tools")` for structured logging
    - Implement `execute(tool, inputs, agent_identifier=None)` method:
      - Validate inputs against tool's input_schema, raise ToolValidationError on failure
      - Resolve credential references via automojo-credentials, raise ConfigurationError on failure
      - Invoke tool.execute(inputs, credentials), measure duration
      - Validate output against tool's output_schema, raise ToolValidationError on failure
      - Return ToolResult with success status on success
      - Return ToolResult with failure status if execute raises exception
    - Log at INFO level on execution begin and success, WARNING on failure and validation errors
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 17.1, 17.2, 17.3, 17.4, 17.5_

  - [ ] 7.2 Write property tests for ToolExecutor (Properties 12, 13, 14)
    - **Property 12: ToolExecutor validates input and rejects invalid inputs** — invalid input raises ToolValidationError without calling execute
    - **Validates: Requirements 5.1, 5.2**
    - **Property 13: ToolExecutor validates output and rejects invalid outputs** — invalid output raises ToolValidationError
    - **Validates: Requirements 5.4, 5.5**
    - **Property 14: ToolExecutor returns correct ToolResult based on execution outcome** — success yields success result, exception yields failure result, both with non-negative duration
    - **Validates: Requirements 5.6, 5.7**

  - [ ] 7.3 Write unit tests for ToolExecutor
    - Test credential resolution success and failure (mock automojo-credentials)
    - Test logging output at correct levels (INFO begin/success, WARNING failure/validation)
    - Test execution duration is recorded
    - Create test file at `source/testroots/automojo/tests/singlehost/agentkit/test_toolexecutor.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 8. Implement ToolChain, ToolChainExecutor, and ToolChainResult
  - [ ] 8.1 Create `source/packages/automojo/agentkit/toolchainresult.py` with the ToolChainResult class
    - Implement `__init__` with chain_name, status, output, step_results, duration, error
    - Implement all read-only properties including `is_success` and `step_results`
    - Implement `as_dict()`, `__repr__`, `__str__`
    - Use STATUS_SUCCESS and STATUS_FAILURE class constants
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 18.9, 18.10_

  - [ ] 8.2 Create `source/packages/automojo/agentkit/toolchain.py` with the ToolChain class
    - Implement `__init__` with name, steps list, and registry reference
    - Validate all tool names exist in registry at construction, raise SemanticError for missing
    - Validate schema compatibility between consecutive steps per mappings, raise ToolValidationError on mismatch
    - Implement `name`, `tool_names`, `step_count` read-only properties
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.10, 7.11_

  - [ ] 8.3 Create `source/packages/automojo/agentkit/toolchainexecutor.py` with the ToolChainExecutor class
    - Implement `__init__` accepting a ToolExecutor
    - Implement `execute(chain, initial_inputs, agent_identifier=None)` method:
      - Execute each step in sequence via ToolExecutor
      - Apply input-output mappings between steps
      - Return ToolChainResult with success if all steps succeed
      - Stop and return ToolChainResult with failure if any step fails
    - _Requirements: 7.6, 7.7, 7.8, 7.9_

  - [ ] 8.4 Write property tests for ToolChain, ToolChainExecutor, ToolChainResult (Properties 17–23)
    - **Property 17: ToolChain validates tool existence at construction** — missing tool raises SemanticError
    - **Validates: Requirements 7.2, 7.3**
    - **Property 18: ToolChain validates schema compatibility at construction** — incompatible schemas raise ToolValidationError
    - **Validates: Requirements 7.4, 7.5**
    - **Property 19: ToolChainExecutor executes steps in sequence with mappings** — steps run in order with mapped outputs
    - **Validates: Requirements 7.6, 7.7**
    - **Property 20: ToolChainExecutor returns correct result based on outcome** — all success yields success result, failure stops execution
    - **Validates: Requirements 7.8, 7.9**
    - **Property 21: ToolChain exposes correct tool names and step count** — tool_names and step_count match steps
    - **Validates: Requirements 7.10, 7.11**
    - **Property 22: ToolChainResult is_success reflects status** — True for success, False for failure
    - **Validates: Requirements 8.3**
    - **Property 23: ToolChainResult fields and as_dict correctness** — all fields accessible, as_dict matches
    - **Validates: Requirements 8.1, 8.2, 8.4, 8.5**

  - [ ] 8.5 Write unit tests for ToolChain, ToolChainExecutor, ToolChainResult
    - Test single-step chain
    - Test ToolChainResult __repr__ and __str__
    - Test chain with no mappings (pass-through)
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_toolchain.py`, `test_toolchainexecutor.py`, `test_toolchainresult.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 18.9, 18.10_

- [ ] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement built-in tools
  - [ ] 10.1 Create `source/packages/automojo/agentkit/builtins/filereadtool.py` with the FileReadTool class
    - Subclass Tool with TOOL_NAME="file_read", INPUT_SCHEMA (file_path required, encoding optional default "utf-8"), OUTPUT_SCHEMA (content string)
    - Implement execute: read file, return content; raise ToolExecutionError for FileNotFoundError and PermissionError
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 10.2 Create `source/packages/automojo/agentkit/builtins/filewritetool.py` with the FileWriteTool class
    - Subclass Tool with TOOL_NAME="file_write", INPUT_SCHEMA (file_path, content required, encoding optional default "utf-8"), OUTPUT_SCHEMA (bytes_written integer)
    - Implement execute: write content, return bytes_written; raise ToolExecutionError for PermissionError
    - _Requirements: 9.5, 9.6, 9.7_

  - [ ] 10.3 Create `source/packages/automojo/agentkit/builtins/httprequesttool.py` with the HttpRequestTool class
    - Subclass Tool with TOOL_NAME="http_request", INPUT_SCHEMA (url, method required; headers, body, timeout_seconds optional), OUTPUT_SCHEMA (status_code, headers, body)
    - Implement execute using urllib or similar; raise ToolExecutionError for timeout and connection errors
    - Support CredentialReference resolution for authentication headers
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 10.4 Create `source/packages/automojo/agentkit/builtins/shellcommandtool.py` with the ShellCommandTool class
    - Subclass Tool with TOOL_NAME="shell_command", INPUT_SCHEMA (command required; working_directory, timeout_seconds, environment, safe_mode optional), OUTPUT_SCHEMA (exit_code, stdout, stderr)
    - Implement execute using subprocess; raise ToolExecutionError for timeout, missing working directory
    - Implement safe_mode metacharacter rejection using SHELL_METACHARACTERS set
    - Default safe_mode to True
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [ ] 10.5 Create `source/packages/automojo/agentkit/builtins/__init__.py` to expose built-in tools
    - _Requirements: 9.1, 10.1, 11.1_

  - [ ] 10.6 Write property tests for built-in tools (Properties 24, 25)
    - **Property 24: File I/O round-trip** — write then read produces original content
    - **Validates: Requirements 9.2, 9.6**
    - **Property 25: ShellCommandTool rejects metacharacters in safe mode** — commands with metacharacters raise ToolExecutionError
    - **Validates: Requirements 11.5**

  - [ ] 10.7 Write unit tests for built-in tools
    - Test FileReadTool with real temp files, file not found, permission error
    - Test FileWriteTool with real temp files, permission error
    - Test HttpRequestTool with mocked HTTP (using automojo.testbase.mocking.Mock), timeout, connection error
    - Test ShellCommandTool with simple commands, timeout, missing working directory, safe_mode on/off
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/builtins/test_filereadtool.py`, `test_filewritetool.py`, `test_httprequesttool.py`, `test_shellcommandtool.py`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 10.1, 10.2, 10.3, 10.4, 10.5, 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement Agent tool integration and plugin support
  - [ ] 12.1 Extend the Agent base class with tool-related properties and methods
    - Add `tools` read-only property returning the Agent's ToolRegistry instance
    - Add `register_tool(tool)` method delegating to the ToolRegistry
    - Add `execute_tool(tool_name, inputs)` method: lookup tool, execute via ToolExecutor, raise SemanticError if not found (include tool name and agent identity)
    - Add `execute_chain(chain, inputs)` method: execute via ToolChainExecutor, return ToolChainResult
    - Initialize ToolRegistry, ToolExecutor, and ToolChainExecutor during Agent construction
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.6_

  - [ ] 12.2 Implement ToolPlugin discovery during Agent initialization
    - During Agent `initialize()` (transition to INITIALIZED state), query "automojo.agentkit.tools" ExtensionPoint
    - Register discovered Tool instances with the Agent's ToolRegistry
    - Log WARNING and skip on plugin load failure or name conflict
    - _Requirements: 13.5, 14.1, 14.2, 14.3, 14.4_

  - [ ] 12.3 Implement ToolRegistry clearing on Agent stop
    - During Agent `stop()` (transition to STOPPED state), call `self._tool_registry.clear()`
    - _Requirements: 13.7_

  - [ ] 12.4 Write property tests for Agent tool integration (Properties 27, 28, 29)
    - **Property 27: Agent tool registration and execution** — register_tool makes tool discoverable, execute_tool returns ToolResult
    - **Validates: Requirements 13.2, 13.3**
    - **Property 28: Agent execute_tool raises SemanticError for unknown tool** — unknown name raises SemanticError with tool name and agent identity
    - **Validates: Requirements 13.4**
    - **Property 29: Agent ToolRegistry cleared on stop** — after stop, registry count is zero
    - **Validates: Requirements 13.7**

  - [ ] 12.5 Write unit tests for Agent tool integration and plugin support
    - Test Agent.tools property returns ToolRegistry
    - Test register_tool and execute_tool end-to-end with mock tool
    - Test execute_chain with mock chain
    - Test plugin discovery with mocked ExtensionPoint (using automojo.testbase.mocking.Mock)
    - Test plugin load failure logging
    - Test plugin name conflict logging and skip
    - Test ToolRegistry cleared after Agent.stop()
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 14.1, 14.2, 14.3, 14.4_

- [ ] 13. Implement string representations and final property tests
  - [ ] 13.1 Verify and complete all `__repr__` and `__str__` methods across all tool system classes
    - Ensure Tool, ToolDescriptor, ToolSchema, ToolResult, ToolChainResult, ToolRegistry, ToolValidationError, ToolExecutionError all have correct repr/str per design
    - _Requirements: 1.7, 1.8, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9, 18.10, 18.11, 18.12, 15.5_

  - [ ] 13.2 Write property test for string representations (Property 31)
    - **Property 31: Tool string representations contain required information** — verify repr/str for Tool, ToolDescriptor, ToolSchema, ToolResult, ToolChainResult, ToolRegistry, and tool exceptions
    - **Validates: Requirements 1.7, 1.8, 18.1–18.12, 15.5**

  - [ ] 13.3 Write property test for tool error fields (Property 30)
    - **Property 30: Tool exception fields are accessible** — ToolValidationError and ToolExecutionError fields match constructor args
    - **Validates: Requirements 15.2, 15.4**

- [ ] 14. Wire package exports and final integration
  - [ ] 14.1 Update `source/packages/automojo/agentkit/__init__.py` to export all tool system classes
    - Export ToolSchema, ToolDescriptor, Tool, ToolResult, ToolRegistry, ToolExecutor, ToolChain, ToolChainExecutor, ToolChainResult, ToolValidationError, ToolExecutionError, create_tool
    - Export built-in tools: FileReadTool, FileWriteTool, HttpRequestTool, ShellCommandTool
    - _Requirements: 1.1, 4.1, 5.1, 7.1, 9.1, 10.1, 11.1, 12.6_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (31 total across Properties 1–31)
- Unit tests validate specific examples, edge cases, and integration with external packages
- All mocking uses `automojo.testbase.mocking.Mock` per project conventions
- Tests reside under `source/testroots/automojo/tests/singlehost/agentkit/` mirroring the source hierarchy
