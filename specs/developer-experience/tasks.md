# Implementation Plan: Developer Experience

## Overview

Implement the Developer Experience feature for the `automojo-agent-kit` SDK. The implementation follows a bottom-up approach: error types and naming utility first, then immutable data models (ScaffoldTemplate, ScaffoldResult, ReplResult, DocEntry, ExampleCode, TypeCheckConfiguration, ApiSurfaceReport, DevExConfiguration), then registries, then abstract base classes and concrete implementations, then the coordination layers (ScaffoldCli, AgentRepl, DocGenerator, TypeAnnotationValidator, RuntimeTypeChecker, ApiSurfaceValidator). All source files go under `source/packages/automojo/agentkit/` with lowercase filenames (no underscores). Tests go under `source/testroots/automojo/tests/singlehost/agentkit/`.

## Tasks

- [ ] 1. Implement developer experience error types
  - [ ] 1.1 Create `devexerrors.py` with ScaffoldError, ReplError, TypeCheckError, and ApiSurfaceError
    - All inherit from AgentKitError with message and optional cause parameters
    - Each provides a __repr__ method including class name and descriptive message
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6_

  - [ ]* 1.2 Write unit tests for developer experience error types
    - Create `test_devexerrors.py` testing construction, message, cause, __repr__ for all four error classes
    - Verify inheritance from AgentKitError
    - _Requirements: 24.1–24.6_

- [ ] 2. Implement NamingConvention utility
  - [ ] 2.1 Create `namingconvention.py` with NamingConvention class
    - Implement to_pascal_case class method converting strings to PascalCase
    - Implement to_file_name class method converting strings to all-lowercase-no-underscores
    - Implement to_snake_case class method converting strings to snake_case
    - Implement to_module_path class method converting file paths to dot-separated module paths
    - Implement validate_class_name class method returning boolean for PascalCase compliance
    - Implement validate_file_name class method returning boolean for all-lowercase-no-underscores compliance
    - Implement __repr__ and __str__ methods
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

  - [ ]* 2.2 Write unit tests for NamingConvention
    - Create `test_namingconvention.py` testing all conversion methods with various inputs
    - Test validate_class_name and validate_file_name with valid and invalid inputs
    - Test to_module_path with file paths
    - Test edge cases: empty strings, single characters, already-formatted names
    - _Requirements: 6.1–6.9_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement scaffold data models
  - [ ] 4.1 Create `scaffoldtemplate.py` with ScaffoldTemplate class
    - Immutable object with name, component_type, path_pattern, content, defaults properties
    - Validate component_type against VALID_COMPONENT_TYPES, raise SemanticError for invalid types
    - Implement render method merging variables with defaults, replacing placeholders, raising ScaffoldError for missing variables
    - Implement render_path method with same placeholder replacement logic
    - Support placeholders: {class_name}, {file_name}, {module_name}, {component_name}
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13_

  - [ ] 4.2 Create `scaffoldcontext.py` with ScaffoldContext class
    - Mutable context with target_directory, component_name, component_type, variables, generated_files
    - All fields read-only except generated_files which supports appending via add_generated_file
    - Implement __repr__ and __str__ methods
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [ ] 4.3 Create `scaffoldresult.py` with ScaffoldResult class
    - Immutable object with component_name, component_type, generated_files, success properties
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11, 5.12, 5.13_

  - [ ]* 4.4 Write unit tests for scaffold data models
    - Create `test_scaffoldtemplate.py` testing construction, properties, render, render_path, missing variable error, invalid component_type, serialization
    - Create `test_scaffoldcontext.py` testing construction, properties, add_generated_file, __repr__, __str__
    - Create `test_scaffoldresult.py` testing construction, properties, serialization, __repr__, __str__
    - _Requirements: 3.1–3.13, 5.1–5.13_

- [ ] 5. Implement ScaffoldTemplateRegistry
  - [ ] 5.1 Create `scaffoldtemplateregistry.py` with ScaffoldTemplateRegistry class
    - Support register, deregister, lookup by name, lookup_by_type, list_all, has_template, count property
    - Raise SemanticError on duplicate template name registration
    - Implement load_extensions for automojo-extension plugin discovery
    - Implement __repr__ and __str__ methods
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11_

  - [ ]* 5.2 Write unit tests for ScaffoldTemplateRegistry
    - Create `test_scaffoldtemplateregistry.py` testing register, deregister, lookup, lookup_by_type, list_all, has_template, count
    - Test duplicate name raises SemanticError
    - Test empty registry edge cases
    - _Requirements: 4.1–4.11_

- [ ] 6. Implement ScaffoldCommand ABC and concrete scaffold commands
  - [ ] 6.1 Create `scaffoldcommand.py` with ScaffoldCommand abstract base class
    - Define abstract properties: name, component_type, description
    - Define abstract execute method accepting component_name, context, template_registry, template_name, dry_run, force
    - Implement __repr__ and __str__ methods
    - _Requirements: 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12_

  - [ ] 6.2 Create `agentscaffoldcommand.py` with AgentScaffoldCommand class
    - Concrete ScaffoldCommand generating Agent subclass file, AgentConfiguration file, and test file
    - Use NamingConvention for PascalCase class names and lowercase file names
    - Support --template, --output-dir, --dry-run, --force options
    - Generate files with complete type hints and docstrings
    - _Requirements: 2.1, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12_

  - [ ] 6.3 Create `toolscaffoldcommand.py` with ToolScaffoldCommand class
    - Concrete ScaffoldCommand generating Tool subclass file with ToolSchema definitions and test file
    - _Requirements: 2.2, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12_

  - [ ] 6.4 Create `workflowscaffoldcommand.py` with WorkflowScaffoldCommand class
    - Concrete ScaffoldCommand generating WorkflowDefinition file with sample DAG and test file
    - _Requirements: 2.3, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12_

  - [ ] 6.5 Create `serializerscaffoldcommand.py` with SerializerScaffoldCommand class
    - Concrete ScaffoldCommand generating MessageSerializer subclass file and test file
    - _Requirements: 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12_

  - [ ]* 6.6 Write unit tests for ScaffoldCommand and concrete commands
    - Create `test_scaffoldcommand.py` testing abstract method enforcement
    - Create `test_agentscaffoldcommand.py` testing execute with dry_run, force, file skip on existing, naming conventions
    - Create `test_toolscaffoldcommand.py` testing execute with generated file structure
    - Create `test_workflowscaffoldcommand.py` testing execute with generated file structure
    - Create `test_serializerscaffoldcommand.py` testing execute with generated file structure
    - _Requirements: 2.1–2.12_

- [ ] 7. Implement ScaffoldCli
  - [ ] 7.1 Create `scaffoldcli.py` with ScaffoldCli class
    - Built on automojo-arcli framework with top-level `agentkit` command group
    - Register scaffold commands, support register_command, load_extensions, execute methods
    - Resolve target directory from AppContext via automojo-this-app, default to cwd
    - Support --dry-run and --force options on all subcommands
    - Display summary of generated files on success, descriptive error on failure with non-zero exit
    - Log at INFO level under `automojo.agentkit.devex.cli`
    - Implement command_count property, __repr__ and __str__ methods
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11_

  - [ ]* 7.2 Write unit tests for ScaffoldCli
    - Create `test_scaffoldcli.py` testing command registration, duplicate command SemanticError, execute dispatch
    - Test dry_run and force option propagation
    - Mock automojo-arcli and automojo-extension using testbase.mocking.Mock
    - _Requirements: 1.1–1.11_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement REPL data models
  - [ ] 9.1 Create `replresult.py` with ReplResult class
    - Immutable object with command_name, output, success, error_message properties
    - Implement as_dict, __repr__, __str__ methods
    - __str__ returns output when successful, error_message when unsuccessful
    - _Requirements: 10.9, 10.10, 10.11, 10.12, 10.13_

  - [ ] 9.2 Create `replsession.py` with ReplSession class
    - Mutable context with agent, history, start_time, correlation_context
    - Implement set_agent, add_to_history methods
    - Implement duration_seconds computed property
    - Implement __repr__ and __str__ methods
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

  - [ ]* 9.3 Write unit tests for REPL data models
    - Create `test_replresult.py` testing construction, properties, as_dict, __repr__, __str__ for success and error cases
    - Create `test_replsession.py` testing agent lifecycle, history tracking, duration calculation, __repr__, __str__
    - _Requirements: 10.1–10.13_

- [ ] 10. Implement ReplCommand ABC and ReplCommandRegistry
  - [ ] 10.1 Create `replcommand.py` with ReplCommand abstract base class
    - Define abstract properties: name, aliases, description, usage
    - Define abstract execute method accepting session and arguments, returning ReplResult
    - Implement __repr__ and __str__ methods
    - _Requirements: 8.1, 8.2, 8.13, 8.14_

  - [ ] 10.2 Create `replcommandregistry.py` with ReplCommandRegistry class
    - Support register (with alias registration), deregister (removing aliases), lookup by name or alias
    - Support list_all (excluding alias duplicates), has_command, count property
    - Raise SemanticError on duplicate name or alias
    - Implement load_extensions for automojo-extension plugin discovery
    - Implement __repr__ and __str__ methods
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11_

  - [ ]* 10.3 Write unit tests for ReplCommand and ReplCommandRegistry
    - Create `test_replcommand.py` testing abstract method enforcement, __repr__, __str__
    - Create `test_replcommandregistry.py` testing register, alias registration, deregister, lookup by name and alias, duplicate detection, list_all, has_command
    - _Requirements: 8.1, 8.2, 8.13, 8.14, 9.1–9.11_

- [ ] 11. Implement ReplFormatter and concrete formatters
  - [ ] 11.1 Create `replformatter.py` with ReplFormatter abstract base class
    - Define abstract properties: formatter_name
    - Define abstract methods: format_result, format_error, format_prompt
    - Implement __repr__ and __str__ methods
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.7, 11.8, 11.9_

  - [ ] 11.2 Create `plaintextreplformatter.py` with PlainTextReplFormatter class
    - Format output as plain text without terminal escape codes
    - _Requirements: 11.5_

  - [ ] 11.3 Create `coloredreplformatter.py` with ColoredReplFormatter class
    - Format output with ANSI color codes for syntax highlighting, error highlighting, and prompt styling
    - _Requirements: 11.6_

  - [ ]* 11.4 Write unit tests for ReplFormatter and concrete formatters
    - Create `test_replformatter.py` testing abstract method enforcement
    - Create `test_plaintextreplformatter.py` testing format_result, format_error, format_prompt output
    - Create `test_coloredreplformatter.py` testing ANSI codes in format_result, format_error, format_prompt output
    - _Requirements: 11.1–11.9_

- [ ] 12. Implement AgentRepl
  - [ ] 12.1 Create `agentrepl.py` with AgentRepl class
    - Accept optional Agent, AgentConfiguration, and ReplFormatter at construction
    - Create ReplSession at startup with CorrelationContext
    - Discover and load ReplCommand plugins via automojo-extension
    - Implement execute_command parsing command name and arguments, looking up in registry, executing, formatting output
    - Handle unknown commands and command exceptions gracefully, continuing the REPL loop
    - Support command completion using registered command names and aliases
    - Provide built-in help and quit commands
    - Display prompt with agent name and LifecycleState when agent active
    - Log at DEBUG level under `automojo.agentkit.devex.repl`
    - Implement session and command_registry properties, __repr__ and __str__ methods
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13_

  - [ ]* 12.2 Write unit tests for AgentRepl
    - Create `test_agentrepl.py` testing execute_command with success and error paths
    - Test unknown command handling
    - Test REPL with no active agent
    - Mock Agent, ReplCommand, and extension loading using testbase.mocking.Mock
    - _Requirements: 7.1–7.13_

- [ ] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Implement documentation system data models
  - [ ] 14.1 Create `docentry.py` with DocEntry class
    - Immutable object with qualified_name, signature, docstring, parameter_descriptions, return_description, examples
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9_

  - [ ] 14.2 Create `examplecode.py` with ExampleCode class
    - Immutable object with title, description, code, expected_output, required_components
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9_

  - [ ]* 14.3 Write unit tests for documentation data models
    - Create `test_docentry.py` testing construction, properties, serialization, __repr__, __str__
    - Create `test_examplecode.py` testing construction, properties, serialization, __repr__, __str__
    - _Requirements: 13.1–13.9, 15.1–15.9_

- [ ] 15. Implement documentation registries
  - [ ] 15.1 Create `docregistry.py` with DocRegistry class
    - Support register, lookup by qualified_name, lookup_by_module prefix, search across docstrings, list_all, count
    - Implement __repr__ and __str__ methods
    - _Requirements: 13.10, 13.11, 13.12, 13.13, 13.14, 13.15, 13.16, 13.17_

  - [ ] 15.2 Create `exampleregistry.py` with ExampleRegistry class
    - Support register, lookup_by_component, list_all, count, load_extensions
    - Implement __repr__ and __str__ methods
    - _Requirements: 15.10, 15.11, 15.12, 15.13, 15.14, 15.15, 15.16_

  - [ ]* 15.3 Write unit tests for documentation registries
    - Create `test_docregistry.py` testing register, lookup, lookup_by_module, search, list_all, count, empty registry
    - Create `test_exampleregistry.py` testing register, lookup_by_component, list_all, count, empty registry
    - _Requirements: 13.10–13.17, 15.10–15.16_

- [ ] 16. Implement DocGenerator and InlineHelpProvider
  - [ ] 16.1 Create `docgenerator.py` with DocGenerator class
    - Accept list of module paths, introspect modules for public classes, methods, functions
    - Extract signatures, type hints, docstrings; skip private members except __init__, __repr__, __str__
    - Populate DocRegistry with generated DocEntry instances
    - Track modules_processed and entries_generated counts
    - Log at INFO level under `automojo.agentkit.devex.docs`
    - Implement __repr__ and __str__ methods
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9_

  - [ ] 16.2 Create `inlinehelpprovider.py` with InlineHelpProvider class
    - Accept DocRegistry at construction
    - Implement get_help, get_command_help, get_class_help, search_help methods
    - Implement entry_count property, __repr__ and __str__ methods
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8_

  - [ ]* 16.3 Write unit tests for DocGenerator and InlineHelpProvider
    - Create `test_docgenerator.py` testing module introspection, public member extraction, private member skipping
    - Create `test_inlinehelpprovider.py` testing get_help, get_command_help, get_class_help, search_help
    - Mock modules and ReplCommand using testbase.mocking.Mock
    - _Requirements: 12.1–12.9, 14.1–14.8_

- [ ] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Implement type checking system
  - [ ] 18.1 Create `typecheckconfiguration.py` with TypeCheckConfiguration class
    - Immutable object with enabled, module_paths, raise_on_mismatch properties
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_

  - [ ] 18.2 Create `typeannotationvalidator.py` with TypeAnnotationValidator class
    - Accept list of module paths, validate public classes/methods/functions for type hints
    - Check parameter type hints and return type hints on all public methods
    - Check __init__ parameter type hints; skip private members except __init__, __repr__, __str__
    - Track warnings list and module_count
    - Log at INFO level under `automojo.agentkit.devex.types`
    - Implement __repr__ and __str__ methods
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10, 16.11_

  - [ ] 18.3 Create `runtimetypechecker.py` with RuntimeTypeChecker class
    - Accept TypeCheckConfiguration at construction
    - Implement check_call validating argument types against parameter type hints
    - Implement check_return validating return value against return type hint
    - Support generic type hints: Optional, List, Dict, Tuple, Union, Type
    - Implement checked decorator wrapping functions for automatic type validation
    - Skip all validation when configuration has runtime checking disabled
    - Raise TypeCheckError or log warning based on raise_on_mismatch setting
    - Log at WARNING level under `automojo.agentkit.devex.types`
    - Implement enabled property, __repr__ and __str__ methods
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 17.10_

  - [ ]* 18.4 Write unit tests for type checking system
    - Create `test_typecheckconfiguration.py` testing construction, properties, serialization
    - Create `test_typeannotationvalidator.py` testing detection of missing parameter and return type hints, private member skipping
    - Create `test_runtimetypechecker.py` testing check_call, check_return, checked decorator, disabled mode pass-through, generic type validation
    - _Requirements: 16.1–16.11, 17.1–17.10, 18.1–18.9_

- [ ] 19. Implement API surface management
  - [ ] 19.1 Create `apisurface.py` with ApiSurface class
    - Accept module_path, introspect module for public classes, functions, constants
    - Expose module_path, public_classes, public_functions, all_exports properties
    - Implement get_class and get_function lookup methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9_

  - [ ] 19.2 Create `apisurfacereport.py` with ApiSurfaceReport class
    - Immutable object with module_path, warnings, errors, compliance_score properties
    - Implement is_compliant property returning True when errors list is empty
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7, 21.8, 21.9, 21.10_

  - [ ] 19.3 Create `apisurfacevalidator.py` with ApiSurfaceValidator class
    - Accept list of module paths, validate each module returning ApiSurfaceReport per module
    - Check for missing __all__, undocumented public classes and methods, missing type hints, inconsistent parameter names
    - Log at INFO level under `automojo.agentkit.devex.api`
    - Implement module_count property, __repr__ and __str__ methods
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6, 20.7, 20.8, 20.9, 20.10_

  - [ ]* 19.4 Write unit tests for API surface management
    - Create `test_apisurface.py` testing module introspection, __all__ detection, get_class, get_function
    - Create `test_apisurfacereport.py` testing construction, properties, is_compliant, serialization
    - Create `test_apisurfacevalidator.py` testing missing __all__ warning, undocumented class warning, missing type hint warning, inconsistent parameter name warning
    - _Requirements: 19.1–19.9, 20.1–20.10, 21.1–21.10_

- [ ] 20. Implement DevExConfiguration
  - [ ] 20.1 Create `devexconfiguration.py` with DevExConfiguration class
    - Contains TypeCheckConfiguration, default_formatter name, documentation_output_dir, template_overrides dict, debug_mode flag
    - Implement as_dict, to_json, from_dict, from_json serialization methods with nested TypeCheckConfiguration
    - Implement __repr__ and __str__ methods
    - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7, 22.8, 22.9_

  - [ ]* 20.2 Write unit tests for DevExConfiguration
    - Create `test_devexconfiguration.py` testing construction, properties, nested TypeCheckConfiguration serialization, defaults
    - _Requirements: 22.1–22.9_

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Wire extension point integration
  - [ ] 22.1 Wire extension point loading across all registries and coordination classes
    - Ensure ScaffoldCli registers ExtensionPoint for ScaffoldCommand plugins and loads at init
    - Ensure ScaffoldTemplateRegistry registers ExtensionPoint for ScaffoldTemplate plugins and loads at init
    - Ensure AgentRepl registers ExtensionPoint for ReplCommand plugins and loads at init
    - Ensure ExampleRegistry registers ExtensionPoint for ExampleCode plugins and loads at init
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8_

  - [ ]* 22.2 Write unit tests for extension point integration
    - Test that each registry and coordination class calls load_extensions during initialization
    - Mock automojo-extension using testbase.mocking.Mock
    - _Requirements: 23.1–23.8_

- [ ] 23. Wire structured logging across all components
  - [ ] 23.1 Verify structured logging integration across all components
    - Ensure ScaffoldCli logs under `automojo.agentkit.devex.cli` at INFO level for operations
    - Ensure AgentRepl logs under `automojo.agentkit.devex.repl` at DEBUG level for commands
    - Ensure DocGenerator logs under `automojo.agentkit.devex.docs` at INFO level for generation
    - Ensure TypeAnnotationValidator and RuntimeTypeChecker log under `automojo.agentkit.devex.types`
    - Ensure ApiSurfaceValidator logs under `automojo.agentkit.devex.api` at INFO level for validation
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7, 25.8, 25.9, 25.10_

  - [ ]* 23.2 Write unit tests for structured logging
    - Verify correct logger names and log levels across all components
    - _Requirements: 25.1–25.10_

- [ ] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- All source files use lowercase filenames with no underscores per project conventions
- Tests use the testbase framework with test_ prefixed functions
- External package integrations (automojo-arcli, automojo-extension, automojo-this-app, automojo-credentials) are mocked in tests using testbase.mocking.Mock
