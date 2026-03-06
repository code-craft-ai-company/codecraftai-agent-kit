# Implementation Plan: Security & Access Control

## Overview

Implement the Security & Access Control feature for the `automojo-agent-kit` SDK. The implementation follows a bottom-up approach: security error types first, then credential data models, access control data models, sanitization data models, audit data models, sandbox data models, then the concrete implementations (sanitizers, filters, stores, enforcer), then the coordination layers (SanitizationPipeline, AuditLogger, SandboxExecutor, SecurityConfiguration, SecurityPipeline), and finally Agent integration. All source files go under `source/packages/automojo/agentkit/` with lowercase filenames. Tests go under `source/testroots/automojo/tests/singlehost/agentkit/`.

## Tasks

- [ ] 1. Implement security error types
  - [ ] 1.1 Create `securityerrors.py` with AccessDeniedError, SanitizationError, SandboxViolationError, and AuditStoreError
    - AccessDeniedError inherits from AgentKitError with principal, resource, action, decision properties and __repr__
    - SanitizationError inherits from AgentKitError with component_name, rule_name properties and __repr__
    - SandboxViolationError inherits from AgentKitError with tool_name, violation, cause properties and __repr__
    - AuditStoreError inherits from AgentKitError with store_name, operation, cause properties and __repr__
    - _Requirements: 26.1–26.12_

  - [ ]* 1.2 Write unit tests for security error types
    - Create `test_securityerrors.py` testing construction, properties, __repr__, and message content for all four error classes
    - _Requirements: 26.1–26.12_

- [ ] 2. Implement credential data models
  - [ ] 2.1 Create `credentialentry.py` with CredentialEntry class
    - Immutable object with name, credential_type, created_at, expires_at, metadata properties
    - Validate credential_type against VALID_TYPES, raise SemanticError for invalid types
    - Implement is_expired method with optional reference timestamp defaulting to UTC now
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - Secret values must never be included in any output
    - _Requirements: 2.1–2.12_

  - [ ]* 2.2 Write unit tests for CredentialEntry
    - Create `test_credentialentry.py` testing construction, read-only properties, is_expired, serialization round-trip, invalid type SemanticError, __repr__, __str__
    - _Requirements: 2.1–2.12_

  - [ ] 2.3 Create `credentialrotationpolicy.py` with CredentialRotationPolicy class
    - Immutable object with rotation_interval, automatic_rotation, rotation_callback properties
    - Implement as_dict and to_json excluding the rotation callback
    - Implement from_dict with automatic_rotation defaulting to False
    - Implement __repr__ and __str__ methods
    - _Requirements: 3.1–3.8_

  - [ ]* 2.4 Write unit tests for CredentialRotationPolicy
    - Create `test_credentialrotationpolicy.py` testing construction, properties, serialization excluding callback, from_dict defaults, __repr__, __str__
    - _Requirements: 3.1–3.8_

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement access control data models
  - [ ] 4.1 Create `accesspolicy.py` with AccessPolicy class
    - Immutable object with name, principal_pattern, resource_pattern, actions, effect properties
    - Validate effect against VALID_EFFECTS, raise SemanticError for invalid effect
    - Validate actions list is non-empty, raise SemanticError for empty actions
    - Implement matches method using fnmatch for principal and resource pattern matching
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 4.1–4.13_

  - [ ]* 4.2 Write unit tests for AccessPolicy
    - Create `test_accesspolicy.py` testing construction, properties, matches with wildcards, invalid effect, empty actions, serialization round-trip, __repr__, __str__
    - _Requirements: 4.1–4.13_

  - [ ] 4.3 Create `accessdecision.py` with AccessDecision class
    - Immutable object with decision, policy_name, principal, resource, action, timestamp properties
    - Implement is_allowed read-only property
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 8.1–8.10_

  - [ ]* 4.4 Write unit tests for AccessDecision
    - Create `test_accessdecision.py` testing construction, properties, is_allowed, serialization round-trip, __repr__, __str__
    - _Requirements: 8.1–8.10_

  - [ ] 4.5 Create `role.py` with Role class
    - Immutable object with name, description, policies (list of AccessPolicy) properties
    - Implement as_dict, to_json, from_dict, from_json serialization methods including embedded policies
    - Implement __repr__ and __str__ methods
    - _Requirements: 6.1–6.7, 6.15–6.16_

  - [ ]* 4.6 Write unit tests for Role
    - Create `test_role.py` testing construction, properties, serialization with embedded policies, __repr__, __str__
    - _Requirements: 6.1–6.7, 6.15–6.16_

  - [ ] 4.7 Create `roleassignment.py` with RoleAssignment class
    - Immutable object with agent_identifier, role_name, expires_at properties
    - Implement is_expired method with optional reference timestamp defaulting to UTC now
    - Implement as_dict, to_json, from_dict serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 6.8–6.14, 6.17–6.18_

  - [ ]* 4.8 Write unit tests for RoleAssignment
    - Create `test_roleassignment.py` testing construction, properties, is_expired, serialization round-trip, __repr__, __str__
    - _Requirements: 6.8–6.14, 6.17–6.18_

- [ ] 5. Implement access policy registry and access enforcer
  - [ ] 5.1 Create `accesspolicyregistry.py` with AccessPolicyRegistry class
    - Registry with register, deregister, lookup, list_all, has_policy, count methods
    - Raise SemanticError on duplicate policy name registration
    - Implement load_from_json_file and load_from_yaml_file with AppContext path resolution
    - Implement __repr__ and __str__ methods
    - _Requirements: 5.1–5.12_

  - [ ]* 5.2 Write unit tests for AccessPolicyRegistry
    - Create `test_accesspolicyregistry.py` testing register, deregister, lookup, duplicate name error, list_all, has_policy, count, JSON/YAML file loading, __repr__, __str__
    - _Requirements: 5.1–5.12_

  - [ ] 5.3 Create `accessenforcer.py` with AccessEnforcer class
    - Accept AccessPolicyRegistry at construction
    - Implement register_role, assign_role, revoke_role methods
    - Implement evaluate method with deny-first semantics: check deny policies first, then allow policies from registry, then allow policies from non-expired role assignments, default deny
    - Implement list_roles and list_role_assignments methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 7.1–7.13_

  - [ ]* 5.4 Write unit tests for AccessEnforcer
    - Create `test_accessenforcer.py` testing deny-first evaluation, allow policies, role-based evaluation, expired role skipping, default deny, list_roles, list_role_assignments, __repr__, __str__
    - _Requirements: 7.1–7.13_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement sanitization data models
  - [ ] 7.1 Create `sanitizationrule.py` with SanitizationRule class
    - Immutable object with name, rule_type, pattern, description properties
    - Validate rule_type against VALID_TYPES, raise SemanticError for invalid types
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 11.1–11.10_

  - [ ]* 7.2 Write unit tests for SanitizationRule
    - Create `test_sanitizationrule.py` testing construction, properties, invalid type error, serialization round-trip, __repr__, __str__
    - _Requirements: 11.1–11.10_

  - [ ] 7.3 Create `sanitizationresult.py` with SanitizationResult class
    - Immutable object with original_value, sanitized_value, modified, applied_rules properties
    - Implement as_dict method
    - Implement __repr__ and __str__ methods
    - _Requirements: 13.1–13.5_

  - [ ]* 7.4 Write unit tests for SanitizationResult
    - Create `test_sanitizationresult.py` testing construction, properties, as_dict, __repr__, __str__
    - _Requirements: 13.1–13.5_

- [ ] 8. Implement input sanitizers
  - [ ] 8.1 Create `inputsanitizer.py` with InputSanitizer abstract base class
    - Abstract base class with sanitizer_name property and abstract sanitize method
    - Implement __repr__ and __str__ methods
    - _Requirements: 9.1–9.3, 9.10–9.11_

  - [ ] 8.2 Create `regexdenysanitizer.py` with RegexDenySanitizer class
    - Extends InputSanitizer, removes content matching deny pattern
    - Include rule name in SanitizationResult applied rules when content is removed
    - _Requirements: 9.4, 9.8_

  - [ ] 8.3 Create `regexallowsanitizer.py` with RegexAllowSanitizer class
    - Extends InputSanitizer, raises SanitizationError when input does not match allow pattern
    - _Requirements: 9.5, 9.9_

  - [ ] 8.4 Create `lengthlimitsanitizer.py` with LengthLimitSanitizer class
    - Extends InputSanitizer, truncates input exceeding max_length
    - _Requirements: 9.6_

  - [ ] 8.5 Create `encodingnormalizesanitizer.py` with EncodingNormalizeSanitizer class
    - Extends InputSanitizer, normalizes to specified Unicode form (NFC, NFD, NFKC, NFKD)
    - Raise SemanticError for invalid normalization form
    - _Requirements: 9.7_

  - [ ]* 8.6 Write unit tests for input sanitizers
    - Create `test_inputsanitizer.py` testing abstract method enforcement
    - Create `test_regexdenysanitizer.py` testing deny pattern removal and applied rules
    - Create `test_regexallowsanitizer.py` testing allow pattern validation and SanitizationError
    - Create `test_lengthlimitsanitizer.py` testing truncation behavior
    - Create `test_encodingnormalizesanitizer.py` testing normalization and invalid form error
    - _Requirements: 9.1–9.11_

- [ ] 9. Implement output filters
  - [ ] 9.1 Create `outputfilter.py` with OutputFilter abstract base class
    - Abstract base class with filter_name property and abstract filter method
    - Implement __repr__ and __str__ methods
    - _Requirements: 10.1–10.3, 10.9–10.10_

  - [ ] 9.2 Create `credentialredactfilter.py` with CredentialRedactFilter class
    - Extends OutputFilter, detects and replaces credential-like patterns with configurable placeholder (default "[REDACTED]")
    - Include rule name in SanitizationResult applied rules when content is redacted
    - _Requirements: 10.4, 10.7_

  - [ ] 9.3 Create `piimaskfilter.py` with PiiMaskFilter class
    - Extends OutputFilter, detects and masks PII patterns (email, phone) with configurable placeholder (default "[MASKED]")
    - Include rule name in SanitizationResult applied rules when content is masked
    - _Requirements: 10.5, 10.8_

  - [ ] 9.4 Create `regexredactfilter.py` with RegexRedactFilter class
    - Extends OutputFilter, redacts content matching regex pattern with configurable replacement
    - _Requirements: 10.6_

  - [ ]* 9.5 Write unit tests for output filters
    - Create `test_outputfilter.py` testing abstract method enforcement
    - Create `test_credentialredactfilter.py` testing credential pattern detection, redaction, custom placeholder
    - Create `test_piimaskfilter.py` testing PII pattern detection, masking, custom placeholder
    - Create `test_regexredactfilter.py` testing regex redaction with custom replacement
    - _Requirements: 10.1–10.10_

- [ ] 10. Implement sanitization pipeline
  - [ ] 10.1 Create `sanitizationpipeline.py` with SanitizationPipeline class
    - Maintain ordered lists of InputSanitizer and OutputFilter instances
    - Implement add_input_sanitizer and add_output_filter methods
    - Implement sanitize_input applying all sanitizers in order, combining applied rules
    - Implement filter_output applying all filters in order, combining applied rules
    - Propagate SanitizationError without invoking subsequent sanitizers
    - Expose input_sanitizer_count and output_filter_count properties
    - Implement __repr__ and __str__ methods
    - _Requirements: 12.1–12.10_

  - [ ]* 10.2 Write unit tests for SanitizationPipeline
    - Create `test_sanitizationpipeline.py` testing add/remove sanitizers and filters, ordered execution, combined applied rules, SanitizationError propagation, counts, __repr__, __str__
    - _Requirements: 12.1–12.10_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Implement audit data models
  - [ ] 12.1 Create `auditentry.py` with AuditEntry class
    - Immutable object with identifier, timestamp, agent_identifier, correlation_id, action_type, principal, resource, outcome, detail, integrity_hash properties
    - Validate outcome against VALID_OUTCOMES, raise SemanticError for invalid outcome
    - Compute integrity hash using SHA-256 over all fields (excluding hash itself) at construction
    - Implement verify_integrity method that recomputes and compares hash
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 15.1–15.11_

  - [ ]* 12.2 Write unit tests for AuditEntry
    - Create `test_auditentry.py` testing construction, properties, integrity hash computation, verify_integrity, invalid outcome error, serialization round-trip, __repr__, __str__
    - _Requirements: 15.1–15.11_

  - [ ] 12.3 Create `auditquery.py` with AuditQuery and AuditQueryResult classes
    - AuditQuery with optional filters: agent_identifier, action_type, principal, resource, outcome, start_time, end_time, max_results
    - AuditQuery implements as_dict, __repr__, __str__
    - AuditQueryResult with entries list and total_count, implements as_dict, __repr__, __str__
    - _Requirements: 17.1–17.15_

  - [ ]* 12.4 Write unit tests for AuditQuery and AuditQueryResult
    - Create `test_auditquery.py` testing construction, filter properties, as_dict, __repr__, __str__ for both classes
    - _Requirements: 17.1–17.15_

- [ ] 13. Implement audit stores
  - [ ] 13.1 Create `auditstore.py` with AuditStore abstract base class
    - Abstract base class with store_name property and abstract append, retrieve, search, count methods
    - Enforce append-only semantics (no update or delete methods)
    - Implement __repr__ and __str__ methods
    - _Requirements: 16.1–16.4, 16.10–16.11_

  - [ ] 13.2 Create `inmemoryauditstore.py` with InMemoryAuditStore class
    - Extends AuditStore, stores entries in a list
    - Implement append, retrieve by identifier, search with AuditQuery filtering, count
    - _Requirements: 16.5_

  - [ ]* 13.3 Write unit tests for InMemoryAuditStore
    - Create `test_inmemoryauditstore.py` testing append, retrieve, search with various filters, count, append-only semantics
    - _Requirements: 16.5_

  - [ ] 13.4 Create `fileauditstore.py` with FileAuditStore class
    - Extends AuditStore, persists entries as JSON lines to file
    - Resolve file path relative to AppContext directory
    - Raise AuditStoreError on I/O failures with file path and error detail
    - Implement append, retrieve, search, count
    - _Requirements: 16.6–16.9_

  - [ ]* 13.5 Write unit tests for FileAuditStore
    - Create `test_fileauditstore.py` testing append/retrieve round-trip, search, count, I/O error handling with AuditStoreError, path resolution
    - _Requirements: 16.6–16.9_

- [ ] 14. Implement audit logger
  - [ ] 14.1 Create `auditlogger.py` with AuditLogger class
    - Accept agent_identifier and AuditStore at construction
    - Implement log_action creating AuditEntry with unique ID, UTC timestamp, SHA-256 integrity hash
    - Implement query method delegating to AuditStore search
    - Expose entry_count property
    - Integrate with StructuredLogger at INFO level for each audit entry
    - Implement __repr__ and __str__ methods
    - _Requirements: 14.1–14.8_

  - [ ]* 14.2 Write unit tests for AuditLogger
    - Create `test_auditlogger.py` testing log_action, query, entry_count, structured logging integration (using Mock), __repr__, __str__
    - _Requirements: 14.1–14.8_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement sandbox data models and executor
  - [ ] 16.1 Create `sandboxpolicy.py` with SandboxPolicy class
    - Immutable object with allowed_paths, allowed_hosts, max_execution_time, max_memory_bytes, allowed_env_vars properties
    - Implement is_path_allowed using os.path normalization
    - Implement is_host_allowed and is_env_allowed methods
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 19.1–19.12_

  - [ ]* 16.2 Write unit tests for SandboxPolicy
    - Create `test_sandboxpolicy.py` testing construction, properties, is_path_allowed with normalization, is_host_allowed, is_env_allowed, serialization round-trip, __repr__, __str__
    - _Requirements: 19.1–19.12_

  - [ ] 16.3 Create `sandboxviolation.py` with SandboxViolation class
    - Immutable object with violation_type, resource, description properties
    - Validate violation_type against VALID_TYPES, raise SemanticError for invalid types
    - Implement as_dict, to_json, from_dict, from_json serialization methods
    - Implement __repr__ and __str__ methods
    - _Requirements: 20.1–20.10_

  - [ ]* 16.4 Write unit tests for SandboxViolation
    - Create `test_sandboxviolation.py` testing construction, properties, invalid type error, serialization round-trip, __repr__, __str__
    - _Requirements: 20.1–20.10_

  - [ ] 16.5 Create `sandboxexecutor.py` with SandboxExecutor class
    - Accept SandboxPolicy at construction
    - Wrap ToolExecutor, validate resource access against SandboxPolicy before execution
    - Enforce file system, network, execution time, memory, and environment variable restrictions
    - Create SandboxViolation and raise SandboxViolationError on violations
    - Return ToolResult on successful execution
    - Implement __repr__ and __str__ methods
    - _Requirements: 18.1–18.12_

  - [ ]* 16.6 Write unit tests for SandboxExecutor
    - Create `test_sandboxexecutor.py` testing policy enforcement for each restriction type, violation creation, SandboxViolationError raising, successful execution pass-through (using Mock for ToolExecutor), __repr__, __str__
    - _Requirements: 18.1–18.12_

- [ ] 17. Implement credential manager
  - [ ] 17.1 Create `credentialmanager.py` with CredentialManager class
    - Accept agent_identifier and optional CredentialRotationPolicy at construction
    - Implement get_credential resolving through automojo-credentials on first access, caching result
    - Implement get_credential_value returning secret value string
    - Raise ConfigurationError for unresolvable credential names
    - Implement invalidate and invalidate_all for cache management
    - Implement automatic rotation when policy configured and credential age exceeds interval
    - Expose cached_count property and list_credential_names method
    - Never expose secret values in __repr__, __str__, or any serialization
    - Implement __repr__ and __str__ methods
    - _Requirements: 1.1–1.12_

  - [ ]* 17.2 Write unit tests for CredentialManager
    - Create `test_credentialmanager.py` testing get_credential caching, get_credential_value, invalidate, invalidate_all, rotation, unresolvable credential error, cached_count, list_credential_names, secret value exclusion from repr/str (using Mock for automojo-credentials)
    - _Requirements: 1.1–1.12_

- [ ] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Implement security configuration
  - [ ] 19.1 Create `securityconfiguration.py` with SecurityConfiguration class
    - Immutable object with access_control_enabled, audit_logging_enabled, input_sanitization_enabled, output_filtering_enabled, sandbox_enabled, default_sandbox_policy, credential_rotation_settings, security_plugin_settings properties
    - Implement from_dict, from_json, from_yaml class methods with field validation
    - Implement from_json_file and from_yaml_file with AppContext path resolution
    - Support CredentialReference resolution through automojo-credentials
    - Raise ConfigurationError for missing required fields or unresolvable credentials
    - Implement as_dict, to_json, to_yaml excluding resolved credential values
    - Implement __repr__ and __str__ methods
    - _Requirements: 21.1–21.18_

  - [ ]* 19.2 Write unit tests for SecurityConfiguration
    - Create `test_securityconfiguration.py` testing from_dict, from_json, from_yaml, file loading, field validation, credential resolution, serialization round-trip, defaults, __repr__, __str__ (using Mock for automojo-credentials and automojo-this-app)
    - _Requirements: 21.1–21.18_

- [ ] 20. Implement security pipeline
  - [ ] 20.1 Create `securitypipeline.py` with SecurityPipeline class
    - Accept SecurityConfiguration and agent_identifier at construction
    - Construct and own CredentialManager, AccessEnforcer, AccessPolicyRegistry, SanitizationPipeline, AuditLogger, SandboxExecutor based on configuration
    - Expose read-only properties for all owned components
    - SandboxExecutor property returns None when sandbox not enabled
    - Pass-through behavior for disabled subsystems (AccessEnforcer allows all, AuditLogger no-op, SanitizationPipeline pass-through)
    - Implement shutdown method flushing AuditLogger and releasing resources
    - Implement __repr__ and __str__ methods
    - _Requirements: 22.1–22.15_

  - [ ]* 20.2 Write unit tests for SecurityPipeline
    - Create `test_securitypipeline.py` testing component construction, property access, disabled subsystem pass-through behavior, shutdown, __repr__, __str__ (using Mock for external dependencies)
    - _Requirements: 22.1–22.15_

- [ ] 21. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 22. Implement Agent security integration and metrics
  - [ ] 22.1 Integrate SecurityPipeline into Agent base class
    - Add security read-only property returning SecurityPipeline
    - Add credential_manager read-only property returning CredentialManager from SecurityPipeline
    - Construct SecurityPipeline on INITIALIZED state transition from SecurityConfiguration
    - Default to all-disabled SecurityConfiguration when not provided
    - Enforce access control on tool execution via AccessEnforcer, raise AccessDeniedError on deny
    - Sanitize tool input and filter tool output through SanitizationPipeline
    - Route tool execution through SandboxExecutor when sandbox enabled
    - Record all agent actions through AuditLogger (tool execution, LLM request, memory operation, message send/receive, workflow step)
    - Flush and shut down SecurityPipeline on STOPPED state transition
    - _Requirements: 23.1–23.12_

  - [ ]* 22.2 Write unit tests for Agent security integration
    - Test SecurityPipeline construction on initialization, access control enforcement, input sanitization, output filtering, sandbox routing, audit logging, shutdown, default configuration (using Mock for Agent, ToolExecutor, and external dependencies)
    - _Requirements: 23.1–23.12_

  - [ ] 22.3 Register built-in security metrics in MetricsRegistry
    - Register six COUNTER MetricDefinition instances: access.allowed, access.denied, sanitization.applied, sandbox.violations, credential.rotations, audit.entries
    - Increment appropriate counters with labels on access decisions, sanitization, sandbox violations, credential rotations, and audit entries
    - _Requirements: 24.1–24.6_

  - [ ]* 22.4 Write unit tests for security metrics registration and incrementing
    - Test metric registration on initialization, counter incrementing with correct labels for each event type (using Mock for MetricsRegistry and MetricsCollector)
    - _Requirements: 24.1–24.6_

- [ ] 23. Implement security plugin integration
  - [ ] 23.1 Define security ExtensionPoints and plugin discovery
    - Define ExtensionPoints: automojo.agentkit.input_sanitizers, automojo.agentkit.output_filters, automojo.agentkit.audit_stores
    - Query ExtensionPoints during Agent initialization and register discovered plugins with SecurityPipeline
    - Log plugin load failures at WARNING level and continue
    - Log conflicting component names at WARNING level and skip
    - _Requirements: 25.1–25.6_

  - [ ]* 23.2 Write unit tests for security plugin integration
    - Test plugin discovery and registration, failed plugin load handling, conflicting name handling (using Mock for automojo-extension)
    - _Requirements: 25.1–25.6_

- [ ] 24. Implement structured logging for security operations
  - [ ] 24.1 Add structured logging throughout security components
    - Log access decisions at INFO (allow) and WARNING (deny) levels
    - Log sanitization rule application at DEBUG level
    - Log sanitization errors at WARNING level
    - Log sandbox violations at WARNING level
    - Log credential rotations at INFO level (no secret values)
    - Log audit entries at DEBUG level
    - All logging under automojo.agentkit.security logger hierarchy
    - _Requirements: 27.1–27.8_

  - [ ]* 24.2 Write unit tests for structured logging
    - Test log output at correct levels for each security event type (using Mock or log capture)
    - _Requirements: 27.1–27.8_

- [ ] 25. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- All source files use lowercase filenames with no underscores under `source/packages/automojo/agentkit/`
- All test files mirror the source hierarchy under `source/testroots/automojo/tests/singlehost/agentkit/`
- External dependencies (automojo-credentials, automojo-extension, automojo-this-app) are mocked in tests using `testbase.mocking.Mock`
