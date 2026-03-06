"""
    Unit tests for the automojo.agentkit.pluginmanager module.

    Tests the PluginManager class including constructor, properties,
    plugin lifecycle operations (load, activate, deactivate, unload),
    dependency validation, lifecycle hook invocation, error handling,
    and string representations.
"""

from automojo.agentkit.pluginmanager import PluginManager
from automojo.agentkit.plugindescriptor import PluginDescriptor
from automojo.agentkit.plugindependency import PluginDependency
from automojo.agentkit.pluginlifecyclehook import PluginLifecycleHook
from automojo.agentkit.pluginconfiguration import PluginConfiguration
from automojo.agentkit.pluginstatus import PluginStatus
from automojo.agentkit.configurationerrors import PluginLoadError


# ---- Test Hook Implementation ----


class TestPluginHook(PluginLifecycleHook):
    """
        Concrete PluginLifecycleHook implementation for testing.
        Tracks method calls and optionally raises configured errors.
    """

    def __init__(self):
        self.calls = []
        self.on_load_error = None
        self.on_activate_error = None
        self.on_deactivate_error = None
        self.on_unload_error = None
        return

    def on_load(self):
        self.calls.append("on_load")
        if self.on_load_error is not None:
            raise self.on_load_error
        return

    def on_activate(self):
        self.calls.append("on_activate")
        if self.on_activate_error is not None:
            raise self.on_activate_error
        return

    def on_deactivate(self):
        self.calls.append("on_deactivate")
        if self.on_deactivate_error is not None:
            raise self.on_deactivate_error
        return

    def on_unload(self):
        self.calls.append("on_unload")
        if self.on_unload_error is not None:
            raise self.on_unload_error
        return


# ---- Helper Functions ----


def _create_descriptor(name="test-plugin", version="1.0.0",
                       description="A test plugin", author="AutomationX",
                       extension_points=None, dependencies=None,
                       status=PluginStatus.DISCOVERED):
    """
        Creates a PluginDescriptor with sensible defaults for testing.

        :param name: The plugin name string.
        :param version: The plugin version string.
        :param description: The plugin description string.
        :param author: The plugin author string.
        :param extension_points: An optional list of extension point name strings.
        :param dependencies: An optional list of PluginDependency objects.
        :param status: The plugin lifecycle status.

        :returns: A PluginDescriptor instance.
    """
    descriptor = PluginDescriptor(
        name=name,
        version=version,
        description=description,
        author=author,
        extension_points=extension_points,
        dependencies=dependencies,
        status=status
    )
    return descriptor


# ---- Constructor Tests ----


def test_constructor_stores_agent_identifier():
    """
        Verify that the constructor stores the agent_identifier field correctly.
    """
    manager = PluginManager(agent_identifier="agent-001")
    stored_id = manager.agent_identifier
    assert stored_id == "agent-001", "constructor should store the agent_identifier"
    return


def test_constructor_stores_plugin_configuration():
    """
        Verify that the constructor accepts a PluginConfiguration parameter.
    """
    config = PluginConfiguration(enabled_plugins=["plugin-a"])
    manager = PluginManager(agent_identifier="agent-001", plugin_configuration=config)
    stored_id = manager.agent_identifier
    assert stored_id == "agent-001", "constructor should accept plugin_configuration"
    return


def test_constructor_defaults_plugin_configuration_to_none():
    """
        Verify that the constructor works without a plugin_configuration argument.
    """
    manager = PluginManager(agent_identifier="agent-002")
    stored_id = manager.agent_identifier
    assert stored_id == "agent-002", "constructor should work without plugin_configuration"
    return


# ---- Property Tests ----


def test_loaded_count_returns_zero_when_no_plugins():
    """
        Verify that loaded_count returns 0 when no plugins are loaded.
    """
    manager = PluginManager(agent_identifier="agent-001")
    count = manager.loaded_count
    assert count == 0, "loaded_count should be 0 when no plugins are loaded"
    return


def test_active_count_returns_zero_when_no_plugins():
    """
        Verify that active_count returns 0 when no plugins are active.
    """
    manager = PluginManager(agent_identifier="agent-001")
    count = manager.active_count
    assert count == 0, "active_count should be 0 when no plugins are active"
    return


def test_loaded_count_includes_loaded_plugins():
    """
        Verify that loaded_count includes plugins with LOADED status.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    count = manager.loaded_count
    assert count == 1, "loaded_count should include LOADED plugins"
    return


def test_loaded_count_includes_active_plugins():
    """
        Verify that loaded_count includes plugins with ACTIVE status.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    manager.activate_plugin("plugin-a")
    count = manager.loaded_count
    assert count == 1, "loaded_count should include ACTIVE plugins"
    return


def test_active_count_returns_one_after_activation():
    """
        Verify that active_count returns 1 after activating a plugin.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    manager.activate_plugin("plugin-a")
    count = manager.active_count
    assert count == 1, "active_count should be 1 after activating a plugin"
    return


# ---- discover Tests ----


def test_discover_returns_empty_list():
    """
        Verify that discover returns an empty list (placeholder implementation).
    """
    manager = PluginManager(agent_identifier="agent-001")
    result = manager.discover()
    assert result == [], "discover should return an empty list"
    return


# ---- load_plugin Tests ----


def test_load_plugin_transitions_status_to_loaded():
    """
        Verify that load_plugin transitions the plugin status to LOADED.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    loaded = manager.get_plugin("plugin-a")
    assert loaded is not None, "plugin should be present after loading"
    assert loaded.status is PluginStatus.LOADED, "plugin status should be LOADED after load_plugin"
    return


def test_load_plugin_invokes_on_load_hook():
    """
        Verify that load_plugin invokes the on_load hook when provided.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    manager.load_plugin(descriptor, hook=hook)
    assert "on_load" in hook.calls, "load_plugin should invoke on_load hook"
    return


def test_load_plugin_with_no_hook_still_transitions_to_loaded():
    """
        Verify that load_plugin transitions to LOADED even without a hook.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor, hook=None)
    loaded = manager.get_plugin("plugin-a")
    assert loaded.status is PluginStatus.LOADED, \
        "plugin status should be LOADED even without a hook"
    return


# ---- activate_plugin Tests ----


def test_activate_plugin_transitions_status_to_active():
    """
        Verify that activate_plugin transitions the plugin status to ACTIVE.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    manager.activate_plugin("plugin-a")
    activated = manager.get_plugin("plugin-a")
    assert activated.status is PluginStatus.ACTIVE, \
        "plugin status should be ACTIVE after activate_plugin"
    return


def test_activate_plugin_invokes_on_activate_hook():
    """
        Verify that activate_plugin invokes the on_activate hook.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    manager.load_plugin(descriptor, hook=hook)
    manager.activate_plugin("plugin-a")
    assert "on_activate" in hook.calls, "activate_plugin should invoke on_activate hook"
    return


def test_activate_plugin_raises_error_when_not_loaded():
    """
        Verify that activate_plugin raises PluginLoadError when the plugin
        is not loaded.
    """
    manager = PluginManager(agent_identifier="agent-001")
    error_raised = False
    try:
        manager.activate_plugin("nonexistent-plugin")
    except PluginLoadError:
        error_raised = True
    assert error_raised is True, \
        "activate_plugin should raise PluginLoadError for unknown plugin"
    return


def test_activate_plugin_raises_error_when_dependency_not_satisfied():
    """
        Verify that activate_plugin raises PluginLoadError when a dependency
        is not satisfied.
    """
    manager = PluginManager(agent_identifier="agent-001")
    dep = PluginDependency(name="missing-plugin")
    descriptor = _create_descriptor(name="plugin-a", dependencies=[dep])
    manager.load_plugin(descriptor)
    error_raised = False
    try:
        manager.activate_plugin("plugin-a")
    except PluginLoadError:
        error_raised = True
    assert error_raised is True, \
        "activate_plugin should raise PluginLoadError when dependency is not satisfied"
    return


def test_activate_plugin_succeeds_when_dependency_is_satisfied():
    """
        Verify that activate_plugin succeeds when the dependency is satisfied
        by another loaded plugin.
    """
    manager = PluginManager(agent_identifier="agent-001")
    dep_descriptor = _create_descriptor(name="dep-plugin", version="1.0.0")
    manager.load_plugin(dep_descriptor)

    dep = PluginDependency(name="dep-plugin")
    descriptor = _create_descriptor(name="plugin-a", dependencies=[dep])
    manager.load_plugin(descriptor)
    manager.activate_plugin("plugin-a")

    activated = manager.get_plugin("plugin-a")
    assert activated.status is PluginStatus.ACTIVE, \
        "activate_plugin should succeed when dependency is satisfied"
    return


# ---- deactivate_plugin Tests ----


def test_deactivate_plugin_transitions_status_to_loaded():
    """
        Verify that deactivate_plugin transitions the plugin status to LOADED
        and invokes the on_deactivate hook.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    manager.load_plugin(descriptor, hook=hook)
    manager.activate_plugin("plugin-a")
    manager.deactivate_plugin("plugin-a")
    deactivated = manager.get_plugin("plugin-a")
    assert deactivated.status is PluginStatus.LOADED, \
        "plugin status should be LOADED after deactivate_plugin"
    assert "on_deactivate" in hook.calls, \
        "deactivate_plugin should invoke on_deactivate hook"
    return


def test_deactivate_plugin_does_nothing_for_unknown_plugin():
    """
        Verify that deactivate_plugin does nothing for an unknown plugin name.
    """
    manager = PluginManager(agent_identifier="agent-001")
    manager.deactivate_plugin("nonexistent-plugin")
    count = manager.loaded_count
    assert count == 0, "deactivate_plugin should do nothing for unknown plugin"
    return


# ---- unload_plugin Tests ----


def test_unload_plugin_deactivates_if_active_and_removes():
    """
        Verify that unload_plugin deactivates an active plugin, invokes
        on_unload hook, and removes it from the manager.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    manager.load_plugin(descriptor, hook=hook)
    manager.activate_plugin("plugin-a")
    manager.unload_plugin("plugin-a")
    result = manager.get_plugin("plugin-a")
    assert result is None, "plugin should be removed after unload_plugin"
    assert "on_deactivate" in hook.calls, \
        "unload_plugin should deactivate an active plugin"
    assert "on_unload" in hook.calls, \
        "unload_plugin should invoke on_unload hook"
    return


def test_unload_plugin_removes_loaded_plugin():
    """
        Verify that unload_plugin removes a loaded (not active) plugin
        and invokes on_unload hook.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    manager.load_plugin(descriptor, hook=hook)
    manager.unload_plugin("plugin-a")
    result = manager.get_plugin("plugin-a")
    assert result is None, "plugin should be removed after unload_plugin"
    assert "on_unload" in hook.calls, \
        "unload_plugin should invoke on_unload hook"
    assert "on_deactivate" not in hook.calls, \
        "unload_plugin should not invoke on_deactivate for non-active plugin"
    return


def test_unload_plugin_does_nothing_for_unknown_plugin():
    """
        Verify that unload_plugin does nothing for an unknown plugin name.
    """
    manager = PluginManager(agent_identifier="agent-001")
    manager.unload_plugin("nonexistent-plugin")
    count = manager.loaded_count
    assert count == 0, "unload_plugin should do nothing for unknown plugin"
    return


# ---- get_plugin Tests ----


def test_get_plugin_returns_descriptor_for_loaded_plugin():
    """
        Verify that get_plugin returns the descriptor for a loaded plugin.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a", version="2.0.0")
    manager.load_plugin(descriptor)
    result = manager.get_plugin("plugin-a")
    assert result is not None, "get_plugin should return a descriptor"
    assert result.name == "plugin-a", "get_plugin should return the correct descriptor"
    assert result.version == "2.0.0", "get_plugin should return the correct version"
    return


def test_get_plugin_returns_none_for_unknown_plugin():
    """
        Verify that get_plugin returns None for an unknown plugin name.
    """
    manager = PluginManager(agent_identifier="agent-001")
    result = manager.get_plugin("nonexistent-plugin")
    assert result is None, "get_plugin should return None for unknown plugin"
    return


# ---- list_all Tests ----


def test_list_all_returns_all_descriptors():
    """
        Verify that list_all returns all loaded plugin descriptors.
    """
    manager = PluginManager(agent_identifier="agent-001")
    desc_a = _create_descriptor(name="plugin-a")
    desc_b = _create_descriptor(name="plugin-b")
    manager.load_plugin(desc_a)
    manager.load_plugin(desc_b)
    result = manager.list_all()
    assert len(result) == 2, "list_all should return all loaded descriptors"
    names = [d.name for d in result]
    assert "plugin-a" in names, "list_all should include plugin-a"
    assert "plugin-b" in names, "list_all should include plugin-b"
    return


def test_list_all_returns_empty_list_when_no_plugins():
    """
        Verify that list_all returns an empty list when no plugins are loaded.
    """
    manager = PluginManager(agent_identifier="agent-001")
    result = manager.list_all()
    assert result == [], "list_all should return empty list when no plugins loaded"
    return


# ---- Lifecycle Hook Exception Tests ----


def test_on_load_hook_exception_is_logged_and_status_still_transitions():
    """
        Verify that an exception in the on_load hook is logged at WARNING
        and the plugin status still transitions to LOADED.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    hook.on_load_error = RuntimeError("load hook failed")
    manager.load_plugin(descriptor, hook=hook)
    loaded = manager.get_plugin("plugin-a")
    assert loaded.status is PluginStatus.LOADED, \
        "plugin status should still transition to LOADED despite hook exception"
    assert "on_load" in hook.calls, "on_load hook should have been called"
    return


def test_on_activate_hook_exception_is_logged_and_status_still_transitions():
    """
        Verify that an exception in the on_activate hook is logged at WARNING
        and the plugin status still transitions to ACTIVE.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    hook.on_activate_error = RuntimeError("activate hook failed")
    manager.load_plugin(descriptor, hook=hook)
    manager.activate_plugin("plugin-a")
    activated = manager.get_plugin("plugin-a")
    assert activated.status is PluginStatus.ACTIVE, \
        "plugin status should still transition to ACTIVE despite hook exception"
    assert "on_activate" in hook.calls, "on_activate hook should have been called"
    return


def test_on_deactivate_hook_exception_is_logged_and_status_still_transitions():
    """
        Verify that an exception in the on_deactivate hook is logged at WARNING
        and the plugin status still transitions to LOADED.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    hook.on_deactivate_error = RuntimeError("deactivate hook failed")
    manager.load_plugin(descriptor, hook=hook)
    manager.activate_plugin("plugin-a")
    manager.deactivate_plugin("plugin-a")
    deactivated = manager.get_plugin("plugin-a")
    assert deactivated.status is PluginStatus.LOADED, \
        "plugin status should still transition to LOADED despite hook exception"
    assert "on_deactivate" in hook.calls, "on_deactivate hook should have been called"
    return


def test_on_unload_hook_exception_is_logged_and_plugin_still_removed():
    """
        Verify that an exception in the on_unload hook is logged at WARNING
        and the plugin is still removed from the manager.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    hook = TestPluginHook()
    hook.on_unload_error = RuntimeError("unload hook failed")
    manager.load_plugin(descriptor, hook=hook)
    manager.unload_plugin("plugin-a")
    result = manager.get_plugin("plugin-a")
    assert result is None, "plugin should be removed despite on_unload hook exception"
    assert "on_unload" in hook.calls, "on_unload hook should have been called"
    return


# ---- __repr__ Tests ----


def test_repr_includes_class_name():
    """
        Verify that __repr__ includes the class name 'PluginManager'.
    """
    manager = PluginManager(agent_identifier="agent-001")
    repr_str = repr(manager)
    contains_class_name = "PluginManager" in repr_str
    assert contains_class_name is True, "__repr__ should include the class name"
    return


def test_repr_includes_agent_identifier():
    """
        Verify that __repr__ includes the agent identifier.
    """
    manager = PluginManager(agent_identifier="agent-007")
    repr_str = repr(manager)
    contains_id = "agent-007" in repr_str
    assert contains_id is True, "__repr__ should include the agent identifier"
    return


def test_repr_includes_loaded_count():
    """
        Verify that __repr__ includes the loaded count.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    repr_str = repr(manager)
    contains_loaded = "loaded_count=1" in repr_str
    assert contains_loaded is True, "__repr__ should include the loaded count"
    return


def test_repr_includes_active_count():
    """
        Verify that __repr__ includes the active count.
    """
    manager = PluginManager(agent_identifier="agent-001")
    repr_str = repr(manager)
    contains_active = "active_count=0" in repr_str
    assert contains_active is True, "__repr__ should include the active count"
    return


# ---- __str__ Tests ----


def test_str_includes_agent_identifier():
    """
        Verify that __str__ includes the agent identifier.
    """
    manager = PluginManager(agent_identifier="agent-042")
    str_val = str(manager)
    contains_id = "agent-042" in str_val
    assert contains_id is True, "__str__ should include the agent identifier"
    return


def test_str_includes_loaded_count():
    """
        Verify that __str__ includes the loaded count.
    """
    manager = PluginManager(agent_identifier="agent-001")
    descriptor = _create_descriptor(name="plugin-a")
    manager.load_plugin(descriptor)
    str_val = str(manager)
    contains_loaded = "loaded=1" in str_val
    assert contains_loaded is True, "__str__ should include the loaded count"
    return


def test_str_includes_active_count():
    """
        Verify that __str__ includes the active count.
    """
    manager = PluginManager(agent_identifier="agent-001")
    str_val = str(manager)
    contains_active = "active=0" in str_val
    assert contains_active is True, "__str__ should include the active count"
    return
