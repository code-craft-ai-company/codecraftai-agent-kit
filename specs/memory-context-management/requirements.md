# Requirements Document — Memory & Context Management

## Introduction

The Memory & Context Management feature extends the `codecraftai-agent-kit` SDK with a unified system for storing, retrieving, and managing agent memory across short-term and long-term horizons. It defines a memory entry abstraction with metadata and tags, pluggable memory backends (in-memory, file-based, vector store, database), memory scoping (per-agent, shared, global), semantic similarity-based retrieval, context window management for fitting conversation history within LLM token limits, and memory lifecycle management (creation, update, expiration, cleanup). The system integrates with the Agent base class so agents own and manage memory stores, with the LLM Integration system so context window management feeds into LLM conversations, with `codecraftai-extension` so memory backend plugins can be discovered and loaded, with `codecraftai-credentials` for backend authentication, with `codecraftai-dataprofiles` for data profile management, and with `codecraftai-this-app` for settings and environment configuration.

## Glossary

- **MemoryEntry**: An immutable object representing a single unit of stored memory, containing a unique identifier, content string, optional embedding vector, metadata dictionary, tags list, creation timestamp, expiration timestamp, and memory scope.
- **MemoryStore**: An abstract base class representing a storage backend for MemoryEntry objects. A MemoryStore provides methods for storing, retrieving, searching, updating, and deleting memory entries. Concrete implementations wrap specific backends (in-memory, file-based, vector store, database).
- **MemoryStoreRegistry**: A registry that tracks all available MemoryStore instances within a runtime, providing lookup by name, scope, and enumeration.
- **MemoryScope**: An enumeration defining the visibility scope of a MemoryEntry: AGENT (visible only to the owning agent), SHARED (visible to a defined group of agents), and GLOBAL (visible to all agents in the runtime).
- **MemoryQuery**: An immutable object representing a search request against a MemoryStore, containing optional filter criteria (tags, metadata, scope, time range) and optional semantic query text for similarity-based retrieval.
- **MemoryQueryResult**: An immutable object encapsulating the result of a MemoryQuery, containing the list of matching MemoryEntry objects, optional relevance scores, and the total count of matches.
- **MemoryIndex**: A component that maintains a searchable index over MemoryEntry objects within a MemoryStore, supporting tag-based filtering, metadata filtering, and semantic similarity search when embeddings are available.
- **EmbeddingProvider**: An abstract base class for generating embedding vectors from text content. Concrete implementations wrap specific embedding services or local models. The EmbeddingProvider is used by MemoryStore implementations that support semantic search.
- **ContextWindow**: A component that manages the selection and arrangement of memory entries and conversation messages to fit within an LLM provider's token limit. The ContextWindow produces a trimmed LlmConversation suitable for completion requests.
- **ContextWindowStrategy**: An enumeration defining the strategy for trimming context to fit within token limits: FIFO (remove oldest non-system messages first), RELEVANCE (remove least relevant entries first based on similarity scores), and SUMMARIZE (summarize older entries to reduce token count).
- **ContextSummarizer**: A component that accepts a list of LlmMessage objects or MemoryEntry objects and produces a condensed summary, reducing token count while preserving key information. The ContextSummarizer uses an LlmProvider to generate summaries.
- **MemoryBackendPlugin**: A MemoryStore implementation discovered and loaded through the `codecraftai-extension` ExtensionPoint mechanism, allowing external packages to contribute memory backends.
- **InMemoryStore**: A built-in MemoryStore implementation that stores MemoryEntry objects in process memory using dictionary-based indexing. Suitable for development, testing, and short-lived agents.
- **FileMemoryStore**: A built-in MemoryStore implementation that persists MemoryEntry objects to JSON files on the local file system. Suitable for single-agent local deployments.
- **MemoryConfiguration**: A configuration object that defines the memory backend type, backend-specific connection parameters, default memory scope, expiration policies, and embedding provider settings for an Agent's memory system.
- **ExpirationPolicy**: A configuration object defining how expired MemoryEntry objects are handled, including the default time-to-live duration and the cleanup interval.
- **Agent**: The base agent class defined in the Core Agent Framework that owns a MemoryStore and uses the ContextWindow for LLM interactions.
- **LlmProvider**: The LLM provider abstraction defined in the LLM Integration feature, used by the ContextSummarizer to generate summaries and by the EmbeddingProvider for embedding generation.
- **LlmConversation**: The conversation object defined in the LLM Integration feature that the ContextWindow produces as output.
- **LlmMessage**: The message object defined in the LLM Integration feature used within conversations and context windows.
- **TokenUsage**: The token usage object defined in the LLM Integration feature, used by the ContextWindow to track token consumption.
- **ExtensionPoint**: An integration surface provided by `codecraftai-extension` that allows external plugins to register MemoryStore implementations with an Agent.
- **CredentialReference**: A named reference resolved through `codecraftai-credentials` that provides secure access to secrets required by a MemoryStore backend (database passwords, API keys for vector store services).
- **ConfigurationError**: An exception raised for configuration-related problems, inherited from AgentKitError.
- **SemanticError**: An exception raised for API misuse, inherited from AgentKitError.
- **MemoryStoreError**: An exception raised when a MemoryStore operation fails due to a backend error (connection failure, write error, query error).
- **ContextWindowError**: An exception raised when the ContextWindow cannot produce a valid context within the configured token limit.

## Requirements

### Requirement 1: Memory Entry Definition

**User Story:** As a developer, I want a well-defined memory entry object with content, metadata, and tags, so that I can store and retrieve structured pieces of agent memory with rich context.

#### Acceptance Criteria

1. THE MemoryEntry SHALL contain a unique string identifier, a content string, an optional embedding vector as a list of floats, a metadata dictionary, a tags list of strings, a creation timestamp, an optional expiration timestamp, and a MemoryScope value.
2. WHEN a MemoryEntry is created without an explicit unique identifier, THE MemoryEntry SHALL generate a UUID-based identifier automatically.
3. WHEN a MemoryEntry is created without an explicit creation timestamp, THE MemoryEntry SHALL set the creation timestamp to the current UTC time.
4. THE MemoryEntry SHALL expose all fields as read-only properties.
5. THE MemoryEntry SHALL provide an is_expired method that accepts an optional reference timestamp and returns True when the expiration timestamp is set and the reference timestamp exceeds the expiration timestamp, defaulting to the current UTC time when no reference timestamp is provided.
6. THE MemoryEntry SHALL provide an as_dict method that returns a dictionary representation of the entry fields.
7. THE MemoryEntry SHALL provide a to_json method that returns a JSON string representation of the entry fields.
8. THE MemoryEntry SHALL provide a class method from_dict that constructs a MemoryEntry from a dictionary.
9. THE MemoryEntry SHALL provide a class method from_json that deserializes a JSON string into a MemoryEntry instance.
10. FOR ALL valid MemoryEntry instances, calling to_json and then from_json SHALL produce an equivalent MemoryEntry object (round-trip property).
11. THE MemoryEntry SHALL provide a __repr__ method that includes the class name, identifier, scope, and a truncated content preview.
12. THE MemoryEntry SHALL provide a __str__ method that returns a human-readable summary including the identifier, scope, tag count, and a truncated content preview.

### Requirement 2: Memory Scope

**User Story:** As a developer, I want to scope memory entries to individual agents, groups of agents, or the entire runtime, so that I can control memory visibility and sharing across agents.

#### Acceptance Criteria

1. THE MemoryScope enumeration SHALL define the values AGENT, SHARED, and GLOBAL.
2. WHEN a MemoryEntry is created with MemoryScope.AGENT, THE MemoryEntry SHALL be visible only to the agent that owns the MemoryStore where the entry is stored.
3. WHEN a MemoryEntry is created with MemoryScope.SHARED, THE MemoryEntry SHALL be visible to all agents that reference the same MemoryStore instance.
4. WHEN a MemoryEntry is created with MemoryScope.GLOBAL, THE MemoryEntry SHALL be visible to all agents in the runtime through any MemoryStore that participates in global scope resolution.
5. THE MemoryScope enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding MemoryScope member.
6. IF an invalid string value is provided to the from_string method, THEN THE MemoryScope SHALL raise a SemanticError identifying the invalid value and listing the valid scope values.

### Requirement 3: Memory Store Abstraction

**User Story:** As a developer, I want a pluggable memory store abstraction with a common interface, so that I can swap memory backends without changing agent code.

#### Acceptance Criteria

1. THE MemoryStore base class SHALL define an abstract interface that includes methods for store (add a MemoryEntry), retrieve (get a MemoryEntry by identifier), search (execute a MemoryQuery), update (replace a MemoryEntry by identifier), delete (remove a MemoryEntry by identifier), and clear (remove all entries).
2. THE MemoryStore base class SHALL require all subclasses to provide an implementation for the store, retrieve, search, update, delete, and clear methods.
3. THE MemoryStore base class SHALL expose a read-only property for the store name as a string.
4. THE MemoryStore base class SHALL expose a read-only property for the count of stored MemoryEntry objects.
5. THE MemoryStore base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the backend requires.
6. THE MemoryStore base class SHALL accept an optional EmbeddingProvider instance at construction time for generating embeddings during store operations.
7. WHEN a MemoryStore is constructed with an EmbeddingProvider and a MemoryEntry is stored without an embedding vector, THE MemoryStore SHALL generate an embedding vector from the entry content using the EmbeddingProvider before storing the entry.
8. THE MemoryStore base class SHALL provide a contains method that accepts a MemoryEntry identifier and returns a boolean indicating whether an entry with the given identifier exists.
9. THE MemoryStore base class SHALL provide a __repr__ method that includes the class name, store name, and entry count.
10. THE MemoryStore base class SHALL provide a __str__ method that returns a human-readable summary including the store name and entry count.

### Requirement 4: Memory Query and Search

**User Story:** As a developer, I want to search memory entries by tags, metadata, scope, time range, and semantic similarity, so that I can retrieve relevant context for agent decision-making.

#### Acceptance Criteria

1. THE MemoryQuery SHALL support filtering by a list of required tags, where a matching entry must contain all specified tags.
2. THE MemoryQuery SHALL support filtering by metadata key-value pairs, where a matching entry must contain all specified metadata key-value pairs.
3. THE MemoryQuery SHALL support filtering by MemoryScope value.
4. THE MemoryQuery SHALL support filtering by a time range defined by an optional start timestamp and an optional end timestamp, matching entries whose creation timestamp falls within the range.
5. THE MemoryQuery SHALL support an optional semantic query text string for similarity-based retrieval.
6. THE MemoryQuery SHALL support an optional max_results integer to limit the number of returned entries.
7. THE MemoryQuery SHALL support an optional min_relevance float threshold for filtering similarity search results, where entries with a relevance score below the threshold are excluded.
8. THE MemoryQuery SHALL provide an as_dict method that returns a dictionary representation of the query fields.
9. THE MemoryQuery SHALL provide a __repr__ method that includes the class name and a summary of active filter criteria.
10. THE MemoryQuery SHALL provide a __str__ method that returns a human-readable summary of the query criteria.
11. THE MemoryQueryResult SHALL contain the list of matching MemoryEntry objects, an optional list of relevance scores as floats corresponding to each entry, and the total count of matches.
12. THE MemoryQueryResult SHALL expose all fields as read-only properties.
13. THE MemoryQueryResult SHALL provide an as_dict method that returns a dictionary representation of the result fields.
14. THE MemoryQueryResult SHALL provide a __repr__ method that includes the class name and the count of matching entries.
15. THE MemoryQueryResult SHALL provide a __str__ method that returns a human-readable summary including the match count and top entry identifiers.

### Requirement 5: In-Memory Store Implementation

**User Story:** As a developer, I want a built-in in-memory store for development and testing, so that I can use the memory system without configuring external backends.

#### Acceptance Criteria

1. THE InMemoryStore SHALL implement the MemoryStore interface using in-process dictionary-based storage.
2. WHEN a MemoryEntry is stored, THE InMemoryStore SHALL index the entry by identifier, tags, and metadata keys for efficient retrieval.
3. WHEN a MemoryQuery includes semantic query text and the stored entries have embedding vectors, THE InMemoryStore SHALL compute cosine similarity between the query embedding and stored entry embeddings and rank results by descending similarity score.
4. WHEN a MemoryQuery includes semantic query text and no EmbeddingProvider is configured, THE InMemoryStore SHALL raise a MemoryStoreError indicating that semantic search requires an EmbeddingProvider.
5. THE InMemoryStore SHALL support the clear method by removing all stored entries and resetting the index.
6. IF a MemoryEntry with a duplicate identifier is stored, THEN THE InMemoryStore SHALL raise a SemanticError that includes the duplicate identifier.

### Requirement 6: File-Based Memory Store Implementation

**User Story:** As a developer, I want a built-in file-based memory store for local persistence, so that agent memory survives process restarts without requiring a database.

#### Acceptance Criteria

1. THE FileMemoryStore SHALL implement the MemoryStore interface using JSON file persistence on the local file system.
2. THE FileMemoryStore SHALL accept a directory path at construction time specifying where memory files are stored.
3. WHEN a MemoryEntry is stored, THE FileMemoryStore SHALL persist the entry as a JSON file within the configured directory, using the entry identifier as the file name.
4. WHEN the FileMemoryStore is constructed, THE FileMemoryStore SHALL load all existing MemoryEntry JSON files from the configured directory into an in-memory index.
5. IF the configured directory does not exist, THEN THE FileMemoryStore SHALL create the directory at construction time.
6. IF a file read or write operation fails, THEN THE FileMemoryStore SHALL raise a MemoryStoreError that includes the file path and the underlying I/O error detail.
7. FOR ALL MemoryEntry objects stored in the FileMemoryStore, writing the entry to a JSON file and then reading the JSON file back SHALL produce an equivalent MemoryEntry object (round-trip property).
8. THE FileMemoryStore SHALL resolve the directory path relative to the AppContext directory provided by `codecraftai-this-app`.

### Requirement 7: Embedding Provider Abstraction

**User Story:** As a developer, I want a pluggable embedding provider for generating vector representations of text, so that memory stores can support semantic similarity search.

#### Acceptance Criteria

1. THE EmbeddingProvider base class SHALL define an abstract interface that includes a method embed that accepts a text string and returns an embedding vector as a list of floats.
2. THE EmbeddingProvider base class SHALL define an abstract method embed_batch that accepts a list of text strings and returns a list of embedding vectors.
3. THE EmbeddingProvider base class SHALL require all subclasses to provide an implementation for the embed and embed_batch methods.
4. THE EmbeddingProvider base class SHALL expose a read-only property for the provider name as a string.
5. THE EmbeddingProvider base class SHALL expose a read-only property for the embedding dimension as an integer, representing the length of the output embedding vectors.
6. THE EmbeddingProvider base class SHALL accept an optional list of CredentialReference names at construction time, declaring which credentials the provider requires.
7. IF the embed method receives an empty string, THEN THE EmbeddingProvider SHALL raise a SemanticError indicating that empty text cannot be embedded.
8. THE EmbeddingProvider base class SHALL provide a __repr__ method that includes the class name, provider name, and embedding dimension.
9. THE EmbeddingProvider base class SHALL provide a __str__ method that returns a human-readable summary including the provider name and embedding dimension.

### Requirement 8: Context Window Management

**User Story:** As a developer, I want a context window manager that selects and arranges memory entries and conversation messages to fit within an LLM token limit, so that agents can make optimal use of the available context window.

#### Acceptance Criteria

1. THE ContextWindow SHALL accept a maximum token count as an integer at construction time, representing the LLM provider's context window size.
2. THE ContextWindow SHALL accept a ContextWindowStrategy at construction time, defining how content is trimmed when the token limit is exceeded.
3. THE ContextWindow SHALL provide a build method that accepts an LlmConversation and an optional list of MemoryEntry objects and returns a new LlmConversation that fits within the configured maximum token count.
4. WHEN the total token count of the conversation and memory entries exceeds the maximum, THE ContextWindow SHALL apply the configured ContextWindowStrategy to reduce the content.
5. WHEN the ContextWindowStrategy is FIFO, THE ContextWindow SHALL remove the oldest non-system messages from the conversation first, preserving system messages and the most recent messages.
6. WHEN the ContextWindowStrategy is RELEVANCE, THE ContextWindow SHALL remove the least relevant memory entries first based on relevance scores, preserving system messages and the most recent conversation messages.
7. WHEN the ContextWindowStrategy is SUMMARIZE, THE ContextWindow SHALL use a ContextSummarizer to condense older messages into a summary message, replacing the original messages with the summary.
8. THE ContextWindow SHALL accept a token counting callable at construction time that accepts a string and returns the token count as an integer, allowing provider-specific tokenization.
9. IF the ContextWindow cannot produce a valid context within the maximum token count after applying the strategy, THEN THE ContextWindow SHALL raise a ContextWindowError that includes the maximum token count and the minimum required token count.
10. THE ContextWindow SHALL preserve the order of system messages at the beginning of the resulting LlmConversation.
11. THE ContextWindow SHALL provide a __repr__ method that includes the class name, maximum token count, and strategy name.
12. THE ContextWindow SHALL provide a __str__ method that returns a human-readable summary including the maximum token count and strategy name.

### Requirement 9: Context Window Strategy

**User Story:** As a developer, I want to choose from multiple context trimming strategies, so that I can control how the context window is managed based on the agent's use case.

#### Acceptance Criteria

1. THE ContextWindowStrategy enumeration SHALL define the values FIFO, RELEVANCE, and SUMMARIZE.
2. THE ContextWindowStrategy enumeration SHALL provide a from_string class method that accepts a string value and returns the corresponding ContextWindowStrategy member.
3. IF an invalid string value is provided to the from_string method, THEN THE ContextWindowStrategy SHALL raise a SemanticError identifying the invalid value and listing the valid strategy values.

### Requirement 10: Context Summarizer

**User Story:** As a developer, I want a summarizer that condenses older conversation messages and memory entries into compact summaries, so that the context window retains key information while staying within token limits.

#### Acceptance Criteria

1. THE ContextSummarizer SHALL accept an LlmProvider instance at construction time for generating summaries.
2. THE ContextSummarizer SHALL provide a summarize_messages method that accepts a list of LlmMessage objects and returns a single LlmMessage containing a condensed summary of the input messages.
3. THE ContextSummarizer SHALL provide a summarize_entries method that accepts a list of MemoryEntry objects and returns a single LlmMessage containing a condensed summary of the entry contents.
4. THE ContextSummarizer SHALL accept an optional maximum summary token count at construction time, constraining the length of generated summaries.
5. WHEN the input list of messages or entries is empty, THE ContextSummarizer SHALL raise a SemanticError indicating that empty input cannot be summarized.
6. IF the LlmProvider request fails during summarization, THEN THE ContextSummarizer SHALL raise a ContextWindowError that includes the LlmProvider name and the underlying error detail.
7. THE ContextSummarizer SHALL provide a __repr__ method that includes the class name and the LlmProvider name.
8. THE ContextSummarizer SHALL provide a __str__ method that returns a human-readable summary including the LlmProvider name and maximum summary token count.

### Requirement 11: Memory Store Registry

**User Story:** As a developer, I want a registry that tracks available memory stores, so that I can discover and look up stores by name or scope.

#### Acceptance Criteria

1. THE MemoryStoreRegistry SHALL support registration of a MemoryStore instance using the store name as the registration key.
2. IF a MemoryStore with a duplicate name is registered, THEN THE MemoryStoreRegistry SHALL raise a SemanticError that includes the duplicate store name.
3. THE MemoryStoreRegistry SHALL support deregistration of a MemoryStore by name.
4. THE MemoryStoreRegistry SHALL support lookup of a registered MemoryStore by name, returning the MemoryStore instance or None when the name is not found.
5. THE MemoryStoreRegistry SHALL support enumeration of all registered MemoryStore instances as a list.
6. THE MemoryStoreRegistry SHALL expose a read-only property for the count of currently registered stores.
7. THE MemoryStoreRegistry SHALL provide a has_store method that accepts a store name and returns a boolean indicating whether a MemoryStore with the given name is registered.
8. THE MemoryStoreRegistry SHALL provide a __repr__ method that includes the class name and the count of registered stores.
9. THE MemoryStoreRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered store names.

### Requirement 12: Memory Configuration

**User Story:** As a developer, I want to configure the memory system declaratively, so that I can define memory backend type, connection parameters, scoping defaults, and expiration policies without modifying code.

#### Acceptance Criteria

1. THE MemoryConfiguration SHALL contain the backend type as a string, backend-specific connection parameters as a dictionary, the default MemoryScope, an ExpirationPolicy, and optional EmbeddingProvider settings as a dictionary.
2. THE MemoryConfiguration SHALL support loading configuration from a Python dictionary.
3. THE MemoryConfiguration SHALL support loading configuration from a JSON file path.
4. THE MemoryConfiguration SHALL support loading configuration from a YAML file path.
5. WHEN a configuration file path is provided, THE MemoryConfiguration SHALL resolve the file path relative to the AppContext directory provided by `codecraftai-this-app`.
6. THE MemoryConfiguration SHALL validate all required fields are present during loading and raise a ConfigurationError when required fields are missing.
7. IF an invalid backend type is provided, THEN THE MemoryConfiguration SHALL raise a ConfigurationError identifying the invalid backend type.
8. THE MemoryConfiguration SHALL support CredentialReference entries for backend authentication that are resolved through `codecraftai-credentials` at initialization time.
9. IF a CredentialReference cannot be resolved, THEN THE MemoryConfiguration SHALL raise a ConfigurationError that identifies the unresolvable credential name.
10. THE MemoryConfiguration SHALL provide an as_dict method that returns a dictionary representation of the configuration, excluding resolved credential values.
11. THE MemoryConfiguration SHALL provide a to_json method that returns a JSON string representation of the configuration, excluding resolved credential values.
12. THE MemoryConfiguration SHALL provide a class method from_dict that constructs a MemoryConfiguration from a dictionary.
13. THE MemoryConfiguration SHALL provide a class method from_json that deserializes a JSON string into a MemoryConfiguration instance.
14. FOR ALL valid MemoryConfiguration instances, calling to_json and then from_json SHALL produce an equivalent MemoryConfiguration object (round-trip property).
15. THE MemoryConfiguration SHALL provide a __repr__ method that includes the class name, backend type, and default scope.
16. THE MemoryConfiguration SHALL provide a __str__ method that returns a human-readable summary including the backend type, default scope, and expiration policy.

### Requirement 13: Expiration Policy and Memory Lifecycle

**User Story:** As a developer, I want to define expiration policies for memory entries and have expired entries cleaned up automatically, so that memory stores do not grow unbounded.

#### Acceptance Criteria

1. THE ExpirationPolicy SHALL contain a default time-to-live duration in seconds as an optional float, and a cleanup interval in seconds as a float.
2. THE ExpirationPolicy SHALL expose all fields as read-only properties.
3. WHEN a MemoryEntry is stored without an explicit expiration timestamp and the ExpirationPolicy defines a default time-to-live, THE MemoryStore SHALL set the entry expiration timestamp to the creation timestamp plus the default time-to-live duration.
4. THE MemoryStore base class SHALL provide a cleanup_expired method that removes all MemoryEntry objects whose expiration timestamp has passed.
5. WHEN the cleanup_expired method is called, THE MemoryStore SHALL return the count of removed entries as an integer.
6. THE ExpirationPolicy SHALL provide an as_dict method that returns a dictionary representation of the policy fields.
7. THE ExpirationPolicy SHALL provide a to_json method that returns a JSON string representation of the policy fields.
8. THE ExpirationPolicy SHALL provide a class method from_dict that constructs an ExpirationPolicy from a dictionary.
9. FOR ALL valid ExpirationPolicy instances, calling to_json and then from_dict on the parsed JSON SHALL produce an ExpirationPolicy with equivalent time-to-live and cleanup interval values.
10. THE ExpirationPolicy SHALL provide a __repr__ method that includes the class name, time-to-live, and cleanup interval.
11. THE ExpirationPolicy SHALL provide a __str__ method that returns a human-readable summary of the expiration settings.

### Requirement 14: Agent Memory Integration

**User Story:** As a developer, I want agents to own memory stores and use context windows through the agent interface, so that memory management is scoped to individual agents and integrated with the agent lifecycle.

#### Acceptance Criteria

1. THE Agent base class SHALL expose a read-only memory property that returns the Agent's primary MemoryStore instance.
2. THE Agent base class SHALL expose a read-only memory_stores property that returns the Agent's MemoryStoreRegistry instance.
3. THE Agent base class SHALL provide a register_memory_store method that accepts a MemoryStore instance and registers the MemoryStore with the Agent's MemoryStoreRegistry.
4. THE Agent base class SHALL provide a store_memory method that accepts content, optional metadata, optional tags, and optional scope, creates a MemoryEntry, and stores the entry in the Agent's primary MemoryStore, returning the MemoryEntry.
5. THE Agent base class SHALL provide a search_memory method that accepts a MemoryQuery and executes the query against the Agent's primary MemoryStore, returning a MemoryQueryResult.
6. THE Agent base class SHALL expose a read-only context_window property that returns the Agent's ContextWindow instance.
7. THE Agent base class SHALL provide a build_context method that accepts an LlmConversation and optional MemoryQuery, retrieves relevant memory entries using the query, and returns a trimmed LlmConversation produced by the ContextWindow.
8. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL construct the MemoryStore and ContextWindow from the Agent's MemoryConfiguration.
9. WHEN an Agent transitions to the INITIALIZED state, THE Agent SHALL discover and register all MemoryBackendPlugin instances from `codecraftai-extension` ExtensionPoint entries targeting the Agent.
10. WHEN an Agent transitions to the STOPPED state, THE Agent's MemoryStoreRegistry SHALL be cleared of all registered stores.
11. IF the Agent's MemoryConfiguration is not provided, THEN THE Agent SHALL default to an InMemoryStore with MemoryScope.AGENT and no expiration policy.

### Requirement 15: Memory Backend Plugin Integration

**User Story:** As a developer, I want to distribute memory backends as plugins through `codecraftai-extension`, so that backend packages can be installed and discovered automatically by agents.

#### Acceptance Criteria

1. THE framework SHALL define an ExtensionPoint named "ccai.agentkit.memory_backends" through `codecraftai-extension` for registering MemoryBackendPlugin implementations.
2. WHEN an Agent is initialized, THE Agent SHALL query the "ccai.agentkit.memory_backends" ExtensionPoint and register all discovered MemoryStore instances with the Agent's MemoryStoreRegistry.
3. IF a MemoryBackendPlugin fails to load, THEN THE Agent SHALL log the failure at WARNING level including the plugin name and the error detail, and continue loading remaining plugins.
4. IF a MemoryBackendPlugin provides a MemoryStore with a name that conflicts with an already registered MemoryStore, THEN THE Agent SHALL log the conflict at WARNING level including both store names and skip the conflicting plugin store.

### Requirement 16: Memory Error Handling

**User Story:** As a developer, I want well-defined error types for memory store and context window failures, so that I can diagnose and handle memory errors precisely.

#### Acceptance Criteria

1. THE MemoryStoreError SHALL inherit from AgentKitError and SHALL be raised when a MemoryStore operation fails due to a backend error.
2. THE MemoryStoreError SHALL contain the store name, the operation name (store, retrieve, search, update, delete, clear), and the original exception as the cause.
3. THE ContextWindowError SHALL inherit from AgentKitError and SHALL be raised when the ContextWindow cannot produce a valid context or when summarization fails.
4. THE ContextWindowError SHALL contain the maximum token count, the strategy name, and a descriptive error message.
5. ALL memory-related exceptions SHALL provide a meaningful __repr__ that includes the exception class name and descriptive message.

### Requirement 17: Memory Serialization

**User Story:** As a developer, I want to serialize and deserialize memory entries, queries, and configurations, so that memory data can be stored, transmitted, and reconstructed.

#### Acceptance Criteria

1. THE MemoryEntry SHALL provide a to_json method that serializes the entry to a JSON string.
2. THE MemoryEntry SHALL provide a class method from_json that deserializes a JSON string into a MemoryEntry instance.
3. THE MemoryQuery SHALL provide a to_json method that serializes the query to a JSON string.
4. THE MemoryQuery SHALL provide a class method from_json that deserializes a JSON string into a MemoryQuery instance.
5. THE MemoryConfiguration SHALL provide a to_json method that serializes the configuration to a JSON string, excluding resolved credential values.
6. THE MemoryConfiguration SHALL provide a class method from_json that deserializes a JSON string into a MemoryConfiguration instance.
7. FOR ALL valid MemoryEntry instances, calling to_json and then from_json SHALL produce an equivalent MemoryEntry object (round-trip property).
8. FOR ALL valid MemoryQuery instances, calling to_json and then from_json SHALL produce an equivalent MemoryQuery object (round-trip property).
9. FOR ALL valid MemoryConfiguration instances, calling to_json and then from_json SHALL produce an equivalent MemoryConfiguration object (round-trip property).

### Requirement 18: Structured Logging for Memory Operations

**User Story:** As a developer, I want memory operations to produce structured log entries, so that I can monitor and debug memory usage using standard Python logging tools.

#### Acceptance Criteria

1. THE framework SHALL use the Python standard logging module with a logger hierarchy under `ccai.agentkit.memory`.
2. WHEN a MemoryEntry is stored, THE MemoryStore SHALL log at INFO level including the store name, entry identifier, and scope.
3. WHEN a MemoryQuery is executed, THE MemoryStore SHALL log at INFO level including the store name and the count of matching entries.
4. WHEN a MemoryEntry is deleted, THE MemoryStore SHALL log at INFO level including the store name and entry identifier.
5. WHEN expired entries are cleaned up, THE MemoryStore SHALL log at INFO level including the store name and the count of removed entries.
6. WHEN a MemoryStore operation fails, THE MemoryStore SHALL log at WARNING level including the store name, operation name, and error detail.
7. WHEN the ContextWindow trims content, THE ContextWindow SHALL log at INFO level including the strategy name, the original token count, and the resulting token count.
8. WHEN the ContextSummarizer generates a summary, THE ContextSummarizer SHALL log at INFO level including the input message count and the summary token count.

### Requirement 19: Memory String Representations

**User Story:** As a developer, I want meaningful string representations on memory system classes, so that I can quickly inspect memory state during debugging sessions.

#### Acceptance Criteria

1. THE MemoryEntry SHALL provide a __repr__ method that includes the class name, identifier, scope, and a truncated content preview.
2. THE MemoryEntry SHALL provide a __str__ method that returns a human-readable summary including the identifier, scope, tag count, and a truncated content preview.
3. THE MemoryStore base class SHALL provide a __repr__ method that includes the class name, store name, and entry count.
4. THE MemoryStore base class SHALL provide a __str__ method that returns a human-readable summary including the store name and entry count.
5. THE MemoryQuery SHALL provide a __repr__ method that includes the class name and a summary of active filter criteria.
6. THE MemoryQuery SHALL provide a __str__ method that returns a human-readable summary of the query criteria.
7. THE MemoryQueryResult SHALL provide a __repr__ method that includes the class name and the count of matching entries.
8. THE MemoryQueryResult SHALL provide a __str__ method that returns a human-readable summary including the match count and top entry identifiers.
9. THE MemoryStoreRegistry SHALL provide a __repr__ method that includes the class name and the count of registered stores.
10. THE MemoryStoreRegistry SHALL provide a __str__ method that returns a human-readable summary listing the registered store names.
11. THE ContextWindow SHALL provide a __repr__ method that includes the class name, maximum token count, and strategy name.
12. THE ContextWindow SHALL provide a __str__ method that returns a human-readable summary including the maximum token count and strategy name.
13. THE ContextSummarizer SHALL provide a __repr__ method that includes the class name and the LlmProvider name.
14. THE ContextSummarizer SHALL provide a __str__ method that returns a human-readable summary including the LlmProvider name and maximum summary token count.
15. THE MemoryConfiguration SHALL provide a __repr__ method that includes the class name, backend type, and default scope.
16. THE MemoryConfiguration SHALL provide a __str__ method that returns a human-readable summary including the backend type, default scope, and expiration policy.
17. THE ExpirationPolicy SHALL provide a __repr__ method that includes the class name, time-to-live, and cleanup interval.
18. THE ExpirationPolicy SHALL provide a __str__ method that returns a human-readable summary of the expiration settings.
