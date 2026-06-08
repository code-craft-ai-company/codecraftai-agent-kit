# Requirements Document — LLM Integration

## Introduction

The LLM Integration feature extends the `codecraftai-agent-kit` SDK with a unified interface for interacting with Large Language Model providers. It defines an LLM provider abstraction with a common interface, a provider registry for managing available providers, prompt template management with versioning, structured output parsing and validation, token usage tracking and cost estimation, streaming response support, retry and fallback strategies across providers, and conversation/message history management. The system integrates with the Agent base class so agents can use LLM providers, with the Tool system so LLMs can invoke tools and receive tool results, with `codecraftai-extension` so LLM provider plugins can be discovered and loaded, with `codecraftai-credentials` for API key and credential management, with `codecraftai-dataprofiles` for data profile management, and with `codecraftai-this-app` for settings and environment configuration.

## Glossary

- **LlmProvider**: An abstract base class representing a Large Language Model service. An LlmProvider accepts a list of messages and returns a completion response. Concrete implementations wrap specific provider APIs (OpenAI, Anthropic, AWS Bedrock, Azure OpenAI, local models).
- **LlmProviderRegistry**: A registry that tracks all available LlmProvider instances within a runtime, providing lookup by name, tag, and enumeration. Each Agent maintains an LlmProviderRegistry instance.
- **LlmMessage**: An immutable object representing a single message in a conversation, containing a role (system, user, assistant, tool), content, and optional metadata such as tool call information.
- **LlmConversation**: An ordered sequence of LlmMessage objects representing a conversation history. The LlmConversation supports appending messages, truncation, and serialization.
- **LlmResponse**: An immutable object encapsulating the result of an LLM completion request, containing the response message, token usage information, provider name, model name, and request duration.
- **LlmStreamChunk**: An immutable object representing a single chunk of a streaming LLM response, containing partial content text and optional metadata.
- **LlmStreamHandler**: A callback interface invoked for each LlmStreamChunk during a streaming completion request. The handler receives chunks as they arrive and a final LlmResponse when the stream completes.
- **TokenUsage**: An immutable object containing the count of prompt tokens, completion tokens, and total tokens consumed by a single LLM request.
- **CostEstimate**: An immutable object containing the estimated cost of a single LLM request, calculated from TokenUsage and provider-specific pricing rates.
- **CostTracker**: A component that accumulates TokenUsage and CostEstimate records across multiple LLM requests, providing totals and per-provider breakdowns.
- **PromptTemplate**: A named, versioned template string with placeholder variables that can be rendered into a final prompt string by supplying variable values.
- **PromptTemplateRegistry**: A registry that tracks available PromptTemplate instances, providing lookup by name and version.
- **OutputParser**: An abstract base class for parsing raw LLM response text into structured Python objects. Concrete implementations handle specific formats (JSON, delimited, regex-based).
- **OutputSchema**: A declarative schema definition used by an OutputParser to validate that parsed output conforms to expected structure and types.
- **RetryPolicy**: A configuration object defining retry behavior for failed LLM requests, including maximum retry count, backoff strategy, and retryable error conditions.
- **FallbackChain**: An ordered list of LlmProvider names that defines the fallback sequence when a provider fails. The FallbackChain tries each provider in order until one succeeds or all fail.
- **LlmToolBridge**: A component that converts Tool descriptors into LLM-compatible function/tool definitions, and converts LLM tool call responses back into tool execution requests.
- **LlmProviderPlugin**: An LlmProvider implementation discovered and loaded through the `codecraftai-extension` ExtensionPoint mechanism, allowing external packages to contribute LLM providers.
- **Agent**: The base agent class defined in the Core Agent Framework that owns an LlmProviderRegistry and uses LLM providers for completion requests.
- **ExtensionPoint**: An integration surface provided by `codecraftai-extension` that allows external plugins to register LlmProvider implementations with an Agent.
- **CredentialReference**: A named reference resolved through `codecraftai-credentials` that provides secure access to API keys and secrets required by an LlmProvider.
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **LlmRequestError**: An exception raised when an LLM provider request fails due to a provider-side error (rate limit, authentication failure, server error).
- **LlmResponseParsingError**: An exception raised when an OutputParser fails to parse or validate LLM response text.

## Requirements

### Requirement 1: LLM Provider Abstraction

**User Story:** As a developer, I want a well-defined LLM provider base class with a common interface, so that I can interact with different LLM services through a consistent API regardless of the underlying provider.

#### Acceptance Criteria

1. THE LlmProvider base class SHALL define an abstract interface that includes methods for complete (synchronous completion), complete_stream (streaming completion), and get_model_info (provider and model metadata).
2. THE LlmProvider base class SHALL require all subclasses to provide an implementation for the complete and complete_stream methods.
3. THE LlmProvider base class SHALL expose a read-only property for the provider name as a string.
4. THE LlmProvider base class SHALL expose a read-only property for the model name as a string.
5. THE LlmProvider base class SHALL expose a read-only property for the provider configuration as a dictionary.
6. THE LlmProvider base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the provider requires.
7. THE LlmProvider base class SHALL accept an optional dictionary of tags at construction time for categorization and discovery purposes.
8. WHEN a LlmProvider subclass does not provide a provider name, THEN THE LlmProvider base class SHALL raise a SemanticError indicating that a provider name is required.
9. WHEN a LlmProvider subclass does not provide a model name, THEN THE LlmProvider base class SHALL raise a SemanticError indicating that a model name is required.
10. THE LlmProvider base class SHALL provide a __repr__ method that includes the class name, provider name, and model name.
11. THE LlmProvider base class SHALL provide a __str__ method that returns a human-readable summary including the provider name and model name.

### Requirement 2: LLM Message and Conversation

**User Story:** As a developer, I want structured message and conversation objects, so that I can build and manage conversation histories for LLM interactions in a consistent format.

#### Acceptance Criteria

1. THE LlmMessage SHALL contain a role string (one of "system", "user", "assistant", "tool"), a content string, and an optional metadata dictionary.
2. THE LlmMessage SHALL expose all fields as read-only properties.
3. WHEN an LlmMessage is created with a role value not in the set of valid roles, THEN THE LlmMessage SHALL raise a SemanticError identifying the invalid role value and listing the valid roles.
4. THE LlmMessage SHALL provide an as_dict method that returns a dictionary representation of the message fields.
5. THE LlmMessage SHALL provide a to_json method that returns a JSON string representation of the message fields.
6. THE LlmMessage SHALL provide a class method from_dict that constructs an LlmMessage from a dictionary.
7. THE LlmMessage SHALL provide a class method from_json that deserializes a JSON string into an LlmMessage instance.
8. FOR ALL valid LlmMessage instances, calling to_json and then from_json SHALL produce an equivalent LlmMessage object (round-trip property).
9. THE LlmConversation SHALL maintain an ordered list of LlmMessage objects.
10. THE LlmConversation SHALL provide an append method that adds an LlmMessage to the end of the conversation.
11. THE LlmConversation SHALL provide a read-only property for the count of messages in the conversation.
12. THE LlmConversation SHALL provide a messages read-only property that returns a copy of the message list.
13. THE LlmConversation SHALL provide a truncate method that accepts a maximum message count and removes the oldest non-system messages to fit within the limit, preserving system messages.
14. THE LlmConversation SHALL provide a to_json method that serializes the conversation to a JSON string.
15. THE LlmConversation SHALL provide a class method from_json that deserializes a JSON string into an LlmConversation instance.
16. FOR ALL valid LlmConversation instances, calling to_json and then from_json SHALL produce an equivalent LlmConversation object (round-trip property).

### Requirement 3: LLM Response

**User Story:** As a developer, I want a structured response object from LLM completion requests, so that I can inspect the response content, token usage, and provider metadata in a consistent way.

#### Acceptance Criteria

1. THE LlmResponse SHALL contain the response LlmMessage, a TokenUsage object, the provider name string, the model name string, and the request duration as a float in seconds.
2. THE LlmResponse SHALL expose all fields as read-only properties.
3. THE LlmResponse SHALL provide an as_dict method that returns a dictionary representation of the response fields.
4. THE LlmResponse SHALL provide a to_json method that returns a JSON string representation of the response fields.
5. THE LlmResponse SHALL provide a class method from_json that deserializes a JSON string into an LlmResponse instance.
6. FOR ALL valid LlmResponse instances, calling to_json and then from_json SHALL produce an equivalent LlmResponse object (round-trip property).
7. THE LlmResponse SHALL provide a __repr__ method that includes the class name, provider name, model name, and total token count.
8. THE LlmResponse SHALL provide a __str__ method that returns a human-readable summary including the provider name, model name, token usage, and duration.

### Requirement 4: Token Usage Tracking

**User Story:** As a developer, I want to track token usage for each LLM request, so that I can monitor consumption and manage costs across providers.

#### Acceptance Criteria

1. THE TokenUsage SHALL contain the prompt token count as an integer, the completion token count as an integer, and the total token count as an integer.
2. THE TokenUsage SHALL expose all fields as read-only properties.
3. THE TokenUsage SHALL validate that the total token count equals the sum of prompt tokens and completion tokens at construction time.
4. IF the total token count does not equal the sum of prompt and completion tokens, THEN THE TokenUsage SHALL raise a SemanticError identifying the mismatch.
5. THE TokenUsage SHALL provide an as_dict method that returns a dictionary representation of the token counts.
6. THE TokenUsage SHALL provide a __repr__ method that includes the class name and all token counts.
7. THE TokenUsage SHALL provide a __str__ method that returns a human-readable summary of the token counts.
8. THE TokenUsage SHALL provide an __add__ method that returns a new TokenUsage whose counts are the sum of the two operands.

### Requirement 5: Cost Estimation

**User Story:** As a developer, I want to estimate the cost of LLM requests based on token usage and provider pricing, so that I can budget and control spending on LLM services.

#### Acceptance Criteria

1. THE CostEstimate SHALL contain the prompt cost as a float, the completion cost as a float, the total cost as a float, and the currency string.
2. THE CostEstimate SHALL expose all fields as read-only properties.
3. THE CostEstimate SHALL validate that the total cost equals the sum of prompt cost and completion cost at construction time.
4. IF the total cost does not equal the sum of prompt cost and completion cost, THEN THE CostEstimate SHALL raise a SemanticError identifying the mismatch.
5. THE CostEstimate SHALL provide an as_dict method that returns a dictionary representation of the cost fields.
6. THE CostEstimate SHALL provide a __repr__ method that includes the class name, total cost, and currency.
7. THE CostEstimate SHALL provide a __str__ method that returns a human-readable summary of the costs.
8. THE CostTracker SHALL accumulate TokenUsage and CostEstimate records across multiple LLM requests.
9. THE CostTracker SHALL provide a read-only property for the total TokenUsage across all tracked requests.
10. THE CostTracker SHALL provide a read-only property for the total CostEstimate across all tracked requests.
11. THE CostTracker SHALL provide a method that returns a per-provider breakdown of TokenUsage and CostEstimate totals as a dictionary keyed by provider name.
12. THE CostTracker SHALL provide a read-only property for the count of tracked requests.
13. THE CostTracker SHALL provide a reset method that clears all accumulated records.

### Requirement 6: Streaming Response Support

**User Story:** As a developer, I want to receive LLM responses as a stream of chunks, so that I can process partial results as they arrive and provide real-time feedback to users.

#### Acceptance Criteria

1. THE LlmStreamChunk SHALL contain a partial content string and an optional metadata dictionary.
2. THE LlmStreamChunk SHALL expose all fields as read-only properties.
3. THE LlmStreamHandler SHALL define a callback interface with an on_chunk method that receives an LlmStreamChunk and an on_complete method that receives the final LlmResponse.
4. WHEN the complete_stream method is called on an LlmProvider, THE LlmProvider SHALL invoke the LlmStreamHandler on_chunk method for each chunk received from the provider.
5. WHEN the streaming response completes, THE LlmProvider SHALL invoke the LlmStreamHandler on_complete method with the final assembled LlmResponse including complete TokenUsage.
6. IF an error occurs during streaming, THEN THE LlmProvider SHALL invoke an on_error method on the LlmStreamHandler with the exception, and raise an LlmRequestError.
7. THE LlmStreamChunk SHALL provide a __repr__ method that includes the class name and a truncated content preview.
8. THE LlmStreamChunk SHALL provide a __str__ method that returns the partial content string.

### Requirement 7: Prompt Template Management

**User Story:** As a developer, I want to define and manage versioned prompt templates with placeholder variables, so that I can reuse and evolve prompts without modifying agent code.

#### Acceptance Criteria

1. THE PromptTemplate SHALL contain a name string, a version string, a template string with placeholder variables using Python str.format syntax, and an optional description string.
2. THE PromptTemplate SHALL expose all fields as read-only properties.
3. THE PromptTemplate SHALL provide a render method that accepts a dictionary of variable values and returns the rendered prompt string with all placeholders replaced.
4. WHEN the render method is called with missing required variables, THE PromptTemplate SHALL raise a SemanticError identifying the missing variable names.
5. THE PromptTemplate SHALL provide a variables read-only property that returns the list of placeholder variable names extracted from the template string.
6. THE PromptTemplate SHALL provide an as_dict method that returns a dictionary representation of the template fields.
7. THE PromptTemplate SHALL provide a to_json method that returns a JSON string representation of the template fields.
8. THE PromptTemplate SHALL provide a class method from_dict that constructs a PromptTemplate from a dictionary.
9. THE PromptTemplate SHALL provide a class method from_json that deserializes a JSON string into a PromptTemplate instance.
10. FOR ALL valid PromptTemplate instances, calling to_json and then from_json SHALL produce an equivalent PromptTemplate object (round-trip property).
11. THE PromptTemplateRegistry SHALL support registration of a PromptTemplate instance using the template name and version as a composite key.
12. IF a PromptTemplate with a duplicate name and version is registered, THEN THE PromptTemplateRegistry SHALL raise a SemanticError that includes the duplicate name and version.
13. THE PromptTemplateRegistry SHALL support lookup of a PromptTemplate by name and optional version, returning the latest version when no version is specified.
14. THE PromptTemplateRegistry SHALL support enumeration of all registered PromptTemplate instances as a list.
15. THE PromptTemplateRegistry SHALL expose a read-only property for the count of registered templates.
16. THE PromptTemplateRegistry SHALL support loading PromptTemplate definitions from a JSON file path.
17. THE PromptTemplateRegistry SHALL support loading PromptTemplate definitions from a YAML file path.

### Requirement 8: Structured Output Parsing

**User Story:** As a developer, I want to parse and validate LLM response text into structured Python objects, so that I can reliably extract data from LLM outputs.

#### Acceptance Criteria

1. THE OutputParser base class SHALL define an abstract interface with a parse method that accepts a raw response string and returns a parsed Python object.
2. THE OutputParser base class SHALL require all subclasses to provide an implementation for the parse method.
3. THE framework SHALL provide a JsonOutputParser that parses LLM response text as JSON and returns a Python dictionary or list.
4. WHEN the JsonOutputParser receives text that is not valid JSON, THEN THE JsonOutputParser SHALL raise an LlmResponseParsingError that includes the raw text and the JSON parsing error detail.
5. THE framework SHALL provide a RegexOutputParser that extracts structured data from LLM response text using a provided regular expression pattern with named capture groups.
6. WHEN the RegexOutputParser pattern does not match the response text, THEN THE RegexOutputParser SHALL raise an LlmResponseParsingError that includes the raw text and the pattern.
7. THE OutputParser base class SHALL accept an optional OutputSchema at construction time for post-parse validation.
8. WHEN an OutputSchema is provided, THE OutputParser SHALL validate the parsed output against the OutputSchema after parsing.
9. IF the parsed output does not conform to the OutputSchema, THEN THE OutputParser SHALL raise an LlmResponseParsingError that includes the validation error details.
10. THE OutputSchema SHALL support defining expected fields with type constraints including string, integer, float, boolean, list, and dictionary types.
11. THE OutputSchema SHALL support marking individual fields as required or optional.
12. THE OutputSchema SHALL provide a validate method that accepts a parsed object and returns a list of validation error strings, returning an empty list when the object is valid.
13. THE OutputSchema SHALL provide an as_dict method that returns a dictionary representation of the schema definition.
14. THE OutputSchema SHALL provide a to_json method that returns a JSON string representation of the schema definition.
15. THE OutputSchema SHALL provide a class method from_dict that constructs an OutputSchema from a dictionary.
16. THE OutputSchema SHALL provide a class method from_json that deserializes a JSON string into an OutputSchema instance.
17. FOR ALL valid OutputSchema instances, calling to_json and then from_json SHALL produce an equivalent OutputSchema object (round-trip property).

### Requirement 9: LLM Provider Registry

**User Story:** As a developer, I want a registry that tracks available LLM providers, so that I can discover and look up providers by name or tags.

#### Acceptance Criteria

1. THE LlmProviderRegistry SHALL support registration of an LlmProvider instance using a composite key of provider name and model name.
2. IF an LlmProvider with a duplicate provider name and model name combination is registered, THEN THE LlmProviderRegistry SHALL raise a SemanticError that includes the duplicate provider name and model name.
3. THE LlmProviderRegistry SHALL support deregistration of an LlmProvider by provider name and model name.
4. THE LlmProviderRegistry SHALL support lookup of a registered LlmProvider by provider name and model name, returning the LlmProvider instance or None when not found.
5. THE LlmProviderRegistry SHALL support lookup of registered LlmProviders by provider name only, returning a list of all LlmProvider instances for that provider.
6. THE LlmProviderRegistry SHALL support lookup of registered LlmProviders by tag key-value pairs, returning a list of LlmProvider instances that match all provided tag criteria.
7. THE LlmProviderRegistry SHALL support enumeration of all registered LlmProvider instances as a list.
8. THE LlmProviderRegistry SHALL expose a read-only property for the count of currently registered providers.
9. THE LlmProviderRegistry SHALL provide a has_provider method that accepts a provider name and model name and returns a boolean indicating whether a matching LlmProvider is registered.

### Requirement 10: Retry and Fallback Strategies

**User Story:** As a developer, I want configurable retry and fallback strategies for LLM requests, so that transient failures are handled automatically and alternative providers are tried when a provider is unavailable.

#### Acceptance Criteria

1. THE RetryPolicy SHALL contain a maximum retry count as an integer, a backoff strategy string (one of "fixed", "exponential", "exponential_with_jitter"), a base delay in seconds as a float, a maximum delay in seconds as a float, and a list of retryable exception types.
2. THE RetryPolicy SHALL expose all fields as read-only properties.
3. THE RetryPolicy SHALL provide a get_delay method that accepts the current retry attempt number and returns the delay in seconds before the next retry, calculated according to the configured backoff strategy.
4. WHEN the backoff strategy is "fixed", THE RetryPolicy get_delay method SHALL return the base delay for all retry attempts.
5. WHEN the backoff strategy is "exponential", THE RetryPolicy get_delay method SHALL return the base delay multiplied by 2 raised to the power of the attempt number, capped at the maximum delay.
6. WHEN the backoff strategy is "exponential_with_jitter", THE RetryPolicy get_delay method SHALL return the exponential delay with a random jitter factor between 0 and 1 applied, capped at the maximum delay.
7. THE RetryPolicy SHALL provide a should_retry method that accepts an exception and the current attempt number and returns a boolean indicating whether the request should be retried.
8. THE FallbackChain SHALL contain an ordered list of LlmProvider name-model pairs defining the fallback sequence.
9. THE FallbackChain SHALL expose a read-only property for the ordered list of provider name-model pairs.
10. THE FallbackChain SHALL provide a next_provider method that accepts the current provider name-model pair and returns the next provider name-model pair in the sequence, or None when the end of the chain is reached.
11. THE RetryPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields.
12. THE RetryPolicy SHALL provide a to_json method that returns a JSON string representation of the policy fields.
13. THE RetryPolicy SHALL provide a class method from_dict that constructs a RetryPolicy from a dictionary.
14. FOR ALL valid RetryPolicy instances (excluding the retryable exception types list), calling to_json and then from_dict on the parsed JSON SHALL produce a RetryPolicy with equivalent maximum retry count, backoff strategy, base delay, and maximum delay values.

### Requirement 11: LLM Tool Bridge

**User Story:** As a developer, I want the LLM system to convert tool descriptors into LLM-compatible function definitions and route LLM tool call responses back to the tool system, so that LLMs can invoke agent tools seamlessly.

#### Acceptance Criteria

1. THE LlmToolBridge SHALL provide a method that accepts a list of ToolDescriptor objects and returns a list of LLM-compatible function definition dictionaries following the OpenAI function calling format.
2. THE LlmToolBridge SHALL provide a method that accepts an LlmMessage containing tool call information and returns a list of tool execution request dictionaries, each containing the tool name and input arguments.
3. THE LlmToolBridge SHALL provide a method that accepts a tool name and a ToolResult and returns an LlmMessage with role "tool" containing the tool execution result.
4. WHEN a ToolDescriptor has an input schema, THE LlmToolBridge SHALL convert the ToolSchema parameters into JSON Schema format for the function definition.
5. IF an LlmMessage does not contain valid tool call information, THEN THE LlmToolBridge SHALL raise a SemanticError indicating that the message does not contain tool calls.
6. FOR ALL valid ToolDescriptor instances, converting to LLM function definitions and inspecting the result SHALL preserve the tool name, description, and parameter names and types from the original ToolDescriptor.

### Requirement 12: Agent LLM Integration

**User Story:** As a developer, I want agents to own an LLM provider registry and execute LLM completion requests through the agent interface, so that LLM usage is scoped to individual agents and integrated with the agent lifecycle.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only llm_providers property that returns the Agent's LlmProviderRegistry instance.
2. THE Agent base class SHALL provide a register_llm_provider method that accepts an LlmProvider instance and registers the LlmProvider with the Agent's LlmProviderRegistry.
3. THE Agent base class SHALL provide a complete method that accepts a provider name, model name, an LlmConversation, and optional parameters, looks up the LlmProvider in the Agent's LlmProviderRegistry, and executes the completion request, returning an LlmResponse.
4. IF the requested provider name and model name combination is not found in the Agent's LlmProviderRegistry, THEN THE complete method SHALL raise a SemanticError that includes the requested provider name, model name, and the agent identity.
5. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all LlmProviderPlugin instances from `codecraftai-extension` ExtensionPoint entries targeting the Agent.
6. WHEN an Agent transitions to the STOPPED state, THE Agent's LlmProviderRegistry SHALL be cleared of all registered providers.
7. THE Agent base class SHALL expose a read-only cost_tracker property that returns the Agent's CostTracker instance.
8. WHEN an LLM completion request returns an LlmResponse, THE Agent SHALL record the TokenUsage and CostEstimate from the response in the Agent's CostTracker.

### Requirement 13: LLM Provider Plugin Integration

**User Story:** As a developer, I want to distribute LLM providers as plugins through `codecraftai-extension`, so that provider packages can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "ccai.agentkit.llm_providers" through `codecraftai-extension` for registering LlmProviderPlugin implementations.
2. WHEN an Agent is initialized, THE Agent SHALL query the "ccai.agentkit.llm_providers" ExtensionPoint and register all discovered LlmProvider instances with the Agent's LlmProviderRegistry.
3. IF an LlmProviderPlugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
4. IF an LlmProviderPlugin provides an LlmProvider with a name-model combination that conflicts with an already registered LlmProvider, THEN THE Agent SHALL log the conflict at WARNING level including both provider identifiers and skip the conflicting plugin provider.

### Requirement 14: Credential Integration for LLM Providers

**User Story:** As a developer, I want LLM providers to securely resolve API keys and credentials through `codecraftai-credentials`, so that secrets are managed centrally and not embedded in agent configuration or code.

#### Acceptance Criteria

1. WHEN an LlmProvider declares CredentialReference names, THE framework SHALL resolve each CredentialReference through the `codecraftai-credentials` package before the provider handles completion requests.
2. IF a CredentialReference declared by an LlmProvider cannot be resolved, THEN THE framework SHALL raise a ConfigurationError that identifies the unresolvable credential name and the provider name.
3. THE LlmProvider SHALL NOT include resolved credential values in the output of any serialization method or string representation.

### Requirement 15: LLM Error Handling

**User Story:** As a developer, I want well-defined error types for LLM request failures and response parsing failures, so that I can diagnose and handle LLM errors precisely.

#### Acceptance Criteria

1. THE LlmRequestError SHALL inherit from AgentKitError and SHALL be raised when an LLM provider request fails due to a provider-side error.
2. THE LlmRequestError SHALL contain the provider name, the model name, the error category string (one of "rate_limit", "authentication", "server_error", "timeout", "connection", "invalid_request"), and the original exception as the cause.
3. THE LlmResponseParsingError SHALL inherit from AgentKitError and SHALL be raised when an OutputParser fails to parse or validate LLM response text.
4. THE LlmResponseParsingError SHALL contain the parser class name, the raw response text, and a descriptive error message.
5. ALL LLM-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name and descriptive message.

### Requirement 16: LLM Completion with Retry and Fallback

**User Story:** As a developer, I want the framework to automatically retry failed LLM requests and fall back to alternative providers, so that transient failures are handled transparently without manual intervention.

#### Acceptance Criteria

1. WHEN an LLM completion request fails and a RetryPolicy is configured, THE framework SHALL retry the request according to the RetryPolicy before raising an error.
2. WHEN all retry attempts are exhausted and a FallbackChain is configured, THE framework SHALL attempt the request with the next provider in the FallbackChain.
3. WHEN a fallback provider succeeds, THE framework SHALL return the LlmResponse from the successful fallback provider.
4. IF all providers in the FallbackChain fail, THEN THE framework SHALL raise an LlmRequestError that includes the original provider name and a summary of all attempted providers and their failure reasons.
5. THE framework SHALL log each retry attempt at INFO level including the provider name, attempt number, and delay before retry.
6. THE framework SHALL log each fallback attempt at WARNING level including the failed provider name and the fallback provider name.

### Requirement 17: LLM Serialization

**User Story:** As a developer, I want to serialize and deserialize LLM messages, conversations, responses, and templates, so that LLM interaction data can be stored, transmitted, and reconstructed.

#### Acceptance Criteria

1. THE LlmMessage SHALL provide a to_json method that serializes the message to a JSON string.
2. THE LlmMessage SHALL provide a class method from_json that deserializes a JSON string into an LlmMessage instance.
3. THE LlmConversation SHALL provide a to_json method that serializes the conversation to a JSON string.
4. THE LlmConversation SHALL provide a class method from_json that deserializes a JSON string into an LlmConversation instance.
5. THE LlmResponse SHALL provide a to_json method that serializes the response to a JSON string.
6. THE LlmResponse SHALL provide a class method from_json that deserializes a JSON string into an LlmResponse instance.
7. THE PromptTemplate SHALL provide a to_json method that serializes the template to a JSON string.
8. THE PromptTemplate SHALL provide a class method from_json that deserializes a JSON string into a PromptTemplate instance.
9. FOR ALL valid LlmMessage instances, calling to_json and then from_json SHALL produce an equivalent LlmMessage object (round-trip property).
10. FOR ALL valid LlmConversation instances, calling to_json and then from_json SHALL produce an equivalent LlmConversation object (round-trip property).
11. FOR ALL valid LlmResponse instances, calling to_json and then from_json SHALL produce an equivalent LlmResponse object (round-trip property).
12. FOR ALL valid PromptTemplate instances, calling to_json and then from_json SHALL produce an equivalent PromptTemplate object (round-trip property).

### Requirement 18: Structured Logging for LLM Operations

**User Story:** As a developer, I want LLM operations to produce structured log entries, so that I can monitor and debug LLM usage using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy under `ccai.agentkit.llm`.
2. WHEN an LLM completion request begins, THE framework SHALL log at INFO level including the provider name, model name, and agent identifier.
3. WHEN an LLM completion request completes successfully, THE framework SHALL log at INFO level including the provider name, model name, token usage, and request duration.
4. WHEN an LLM completion request fails, THE framework SHALL log at WARNING level including the provider name, model name, error category, and error detail.
5. WHEN a retry attempt is made, THE framework SHALL log at INFO level including the provider name, attempt number, and delay.
6. WHEN a fallback provider is attempted, THE framework SHALL log at WARNING level including the failed provider name and the fallback provider name.

### Requirement 19: LLM String Representations

**User Story:** As a developer, I want meaningful string representations on LLM system classes, so that I can quickly inspect LLM state during debugging sessions.

#### Acceptance Criteria

1. THE LlmProvider base class SHALL provide a __repr__ method that includes the class name, provider name, and model name.
2. THE LlmProvider base class SHALL provide a __str__ method that returns a human-readable summary including the provider name and model name.
3. THE LlmMessage SHALL provide a __repr__ method that includes the class name, role, and a truncated content preview.
4. THE LlmMessage SHALL provide a __str__ method that returns a human-readable summary including the role and content.
5. THE LlmConversation SHALL provide a __repr__ method that includes the class name and message count.
6. THE LlmConversation SHALL provide a __str__ method that returns a human-readable summary listing the message roles in order.
7. THE LlmResponse SHALL provide a __repr__ method that includes the class name, provider name, model name, and total token count.
8. THE LlmResponse SHALL provide a __str__ method that returns a human-readable summary including the provider name, model name, token usage, and duration.
9. THE TokenUsage SHALL provide a __repr__ method that includes the class name and all token counts.
10. THE TokenUsage SHALL provide a __str__ method that returns a human-readable summary of the token counts.
11. THE CostEstimate SHALL provide a __repr__ method that includes the class name, total cost, and currency.
12. THE CostEstimate SHALL provide a __str__ method that returns a human-readable summary of the costs.
13. THE PromptTemplate SHALL provide a __repr__ method that includes the class name, template name, and version.
14. THE PromptTemplate SHALL provide a __str__ method that returns a human-readable summary including the template name, version, and variable names.
15. THE RetryPolicy SHALL provide a __repr__ method that includes the class name, maximum retry count, and backoff strategy.
16. THE RetryPolicy SHALL provide a __str__ method that returns a human-readable summary of the retry configuration.
17. THE LlmProviderRegistry SHALL provide a __repr__ method that includes the class name and the count of registered providers.
18. THE LlmProviderRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered provider name-model pairs.
