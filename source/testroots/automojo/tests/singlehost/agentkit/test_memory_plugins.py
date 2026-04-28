"""
    .. module:: automojo.tests.singlehost.agentkit.test_memory_plugins
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for memory backend plugin integration.

    Tests that the Agent discovers and registers MemoryBackendPlugin
    instances from the "automojo.agentkit.memory_backends" ExtensionPoint
    during initialization. Validates plugin load failure logging,
    store name conflict handling, and graceful degradation when
    automojo-extension is not available.

    **Validates: Requirements 15.1, 15.2, 15.3, 15.4**
"""

import logging
import sys
import types

from automojo.agentkit.agent import Agent
from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.agentregistry import AgentRegistry
from automojo.agentkit.inmemorystore import InMemoryStore
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.memoryconfiguration import MemoryConfiguration
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


def _create_config(name="plugin-test-agent", version="1.0.0"):
    """
        Creates a minimal AgentConfiguration for testing.
    """
    identity = {"name": name, "version": version}
    config_dict = {"identity": identity}
    config = AgentConfiguration.from_dict(config_dict)
    return config


class PluginTestAgent(Agent):
    """
        Concrete Agent subclass that wires memory initialization into
        the lifecycle for testing plugin discovery.
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
        self._perform_transition(LifecycleState.RUNNING, "on_start")
        return

    def pause(self) -> None:
        self._perform_transition(LifecycleState.PAUSED, "on_pause")
        return

    def resume(self) -> None:
        self._perform_transition(LifecycleState.RUNNING, "on_resume")
        return

    def stop(self) -> None:
        self._perform_transition(LifecycleState.STOPPED, "on_stop")
        return

    def reset(self) -> None:
        self._perform_transition(LifecycleState.INITIALIZED, "on_initialize")
        return


def _inject_mock_extension_module(mock_extension_point_class):
    """
        Injects a mock automojo.extension module into sys.modules so that
        the dynamic import inside _discover_memory_backend_plugins succeeds.

        Returns a tuple (had_module, original_module) for cleanup.
    """
    had_module = "automojo.extension" in sys.modules
    original_module = sys.modules.get("automojo.extension", None)

    mock_extension_module = types.ModuleType("automojo.extension")
    mock_extension_module.ExtensionPoint = mock_extension_point_class
    sys.modules["automojo.extension"] = mock_extension_module

    rtnval = (had_module, original_module)
    return rtnval


def _restore_extension_module(had_module, original_module):
    """
        Restores the original automojo.extension module in sys.modules.
    """
    if had_module:
        sys.modules["automojo.extension"] = original_module
    else:
        if "automojo.extension" in sys.modules:
            del sys.modules["automojo.extension"]
    return


# ---------------------------------------------------------------------------
# Test: Extension point discovery registers plugin stores
# ---------------------------------------------------------------------------

def test_plugin_discovery_registers_discovered_stores():
    """
        Verifies that _discover_memory_backend_plugins queries the
        "automojo.agentkit.memory_backends" extension point and registers
        discovered MemoryStore instances with the agent's MemoryStoreRegistry.
    """
    _reset_registry()

    config = _create_config(name="discover-agent")
    agent = PluginTestAgent(configuration=config)

    plugin_store = InMemoryStore(store_name="redis-backend")

    class MockExtensionPoint:
        """
            Mock ExtensionPoint that returns a list of discovered stores.
        """

        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return [plugin_store]

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        has_plugin_store = agent.memory_stores.has_store(name="redis-backend")
        assert has_plugin_store is True, \
            "Plugin store 'redis-backend' should be registered after discovery."

        has_primary = agent.memory_stores.has_store(name="primary")
        assert has_primary is True, \
            "Primary store should still be registered."

        count = agent.memory_stores.count
        expected_count = 2
        assert count == expected_count, \
            "Registry should have 2 stores (primary + plugin), got {}.".format(count)

    finally:
        _restore_extension_module(had_module, original_module)

    return


def test_plugin_discovery_registers_multiple_stores():
    """
        Verifies that multiple plugin stores are all registered when
        discovered from the extension point.
    """
    _reset_registry()

    config = _create_config(name="multi-plugin-agent")
    agent = PluginTestAgent(configuration=config)

    plugin_store_a = InMemoryStore(store_name="redis-backend")
    plugin_store_b = InMemoryStore(store_name="postgres-backend")

    class MockExtensionPoint:
        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return [plugin_store_a, plugin_store_b]

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        has_redis = agent.memory_stores.has_store(name="redis-backend")
        assert has_redis is True, "Plugin store 'redis-backend' should be registered."

        has_postgres = agent.memory_stores.has_store(name="postgres-backend")
        assert has_postgres is True, "Plugin store 'postgres-backend' should be registered."

        count = agent.memory_stores.count
        expected_count = 3
        assert count == expected_count, \
            "Registry should have 3 stores (primary + 2 plugins), got {}.".format(count)

    finally:
        _restore_extension_module(had_module, original_module)

    return


# ---------------------------------------------------------------------------
# Test: Plugin load failure logs WARNING and continues
# ---------------------------------------------------------------------------

def test_plugin_load_failure_logs_warning_and_continues():
    """
        Verifies that when a plugin store raises an exception during
        registration, the agent logs a WARNING and continues loading
        remaining plugins without crashing.
    """
    _reset_registry()

    config = _create_config(name="fail-plugin-agent")
    agent = PluginTestAgent(configuration=config)

    good_store = InMemoryStore(store_name="good-backend")

    class BrokenPlugin:
        """
            A plugin entry that raises when store_name is accessed.
        """

        @property
        def store_name(self):
            raise RuntimeError("Plugin initialization failed: missing config")

    broken_plugin = BrokenPlugin()

    class MockExtensionPoint:
        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return [broken_plugin, good_store]

    log_records = []
    handler = logging.Handler()
    handler.emit = lambda record: log_records.append(record)

    logger = agent.get_logger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        state = agent.state
        is_initialized = state is LifecycleState.INITIALIZED
        assert is_initialized is True, \
            "Agent should be INITIALIZED despite plugin failure."

        has_good = agent.memory_stores.has_store(name="good-backend")
        assert has_good is True, \
            "Good plugin store should still be registered after broken plugin."

        warning_found = False
        for record in log_records:
            if record.levelno == logging.WARNING:
                msg = record.getMessage()
                if "Failed to load memory backend plugin" in msg:
                    warning_found = True
                    break

        assert warning_found is True, \
            "A WARNING log should be emitted for the failed plugin."

    finally:
        _restore_extension_module(had_module, original_module)
        logger.removeHandler(handler)

    return


def test_plugin_discovery_failure_logs_warning():
    """
        Verifies that when the extension point query itself raises an
        exception, the agent logs a WARNING and continues initialization.
    """
    _reset_registry()

    config = _create_config(name="discovery-fail-agent")
    agent = PluginTestAgent(configuration=config)

    class MockExtensionPoint:
        def __init__(self, name):
            raise RuntimeError("Extension point registry unavailable")

    log_records = []
    handler = logging.Handler()
    handler.emit = lambda record: log_records.append(record)

    logger = agent.get_logger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        state = agent.state
        is_initialized = state is LifecycleState.INITIALIZED
        assert is_initialized is True, \
            "Agent should be INITIALIZED despite discovery failure."

        has_primary = agent.memory_stores.has_store(name="primary")
        assert has_primary is True, \
            "Primary store should still be registered."

        warning_found = False
        for record in log_records:
            if record.levelno == logging.WARNING:
                msg = record.getMessage()
                if "Memory backend plugin discovery failed" in msg:
                    warning_found = True
                    break

        assert warning_found is True, \
            "A WARNING log should be emitted for the discovery failure."

    finally:
        _restore_extension_module(had_module, original_module)
        logger.removeHandler(handler)

    return


def test_extension_not_available_logs_info_and_continues():
    """
        Verifies that when automojo-extension is not installed (ImportError),
        the agent logs at INFO level and continues initialization normally.
    """
    _reset_registry()

    config = _create_config(name="no-extension-agent")
    agent = PluginTestAgent(configuration=config)

    log_records = []
    handler = logging.Handler()
    handler.emit = lambda record: log_records.append(record)

    logger = agent.get_logger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Ensure automojo.extension is NOT in sys.modules
    had_module = "automojo.extension" in sys.modules
    original_module = sys.modules.get("automojo.extension", None)
    if "automojo.extension" in sys.modules:
        del sys.modules["automojo.extension"]

    try:
        agent.initialize()

        state = agent.state
        is_initialized = state is LifecycleState.INITIALIZED
        assert is_initialized is True, \
            "Agent should be INITIALIZED when extension module is unavailable."

        has_primary = agent.memory_stores.has_store(name="primary")
        assert has_primary is True, \
            "Primary store should still be registered."

        info_found = False
        for record in log_records:
            if record.levelno == logging.INFO:
                msg = record.getMessage()
                if "automojo-extension not available" in msg:
                    info_found = True
                    break

        assert info_found is True, \
            "An INFO log should be emitted when automojo-extension is not available."

    finally:
        if had_module:
            sys.modules["automojo.extension"] = original_module
        else:
            if "automojo.extension" in sys.modules:
                del sys.modules["automojo.extension"]
        logger.removeHandler(handler)

    return


# ---------------------------------------------------------------------------
# Test: Store name conflict logs WARNING and skips
# ---------------------------------------------------------------------------

def test_plugin_name_conflict_logs_warning_and_skips():
    """
        Verifies that when a plugin store has the same name as an already
        registered store, the agent logs a WARNING and skips the conflicting
        plugin store.
    """
    _reset_registry()

    config = _create_config(name="conflict-agent")
    agent = PluginTestAgent(configuration=config)

    # This store has the same name as the primary store ("primary")
    conflicting_store = InMemoryStore(store_name="primary")

    class MockExtensionPoint:
        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return [conflicting_store]

    log_records = []
    handler = logging.Handler()
    handler.emit = lambda record: log_records.append(record)

    logger = agent.get_logger()
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        state = agent.state
        is_initialized = state is LifecycleState.INITIALIZED
        assert is_initialized is True, \
            "Agent should be INITIALIZED despite name conflict."

        count = agent.memory_stores.count
        expected_count = 1
        assert count == expected_count, \
            "Registry should have only 1 store (primary), got {}.".format(count)

        warning_found = False
        for record in log_records:
            if record.levelno == logging.WARNING:
                msg = record.getMessage()
                if "name conflict" in msg and "primary" in msg:
                    warning_found = True
                    break

        assert warning_found is True, \
            "A WARNING log should be emitted for the name conflict."

    finally:
        _restore_extension_module(had_module, original_module)
        logger.removeHandler(handler)

    return


def test_plugin_name_conflict_does_not_replace_existing_store():
    """
        Verifies that a conflicting plugin store does not replace the
        already registered store in the registry.
    """
    _reset_registry()

    config = _create_config(name="no-replace-agent")
    agent = PluginTestAgent(configuration=config)

    conflicting_store = InMemoryStore(store_name="primary")
    non_conflicting_store = InMemoryStore(store_name="extra-backend")

    class MockExtensionPoint:
        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return [conflicting_store, non_conflicting_store]

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        original_primary = agent.memory
        is_original = original_primary is not conflicting_store
        assert is_original is True, \
            "The original primary store should not be replaced by the conflicting plugin."

        has_extra = agent.memory_stores.has_store(name="extra-backend")
        assert has_extra is True, \
            "Non-conflicting plugin store should still be registered."

        count = agent.memory_stores.count
        expected_count = 2
        assert count == expected_count, \
            "Registry should have 2 stores (primary + extra), got {}.".format(count)

    finally:
        _restore_extension_module(had_module, original_module)

    return


def test_plugin_discovery_queries_correct_extension_point_name():
    """
        Verifies that the agent queries the extension point with the
        name "automojo.agentkit.memory_backends".
    """
    _reset_registry()

    config = _create_config(name="name-check-agent")
    agent = PluginTestAgent(configuration=config)

    queried_names = []

    class MockExtensionPoint:
        def __init__(self, name):
            queried_names.append(name)
            self._name = name
            return

        def query(self):
            return []

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        expected_name = "automojo.agentkit.memory_backends"
        found = expected_name in queried_names
        assert found is True, \
            "Extension point '{}' should be queried, got {}.".format(
                expected_name, queried_names
            )

    finally:
        _restore_extension_module(had_module, original_module)

    return


def test_plugin_discovery_with_empty_results():
    """
        Verifies that when the extension point returns no plugins,
        the agent initializes normally with only the primary store.
    """
    _reset_registry()

    config = _create_config(name="empty-plugins-agent")
    agent = PluginTestAgent(configuration=config)

    class MockExtensionPoint:
        def __init__(self, name):
            self._name = name
            return

        def query(self):
            return []

    had_module, original_module = _inject_mock_extension_module(MockExtensionPoint)

    try:
        agent.initialize()

        count = agent.memory_stores.count
        expected_count = 1
        assert count == expected_count, \
            "Registry should have only the primary store, got {}.".format(count)

        has_primary = agent.memory_stores.has_store(name="primary")
        assert has_primary is True, \
            "Primary store should be registered."

    finally:
        _restore_extension_module(had_module, original_module)

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
