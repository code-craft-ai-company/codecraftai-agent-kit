# Implementation Plan: Memory & Context Management

## Overview

Incremental implementation of the Memory & Context Management feature for the `codecraftai-agent-kit` SDK. Tasks build bottom-up: error types and enumerations first, then foundational value objects (MemoryEntry, MemoryQuery, MemoryQueryResult, ExpirationPolicy), then internal indexing (MemoryIndex), then abstract base classes (EmbeddingProvider, MemoryStore), then concrete store implementations (InMemoryStore, FileMemoryStore), then registry (MemoryStoreRegistry), then context window system (ContextWindowStrategy, ContextSummarizer, ContextWindow), then configuration (MemoryConfiguration), then agent integration and plugin support. Each task references specific requirements. Tests are placed close to the code they validate.

## Tasks

- [x] 1. Implement memory error types and enumerations
  - [x] 1.1 Create `source/packages/ccai/agentkit/memoryerrors.py` with MemoryStoreError and ContextWindowError
    - MemoryStoreError inherits from AgentKitError, stores store_name, operation, cause
    - Format error message including store name, operation, and cause string
    - Provide `store_name`, `operation`, `cause` read-only properties and `__repr__`
    - ContextWindowError inherits from AgentKitError, stores max_tokens, strategy, error_message
    - Provide `max_tokens`, `strategy`, `error_message` read-only properties and `__repr__`
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

  - [x] 1.2 Create `source/packages/ccai/agentkit/memoryscope.py` with the MemoryScope enumeration
    - Define AGENT, SHARED, GLOBAL values
    - Implement `from_string` class method with case-insensitive matching
    - Raise SemanticError for invalid values listing valid options
    - Implement `__repr__` and `__str__`
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 1.3 Write unit tests for MemoryStoreError, ContextWindowError, and MemoryScope
    - Test MemoryStoreError fields (store_name, operation, cause) and repr
    - Test ContextWindowError fields (max_tokens, strategy, error_message) and repr
    - Test MemoryScope.from_string with valid values (case-insensitive)
    - Test MemoryScope.from_string raises SemanticError for invalid values
    - Test MemoryScope __repr__ and __str__
    - Create test files at `source/testroots/ccai/tests/singlehost/agentkit/test_memoryerrors.py` and `test_memoryscope.py`
    - _Requirements: 2.1, 2.5, 2.6, 16.1, 16.2, 16.3, 16.4, 16.5_

- [x] 2. Implement MemoryEntry and ExpirationPolicy value objects
  - [x] 2.1 Create `source/packages/ccai/agentkit/memoryentry.py` with the MemoryEntry class
    - Implement `__init__` with content, scope, optional identifier (auto UUID), optional embedding, optional metadata (default {}), optional tags (default []), optional created_at (default UTC now), optional expires_at
    - Implement all read-only properties returning defensive copies for mutable fields (embedding, metadata, tags)
    - Implement `is_expired(reference_time=None)` defaulting to current UTC time
    - Implement `as_dict(brief=False)`, `to_json()`, `from_dict(cls, data)`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, identifier, scope, truncated content), `__str__` (identifier, scope, tag count, truncated content), `__eq__`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 17.1, 17.2, 17.7, 19.1, 19.2_

  - [x] 2.2 Create `source/packages/ccai/agentkit/expirationpolicy.py` with the ExpirationPolicy class
    - Implement `__init__` with optional default_ttl (float, seconds) and cleanup_interval (float, default 300.0)
    - Implement `default_ttl` and `cleanup_interval` read-only properties
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, data)`, `from_json(cls, json_str)`
    - Implement `__repr__`, `__str__`, `__eq__`
    - _Requirements: 13.1, 13.2, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 19.17, 19.18_

  - [x] 2.3 Write property tests for MemoryEntry and ExpirationPolicy round-trip serialization
    - **Property 1: MemoryEntry JSON round-trip** — for all valid MemoryEntry instances, `MemoryEntry.from_json(entry.to_json())` produces an equivalent MemoryEntry
    - **Validates: Requirements 1.7, 1.8, 1.9, 1.10, 17.1, 17.2, 17.7**
    - **Property 2: ExpirationPolicy round-trip** — for all valid ExpirationPolicy instances, `ExpirationPolicy.from_dict(json.loads(policy.to_json()))` produces an equivalent ExpirationPolicy
    - **Validates: Requirements 13.7, 13.8, 13.9**

  - [x] 2.4 Write unit tests for MemoryEntry and ExpirationPolicy
    - Test MemoryEntry auto-generated UUID when identifier not provided
    - Test MemoryEntry auto-generated created_at when not provided
    - Test MemoryEntry read-only properties return defensive copies
    - Test MemoryEntry.is_expired with expired, non-expired, and no-expiration entries
    - Test MemoryEntry as_dict, to_json, from_dict, from_json
    - Test MemoryEntry __repr__, __str__, __eq__
    - Test ExpirationPolicy construction with and without default_ttl
    - Test ExpirationPolicy as_dict, to_json, from_dict, from_json
    - Test ExpirationPolicy __repr__, __str__, __eq__
    - Create test files at `source/testroots/ccai/tests/singlehost/agentkit/test_memoryentry.py` and `test_expirationpolicy.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 1.12, 13.1, 13.2, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 4. Implement MemoryQuery and MemoryQueryResult
  - [x] 4.1 Create `source/packages/ccai/agentkit/memoryquery.py` with the MemoryQuery class
    - Implement `__init__` with optional tags, metadata, scope, start_time, end_time, semantic_text, max_results, min_relevance
    - Implement all read-only properties returning defensive copies for mutable fields
    - Implement `as_dict()`, `to_json()`, `from_dict(cls, data)`, `from_json(cls, json_str)`
    - Implement `__repr__` (class name, summary of active filter criteria), `__str__` (human-readable criteria), `__eq__`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 17.3, 17.4, 17.8, 19.5, 19.6_

  - [x] 4.2 Create `source/packages/ccai/agentkit/memoryqueryresult.py` with the MemoryQueryResult class
    - Implement `__init__` with entries list, optional scores list, optional total_count (default len(entries))
    - Implement `entries`, `scores`, `total_count` read-only properties returning defensive copies
    - Implement `as_dict()` serializing entries via their as_dict method
    - Implement `__repr__` (class name, count), `__str__` (match count, top entry identifiers)
    - _Requirements: 4.11, 4.12, 4.13, 4.14, 4.15, 19.7, 19.8_

  - [x] 4.3 Write property tests for MemoryQuery round-trip serialization
    - **Property 3: MemoryQuery JSON round-trip** — for all valid MemoryQuery instances, `MemoryQuery.from_json(query.to_json())` produces an equivalent MemoryQuery
    - **Validates: Requirements 4.8, 17.3, 17.4, 17.8**

  - [x] 4.4 Write unit tests for MemoryQuery and MemoryQueryResult
    - Test MemoryQuery construction with various filter combinations
    - Test MemoryQuery read-only properties return defensive copies
    - Test MemoryQuery as_dict, to_json, from_dict, from_json
    - Test MemoryQuery __repr__, __str__, __eq__
    - Test MemoryQueryResult construction with and without scores
    - Test MemoryQueryResult default total_count equals len(entries)
    - Test MemoryQueryResult as_dict, __repr__, __str__
    - Create test files at `source/testroots/ccai/tests/singlehost/agentkit/test_memoryquery.py` and `test_memoryqueryresult.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10, 4.11, 4.12, 4.13, 4.14, 4.15_

- [x] 5. Implement MemoryIndex and EmbeddingProvider
  - [x] 5.1 Create `source/packages/ccai/agentkit/memoryindex.py` with the MemoryIndex class
    - Implement `__init__` initializing entries dict, tag_index dict, metadata_index dict
    - Implement `add(entry)` indexing by identifier, tags, and metadata key-value pairs
    - Implement `remove(identifier)` cleaning up all index references
    - Implement `clear()` resetting all indexes
    - Implement `contains(identifier)` and `get(identifier)` lookup methods
    - Implement `count` read-only property
    - Implement `search(query, query_embedding=None)` applying tag, metadata, scope, time range filters and cosine similarity ranking
    - Implement `_cosine_similarity(vec_a, vec_b)` static method
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.2, 5.3_

  - [x] 5.2 Create `source/packages/ccai/agentkit/embeddingprovider.py` with the EmbeddingProvider abstract base class
    - Implement `__init__` with provider_name, embedding_dimension, optional credential_names
    - Validate provider_name is non-empty and embedding_dimension is positive, raise SemanticError
    - Implement `provider_name`, `embedding_dimension`, `credential_names` read-only properties
    - Define abstract `embed(text)` and `embed_batch(texts)` methods
    - Implement `__repr__` and `__str__`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

  - [x] 5.3 Write unit tests for MemoryIndex and EmbeddingProvider
    - Test MemoryIndex add, remove, clear, contains, get, count
    - Test MemoryIndex search with tag filters (AND logic)
    - Test MemoryIndex search with metadata filters (AND logic)
    - Test MemoryIndex search with scope filter
    - Test MemoryIndex search with time range filter
    - Test MemoryIndex search with cosine similarity ranking and min_relevance threshold
    - Test MemoryIndex search with max_results limit
    - Test MemoryIndex _cosine_similarity with known vectors
    - Test EmbeddingProvider construction validation (empty name, non-positive dimension)
    - Test EmbeddingProvider __repr__ and __str__
    - Create test files at `source/testroots/ccai/tests/singlehost/agentkit/test_memoryindex.py` and `test_embeddingprovider.py`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5.2, 5.3, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 7. Implement MemoryStore abstract base class
  - [x] 7.1 Create `source/packages/ccai/agentkit/memorystore.py` with the MemoryStore abstract base class
    - Implement `__init__` with store_name, optional embedding_provider, optional expiration_policy, optional credential_names
    - Validate store_name is non-empty, raise SemanticError
    - Implement `store_name`, `embedding_provider`, `expiration_policy` read-only properties
    - Define abstract `count` property and abstract `store`, `retrieve`, `search`, `update`, `delete`, `clear` methods
    - Implement `contains(identifier)` using retrieve
    - Implement `cleanup_expired(reference_time=None)` iterating all entries and deleting expired ones, returning removed count
    - Implement `_generate_embedding_if_needed(entry)` creating new MemoryEntry with embedding when provider is configured and entry lacks embedding
    - Implement `_apply_expiration_policy(entry)` creating new MemoryEntry with expires_at when policy defines default_ttl and entry lacks expiration
    - Implement `__repr__` and `__str__`
    - Use logger `ccai.agentkit.memory` for structured logging
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 13.3, 13.4, 13.5, 18.5, 19.3, 19.4_

  - [x] 7.2 Write unit tests for MemoryStore base class
    - Test MemoryStore construction validation (empty name raises SemanticError)
    - Test MemoryStore contains delegates to retrieve
    - Test MemoryStore _generate_embedding_if_needed with and without provider
    - Test MemoryStore _apply_expiration_policy with and without policy/TTL
    - Test MemoryStore cleanup_expired removes expired entries and returns count
    - Test MemoryStore __repr__ and __str__
    - Use a concrete test subclass that implements abstract methods with simple in-memory storage
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_memorystore.py`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 13.3, 13.4, 13.5_

- [x] 8. Implement InMemoryStore
  - [x] 8.1 Create `source/packages/ccai/agentkit/inmemorystore.py` with the InMemoryStore class
    - Extend MemoryStore, initialize with MemoryIndex
    - Implement `count` property delegating to index
    - Implement `store(entry)` — check duplicate identifier (raise SemanticError), apply expiration policy, generate embedding if needed, add to index, log at INFO
    - Implement `retrieve(identifier)` delegating to index get
    - Implement `search(query)` — generate query embedding if semantic_text present (raise MemoryStoreError if no EmbeddingProvider), delegate to index search, log at INFO
    - Implement `update(identifier, entry)` — remove old, generate embedding, add new
    - Implement `delete(identifier)` — remove from index, log at INFO
    - Implement `clear()` — clear index
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 18.2, 18.3, 18.4_

  - [x] 8.2 Write property tests for InMemoryStore
    - **Property 4: InMemoryStore store-retrieve consistency** — for all valid MemoryEntry instances, storing an entry and then retrieving by identifier returns an equivalent entry
    - **Validates: Requirements 5.1, 5.2, 3.7**
    - **Property 5: InMemoryStore duplicate identifier rejection** — storing two entries with the same identifier raises SemanticError
    - **Validates: Requirements 5.6**

  - [x] 8.3 Write unit tests for InMemoryStore
    - Test store, retrieve, search, update, delete, clear operations
    - Test store with duplicate identifier raises SemanticError
    - Test search with tag, metadata, scope, time range filters
    - Test search with semantic text raises MemoryStoreError when no EmbeddingProvider
    - Test search with semantic text and mock EmbeddingProvider returns ranked results
    - Test store auto-generates embedding when EmbeddingProvider configured
    - Test store applies ExpirationPolicy default TTL
    - Test cleanup_expired removes expired entries
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_inmemorystore.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 13.3, 13.4, 13.5_

- [x] 9. Implement FileMemoryStore
  - [x] 9.1 Create `source/packages/ccai/agentkit/filememorystore.py` with the FileMemoryStore class
    - Extend MemoryStore, accept directory_path, initialize MemoryIndex
    - Create directory if it does not exist at construction time
    - Implement `_load_existing_entries()` loading all .json files from directory into index, raising MemoryStoreError on I/O failure
    - Implement `_entry_filepath(identifier)`, `_write_entry_file(entry)`, `_delete_entry_file(identifier)` helper methods
    - Implement `store(entry)` — check duplicate, apply expiration policy, generate embedding, write file, add to index, log at INFO
    - Implement `retrieve(identifier)` delegating to index
    - Implement `search(query)` with semantic support, log at INFO
    - Implement `update(identifier, entry)` — delete old file, remove from index, generate embedding, write new file, add to index
    - Implement `delete(identifier)` — delete file, remove from index, log at INFO
    - Implement `clear()` — delete all files, clear index
    - Raise MemoryStoreError with file path and I/O error detail on failures
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 18.2, 18.3, 18.4_

  - [x] 9.2 Write property tests for FileMemoryStore
    - **Property 6: FileMemoryStore JSON file round-trip** — for all valid MemoryEntry instances, storing an entry and constructing a new FileMemoryStore from the same directory loads an equivalent entry
    - **Validates: Requirements 6.3, 6.4, 6.7**

  - [x] 9.3 Write unit tests for FileMemoryStore
    - Test store creates JSON file in directory
    - Test retrieve returns stored entry
    - Test constructor loads existing entries from directory
    - Test constructor creates directory if missing
    - Test store with duplicate identifier raises SemanticError
    - Test delete removes JSON file
    - Test clear removes all JSON files
    - Test I/O failure raises MemoryStoreError with file path
    - Use temporary directories for test isolation
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_filememorystore.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 11. Implement MemoryStoreRegistry
  - [x] 11.1 Create `source/packages/ccai/agentkit/memorystoreregistry.py` with the MemoryStoreRegistry class
    - Implement `__init__` initializing empty stores dict
    - Implement `register(store)` using store_name as key, raise SemanticError on duplicate name
    - Implement `deregister(name)` removing by name
    - Implement `lookup(name)` returning MemoryStore or None
    - Implement `list_all()` returning list of all registered stores
    - Implement `count` read-only property and `has_store(name)` method
    - Implement `clear()` removing all stores
    - Implement `__repr__` and `__str__`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 19.9, 19.10_

  - [x] 11.2 Write unit tests for MemoryStoreRegistry
    - Test register, deregister, lookup, list_all, count, has_store, clear
    - Test register with duplicate name raises SemanticError
    - Test lookup returns None for unknown name
    - Test __repr__ and __str__
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_memorystoreregistry.py`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9_

- [x] 12. Implement ContextWindowStrategy and ContextSummarizer
  - [x] 12.1 Create `source/packages/ccai/agentkit/contextwindowstrategy.py` with the ContextWindowStrategy enumeration
    - Define FIFO, RELEVANCE, SUMMARIZE values
    - Implement `from_string` class method with case-insensitive matching
    - Raise SemanticError for invalid values listing valid options
    - Implement `__repr__` and `__str__`
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 12.2 Create `source/packages/ccai/agentkit/contextsummarizer.py` with the ContextSummarizer class
    - Implement `__init__` with llm_provider and optional max_summary_tokens
    - Implement `llm_provider` and `max_summary_tokens` read-only properties
    - Implement `summarize_messages(messages)` — raise SemanticError if empty, build summary prompt, call llm_provider.complete, return LlmMessage with summary, raise ContextWindowError on LLM failure, log at INFO
    - Implement `summarize_entries(entries)` — raise SemanticError if empty, build summary prompt, call llm_provider.complete, return LlmMessage with summary, raise ContextWindowError on LLM failure, log at INFO
    - Implement `__repr__` and `__str__`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 18.8, 19.13, 19.14_

  - [x] 12.3 Write unit tests for ContextWindowStrategy and ContextSummarizer
    - Test ContextWindowStrategy.from_string with valid values
    - Test ContextWindowStrategy.from_string raises SemanticError for invalid values
    - Test ContextSummarizer.summarize_messages with mock LlmProvider
    - Test ContextSummarizer.summarize_messages raises SemanticError for empty input
    - Test ContextSummarizer.summarize_messages raises ContextWindowError on LLM failure
    - Test ContextSummarizer.summarize_entries with mock LlmProvider
    - Test ContextSummarizer.summarize_entries raises SemanticError for empty input
    - Test ContextSummarizer __repr__ and __str__
    - Create test files at `source/testroots/ccai/tests/singlehost/agentkit/test_contextwindowstrategy.py` and `test_contextsummarizer.py`
    - _Requirements: 9.1, 9.2, 9.3, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8_

- [x] 13. Implement ContextWindow
  - [x] 13.1 Create `source/packages/ccai/agentkit/contextwindow.py` with the ContextWindow class
    - Implement `__init__` with max_tokens, strategy, token_counter callable, optional summarizer
    - Validate max_tokens > 0 and token_counter is not None, raise SemanticError
    - Implement `max_tokens` and `strategy` read-only properties
    - Implement `build(conversation, memory_entries=None)` — prepend memory entries as system messages, count tokens, apply strategy if over limit, raise ContextWindowError if still over limit after trimming, log at INFO
    - Implement `_count_messages_tokens(messages)` summing token_counter over message contents
    - Implement `_apply_fifo(messages)` — separate system/non-system, remove oldest non-system first
    - Implement `_apply_relevance(messages, memory_entries)` — separate memory messages from other system messages, remove least relevant memory messages first
    - Implement `_apply_summarize(messages)` — raise ContextWindowError if no summarizer, split non-system messages at midpoint, summarize older half
    - Implement `__repr__` and `__str__`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12, 18.7, 19.11, 19.12_

  - [x] 13.2 Write property tests for ContextWindow
    - **Property 7: ContextWindow build output fits within token limit** — for all valid conversations and max_tokens, the output of build has total tokens <= max_tokens (when build does not raise ContextWindowError)
    - **Validates: Requirements 8.3, 8.4**
    - **Property 8: ContextWindow FIFO preserves system messages** — for all conversations with system messages, applying FIFO strategy never removes system messages
    - **Validates: Requirements 8.5, 8.10**

  - [x] 13.3 Write unit tests for ContextWindow
    - Test build with conversation fitting within limit returns unchanged
    - Test build with FIFO strategy removes oldest non-system messages
    - Test build with RELEVANCE strategy removes least relevant memory entries
    - Test build with SUMMARIZE strategy calls summarizer and replaces older messages
    - Test build raises ContextWindowError when cannot fit after trimming
    - Test build preserves system message order
    - Test build prepends memory entries as system messages
    - Test construction validation (max_tokens <= 0, None token_counter)
    - Test SUMMARIZE without summarizer raises ContextWindowError
    - Test __repr__ and __str__
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_contextwindow.py`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 8.10, 8.11, 8.12_

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 15. Implement MemoryConfiguration
  - [x] 15.1 Create `source/packages/ccai/agentkit/memoryconfiguration.py` with the MemoryConfiguration class
    - Implement `__init__` with backend_type, optional connection_params, optional default_scope (default AGENT), optional expiration_policy, optional embedding_settings, optional credential_names
    - Implement all read-only properties returning defensive copies for mutable fields
    - Implement `as_dict()` excluding resolved credential values, `to_json()`
    - Implement `from_dict(cls, data)` validating backend_type is present (raise ConfigurationError), parsing default_scope and expiration_policy
    - Implement `from_json(cls, json_str)`, `from_json_file(cls, file_path)`, `from_yaml_file(cls, file_path)`
    - Raise ConfigurationError for missing required fields, invalid backend type, unresolvable credentials, and file I/O failures
    - Implement `__repr__`, `__str__`, `__eq__`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11, 12.12, 12.13, 12.14, 12.15, 12.16, 17.5, 17.6, 17.9, 19.15, 19.16_

  - [x] 15.2 Write property tests for MemoryConfiguration round-trip serialization
    - **Property 9: MemoryConfiguration JSON round-trip** — for all valid MemoryConfiguration instances, `MemoryConfiguration.from_json(config.to_json())` produces an equivalent MemoryConfiguration
    - **Validates: Requirements 12.10, 12.11, 12.12, 12.13, 12.14, 17.5, 17.6, 17.9**

  - [x] 15.3 Write unit tests for MemoryConfiguration
    - Test construction with all parameters
    - Test from_dict raises ConfigurationError when backend_type missing
    - Test from_dict parses default_scope and expiration_policy
    - Test from_json and to_json round-trip
    - Test from_json_file with valid JSON file
    - Test from_yaml_file with valid YAML file
    - Test from_json_file raises ConfigurationError on missing file
    - Test as_dict excludes resolved credential values
    - Test __repr__, __str__, __eq__
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_memoryconfiguration.py`
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11, 12.12, 12.13, 12.14, 12.15, 12.16_

- [x] 16. Implement Agent memory integration
  - [x] 16.1 Extend the Agent base class with memory properties and methods
    - Add `_memory_store`, `_memory_store_registry`, `_context_window`, `_memory_configuration` instance attributes
    - Implement `memory` read-only property returning the primary MemoryStore
    - Implement `memory_stores` read-only property returning the MemoryStoreRegistry
    - Implement `context_window` read-only property returning the ContextWindow
    - Implement `register_memory_store(store)` delegating to registry
    - Implement `store_memory(content, metadata=None, tags=None, scope=None)` creating a MemoryEntry and storing in primary store
    - Implement `search_memory(query)` delegating to primary store search
    - Implement `build_context(conversation, memory_query=None)` — if query provided, search memory and pass entries to context_window.build
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x] 16.2 Wire memory initialization into Agent lifecycle
    - On INITIALIZED state transition: construct MemoryStore and ContextWindow from MemoryConfiguration
    - On INITIALIZED state transition: discover and register MemoryBackendPlugin instances from ExtensionPoint
    - On STOPPED state transition: clear MemoryStoreRegistry
    - Default to InMemoryStore with MemoryScope.AGENT and no expiration when MemoryConfiguration is not provided
    - _Requirements: 14.8, 14.9, 14.10, 14.11_

  - [x] 16.3 Write unit tests for Agent memory integration
    - Test Agent.memory returns primary MemoryStore
    - Test Agent.memory_stores returns MemoryStoreRegistry
    - Test Agent.context_window returns ContextWindow
    - Test Agent.register_memory_store adds to registry
    - Test Agent.store_memory creates and stores MemoryEntry
    - Test Agent.search_memory delegates to primary store
    - Test Agent.build_context with and without memory query
    - Test Agent defaults to InMemoryStore when no MemoryConfiguration
    - Test Agent INITIALIZED state constructs memory system from config
    - Test Agent STOPPED state clears registry
    - Use mock MemoryStore, ContextWindow, and LlmProvider
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_agent_memory.py`
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10, 14.11_

- [x] 17. Implement memory backend plugin integration
  - [x] 17.1 Define the `ccai.agentkit.memory_backends` ExtensionPoint
    - Register the extension point name for memory backend plugin discovery
    - Implement plugin loading during Agent initialization: query extension point, register discovered stores
    - Log WARNING on plugin load failure (include plugin name and error detail), continue loading remaining plugins
    - Log WARNING on store name conflict, skip conflicting plugin store
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 17.2 Write unit tests for memory backend plugin integration
    - Test extension point discovery registers plugin stores
    - Test plugin load failure logs WARNING and continues
    - Test store name conflict logs WARNING and skips
    - Use mock ExtensionPoint and mock MemoryStore plugins
    - Create test file at `source/testroots/ccai/tests/singlehost/agentkit/test_memory_plugins.py`
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

- [x] 18. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (round-trip serialization, store-retrieve consistency)
- Unit tests validate specific examples, edge cases, and error conditions
- All test files use the testbase framework (not pytest or unittest)
- All mocking uses testbase mocking (not unittest.mock)
- Property-based tests use ccai.testbase.properties (built-in testbase property testing engine)
- Class filenames are all lowercase with no underscores per project conventions
- Test file hierarchy mirrors source hierarchy under `source/testroots/ccai/tests/singlehost/agentkit/`
