"""
    .. module:: automojo.tests.singlehost.agentkit.test_agent_memory
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for Agent memory integration.

    Tests Agent memory properties (memory, memory_stores, context_window),
    memory convenience methods (register_memory_store, store_memory,
    search_memory, build_context), lifecycle wiring (_initialize_memory,
    _stop_memory), default InMemoryStore when no MemoryConfiguration is
    provided, and memory backend plugin discovery.

    **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7,
    14.8, 14.9, 14.10, 14.11**
"""

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.contextwindow import ContextWindow
from automojo.agentkit.contextwindowstrategy import ContextWindowStrategy
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.inmemorystore import InMemoryStore
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.llmconversation import LLMConversation
from automojo.agentkit.llmmessage import LLMMessage
from automojo.agentkit.memoryconfiguration import MemoryConfiguration
from automojo.agentkit.memoryentry import MemoryEntry
from automojo.agentkit.memoryquery import MemoryQuery
from automojo.agentkit.memoryscope import MemoryScope
from automojo.agentkit.memorystore import MemoryStore
from automojo.agentkit.memorystoreregistry import MemoryStoreRegistry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_registry():
    """
        Resets the AgentRegistry singleton and clears all registered agents.
    """
    registry = AgentRegistry.instance()
    registry._reset()
    return


def _create_config(name="test-agent", version="1.0.0", settings=None):
    """
        Creates a minimal AgentConfiguration for testing.
    """
    identity = {"name": name, "version": version}
    config_dict = {"identity": identity}
    if settings is not None:
        config_dict["settings"] = settings
    config = AgentConfiguration.from_dict(config_dict)
    return config


class MemoryTestAgent(Agent):
    """
        Concrete Agent subclass that wires memory initialization and
        cleanup into the lifecycle methods.
    """

    def initialize(self) -> None:
        """
            Initializes memory then transitions to INITIALIZED state.
        """
        memory_config = None
        settings = self._configuration.settings
        if "memory" in settings:
            memory_config = MemoryConfiguration.from_dict(settings["memory"])
        self._initialize_memory(memory_configuration=memory_config)
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return

    def start(self) -> None:
        """
            Transitions the agent to RUNNING state.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        """
            Transitions the agent to PAUSED state.
        """
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        """
            Transitions the agent to RUNNING state from PAUSED.
        """
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        """
            Clears memory then transitions to STOPPED state.
        """
        self._stop_memory()
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        """
            Resets the agent to INITIALIZED state.
        """
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


# ---------------------------------------------------------------------------
# Test: Agent.memory returns primary MemoryStore
# ---------------------------------------------------------------------------

def test_agent_memory_returns_primary_store():
    """
        After initialization, Agent.memory returns the primary MemoryStore.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    store = agent.memory

    assert store is not None, "Agent.memory should not be None after initialization."
    assert isinstance(store, InMemoryStore), "Default primary store should be InMemoryStore."
    assert store.store_name == "primary", "Primary store name should be 'primary'."
    return


def test_agent_memory_is_none_before_initialization():
    """
        Before initialization, Agent.memory returns None.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)

    store = agent.memory

    assert store is None, "Agent.memory should be None before initialization."
    return


# ---------------------------------------------------------------------------
# Test: Agent.memory_stores returns MemoryStoreRegistry
# ---------------------------------------------------------------------------

def test_agent_memory_stores_returns_registry():
    """
        After initialization, Agent.memory_stores returns a MemoryStoreRegistry
        containing the primary store.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    registry = agent.memory_stores

    assert registry is not None, "Agent.memory_stores should not be None."
    assert isinstance(registry, MemoryStoreRegistry), "Should be a MemoryStoreRegistry."
    assert registry.count >= 1, "Registry should contain at least the primary store."
    assert registry.has_store("primary") is True, "Registry should contain 'primary' store."
    return


# ---------------------------------------------------------------------------
# Test: Agent.context_window returns ContextWindow
# ---------------------------------------------------------------------------

def test_agent_context_window_returns_context_window():
    """
        After initialization, Agent.context_window returns a ContextWindow.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    cw = agent.context_window

    assert cw is not None, "Agent.context_window should not be None after initialization."
    assert isinstance(cw, ContextWindow), "Should be a ContextWindow instance."
    return


def test_agent_context_window_is_none_before_initialization():
    """
        Before initialization, Agent.context_window returns None.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)

    cw = agent.context_window

    assert cw is None, "Agent.context_window should be None before initialization."
    return


# ---------------------------------------------------------------------------
# Test: Agent.register_memory_store adds to registry
# ---------------------------------------------------------------------------

def test_agent_register_memory_store_adds_to_registry():
    """
        Registering a MemoryStore via the Agent adds it to the registry.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    extra_store = InMemoryStore(store_name="extra-store")
    agent.register_memory_store(store=extra_store)

    assert agent.memory_stores.has_store("extra-store") is True, \
        "Registry should contain the newly registered store."
    assert agent.memory_stores.count == 2, \
        "Registry should contain primary + extra store."
    return


# ---------------------------------------------------------------------------
# Test: Agent.store_memory creates and stores MemoryEntry
# ---------------------------------------------------------------------------

def test_agent_store_memory_creates_and_stores_entry():
    """
        store_memory creates a MemoryEntry and stores it in the primary store.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    entry = agent.store_memory(
        content="test memory content",
        metadata={"key": "value"},
        tags=["tag1", "tag2"],
        scope=MemoryScope.AGENT,
    )

    assert entry is not None, "store_memory should return a MemoryEntry."
    assert entry.content == "test memory content", "Content should match."
    assert entry.metadata == {"key": "value"}, "Metadata should match."
    assert entry.tags == ["tag1", "tag2"], "Tags should match."
    assert entry.scope == MemoryScope.AGENT, "Scope should match."
    assert agent.memory.count == 1, "Primary store should contain one entry."
    return


def test_agent_store_memory_defaults_scope_to_agent():
    """
        store_memory defaults scope to AGENT when not provided.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    entry = agent.store_memory(content="default scope test")

    assert entry.scope == MemoryScope.AGENT, "Default scope should be AGENT."
    return


def test_agent_store_memory_raises_when_no_store():
    """
        store_memory raises SemanticError when no primary store is configured.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)

    raised = False
    try:
        agent.store_memory(content="should fail")
    except SemanticError:
        raised = True

    assert raised is True, "store_memory should raise SemanticError when no store."
    return


# ---------------------------------------------------------------------------
# Test: Agent.search_memory delegates to primary store
# ---------------------------------------------------------------------------

def test_agent_search_memory_delegates_to_primary_store():
    """
        search_memory delegates to the primary store and returns results.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    agent.store_memory(content="alpha", tags=["important"])
    agent.store_memory(content="beta", tags=["important", "extra"])
    agent.store_memory(content="gamma", tags=["other"])

    query = MemoryQuery(tags=["important"])
    result = agent.search_memory(query=query)

    assert result.total_count == 2, "Should find 2 entries with tag 'important'."
    return


def test_agent_search_memory_raises_when_no_store():
    """
        search_memory raises SemanticError when no primary store is configured.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)

    raised = False
    try:
        agent.search_memory(query=MemoryQuery())
    except SemanticError:
        raised = True

    assert raised is True, "search_memory should raise SemanticError when no store."
    return


# ---------------------------------------------------------------------------
# Test: Agent.build_context with and without memory query
# ---------------------------------------------------------------------------

def test_agent_build_context_without_memory_query():
    """
        build_context without a memory query returns a conversation
        that fits within the token limit.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
        LLMMessage(role="assistant", content="Hi there"),
    ])

    result = agent.build_context(conversation=conversation)

    assert result is not None, "build_context should return a conversation."
    assert result.count == 2, "Should contain the original 2 messages."
    return


def test_agent_build_context_with_memory_query():
    """
        build_context with a memory query includes matching memory entries
        as system messages in the resulting conversation.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    agent.store_memory(content="important context", tags=["relevant"])
    agent.store_memory(content="other context", tags=["irrelevant"])

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="What do you know?"),
    ])

    query = MemoryQuery(tags=["relevant"])
    result = agent.build_context(conversation=conversation, memory_query=query)

    assert result is not None, "build_context should return a conversation."
    assert result.count > 1, "Should include memory entries as system messages."

    system_messages = [m for m in result.messages if m.role == "system"]
    assert len(system_messages) >= 1, "Should have at least one system message from memory."

    memory_contents = [m.content for m in system_messages]
    found_memory = any("[Memory]" in c for c in memory_contents)
    assert found_memory is True, "Memory entries should be prefixed with [Memory]."
    return


def test_agent_build_context_raises_when_no_context_window():
    """
        build_context raises SemanticError when no ContextWindow is configured.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)

    conversation = LLMConversation(messages=[
        LLMMessage(role="user", content="Hello"),
    ])

    raised = False
    try:
        agent.build_context(conversation=conversation)
    except SemanticError:
        raised = True

    assert raised is True, "build_context should raise SemanticError when no context window."
    return


# ---------------------------------------------------------------------------
# Test: Agent defaults to InMemoryStore when no MemoryConfiguration
# ---------------------------------------------------------------------------

def test_agent_defaults_to_inmemorystore_without_config():
    """
        When no MemoryConfiguration is provided, the Agent defaults to
        an InMemoryStore with store name 'primary'.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    store = agent.memory

    assert isinstance(store, InMemoryStore), "Default store should be InMemoryStore."
    assert store.store_name == "primary", "Default store name should be 'primary'."
    return


# ---------------------------------------------------------------------------
# Test: Agent INITIALIZED state constructs memory system from config
# ---------------------------------------------------------------------------

def test_agent_initialized_constructs_memory_from_config():
    """
        When a MemoryConfiguration is provided via settings, the Agent
        constructs the memory system from that configuration.
    """
    _reset_registry()
    memory_settings = {
        "backend_type": "inmemory",
        "default_scope": "AGENT",
    }
    config = _create_config(settings={"memory": memory_settings})
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    store = agent.memory

    assert store is not None, "Memory store should be initialized."
    assert isinstance(store, InMemoryStore), "Should be InMemoryStore for 'inmemory' backend."
    assert agent.context_window is not None, "Context window should be initialized."
    return


def test_agent_initialized_constructs_memory_with_context_window_settings():
    """
        When context_window settings are provided in connection_params,
        the ContextWindow is configured accordingly.
    """
    _reset_registry()
    memory_settings = {
        "backend_type": "inmemory",
        "connection_params": {
            "context_window": {
                "max_tokens": 2048,
                "strategy": "RELEVANCE",
            }
        },
    }
    config = _create_config(settings={"memory": memory_settings})
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    cw = agent.context_window

    assert cw is not None, "Context window should be initialized."
    assert cw.max_tokens == 2048, "max_tokens should match configuration."
    assert cw.strategy == ContextWindowStrategy.RELEVANCE, "Strategy should match configuration."
    return


# ---------------------------------------------------------------------------
# Test: Agent STOPPED state clears registry
# ---------------------------------------------------------------------------

def test_agent_stopped_clears_memory_registry():
    """
        When the Agent transitions to STOPPED, the MemoryStoreRegistry
        is cleared and memory references are reset.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    assert agent.memory is not None, "Memory should be set after initialization."
    assert agent.memory_stores.count >= 1, "Registry should have stores."

    agent.start()
    agent.stop()

    assert agent.memory is None, "Memory should be None after stop."
    assert agent.context_window is None, "Context window should be None after stop."
    assert agent.memory_stores.count == 0, "Registry should be empty after stop."
    return


# ---------------------------------------------------------------------------
# Test: Agent re-initialization after stop reconstructs memory
# ---------------------------------------------------------------------------

def test_agent_reinitialize_after_stop_reconstructs_memory():
    """
        After stopping and re-initializing, the Agent reconstructs
        the memory system with a fresh store and registry.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    agent.store_memory(content="before stop")
    assert agent.memory.count == 1, "Should have one entry before stop."

    agent.start()
    agent.stop()

    assert agent.memory is None, "Memory should be None after stop."

    agent.initialize()

    assert agent.memory is not None, "Memory should be restored after re-init."
    assert agent.memory.count == 0, "Fresh store should be empty."
    return


# ---------------------------------------------------------------------------
# Test: Multiple stores in registry
# ---------------------------------------------------------------------------

def test_agent_multiple_stores_in_registry():
    """
        Multiple MemoryStore instances can be registered and looked up
        through the Agent's registry.
    """
    _reset_registry()
    config = _create_config()
    agent = MemoryTestAgent(configuration=config)
    agent.initialize()

    store_a = InMemoryStore(store_name="store-a")
    store_b = InMemoryStore(store_name="store-b")
    agent.register_memory_store(store=store_a)
    agent.register_memory_store(store=store_b)

    assert agent.memory_stores.count == 3, "Should have primary + 2 extra stores."
    assert agent.memory_stores.lookup("store-a") is store_a, "Should find store-a."
    assert agent.memory_stores.lookup("store-b") is store_b, "Should find store-b."
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
