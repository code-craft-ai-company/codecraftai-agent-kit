# Requirements Document — Security & Access Control

## Introduction

The Security & Access Control feature extends the `automojo-agent-kit` SDK with a comprehensive system for securing agent operations, managing credentials, controlling access to tools and resources, sanitizing inputs and outputs, auditing agent actions, and executing tools in sandboxed environments. It defines a credential manager for secure secret injection and rotation, a role-based access control (RBAC) system with policies governing tool and resource access, an input sanitization and output filtering pipeline for preventing injection attacks and data leakage, an audit logger that records all agent actions with tamper-evident entries, and a sandboxed tool execution environment that isolates tool execution from the host system. The system integrates with the Agent base class so agents enforce security policies throughout their lifecycle, with the Tool & Capability System so tool execution is governed by access policies and sandboxing, with the LLM Integration system so LLM requests are subject to input sanitization and output filtering, with the Memory & Context Management system so memory operations are audited and access-controlled, with the Communication & Messaging system so message exchanges are audited and credential-secured, with the Workflow & Orchestration system so workflow steps are subject to access control and audit logging, with the Observability & Debugging system so security events are traced and metered, with `automojo-extension` so security plugins can be discovered and loaded, with `automojo-credentials` for underlying credential storage and retrieval, with `automojo-dataprofiles` for data profile management, and with `automojo-this-app` for settings and environment configuration.

## Glossary

- **CredentialManager**: A component that manages the lifecycle of credentials for an Agent, providing secure retrieval, caching, rotation, and injection of secrets into tools, transports, LLM providers, and memory backends. The CredentialManager delegates storage and retrieval to `automojo-credentials` and adds lifecycle management on top.
- **CredentialEntry**: An immutable object representing a resolved credential, containing a credential name, a credential type string (one of "api_key", "password", "token", "certificate", "secret"), a creation timestamp, an optional expiration timestamp, and metadata. The CredentialEntry does not expose the secret value directly; the value is accessed only through the CredentialManager.
- **CredentialRotationPolicy**: A configuration object defining how and when credentials are rotated, including the rotation interval in seconds, a rotation callback for obtaining new credential values, and whether automatic rotation is enabled.
- **AccessPolicy**: An immutable object representing a single access control rule, containing a policy name, a principal pattern string (agent identifier or role), a resource pattern string (tool name, memory store name, or resource identifier), a list of permitted action strings (e.g., "execute", "read", "write", "delete"), and an effect string (one of "allow", "deny").
- **AccessPolicyRegistry**: A registry that tracks all AccessPolicy instances for an Agent, providing lookup by principal, resource, and action, and supporting policy evaluation for access decisions.
- **AccessDecision**: An immutable object representing the result of an access control evaluation, containing the decision (allow or deny), the matching AccessPolicy name, the principal, the resource, the action, and a timestamp.
- **AccessEnforcer**: A component that evaluates access requests against the AccessPolicyRegistry and returns an AccessDecision. The AccessEnforcer applies deny-first evaluation, where deny policies take precedence over allow policies.
- **Role**: An immutable object representing a named role with a set of permitted actions on resource patterns. Roles are assigned to agents and used by the AccessEnforcer for role-based access control.
- **RoleAssignment**: An immutable object representing the assignment of a Role to an agent identifier, containing the agent identifier, the role name, and an optional expiration timestamp.
- **InputSanitizer**: An abstract base class for sanitizing input data before it is passed to tools, LLM providers, or other components. Concrete implementations handle specific sanitization strategies (pattern-based filtering, allowlist validation, encoding normalization).
- **OutputFilter**: An abstract base class for filtering output data before it is returned from tools, LLM providers, or other components. Concrete implementations handle specific filtering strategies (credential redaction, PII masking, content policy enforcement).
- **SanitizationRule**: An immutable object representing a single sanitization or filtering rule, containing a rule name, a rule type string (one of "regex_deny", "regex_allow", "encoding_normalize", "length_limit", "credential_redact", "pii_mask"), a pattern or configuration string, and a description.
- **SanitizationPipeline**: A component that chains multiple InputSanitizer and OutputFilter instances into an ordered processing pipeline, applying each sanitizer or filter in sequence to input or output data.
- **SanitizationResult**: An immutable object representing the outcome of a sanitization or filtering operation, containing the original value, the sanitized value, a boolean indicating whether the value was modified, and a list of applied rule names.
- **AuditLogger**: A component that records all agent actions as AuditEntry objects in an ordered, append-only log. The AuditLogger integrates with the Observability & Debugging system for structured logging and tracing.
- **AuditEntry**: An immutable object representing a single audited action, containing a unique identifier, a timestamp, an agent identifier, a correlation identifier, an action type string, a principal string, a resource string, an outcome string (one of "success", "failure", "denied"), a detail dictionary, and an integrity hash for tamper detection.
- **AuditStore**: An abstract base class for persisting AuditEntry objects. Concrete implementations handle specific storage backends (in-memory, file-based). The AuditStore provides append-only semantics.
- **AuditQuery**: An immutable object representing a search request against an AuditStore, containing optional filter criteria (agent identifier, action type, principal, resource, outcome, time range).
- **AuditQueryResult**: An immutable object encapsulating the result of an AuditQuery, containing the list of matching AuditEntry objects and the total count of matches.
- **SandboxExecutor**: A component that executes tools in an isolated environment with restricted access to system resources. The SandboxExecutor wraps the ToolExecutor and applies resource limits, file system restrictions, and network restrictions.
- **SandboxPolicy**: An immutable configuration object defining the restrictions applied by the SandboxExecutor, including allowed file system paths, allowed network hosts, maximum execution time in seconds, maximum memory usage in bytes, and allowed environment variables.
- **SandboxViolation**: An immutable object representing a security violation detected during sandboxed execution, containing the violation type string (one of "file_access", "network_access", "timeout", "memory_limit", "environment_access"), the violating resource identifier, and a description.
- **SecurityConfiguration**: A configuration object that defines the security settings for an Agent, including access control enablement, audit logging enablement, input sanitization enablement, output filtering enablement, sandbox enablement, default SandboxPolicy, credential rotation settings, and security plugin settings.
- **SecurityPipeline**: A component that coordinates the CredentialManager, AccessEnforcer, SanitizationPipeline, AuditLogger, and SandboxExecutor for an Agent, routing security operations through the configured components.
- **SecurityPlugin**: A security component implementation (InputSanitizer, OutputFilter, or AuditStore) discovered and loaded through the `automojo-extension` ExtensionPoint mechanism, allowing external packages to contribute security components.
- **Agent**: The base agent class defined in the Core Agent Framework that owns a SecurityPipeline and enforces security policies throughout its lifecycle.
- **ToolExecutor**: The tool executor defined in the Tool & Capability System, wrapped by the SandboxExecutor for isolated tool execution.
- **ToolResult**: The tool result object defined in the Tool & Capability System, returned by tool execution.
- **ToolDescriptor**: The tool descriptor defined in the Tool & Capability System, used for access control resource identification.
- **CorrelationContext**: The correlation context defined in the Observability & Debugging feature, used for correlating audit entries with trace spans.
- **StructuredLogger**: The structured logger defined in the Observability & Debugging feature, used by the AuditLogger for structured log output.
- **TraceSpan**: The trace span defined in the Observability & Debugging feature, used for tracing security operations.
- **MetricsCollector**: The metrics collector defined in the Observability & Debugging feature, used for recording security metrics.
- **ExtensionPoint**: An integration surface provided by `automojo-extension` that allows external plugins to register security component implementations with an Agent.
- **CredentialReference**: A named reference resolved through `automojo-credentials` that provides secure access to secrets required by the security system.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **AccessDeniedError**: An exception raised when an access control evaluation results in a deny decision, inherited from AgentKitError.
- **SanitizationError**: An exception raised when an input sanitization or output filtering operation detects a policy violation that cannot be resolved by sanitization, inherited from AgentKitError.
- **SandboxViolationError**: An exception raised when a sandboxed tool execution violates a SandboxPolicy restriction, inherited from AgentKitError.
- **AuditStoreError**: An exception raised when an AuditStore operation fails due to a backend error, inherited from AgentKitError.

## Requirements

### Requirement 1: Credential Manager

**User Story:** As a developer, I want a credential manager that securely retrieves, caches, and injects credentials into agent components, so that secrets are managed centrally with lifecycle support and are never exposed in logs or serialized output.

#### Acceptance Criteria

1. THE CredentialManager SHALL accept an agent identifier string and an optional CredentialRotationPolicy at construction time.
2. THE CredentialManager SHALL provide a get_credential method that accepts a credential name string and returns a CredentialEntry, resolving the credential through `automojo-credentials` on first access and caching the resolved entry for subsequent requests.
3. THE CredentialManager SHALL provide a get_credential_value method that accepts a credential name string and returns the secret value as a string, resolving through `automojo-credentials`.
4. IF a credential name cannot be resolved through `automojo-credentials`, THEN THE CredentialManager SHALL raise a ConfigurationError that identifies the unresolvable credential name and the agent identifier.
5. THE CredentialManager SHALL provide an invalidate method that accepts a credential name string and removes the cached CredentialEntry, forcing re-resolution on the next access.
6. THE CredentialManager SHALL provide an invalidate_all method that removes all cached CredentialEntry objects.
7. WHEN a CredentialRotationPolicy is configured with automatic rotation enabled, THE CredentialManager SHALL re-resolve credentials whose age exceeds the rotation interval, replacing the cached entry with the newly resolved entry.
8. THE CredentialManager SHALL provide a read-only property for the count of currently cached credentials.
9. THE CredentialManager SHALL provide a list_credential_names method that returns the list of cached credential name strings without exposing secret values.
10. THE CredentialManager SHALL NOT include credential secret values in the output of any serialization method, string representation, or log entry.
11. THE CredentialManager SHALL provide a __repr__ method that includes the class name, agent identifier, and cached credential count.
12. THE CredentialManager SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and cached credential count.

### Requirement 2: Credential Entry

**User Story:** As a developer, I want a structured credential metadata object that describes a credential without exposing its secret value, so that I can inspect credential information safely during debugging.

#### Acceptance Criteria

1. THE CredentialEntry SHALL contain a credential name string, a credential type string (one of "api_key", "password", "token", "certificate", "secret"), a creation timestamp, an optional expiration timestamp, and a metadata dictionary.
2. THE CredentialEntry SHALL expose all fields as read-only properties.
3. THE CredentialEntry SHALL NOT contain or expose the credential secret value.
4. THE CredentialEntry SHALL provide an is_expired method that accepts an optional reference timestamp and returns True when the expiration timestamp is set and the reference timestamp exceeds the expiration timestamp, defaulting to the current UTC time when no reference timestamp is provided.
5. WHEN a CredentialEntry is created with a credential type not in the set of valid types, THEN THE CredentialEntry SHALL raise a SemanticError identifying the invalid type and listing the valid credential types.
6. THE CredentialEntry SHALL provide an as_dict method that returns a dictionary representation of the entry fields.
7. THE CredentialEntry SHALL provide a to_json method that returns a JSON string representation of the entry fields.
8. THE CredentialEntry SHALL provide a class method from_dict that constructs a CredentialEntry from a dictionary.
9. THE CredentialEntry SHALL provide a class method from_json that deserializes a JSON string into a CredentialEntry instance.
10. FOR ALL valid CredentialEntry instances, calling to_json and then from_json SHALL produce an equivalent CredentialEntry object (round-trip property).
11. THE CredentialEntry SHALL provide a __repr__ method that includes the class name, credential name, and credential type.
12. THE CredentialEntry SHALL provide a __str__ method that returns a human-readable summary including the credential name, type, and expiration status.

### Requirement 3: Credential Rotation Policy

**User Story:** As a developer, I want to configure credential rotation policies, so that credentials are automatically refreshed at defined intervals to reduce the risk of compromised secrets.

#### Acceptance Criteria

1. THE CredentialRotationPolicy SHALL contain a rotation interval in seconds as a float, an automatic rotation enabled flag as a boolean, and an optional rotation callback callable that accepts a credential name and returns a new secret value string.
2. THE CredentialRotationPolicy SHALL expose all fields as read-only properties.
3. THE CredentialRotationPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields, excluding the rotation callback.
4. THE CredentialRotationPolicy SHALL provide a to_json method that returns a JSON string representation of the policy fields, excluding the rotation callback.
5. THE CredentialRotationPolicy SHALL provide a class method from_dict that constructs a CredentialRotationPolicy from a dictionary, with automatic rotation defaulting to False when not specified.
6. FOR ALL valid CredentialRotationPolicy instances (excluding the rotation callback), calling to_json and then from_dict on the parsed JSON SHALL produce a CredentialRotationPolicy with equivalent rotation interval and automatic rotation enabled values.
7. THE CredentialRotationPolicy SHALL provide a __repr__ method that includes the class name, rotation interval, and automatic rotation enabled status.
8. THE CredentialRotationPolicy SHALL provide a __str__ method that returns a human-readable summary including the rotation interval and automatic rotation enabled status.

### Requirement 4: Access Policy Definition

**User Story:** As a developer, I want to define access control policies with principal, resource, and action patterns, so that I can declaratively control which agents can perform which actions on which resources.

#### Acceptance Criteria

1. THE AccessPolicy SHALL contain a policy name string, a principal pattern string, a resource pattern string, a list of permitted action strings, and an effect string (one of "allow", "deny").
2. THE AccessPolicy SHALL expose all fields as read-only properties.
3. THE AccessPolicy SHALL support wildcard matching in principal and resource patterns using the "*" character to match any sequence of characters.
4. WHEN an AccessPolicy is created with an effect value not in the set of valid effects, THEN THE AccessPolicy SHALL raise a SemanticError identifying the invalid effect and listing the valid effect values.
5. WHEN an AccessPolicy is created with an empty list of permitted actions, THEN THE AccessPolicy SHALL raise a SemanticError indicating that at least one action is required.
6. THE AccessPolicy SHALL provide a matches method that accepts a principal string, a resource string, and an action string, and returns a boolean indicating whether the policy matches the provided values.
7. THE AccessPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields.
8. THE AccessPolicy SHALL provide a to_json method that returns a JSON string representation of the policy fields.
9. THE AccessPolicy SHALL provide a class method from_dict that constructs an AccessPolicy from a dictionary.
10. THE AccessPolicy SHALL provide a class method from_json that deserializes a JSON string into an AccessPolicy instance.
11. FOR ALL valid AccessPolicy instances, calling to_json and then from_json SHALL produce an equivalent AccessPolicy object (round-trip property).
12. THE AccessPolicy SHALL provide a __repr__ method that includes the class name, policy name, and effect.
13. THE AccessPolicy SHALL provide a __str__ method that returns a human-readable summary including the policy name, principal pattern, resource pattern, actions, and effect.

### Requirement 5: Access Policy Registry

**User Story:** As a developer, I want a registry that tracks access control policies, so that I can manage and evaluate policies for access decisions.

#### Acceptance Criteria

1. THE AccessPolicyRegistry SHALL support registration of an AccessPolicy instance using the policy name as the registration key.
2. IF an AccessPolicy with a duplicate name is registered, THEN THE AccessPolicyRegistry SHALL raise a SemanticError that includes the duplicate policy name.
3. THE AccessPolicyRegistry SHALL support deregistration of an AccessPolicy by name.
4. THE AccessPolicyRegistry SHALL support lookup of a registered AccessPolicy by name, returning the AccessPolicy instance or None when the name is not found.
5. THE AccessPolicyRegistry SHALL support enumeration of all registered AccessPolicy instances as a list.
6. THE AccessPolicyRegistry SHALL expose a read-only property for the count of currently registered policies.
7. THE AccessPolicyRegistry SHALL provide a has_policy method that accepts a policy name and returns a boolean indicating whether an AccessPolicy with the given name is registered.
8. THE AccessPolicyRegistry SHALL support loading AccessPolicy definitions from a JSON file path.
9. THE AccessPolicyRegistry SHALL support loading AccessPolicy definitions from a YAML file path.
10. WHEN a configuration file path is provided, THE AccessPolicyRegistry SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
11. THE AccessPolicyRegistry SHALL provide a __repr__ method that includes the class name and the count of registered policies.
12. THE AccessPolicyRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered policy names and effects.

### Requirement 6: Role-Based Access Control

**User Story:** As a developer, I want to define roles with permitted actions and assign roles to agents, so that I can manage access control through role assignments rather than individual policy rules.

#### Acceptance Criteria

1. THE Role SHALL contain a role name string, a description string, and a list of AccessPolicy objects that define the permissions granted by the role.
2. THE Role SHALL expose all fields as read-only properties.
3. THE Role SHALL provide an as_dict method that returns a dictionary representation of the role fields including the embedded policies.
4. THE Role SHALL provide a to_json method that returns a JSON string representation of the role fields.
5. THE Role SHALL provide a class method from_dict that constructs a Role from a dictionary.
6. THE Role SHALL provide a class method from_json that deserializes a JSON string into a Role instance.
7. FOR ALL valid Role instances, calling to_json and then from_json SHALL produce an equivalent Role object (round-trip property).
8. THE RoleAssignment SHALL contain an agent identifier string, a role name string, and an optional expiration timestamp.
9. THE RoleAssignment SHALL expose all fields as read-only properties.
10. THE RoleAssignment SHALL provide an is_expired method that accepts an optional reference timestamp and returns True when the expiration timestamp is set and the reference timestamp exceeds the expiration timestamp, defaulting to the current UTC time when no reference timestamp is provided.
11. THE RoleAssignment SHALL provide an as_dict method that returns a dictionary representation of the assignment fields.
12. THE RoleAssignment SHALL provide a to_json method that returns a JSON string representation of the assignment fields.
13. THE RoleAssignment SHALL provide a class method from_dict that constructs a RoleAssignment from a dictionary.
14. FOR ALL valid RoleAssignment instances, calling to_json and then from_dict on the parsed JSON SHALL produce a RoleAssignment with equivalent agent identifier, role name, and expiration timestamp values.
15. THE Role SHALL provide a __repr__ method that includes the class name, role name, and policy count.
16. THE Role SHALL provide a __str__ method that returns a human-readable summary including the role name, description, and policy count.
17. THE RoleAssignment SHALL provide a __repr__ method that includes the class name, agent identifier, and role name.
18. THE RoleAssignment SHALL provide a __str__ method that returns a human-readable summary including the agent identifier, role name, and expiration status.

### Requirement 7: Access Enforcer

**User Story:** As a developer, I want an access enforcer that evaluates access requests against registered policies and roles, so that access control decisions are made consistently with deny-first semantics.

#### Acceptance Criteria

1. THE AccessEnforcer SHALL accept an AccessPolicyRegistry at construction time.
2. THE AccessEnforcer SHALL provide a register_role method that accepts a Role and stores the role for role-based evaluation.
3. THE AccessEnforcer SHALL provide an assign_role method that accepts a RoleAssignment and associates the role with the specified agent identifier.
4. THE AccessEnforcer SHALL provide a revoke_role method that accepts an agent identifier and a role name and removes the role assignment.
5. THE AccessEnforcer SHALL provide an evaluate method that accepts a principal string, a resource string, and an action string, and returns an AccessDecision.
6. WHEN evaluating an access request, THE AccessEnforcer SHALL first check all deny policies; if any deny policy matches, the AccessEnforcer SHALL return an AccessDecision with a deny result.
7. WHEN no deny policy matches, THE AccessEnforcer SHALL check all allow policies from the AccessPolicyRegistry and from the roles assigned to the principal; if any allow policy matches, the AccessEnforcer SHALL return an AccessDecision with an allow result.
8. WHEN no policy matches the access request, THE AccessEnforcer SHALL return an AccessDecision with a deny result (default deny).
9. WHEN evaluating role-based policies, THE AccessEnforcer SHALL skip RoleAssignment entries that have expired.
10. THE AccessEnforcer SHALL provide a list_roles method that returns the list of registered Role objects.
11. THE AccessEnforcer SHALL provide a list_role_assignments method that accepts an optional agent identifier and returns the list of RoleAssignment objects, filtered by agent identifier when provided.
12. THE AccessEnforcer SHALL provide a __repr__ method that includes the class name, policy count, and role count.
13. THE AccessEnforcer SHALL provide a __str__ method that returns a human-readable summary including the policy count, role count, and role assignment count.

### Requirement 8: Access Decision

**User Story:** As a developer, I want a structured access decision object, so that I can inspect the result of an access control evaluation including which policy matched.

#### Acceptance Criteria

1. THE AccessDecision SHALL contain the decision string (one of "allow", "deny"), the matching policy name string (or "default_deny" when no policy matched), the principal string, the resource string, the action string, and a timestamp.
2. THE AccessDecision SHALL expose all fields as read-only properties.
3. THE AccessDecision SHALL provide an is_allowed read-only property that returns True when the decision is "allow".
4. THE AccessDecision SHALL provide an as_dict method that returns a dictionary representation of the decision fields.
5. THE AccessDecision SHALL provide a to_json method that returns a JSON string representation of the decision fields.
6. THE AccessDecision SHALL provide a class method from_dict that constructs an AccessDecision from a dictionary.
7. THE AccessDecision SHALL provide a class method from_json that deserializes a JSON string into an AccessDecision instance.
8. FOR ALL valid AccessDecision instances, calling to_json and then from_json SHALL produce an equivalent AccessDecision object (round-trip property).
9. THE AccessDecision SHALL provide a __repr__ method that includes the class name, decision, principal, resource, and action.
10. THE AccessDecision SHALL provide a __str__ method that returns a human-readable summary including the decision, principal, resource, action, and matching policy name.

### Requirement 9: Input Sanitizer

**User Story:** As a developer, I want pluggable input sanitizers that clean and validate input data before it reaches tools and LLM providers, so that injection attacks and malformed input are prevented.

#### Acceptance Criteria

1. THE InputSanitizer base class SHALL define an abstract interface with a sanitize method that accepts an input string and returns a SanitizationResult.
2. THE InputSanitizer base class SHALL require all subclasses to provide an implementation for the sanitize method.
3. THE InputSanitizer base class SHALL expose a read-only property for the sanitizer name as a string.
4. THE framework SHALL provide a RegexDenySanitizer that rejects or removes input content matching a provided regular expression pattern.
5. THE framework SHALL provide a RegexAllowSanitizer that rejects input content that does not match a provided regular expression allowlist pattern.
6. THE framework SHALL provide a LengthLimitSanitizer that truncates input content exceeding a configured maximum length.
7. THE framework SHALL provide an EncodingNormalizeSanitizer that normalizes input content to a specified Unicode normalization form (NFC, NFD, NFKC, NFKD).
8. WHEN the RegexDenySanitizer detects a match against the deny pattern, THE RegexDenySanitizer SHALL remove the matching content from the input and include the rule name in the SanitizationResult applied rules list.
9. WHEN the RegexAllowSanitizer detects input that does not match the allow pattern, THE RegexAllowSanitizer SHALL raise a SanitizationError that includes the sanitizer name and a description of the violation.
10. THE InputSanitizer base class SHALL provide a __repr__ method that includes the class name and sanitizer name.
11. THE InputSanitizer base class SHALL provide a __str__ method that returns a human-readable summary including the sanitizer name.

### Requirement 10: Output Filter

**User Story:** As a developer, I want pluggable output filters that redact sensitive data and enforce content policies on output from tools and LLM providers, so that credentials and sensitive information are not leaked.

#### Acceptance Criteria

1. THE OutputFilter base class SHALL define an abstract interface with a filter method that accepts an output string and returns a SanitizationResult.
2. THE OutputFilter base class SHALL require all subclasses to provide an implementation for the filter method.
3. THE OutputFilter base class SHALL expose a read-only property for the filter name as a string.
4. THE framework SHALL provide a CredentialRedactFilter that detects and replaces credential-like patterns (API keys, tokens, passwords) in output with a configurable redaction placeholder string, defaulting to "[REDACTED]".
5. THE framework SHALL provide a PiiMaskFilter that detects and masks personally identifiable information patterns (email addresses, phone numbers) in output with a configurable mask placeholder string, defaulting to "[MASKED]".
6. THE framework SHALL provide a RegexRedactFilter that redacts output content matching a provided regular expression pattern with a configurable replacement string.
7. WHEN the CredentialRedactFilter detects a credential-like pattern, THE CredentialRedactFilter SHALL replace the matched content with the redaction placeholder and include the rule name in the SanitizationResult applied rules list.
8. WHEN the PiiMaskFilter detects a PII pattern, THE PiiMaskFilter SHALL replace the matched content with the mask placeholder and include the rule name in the SanitizationResult applied rules list.
9. THE OutputFilter base class SHALL provide a __repr__ method that includes the class name and filter name.
10. THE OutputFilter base class SHALL provide a __str__ method that returns a human-readable summary including the filter name.

### Requirement 11: Sanitization Rule

**User Story:** As a developer, I want structured sanitization rule objects that describe individual sanitization and filtering rules, so that I can configure and inspect the sanitization pipeline declaratively.

#### Acceptance Criteria

1. THE SanitizationRule SHALL contain a rule name string, a rule type string (one of "regex_deny", "regex_allow", "encoding_normalize", "length_limit", "credential_redact", "pii_mask"), a pattern or configuration string, and a description string.
2. THE SanitizationRule SHALL expose all fields as read-only properties.
3. WHEN a SanitizationRule is created with a rule type not in the set of valid types, THEN THE SanitizationRule SHALL raise a SemanticError identifying the invalid type and listing the valid rule types.
4. THE SanitizationRule SHALL provide an as_dict method that returns a dictionary representation of the rule fields.
5. THE SanitizationRule SHALL provide a to_json method that returns a JSON string representation of the rule fields.
6. THE SanitizationRule SHALL provide a class method from_dict that constructs a SanitizationRule from a dictionary.
7. THE SanitizationRule SHALL provide a class method from_json that deserializes a JSON string into a SanitizationRule instance.
8. FOR ALL valid SanitizationRule instances, calling to_json and then from_json SHALL produce an equivalent SanitizationRule object (round-trip property).
9. THE SanitizationRule SHALL provide a __repr__ method that includes the class name, rule name, and rule type.
10. THE SanitizationRule SHALL provide a __str__ method that returns a human-readable summary including the rule name, type, and description.

### Requirement 12: Sanitization Pipeline

**User Story:** As a developer, I want to chain multiple sanitizers and filters into an ordered pipeline, so that input and output data passes through all configured security checks in sequence.

#### Acceptance Criteria

1. THE SanitizationPipeline SHALL maintain an ordered list of InputSanitizer instances for input processing and an ordered list of OutputFilter instances for output processing.
2. THE SanitizationPipeline SHALL provide an add_input_sanitizer method that accepts an InputSanitizer and appends the sanitizer to the input processing list.
3. THE SanitizationPipeline SHALL provide an add_output_filter method that accepts an OutputFilter and appends the filter to the output processing list.
4. THE SanitizationPipeline SHALL provide a sanitize_input method that accepts an input string and applies all registered InputSanitizer instances in order, returning a SanitizationResult containing the final sanitized value and the combined list of applied rule names.
5. THE SanitizationPipeline SHALL provide a filter_output method that accepts an output string and applies all registered OutputFilter instances in order, returning a SanitizationResult containing the final filtered value and the combined list of applied rule names.
6. IF any InputSanitizer in the pipeline raises a SanitizationError, THEN THE SanitizationPipeline SHALL propagate the SanitizationError without invoking subsequent sanitizers.
7. THE SanitizationPipeline SHALL provide a read-only property for the count of registered input sanitizers.
8. THE SanitizationPipeline SHALL provide a read-only property for the count of registered output filters.
9. THE SanitizationPipeline SHALL provide a __repr__ method that includes the class name, input sanitizer count, and output filter count.
10. THE SanitizationPipeline SHALL provide a __str__ method that returns a human-readable summary including the input sanitizer count and output filter count.

### Requirement 13: Sanitization Result

**User Story:** As a developer, I want a structured result from sanitization and filtering operations, so that I can inspect whether data was modified and which rules were applied.

#### Acceptance Criteria

1. THE SanitizationResult SHALL contain the original value as a string, the sanitized value as a string, a boolean indicating whether the value was modified, and a list of applied rule name strings.
2. THE SanitizationResult SHALL expose all fields as read-only properties.
3. THE SanitizationResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
4. THE SanitizationResult SHALL provide a __repr__ method that includes the class name, modified status, and applied rule count.
5. THE SanitizationResult SHALL provide a __str__ method that returns a human-readable summary including the modified status and applied rule names.

### Requirement 14: Audit Logger

**User Story:** As a developer, I want an audit logger that records all agent actions with tamper-evident entries, so that I can review a complete, trustworthy history of agent behavior for compliance and debugging.

#### Acceptance Criteria

1. THE AuditLogger SHALL accept an agent identifier string and an AuditStore instance at construction time.
2. THE AuditLogger SHALL provide a log_action method that accepts an action type string, a principal string, a resource string, an outcome string (one of "success", "failure", "denied"), a correlation identifier string, and an optional detail dictionary, and creates and persists an AuditEntry to the AuditStore.
3. WHEN an AuditEntry is created, THE AuditLogger SHALL generate a unique identifier, set the timestamp to the current UTC time, and compute an integrity hash over the entry fields using SHA-256.
4. THE AuditLogger SHALL provide a query method that accepts an AuditQuery and returns an AuditQueryResult from the AuditStore.
5. THE AuditLogger SHALL provide a read-only property for the count of recorded audit entries.
6. THE AuditLogger SHALL integrate with the StructuredLogger from the Observability & Debugging system, logging each audit entry at INFO level with the action type, principal, resource, and outcome.
7. THE AuditLogger SHALL provide a __repr__ method that includes the class name, agent identifier, and entry count.
8. THE AuditLogger SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and entry count.

### Requirement 15: Audit Entry

**User Story:** As a developer, I want structured audit entries with integrity hashes, so that I can verify the tamper-evident history of agent actions.

#### Acceptance Criteria

1. THE AuditEntry SHALL contain a unique string identifier, a timestamp, an agent identifier string, a correlation identifier string, an action type string, a principal string, a resource string, an outcome string (one of "success", "failure", "denied"), a detail dictionary, and an integrity hash string.
2. THE AuditEntry SHALL expose all fields as read-only properties.
3. THE AuditEntry SHALL provide a verify_integrity method that recomputes the integrity hash from the entry fields and returns True when the recomputed hash matches the stored integrity hash.
4. WHEN an AuditEntry is created with an outcome value not in the set of valid outcomes, THEN THE AuditEntry SHALL raise a SemanticError identifying the invalid outcome and listing the valid outcome values.
5. THE AuditEntry SHALL provide an as_dict method that returns a dictionary representation of the entry fields including the integrity hash.
6. THE AuditEntry SHALL provide a to_json method that returns a JSON string representation of the entry fields.
7. THE AuditEntry SHALL provide a class method from_dict that constructs an AuditEntry from a dictionary.
8. THE AuditEntry SHALL provide a class method from_json that deserializes a JSON string into an AuditEntry instance.
9. FOR ALL valid AuditEntry instances, calling to_json and then from_json SHALL produce an equivalent AuditEntry object (round-trip property).
10. THE AuditEntry SHALL provide a __repr__ method that includes the class name, identifier, action type, and outcome.
11. THE AuditEntry SHALL provide a __str__ method that returns a human-readable summary including the timestamp, action type, principal, resource, and outcome.

### Requirement 16: Audit Store

**User Story:** As a developer, I want a pluggable audit store abstraction for persisting audit entries, so that I can swap audit storage backends without changing agent code.

#### Acceptance Criteria

1. THE AuditStore base class SHALL define an abstract interface that includes methods for append (add an AuditEntry), retrieve (get an AuditEntry by identifier), search (execute an AuditQuery), and count (return the total number of entries).
2. THE AuditStore base class SHALL require all subclasses to provide an implementation for the append, retrieve, search, and count methods.
3. THE AuditStore base class SHALL expose a read-only property for the store name as a string.
4. THE AuditStore base class SHALL enforce append-only semantics; the AuditStore SHALL NOT provide methods for updating or deleting individual AuditEntry objects.
5. THE framework SHALL provide an InMemoryAuditStore that stores AuditEntry objects in process memory using list-based storage.
6. THE framework SHALL provide a FileAuditStore that persists AuditEntry objects as JSON lines to a specified file path.
7. WHEN the FileAuditStore is constructed with a file path, THE FileAuditStore SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
8. IF a file read or write operation fails in the FileAuditStore, THEN THE FileAuditStore SHALL raise an AuditStoreError that includes the file path and the underlying I/O error detail.
9. FOR ALL AuditEntry objects stored in the FileAuditStore, writing the entry to the file and then reading the entry back SHALL produce an equivalent AuditEntry object (round-trip property).
10. THE AuditStore base class SHALL provide a __repr__ method that includes the class name, store name, and entry count.
11. THE AuditStore base class SHALL provide a __str__ method that returns a human-readable summary including the store name and entry count.

### Requirement 17: Audit Query and Result

**User Story:** As a developer, I want to search audit entries by agent identifier, action type, principal, resource, outcome, and time range, so that I can investigate specific agent actions for compliance and debugging.

#### Acceptance Criteria

1. THE AuditQuery SHALL support filtering by agent identifier string.
2. THE AuditQuery SHALL support filtering by action type string.
3. THE AuditQuery SHALL support filtering by principal string.
4. THE AuditQuery SHALL support filtering by resource string.
5. THE AuditQuery SHALL support filtering by outcome string.
6. THE AuditQuery SHALL support filtering by a time range defined by an optional start timestamp and an optional end timestamp.
7. THE AuditQuery SHALL support an optional max_results integer to limit the number of returned entries.
8. THE AuditQuery SHALL provide an as_dict method that returns a dictionary representation of the query fields.
9. THE AuditQuery SHALL provide a __repr__ method that includes the class name and a summary of active filter criteria.
10. THE AuditQuery SHALL provide a __str__ method that returns a human-readable summary of the query criteria.
11. THE AuditQueryResult SHALL contain the list of matching AuditEntry objects and the total count of matches.
12. THE AuditQueryResult SHALL expose all fields as read-only properties.
13. THE AuditQueryResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
14. THE AuditQueryResult SHALL provide a __repr__ method that includes the class name and the count of matching entries.
15. THE AuditQueryResult SHALL provide a __str__ method that returns a human-readable summary including the match count.

### Requirement 18: Sandbox Executor

**User Story:** As a developer, I want to execute tools in a sandboxed environment with restricted access to system resources, so that untrusted or third-party tools cannot compromise the host system.

#### Acceptance Criteria

1. THE SandboxExecutor SHALL accept a SandboxPolicy at construction time defining the resource restrictions for sandboxed execution.
2. THE SandboxExecutor SHALL wrap the ToolExecutor and intercept tool execution requests to apply sandbox restrictions.
3. WHEN a tool execution is requested through the SandboxExecutor, THE SandboxExecutor SHALL validate the tool's resource access against the SandboxPolicy before invoking the ToolExecutor.
4. THE SandboxExecutor SHALL enforce file system access restrictions by validating that any file paths accessed by the tool fall within the allowed file system paths defined in the SandboxPolicy.
5. THE SandboxExecutor SHALL enforce network access restrictions by validating that any network connections attempted by the tool target hosts within the allowed network hosts defined in the SandboxPolicy.
6. THE SandboxExecutor SHALL enforce execution time restrictions by terminating tool execution that exceeds the maximum execution time defined in the SandboxPolicy.
7. THE SandboxExecutor SHALL enforce memory usage restrictions by monitoring tool execution memory consumption and terminating execution that exceeds the maximum memory usage defined in the SandboxPolicy.
8. THE SandboxExecutor SHALL restrict environment variable access to only the allowed environment variables defined in the SandboxPolicy.
9. IF a sandbox restriction is violated during tool execution, THEN THE SandboxExecutor SHALL terminate the execution, create a SandboxViolation record, and raise a SandboxViolationError that includes the violation details.
10. THE SandboxExecutor SHALL return a ToolResult consistent with the ToolExecutor interface when execution completes successfully within sandbox restrictions.
11. THE SandboxExecutor SHALL provide a __repr__ method that includes the class name and a summary of the SandboxPolicy restrictions.
12. THE SandboxExecutor SHALL provide a __str__ method that returns a human-readable summary including the allowed paths count, allowed hosts count, and maximum execution time.

### Requirement 19: Sandbox Policy

**User Story:** As a developer, I want to configure sandbox restrictions declaratively, so that I can define file system, network, time, memory, and environment constraints for tool execution without modifying code.

#### Acceptance Criteria

1. THE SandboxPolicy SHALL contain a list of allowed file system path strings, a list of allowed network host strings, a maximum execution time in seconds as a float, a maximum memory usage in bytes as an integer, and a list of allowed environment variable name strings.
2. THE SandboxPolicy SHALL expose all fields as read-only properties.
3. THE SandboxPolicy SHALL provide a is_path_allowed method that accepts a file path string and returns a boolean indicating whether the path falls within any of the allowed file system paths.
4. THE SandboxPolicy SHALL provide a is_host_allowed method that accepts a host string and returns a boolean indicating whether the host matches any of the allowed network hosts.
5. THE SandboxPolicy SHALL provide a is_env_allowed method that accepts an environment variable name string and returns a boolean indicating whether the variable is in the allowed environment variables list.
6. THE SandboxPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields.
7. THE SandboxPolicy SHALL provide a to_json method that returns a JSON string representation of the policy fields.
8. THE SandboxPolicy SHALL provide a class method from_dict that constructs a SandboxPolicy from a dictionary.
9. THE SandboxPolicy SHALL provide a class method from_json that deserializes a JSON string into a SandboxPolicy instance.
10. FOR ALL valid SandboxPolicy instances, calling to_json and then from_json SHALL produce an equivalent SandboxPolicy object (round-trip property).
11. THE SandboxPolicy SHALL provide a __repr__ method that includes the class name, allowed path count, allowed host count, and maximum execution time.
12. THE SandboxPolicy SHALL provide a __str__ method that returns a human-readable summary including the allowed path count, allowed host count, maximum execution time, and maximum memory usage.

### Requirement 20: Sandbox Violation

**User Story:** As a developer, I want structured violation records when sandbox restrictions are breached, so that I can inspect and audit security violations during tool execution.

#### Acceptance Criteria

1. THE SandboxViolation SHALL contain a violation type string (one of "file_access", "network_access", "timeout", "memory_limit", "environment_access"), a violating resource identifier string, and a description string.
2. THE SandboxViolation SHALL expose all fields as read-only properties.
3. WHEN a SandboxViolation is created with a violation type not in the set of valid types, THEN THE SandboxViolation SHALL raise a SemanticError identifying the invalid type and listing the valid violation types.
4. THE SandboxViolation SHALL provide an as_dict method that returns a dictionary representation of the violation fields.
5. THE SandboxViolation SHALL provide a to_json method that returns a JSON string representation of the violation fields.
6. THE SandboxViolation SHALL provide a class method from_dict that constructs a SandboxViolation from a dictionary.
7. THE SandboxViolation SHALL provide a class method from_json that deserializes a JSON string into a SandboxViolation instance.
8. FOR ALL valid SandboxViolation instances, calling to_json and then from_json SHALL produce an equivalent SandboxViolation object (round-trip property).
9. THE SandboxViolation SHALL provide a __repr__ method that includes the class name, violation type, and violating resource.
10. THE SandboxViolation SHALL provide a __str__ method that returns a human-readable summary including the violation type, violating resource, and description.

### Requirement 21: Security Configuration

**User Story:** As a developer, I want to configure the security system declaratively, so that I can define access control, audit logging, sanitization, and sandbox settings without modifying code.

#### Acceptance Criteria

1. THE SecurityConfiguration SHALL contain access control enabled as a boolean, audit logging enabled as a boolean, input sanitization enabled as a boolean, output filtering enabled as a boolean, sandbox enabled as a boolean, a default SandboxPolicy as an optional dictionary, credential rotation settings as an optional dictionary, and security plugin settings as a dictionary.
2. THE SecurityConfiguration SHALL support loading configuration from a Python dictionary.
3. THE SecurityConfiguration SHALL support loading configuration from a JSON file path.
4. THE SecurityConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE SecurityConfiguration SHALL resolve the file path relative to the AppContext directory provided by `automojo-this-app`.
6. THE SecurityConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. THE SecurityConfiguration SHALL support CredentialReference entries for security backend authentication that are resolved through `automojo-credentials` at initialization time.
8. IF a CredentialReference cannot be resolved, THEN THE SecurityConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
9. THE SecurityConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration, excluding resolved credential values.
10. THE SecurityConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration, excluding resolved credential values.
11. THE SecurityConfiguration SHALL provide a to_yaml method that returns a YAML string representation of the configuration, excluding resolved credential values.
12. THE SecurityConfiguration SHALL provide a class method from_dict that constructs a SecurityConfiguration from a dictionary.
13. THE SecurityConfiguration SHALL provide a class method from_json that deserializes a JSON string into a SecurityConfiguration instance.
14. THE SecurityConfiguration SHALL provide a class method from_yaml that deserializes a YAML string into a SecurityConfiguration instance.
15. FOR ALL valid SecurityConfiguration instances, calling to_json and then from_json SHALL produce an equivalent SecurityConfiguration object (round-trip property).
16. FOR ALL valid SecurityConfiguration instances, calling to_yaml and then from_yaml SHALL produce an equivalent SecurityConfiguration object (round-trip property).
17. THE SecurityConfiguration SHALL provide a __repr__ method that includes the class name, access control enabled, audit logging enabled, and sandbox enabled status.
18. THE SecurityConfiguration SHALL provide a __str__ method that returns a human-readable summary including the access control enabled, audit logging enabled, input sanitization enabled, output filtering enabled, and sandbox enabled status.

### Requirement 22: Security Pipeline

**User Story:** As a developer, I want a coordinating component that routes security operations through the credential manager, access enforcer, sanitization pipeline, audit logger, and sandbox executor, so that all security subsystems work together through a single integration point.

#### Acceptance Criteria

1. THE SecurityPipeline SHALL accept a SecurityConfiguration at construction time for configuring the pipeline behavior.
2. THE SecurityPipeline SHALL construct and own the CredentialManager, AccessEnforcer, AccessPolicyRegistry, SanitizationPipeline, AuditLogger, and SandboxExecutor instances based on the SecurityConfiguration.
3. THE SecurityPipeline SHALL provide a read-only property for the CredentialManager instance.
4. THE SecurityPipeline SHALL provide a read-only property for the AccessEnforcer instance.
5. THE SecurityPipeline SHALL provide a read-only property for the AccessPolicyRegistry instance.
6. THE SecurityPipeline SHALL provide a read-only property for the SanitizationPipeline instance.
7. THE SecurityPipeline SHALL provide a read-only property for the AuditLogger instance.
8. THE SecurityPipeline SHALL provide a read-only property for the SandboxExecutor instance, returning None when sandbox is not enabled.
9. WHEN access control is disabled in the SecurityConfiguration, THE AccessEnforcer SHALL operate as a pass-through, returning allow decisions for all access requests.
10. WHEN audit logging is disabled in the SecurityConfiguration, THE AuditLogger SHALL operate as a no-op, discarding audit entries without persisting.
11. WHEN input sanitization is disabled in the SecurityConfiguration, THE SanitizationPipeline SHALL pass input through without applying sanitizers.
12. WHEN output filtering is disabled in the SecurityConfiguration, THE SanitizationPipeline SHALL pass output through without applying filters.
13. THE SecurityPipeline SHALL provide a shutdown method that flushes the AuditLogger and releases resources held by security components.
14. THE SecurityPipeline SHALL provide a __repr__ method that includes the class name and the enabled status of each security subsystem.
15. THE SecurityPipeline SHALL provide a __str__ method that returns a human-readable summary including the enabled status of access control, audit logging, sanitization, and sandbox.

### Requirement 23: Agent Security Integration

**User Story:** As a developer, I want agents to own a security pipeline and enforce security policies throughout their lifecycle, so that all agent operations are automatically secured.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only security property that returns the Agent's SecurityPipeline instance.
2. THE Agent base class SHALL expose a read-only credential_manager property that returns the Agent's CredentialManager instance from the SecurityPipeline.
3. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL construct the SecurityPipeline from the Agent's SecurityConfiguration.
4. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all SecurityPlugin instances from `automojo-extension` ExtensionPoint entries targeting the Agent.
5. WHEN a tool execution is requested through the Agent, THE SecurityPipeline SHALL evaluate the access request through the AccessEnforcer before executing the tool.
6. IF the AccessEnforcer returns a deny decision for a tool execution request, THEN THE Agent SHALL raise an AccessDeniedError that includes the agent identifier, tool name, and the AccessDecision.
7. WHEN a tool execution is requested and access is allowed, THE SecurityPipeline SHALL sanitize the tool input through the SanitizationPipeline before execution.
8. WHEN a tool execution completes, THE SecurityPipeline SHALL filter the tool output through the SanitizationPipeline before returning the result.
9. WHEN a tool execution is requested and sandbox is enabled, THE SecurityPipeline SHALL execute the tool through the SandboxExecutor instead of the standard ToolExecutor.
10. WHEN any agent action occurs (tool execution, LLM request, memory operation, message send/receive, workflow step execution), THE AuditLogger SHALL record the action with the appropriate action type, principal, resource, and outcome.
11. WHEN an Agent transitions to the STOPPED state, THE Agent SHALL flush and shut down the SecurityPipeline.
12. IF the Agent's SecurityConfiguration is not provided, THEN THE Agent SHALL default to a SecurityConfiguration with access control disabled, audit logging disabled, input sanitization disabled, output filtering disabled, and sandbox disabled.

### Requirement 24: Built-in Security Metrics

**User Story:** As a developer, I want the framework to automatically register and collect standard security metrics, so that I get useful security operational data without manual instrumentation.

#### Acceptance Criteria

1. WHEN an Agent is initialized with security enabled, THE framework SHALL register the following MetricDefinition instances in the Agent's MetricsRegistry:
   - "agent.security.access.allowed" as a COUNTER with unit "count" and description "Count of access requests allowed"
   - "agent.security.access.denied" as a COUNTER with unit "count" and description "Count of access requests denied"
   - "agent.security.sanitization.applied" as a COUNTER with unit "count" and description "Count of sanitization rules applied"
   - "agent.security.sandbox.violations" as a COUNTER with unit "count" and description "Count of sandbox violations detected"
   - "agent.security.credential.rotations" as a COUNTER with unit "count" and description "Count of credential rotations performed"
   - "agent.security.audit.entries" as a COUNTER with unit "count" and description "Count of audit entries recorded"
2. WHEN an access decision is made, THE framework SHALL increment the appropriate access counter ("agent.security.access.allowed" or "agent.security.access.denied") with labels including the agent identifier, principal, and resource.
3. WHEN a sanitization rule is applied, THE framework SHALL increment the "agent.security.sanitization.applied" counter with labels including the agent identifier and rule name.
4. WHEN a sandbox violation is detected, THE framework SHALL increment the "agent.security.sandbox.violations" counter with labels including the agent identifier and violation type.
5. WHEN a credential rotation occurs, THE framework SHALL increment the "agent.security.credential.rotations" counter with labels including the agent identifier and credential name.
6. WHEN an audit entry is recorded, THE framework SHALL increment the "agent.security.audit.entries" counter with labels including the agent identifier and action type.

### Requirement 25: Security Plugin Integration

**User Story:** As a developer, I want to distribute security components as plugins through `automojo-extension`, so that custom sanitizers, filters, and audit stores can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.input_sanitizers" through `automojo-extension` for registering InputSanitizer plugin implementations.
2. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.output_filters" through `automojo-extension` for registering OutputFilter plugin implementations.
3. THE framework SHALL define an ExtensionPoint named "automojo.agentkit.audit_stores" through `automojo-extension` for registering AuditStore plugin implementations.
4. WHEN an Agent is initialized, THE Agent SHALL query the security ExtensionPoints and register all discovered plugin instances with the Agent's SecurityPipeline.
5. IF a SecurityPlugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
6. IF a SecurityPlugin provides a component that conflicts with an already registered component of the same type and name, THEN THE Agent SHALL log the conflict at WARNING level and skip the conflicting plugin component.

### Requirement 26: Security Error Handling

**User Story:** As a developer, I want well-defined error types for security operation failures, so that I can diagnose and handle security errors precisely.

#### Acceptance Criteria

1. THE AccessDeniedError SHALL inherit from AgentKitError and SHALL be raised when an access control evaluation results in a deny decision.
2. THE AccessDeniedError SHALL contain the principal string, the resource string, the action string, and the AccessDecision object.
3. THE AccessDeniedError SHALL provide a meaningful __repr__ that includes the exception class name, principal, resource, action, and matching policy name.
4. THE SanitizationError SHALL inherit from AgentKitError and SHALL be raised when an input sanitization or output filtering operation detects a policy violation that cannot be resolved by sanitization.
5. THE SanitizationError SHALL contain the sanitizer or filter name, the rule name, and a descriptive message.
6. THE SanitizationError SHALL provide a meaningful __repr__ that includes the exception class name, sanitizer or filter name, and rule name.
7. THE SandboxViolationError SHALL inherit from AgentKitError and SHALL be raised when a sandboxed tool execution violates a SandboxPolicy restriction.
8. THE SandboxViolationError SHALL contain the tool name, the SandboxViolation object, and the original exception as the cause when applicable.
9. THE SandboxViolationError SHALL provide a meaningful __repr__ that includes the exception class name, tool name, violation type, and violating resource.
10. THE AuditStoreError SHALL inherit from AgentKitError and SHALL be raised when an AuditStore operation fails due to a backend error.
11. THE AuditStoreError SHALL contain the store name, the operation name, and the original exception as the cause.
12. THE AuditStoreError SHALL provide a meaningful __repr__ that includes the exception class name, store name, and operation name.

### Requirement 27: Structured Logging for Security Operations

**User Story:** As a developer, I want security operations to produce structured log entries, so that I can monitor and debug security behavior using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy under `automojo.agentkit.security`.
2. WHEN an access decision is made, THE framework SHALL log at INFO level including the principal, resource, action, and decision.
3. WHEN an access request is denied, THE framework SHALL log at WARNING level including the principal, resource, action, and the matching deny policy name.
4. WHEN a sanitization rule is applied to input, THE framework SHALL log at DEBUG level including the sanitizer name and rule name.
5. WHEN a sanitization error occurs, THE framework SHALL log at WARNING level including the sanitizer name, rule name, and error detail.
6. WHEN a sandbox violation is detected, THE framework SHALL log at WARNING level including the tool name, violation type, and violating resource.
7. WHEN a credential is rotated, THE framework SHALL log at INFO level including the credential name (without the secret value).
8. WHEN an audit entry is recorded, THE framework SHALL log at DEBUG level including the action type, principal, resource, and outcome.

### Requirement 28: Security String Representations

**User Story:** As a developer, I want meaningful string representations on security system classes, so that I can quickly inspect security state during debugging sessions.

#### Acceptance Criteria

1. THE CredentialManager SHALL provide a __repr__ method that includes the class name, agent identifier, and cached credential count.
2. THE CredentialManager SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and cached credential count.
3. THE CredentialEntry SHALL provide a __repr__ method that includes the class name, credential name, and credential type.
4. THE CredentialEntry SHALL provide a __str__ method that returns a human-readable summary including the credential name, type, and expiration status.
5. THE AccessPolicy SHALL provide a __repr__ method that includes the class name, policy name, and effect.
6. THE AccessPolicy SHALL provide a __str__ method that returns a human-readable summary including the policy name, principal pattern, resource pattern, actions, and effect.
7. THE AccessEnforcer SHALL provide a __repr__ method that includes the class name, policy count, and role count.
8. THE AccessEnforcer SHALL provide a __str__ method that returns a human-readable summary including the policy count, role count, and role assignment count.
9. THE AccessDecision SHALL provide a __repr__ method that includes the class name, decision, principal, resource, and action.
10. THE AccessDecision SHALL provide a __str__ method that returns a human-readable summary including the decision, principal, resource, action, and matching policy name.
11. THE AuditLogger SHALL provide a __repr__ method that includes the class name, agent identifier, and entry count.
12. THE AuditLogger SHALL provide a __str__ method that returns a human-readable summary including the agent identifier and entry count.
13. THE AuditEntry SHALL provide a __repr__ method that includes the class name, identifier, action type, and outcome.
14. THE AuditEntry SHALL provide a __str__ method that returns a human-readable summary including the timestamp, action type, principal, resource, and outcome.
15. THE SandboxExecutor SHALL provide a __repr__ method that includes the class name and a summary of the SandboxPolicy restrictions.
16. THE SandboxExecutor SHALL provide a __str__ method that returns a human-readable summary including the allowed paths count, allowed hosts count, and maximum execution time.
17. THE SecurityPipeline SHALL provide a __repr__ method that includes the class name and the enabled status of each security subsystem.
18. THE SecurityPipeline SHALL provide a __str__ method that returns a human-readable summary including the enabled status of access control, audit logging, sanitization, and sandbox.
19. THE AccessPolicyRegistry SHALL provide a __repr__ method that includes the class name and the count of registered policies.
20. THE AccessPolicyRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered policy names and effects.
