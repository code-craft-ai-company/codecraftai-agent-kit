# Implementation Plan: LLM Integration

## Overview

Incremental implementation of the LLM Integration feature for the `automojo-agent-kit` SDK. Tasks build bottom-up: foundational value objects first (errors, token usage, cost estimate, messages), then core abstractions (LLM provider, response, streaming), then registries and management (provider registry, prompt template registry), then output parsing and validation, then retry/fallback strategies, then tool bridge, then agent integration and plugin support. Each task references specific requirements and design properties. Tests are placed close to the code they validate.

## Tasks

- [x] 1. Implement LLM error types and foundational value objects
  - [x] 1.1 Create `source/packages/automojo/agentkit/llmerrors.py` with LlmRequestError and LlmResponseParsingError
    - LlmRequestError inherits from AgentKitError, stores provider_name, model_name, category, cause
    - Validate category against VALID_CATEGORIES set
    - Use multi-line error message formation pattern with `os.linesep`
    - LlmResponseParsingError inherits from AgentKitError, stores parser_name, raw_text, error_message
    - Include truncated raw text preview (first 200 chars) in error message
    - Both provide `__repr__` with class name and descriptive fields
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 1.2 Create `source/packages/automojo/agentkit/tokenusage.py` with the TokenUsage class
    - Implement `__init__` with prompt_tokens, completion_tokens, total_tokens
    - Validate total_tokens equals prompt_tokens + completion_tokens, raise SemanticError on mismatch
    - Implement all read-only properties
    - Implement `as_dict()`, `__add__`, `__eq__`, `__repr__`, `__str__`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 19.9, 19.10_

  - [x] 1.3 Create `source/packages/automojo/agentkit/costestimate.py` with the CostEstimate class
    - Implement `__init__` with prompt_cost, completion_cost, total_cost, currency (default "USD")
    - Validate total_cost equals prompt_cost + completion_cost within floating-point tolerance (1e-9), raise SemanticError on mismatch
    - Implement all read-only properties
    - Implement `as_dict()`, `__eq__`, `__repr__`, `__str__`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 19.11, 19.12_

  - [x] 1.4 Write property tests for TokenUsage and CostEstimate (Properties 13, 14, 15)
    - **Property 13: TokenUsage construction validates total equals sum**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    - **Property 14: TokenUsage addition produces correct sums**
    - **Validates: Requirements 4.8**
    - **Property 15: CostEstimate construction validates total equals sum**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

  - [x] 1.5 Write unit tests for LlmErrors, TokenUsage, and CostEstimate
    - Test LlmRequestError fields (provider_name, model_name, category, cause) and repr
    - Test LlmResponseParsingError fields (parser_name, raw_text, error_message) and repr
    - Test TokenUsage with valid and invalid totals
    - Test TokenUsage __repr__, __str__, __add__, __eq__
    - Test CostEstimate with valid and invalid totals
    - Test CostEstimate __repr__, __str__, __eq__
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_llmerrors.py`, `test_tokenusage.py`, `test_costestimate.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 15.1, 15.2, 15.3, 15.4, 15.5, 19.9, 19.10, 19.11, 19.12_

- [x] 2. Implement LlmMessage and LlmConversation
  - [x] 2.1 Create `source/packages/automojo/agentkit/llmmessage.py` with the LlmMessage class
    - Implement `__init__` with role, content, metadata; validate role against VALID_ROLES set, raise SemanticError for invalid role
    - Implement all read-only properties (role, content, metadata returns copy)
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, data)`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, role, truncated content preview), `__str__` (role and content), `__eq__`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 17.1, 17.2, 17.9, 19.3, 19.4_

  - [x] 2.2 Create `source/packages/automojo/agentkit/llmconversation.py` with the LlmConversation class
    - Implement `__init__` with optional messages list
    - Implement `count` and `messages` (returns copy) read-only properties
    - Implement `append(message)`, `truncate(max_messages)` preserving system messages
    - Implement `as_dict()`, `to_json()`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, message count), `__str__` (roles list), `__eq__`
    - _Requirements: 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 17.3, 17.4, 17.10, 19.5, 19.6_

  - [x] 2.3 Write property tests for LlmMessage and LlmConversation (Properties 1, 2, 9, 10, 11, 12)
    - **Property 1: LlmMessage JSON round-trip**
    - **Validates: Requirements 2.4, 2.5, 2.6, 2.7, 2.8, 17.1, 17.2, 17.9**
    - **Property 2: LlmConversation JSON round-trip**
    - **Validates: Requirements 2.14, 2.15, 2.16, 17.3, 17.4, 17.10**
    - **Property 9: LlmMessage construction rejects invalid roles**
    - **Validates: Requirements 2.3**
    - **Property 10: LlmConversation append increases count and preserves order**
    - **Validates: Requirements 2.9, 2.10, 2.11**
    - **Property 11: LlmConversation messages property returns a copy**
    - **Validates: Requirements 2.12**
    - **Property 12: LlmConversation truncate preserves system messages**
    - **Validates: Requirements 2.13**

  - [x] 2.4 Write unit tests for LlmMessage and LlmConversation
    - Test LlmMessage with all valid roles, invalid role raises SemanticError
    - Test LlmMessage with empty metadata, special characters in content
    - Test LlmMessage __repr__, __str__, __eq__
    - Test LlmConversation append, truncate with various message mixes
    - Test LlmConversation empty conversation serialization
    - Test LlmConversation __repr__, __str__, __eq__
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_llmmessage.py`, `test_llmconversation.py`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 17.1, 17.2, 17.3, 17.4, 17.9, 17.10, 19.3, 19.4, 19.5, 19.6_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement LlmProvider base class and LlmResponse
  - [x] 4.1 Create `source/packages/automojo/agentkit/llmprovider.py` with the LlmProvider abstract base class
    - Implement `__init__` with provider_name, model_name, config, credential_names, tags
    - Raise SemanticError if provider_name is None or empty/whitespace
    - Raise SemanticError if model_name is None or empty/whitespace
    - Implement all read-only properties (provider_name, model_name, config returns copy, credential_names returns copy, tags returns copy)
    - Declare abstract `complete(conversation, **kwargs)` and `complete_stream(conversation, handler, **kwargs)` methods
    - Implement `get_model_info()` returning dict with provider_name, model_name, config
    - Implement `__repr__` (class name, provider_name, model_name) and `__str__` (provider name / model name)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 19.1, 19.2_

  - [x] 4.2 Create `source/packages/automojo/agentkit/llmresponse.py` with the LlmResponse class
    - Implement `__init__` with message (LlmMessage), token_usage (TokenUsage), provider_name, model_name, duration
    - Implement all read-only properties
    - Implement `as_dict()`, `to_json()`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, provider, model, total tokens), `__str__` (provider, model, token usage, duration), `__eq__`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 17.5, 17.6, 17.11, 19.7, 19.8_

  - [x] 4.3 Write property tests for LlmProvider and LlmResponse (Properties 3, 7, 8)
    - **Property 3: LlmResponse JSON round-trip**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 17.5, 17.6, 17.11**
    - **Property 7: LlmProvider construction preserves fields**
    - **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7**
    - **Property 8: LlmProvider construction rejects missing name or model**
    - **Validates: Requirements 1.8, 1.9**

  - [x] 4.4 Write unit tests for LlmProvider and LlmResponse
    - Test LlmProvider abstract method enforcement (cannot instantiate directly)
    - Test LlmProvider with valid args, missing name, missing model
    - Test LlmProvider __repr__, __str__, get_model_info
    - Test LlmProvider config/credential_names/tags return copies
    - Test LlmResponse with valid fields, serialization edge cases
    - Test LlmResponse __repr__, __str__, __eq__
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_llmprovider.py`, `test_llmresponse.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 17.5, 17.6, 17.11, 19.1, 19.2, 19.7, 19.8_

- [x] 5. Implement streaming support
  - [x] 5.1 Create `source/packages/automojo/agentkit/llmstreamchunk.py` with the LlmStreamChunk class
    - Implement `__init__` with content, optional metadata
    - Implement all read-only properties (content, metadata returns copy)
    - Implement `__repr__` (class name, truncated content preview at 30 chars) and `__str__` (returns content)
    - _Requirements: 6.1, 6.2, 6.7, 6.8_

  - [x] 5.2 Create `source/packages/automojo/agentkit/llmstreamhandler.py` with the LlmStreamHandler abstract base class
    - Declare abstract `on_chunk(chunk)`, `on_complete(response)`, `on_error(error)` methods
    - _Requirements: 6.3, 6.4, 6.5, 6.6_

  - [x] 5.3 Write unit tests for LlmStreamChunk and LlmStreamHandler
    - Test LlmStreamChunk with various content lengths, empty metadata
    - Test LlmStreamChunk __repr__ truncation at 30 chars, __str__ returns content
    - Test LlmStreamHandler abstract method enforcement
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_llmstreamchunk.py`, `test_llmstreamhandler.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.7, 6.8_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement CostTracker
  - [x] 7.1 Create `source/packages/automojo/agentkit/costtracker.py` with the CostTracker class
    - Implement `__init__` with empty records list
    - Implement `record(provider_name, token_usage, cost_estimate)` to append entries
    - Implement `total_token_usage` read-only property summing all TokenUsage records via __add__
    - Implement `total_cost_estimate` read-only property summing all CostEstimate records
    - Implement `per_provider_breakdown()` returning dict keyed by provider name with token_usage and cost_estimate
    - Implement `request_count` read-only property
    - Implement `reset()` clearing all records
    - _Requirements: 5.8, 5.9, 5.10, 5.11, 5.12, 5.13_

  - [x] 7.2 Write property test for CostTracker (Property 16)
    - **Property 16: CostTracker accumulation and per-provider breakdown**
    - **Validates: Requirements 5.8, 5.9, 5.10, 5.11, 5.12, 5.13**

  - [x] 7.3 Write unit tests for CostTracker
    - Test empty tracker totals (zero values)
    - Test single record, multiple records, multiple providers
    - Test per_provider_breakdown grouping
    - Test reset clears all records
    - Create test file at `source/testroots/automojo/tests/singlehost/agentkit/test_costtracker.py`
    - _Requirements: 5.8, 5.9, 5.10, 5.11, 5.12, 5.13_

- [x] 8. Implement LlmProviderRegistry
  - [x] 8.1 Create `source/packages/automojo/agentkit/llmproviderregistry.py` with the LlmProviderRegistry class
    - Implement `__init__` with internal `_providers` dict
    - Implement `register(provider)` using (provider_name, model_name) as composite key, raise SemanticError on duplicate
    - Implement `deregister(provider_name, model_name)` removing provider if exists
    - Implement `lookup(provider_name, model_name)` returning LlmProvider or None
    - Implement `lookup_by_provider(provider_name)` returning list of providers for that name
    - Implement `lookup_by_tags(**tags)` returning list of providers matching all tag criteria
    - Implement `list_all()`, `has_provider(provider_name, model_name)`, `clear()`
    - Implement `count` read-only property
    - Implement `__repr__` (class name, count) and `__str__` (registered provider/model pairs)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 19.17, 19.18_

  - [x] 8.2 Write property tests for LlmProviderRegistry (Properties 26, 27, 28)
    - **Property 26: LlmProviderRegistry registration, lookup, and enumeration**
    - **Validates: Requirements 9.1, 9.2, 9.4, 9.5, 9.7, 9.8, 9.9**
    - **Property 27: LlmProviderRegistry deregistration removes provider**
    - **Validates: Requirements 9.3**
    - **Property 28: LlmProviderRegistry lookup by tags returns matching providers**
    - **Validates: Requirements 9.6**

  - [x] 8.3 Write unit tests for LlmProviderRegistry
    - Test empty registry count is 0
    - Test register, lookup, deregister, has_provider
    - Test duplicate registration raises SemanticError
    - Test lookup_by_provider with multiple models
    - Test lookup_by_tags with no matches, partial matches, full matches
    - Test clear removes all providers
    - Test __repr__ and __str__
    - Create test file at `source/testroots/automojo/tests/singlehost/agentkit/test_llmproviderregistry.py`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 19.17, 19.18_

- [x] 9. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement PromptTemplate and PromptTemplateRegistry
  - [x] 10.1 Create `source/packages/automojo/agentkit/prompttemplate.py` with the PromptTemplate class
    - Implement `__init__` with name, version, template, optional description
    - Implement `_extract_variables()` using `string.Formatter` to parse placeholder names
    - Implement all read-only properties (name, version, template, description, variables returns copy)
    - Implement `render(values)` replacing placeholders, raise SemanticError for missing variables
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, data)`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, name, version), `__str__` (name, version, variable names), `__eq__`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 17.7, 17.8, 17.12, 19.13, 19.14_

  - [x] 10.2 Create `source/packages/automojo/agentkit/prompttemplateregistry.py` with the PromptTemplateRegistry class
    - Implement `__init__` with internal `_templates` dict
    - Implement `register(template)` using (name, version) as composite key, raise SemanticError on duplicate
    - Implement `lookup(name, version=None)` returning template or None; return latest version when no version specified
    - Implement `list_all()` and `count` read-only property
    - Implement `load_from_json_file(file_path)` loading templates from JSON file
    - Implement `load_from_yaml_file(file_path)` loading templates from YAML file
    - _Requirements: 7.11, 7.12, 7.13, 7.14, 7.15, 7.16, 7.17_

  - [x] 10.3 Write property tests for PromptTemplate and PromptTemplateRegistry (Properties 4, 17, 18, 19, 20)
    - **Property 4: PromptTemplate JSON round-trip**
    - **Validates: Requirements 7.6, 7.7, 7.8, 7.9, 7.10, 17.7, 17.8, 17.12**
    - **Property 17: PromptTemplate render produces correct output**
    - **Validates: Requirements 7.3**
    - **Property 18: PromptTemplate render rejects missing variables**
    - **Validates: Requirements 7.4**
    - **Property 19: PromptTemplate variables property extracts all placeholders**
    - **Validates: Requirements 7.5**
    - **Property 20: PromptTemplateRegistry registration, lookup, and enumeration**
    - **Validates: Requirements 7.11, 7.12, 7.13, 7.14, 7.15**

  - [x] 10.4 Write unit tests for PromptTemplate and PromptTemplateRegistry
    - Test PromptTemplate with no variables, single variable, multiple variables
    - Test render with complete values, missing values raises SemanticError
    - Test PromptTemplate __repr__, __str__, __eq__
    - Test PromptTemplateRegistry register, lookup by name+version, lookup latest version
    - Test duplicate registration raises SemanticError
    - Test load_from_json_file and load_from_yaml_file with temp files
    - Test empty registry count is 0
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_prompttemplate.py`, `test_prompttemplateregistry.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 7.11, 7.12, 7.13, 7.14, 7.15, 7.16, 7.17, 17.7, 17.8, 17.12, 19.13, 19.14_

- [x] 11. Implement OutputSchema and OutputParsers
  - [x] 11.1 Create `source/packages/automojo/agentkit/outputschema.py` with the OutputSchema class
    - Implement `__init__` with fields list (each field has name, type, required)
    - Implement `fields` read-only property (returns copy)
    - Implement `validate(parsed_output)` returning list of error strings for missing required fields and type mismatches
    - Use SUPPORTED_TYPES and TYPE_MAP class constants
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, data)`, `from_json(cls, json_str)`, `__eq__`
    - _Requirements: 8.10, 8.11, 8.12, 8.13, 8.14, 8.15, 8.16, 8.17_

  - [x] 11.2 Create `source/packages/automojo/agentkit/outputparser.py` with the OutputParser abstract base class
    - Implement `__init__` with optional OutputSchema
    - Implement `schema` read-only property
    - Declare abstract `_parse_raw(raw_text)` method
    - Implement `parse(raw_text)` calling `_parse_raw` then validating against schema if present, raise LlmResponseParsingError on validation failure
    - _Requirements: 8.1, 8.2, 8.7, 8.8, 8.9_

  - [x] 11.3 Create `source/packages/automojo/agentkit/jsonoutputparser.py` with the JsonOutputParser class
    - Subclass OutputParser
    - Implement `_parse_raw(raw_text)` using `json.loads`, raise LlmResponseParsingError with raw text and JSON error detail on failure
    - _Requirements: 8.3, 8.4_

  - [x] 11.4 Create `source/packages/automojo/agentkit/regexoutputparser.py` with the RegexOutputParser class
    - Subclass OutputParser
    - Implement `__init__` with pattern string and optional schema, compile regex
    - Implement `pattern` read-only property
    - Implement `_parse_raw(raw_text)` using compiled regex search, return groupdict, raise LlmResponseParsingError with raw text and pattern on no match
    - _Requirements: 8.5, 8.6_

  - [x] 11.5 Write property tests for OutputSchema and OutputParsers (Properties 5, 21, 22, 23, 24, 25)
    - **Property 5: OutputSchema JSON round-trip**
    - **Validates: Requirements 8.13, 8.14, 8.15, 8.16, 8.17**
    - **Property 21: OutputSchema validates correct objects as valid**
    - **Validates: Requirements 8.10, 8.11, 8.12**
    - **Property 22: OutputSchema reports missing required fields and type mismatches**
    - **Validates: Requirements 8.10, 8.11, 8.12**
    - **Property 23: JsonOutputParser parses valid JSON and rejects invalid JSON**
    - **Validates: Requirements 8.3, 8.4**
    - **Property 24: RegexOutputParser extracts named groups and rejects non-matching text**
    - **Validates: Requirements 8.5, 8.6**
    - **Property 25: OutputParser validates parsed output against OutputSchema**
    - **Validates: Requirements 8.7, 8.8, 8.9**

  - [x] 11.6 Write unit tests for OutputSchema and OutputParsers
    - Test OutputSchema with mixed required/optional fields, empty fields list
    - Test OutputSchema validate with correct objects, missing fields, type mismatches
    - Test JsonOutputParser with valid JSON (dict, list, nested), invalid JSON
    - Test RegexOutputParser with matching and non-matching patterns, named groups
    - Test OutputParser with schema validation integration
    - Test LlmResponseParsingError raised with correct fields
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_outputschema.py`, `test_outputparser.py`, `test_jsonoutputparser.py`, `test_regexoutputparser.py`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 8.13, 8.14, 8.15, 8.16, 8.17_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement RetryPolicy and FallbackChain
  - [x] 13.1 Create `source/packages/automojo/agentkit/retrypolicy.py` with the RetryPolicy class
    - Implement `__init__` with max_retries, backoff_strategy, base_delay, max_delay, optional retryable_exceptions list
    - Implement all read-only properties
    - Implement `get_delay(attempt)` with fixed, exponential, and exponential_with_jitter strategies
    - Fixed: return base_delay; Exponential: min(base_delay * 2^attempt, max_delay); Jitter: exponential capped * random.random()
    - Implement `should_retry(exception, attempt)` checking max_retries and retryable exception types
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, data)`
    - Implement `__repr__` (class name, max_retries, strategy) and `__str__` (full config summary)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.11, 10.12, 10.13, 10.14, 19.15, 19.16_

  - [x] 13.2 Create `source/packages/automojo/agentkit/fallbackchain.py` with the FallbackChain class
    - Implement `__init__` with ordered list of (provider_name, model_name) tuples
    - Implement `providers` read-only property (returns copy)
    - Implement `next_provider(current_provider_name, current_model_name)` returning next tuple or None
    - _Requirements: 10.8, 10.9, 10.10_

  - [x] 13.3 Write property tests for RetryPolicy and FallbackChain (Properties 6, 29, 30, 31, 32, 33)
    - **Property 6: RetryPolicy serialization round-trip**
    - **Validates: Requirements 10.11, 10.12, 10.13, 10.14**
    - **Property 29: RetryPolicy fixed delay returns base_delay**
    - **Validates: Requirements 10.3, 10.4**
    - **Property 30: RetryPolicy exponential delay is bounded**
    - **Validates: Requirements 10.3, 10.5**
    - **Property 31: RetryPolicy exponential_with_jitter delay is bounded**
    - **Validates: Requirements 10.3, 10.6**
    - **Property 32: RetryPolicy should_retry respects max_retries and exception types**
    - **Validates: Requirements 10.7**
    - **Property 33: FallbackChain next_provider returns correct sequence**
    - **Validates: Requirements 10.8, 10.9, 10.10**

  - [x] 13.4 Write unit tests for RetryPolicy and FallbackChain
    - Test RetryPolicy with each backoff strategy and specific attempt numbers
    - Test should_retry at boundary (attempt == max_retries), with matching and non-matching exception types
    - Test RetryPolicy __repr__, __str__
    - Test RetryPolicy serialization as_dict, to_json, from_dict
    - Test FallbackChain with single provider, multiple providers, provider not in chain
    - Test FallbackChain next_provider at end of chain returns None
    - Create test files at `source/testroots/automojo/tests/singlehost/agentkit/test_retrypolicy.py`, `test_fallbackchain.py`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.11, 10.12, 10.13, 10.14, 19.15, 19.16_

- [x] 14. Implement LlmToolBridge
  - [x] 14.1 Create `source/packages/automojo/agentkit/llmtoolbridge.py` with the LlmToolBridge class
    - Implement TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA class constant mapping tool types to JSON Schema types
    - Implement `descriptors_to_functions(descriptors)` converting ToolDescriptor list to OpenAI function calling format dicts
    - Implement `_descriptor_to_function(descriptor)` for single conversion with name, description, parameters (properties, required)
    - Implement `message_to_tool_calls(message)` extracting tool calls from LlmMessage metadata, raise SemanticError if no tool_calls
    - Implement `tool_result_to_message(tool_name, result)` converting ToolResult to LlmMessage with role "tool"
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

  - [x] 14.2 Write property tests for LlmToolBridge (Properties 34, 35, 36)
    - **Property 34: LlmToolBridge preserves tool descriptor information**
    - **Validates: Requirements 11.1, 11.4, 11.6**
    - **Property 35: LlmToolBridge tool_result_to_message produces tool role message**
    - **Validates: Requirements 11.3**
    - **Property 36: LlmToolBridge rejects messages without tool calls**
    - **Validates: Requirements 11.5**

  - [x] 14.3 Write unit tests for LlmToolBridge
    - Test descriptors_to_functions with various ToolDescriptor schemas (string, integer, float, boolean, list, dictionary params)
    - Test message_to_tool_calls with valid tool call metadata, missing tool_calls raises SemanticError
    - Test tool_result_to_message produces correct role and metadata
    - Test conversion preserves tool name, description, parameter names and types
    - Create test file at `source/testroots/automojo/tests/singlehost/agentkit/test_llmtoolbridge.py`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement Agent LLM integration, plugin support, and retry/fallback execution
  - [x] 16.1 Extend the Agent base class with LLM-related properties and methods
    - Add `llm_providers` read-only property returning the Agent's LlmProviderRegistry instance
    - Add `cost_tracker` read-only property returning the Agent's CostTracker instance
    - Add `register_llm_provider(provider)` method delegating to the LlmProviderRegistry
    - Add `complete(provider_name, model_name, conversation, **kwargs)` method:
      - Lookup provider in LlmProviderRegistry, raise SemanticError if not found (include provider name, model name, agent identity)
      - Resolve credential references via automojo-credentials, raise ConfigurationError on failure
      - Execute provider.complete(conversation, **kwargs)
      - Record token_usage and cost_estimate in CostTracker
      - Return LlmResponse
    - Initialize LlmProviderRegistry and CostTracker during Agent construction
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.7, 12.8_

  - [x] 16.2 Implement retry and fallback execution in Agent complete method
    - When a RetryPolicy is configured and completion fails, retry according to policy
    - Log each retry attempt at INFO level (provider name, attempt number, delay)
    - When all retries exhausted and FallbackChain is configured, try next provider
    - Log each fallback attempt at WARNING level (failed provider, fallback provider)
    - If fallback succeeds, return LlmResponse from fallback provider
    - If all providers fail, raise LlmRequestError with summary of all attempted providers
    - Use `logging.getLogger("automojo.agentkit.llm")` for structured logging
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

  - [x] 16.3 Implement LlmProviderPlugin discovery during Agent initialization
    - During Agent `initialize()` (transition to INITIALIZED state), query "automojo.agentkit.llm_providers" ExtensionPoint
    - Register discovered LlmProvider instances with the Agent's LlmProviderRegistry
    - Log WARNING and continue on plugin load failure (include plugin name and error detail)
    - Log WARNING and skip on name-model conflict (include both provider identifiers)
    - _Requirements: 12.5, 13.1, 13.2, 13.3, 13.4_

  - [x] 16.4 Implement LlmProviderRegistry clearing on Agent stop
    - During Agent `stop()` (transition to STOPPED state), call `self._llm_provider_registry.clear()`
    - _Requirements: 12.6_

  - [x] 16.5 Implement credential resolution for LLM providers
    - Before completion requests, resolve each CredentialReference declared by the provider through `automojo-credentials`
    - Raise ConfigurationError if any credential cannot be resolved (include credential name and provider name)
    - Ensure resolved credential values are NOT included in any serialization or string representation
    - _Requirements: 14.1, 14.2, 14.3_

  - [x] 16.6 Implement structured logging for LLM operations
    - Use `logging.getLogger("automojo.agentkit.llm")` logger hierarchy
    - Log INFO on completion request begin (provider name, model name, agent identifier)
    - Log INFO on completion request success (provider name, model name, token usage, duration)
    - Log WARNING on completion request failure (provider name, model name, error category, error detail)
    - Log INFO on retry attempt (provider name, attempt number, delay)
    - Log WARNING on fallback attempt (failed provider name, fallback provider name)
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

  - [x] 16.7 Write property tests for Agent LLM integration (Properties 37, 38, 39)
    - **Property 37: Agent LlmProviderRegistry cleared on stop**
    - **Validates: Requirements 12.6**
    - **Property 38: Agent complete raises SemanticError for unknown provider**
    - **Validates: Requirements 12.4**
    - **Property 39: LLM error fields are accessible**
    - **Validates: Requirements 15.2, 15.4**

  - [x] 16.8 Write unit tests for Agent LLM integration, plugin support, and retry/fallback
    - Test Agent.llm_providers property returns LlmProviderRegistry
    - Test Agent.cost_tracker property returns CostTracker
    - Test register_llm_provider and complete end-to-end with mock LlmProvider (using automojo.testbase.mocking.Mock)
    - Test complete with unknown provider raises SemanticError with provider name, model name, agent identity
    - Test complete records token usage and cost in CostTracker
    - Test retry behavior with mock provider that fails then succeeds
    - Test fallback behavior with mock providers
    - Test all providers fail raises LlmRequestError with summary
    - Test plugin discovery with mocked ExtensionPoint
    - Test plugin load failure logging (WARNING level)
    - Test plugin name-model conflict logging and skip
    - Test LlmProviderRegistry cleared after Agent.stop()
    - Test credential resolution success and failure (mock automojo-credentials)
    - Test credential values not in serialization output
    - Test logging output at correct levels (INFO begin/success, WARNING failure/fallback)
    - Create test file at `source/testroots/automojo/tests/singlehost/agentkit/test_agent_llm_integration.py`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 13.1, 13.2, 13.3, 13.4, 14.1, 14.2, 14.3, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [x] 17. Verify string representations and credential exclusion across all LLM classes
  - [x] 17.1 Verify and complete all `__repr__` and `__str__` methods across all LLM system classes
    - Ensure LlmProvider, LlmMessage, LlmConversation, LlmResponse, TokenUsage, CostEstimate, PromptTemplate, RetryPolicy, LlmProviderRegistry, LlmStreamChunk, LlmRequestError, LlmResponseParsingError all have correct repr/str per design
    - _Requirements: 1.10, 1.11, 6.7, 6.8, 15.5, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10, 19.11, 19.12, 19.13, 19.14, 19.15, 19.16, 19.17, 19.18_

  - [x] 17.2 Write property tests for string representations and credential exclusion (Properties 40, 41)
    - **Property 40: LLM string representations contain required information**
    - **Validates: Requirements 1.10, 1.11, 6.7, 6.8, 15.5, 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10, 19.11, 19.12, 19.13, 19.14, 19.15, 19.16, 19.17, 19.18**
    - **Property 41: Credential values excluded from serialization and string output**
    - **Validates: Requirements 14.3**

- [x] 18. Wire package exports and final integration
  - [x] 18.1 Update `source/packages/automojo/agentkit/__init__.py` to export all LLM system classes
    - Export LlmProvider, LlmMessage, LlmConversation, LlmResponse, LlmStreamChunk, LlmStreamHandler
    - Export TokenUsage, CostEstimate, CostTracker
    - Export PromptTemplate, PromptTemplateRegistry
    - Export OutputParser, JsonOutputParser, RegexOutputParser, OutputSchema
    - Export LlmProviderRegistry, RetryPolicy, FallbackChain
    - Export LlmToolBridge
    - Export LlmRequestError, LlmResponseParsingError
    - _Requirements: 1.1, 2.1, 2.9, 3.1, 4.1, 5.1, 5.8, 6.1, 6.3, 7.1, 7.11, 8.1, 8.3, 8.5, 8.10, 9.1, 10.1, 10.8, 11.1, 15.1, 15.3_

- [x] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (41 total across Properties 1–41)
- Unit tests validate specific examples, edge cases, and integration with external packages
- All mocking uses `automojo.testbase.mocking.Mock` per project conventions
- Property-based tests use automojo.testbase.properties (built-in testbase property testing engine) with minimum 100 iterations per property
- Tests reside under `source/testroots/automojo/tests/singlehost/agentkit/` mirroring the source hierarchy
- Class filenames are all lowercase with no underscores per project naming conventions
- The LLM system integrates with Core Agent Framework, Tool & Capability System, automojo-extension, and automojo-credentials
