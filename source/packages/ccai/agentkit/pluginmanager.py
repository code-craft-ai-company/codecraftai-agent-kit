"""
    Defines the PluginManager class that coordinates plugin discovery,
    loading, validation, and lifecycle management for an Agent in the
    codecraftai-agent-kit framework.

    The PluginManager manages plugins through their lifecycle states
    (DISCOVERED -> LOADING -> LOADED -> ACTIVE) and handles failures
    (-> FAILED). It delegates discovery and loading to codecraftai-extension
    and adds agent-specific lifecycle integration.
"""

import logging

from ccai.agentkit.configurationerrors import PluginLoadError
from ccai.agentkit.pluginconfiguration import PluginConfiguration
from ccai.agentkit.plugindescriptor import PluginDescriptor
from ccai.agentkit.pluginlifecyclehook import PluginLifecycleHook
from ccai.agentkit.pluginstatus import PluginStatus


class PluginManager:
    """
        Coordinates plugin discovery, loading, validation, and lifecycle
        management for an Agent. Delegates discovery and loading to
        codecraftai-extension and adds agent-specific lifecycle integration.

        :param agent_identifier: The identifier of the agent this manager belongs to.
        :param plugin_configuration: An optional PluginConfiguration instance.
    """

    def __init__(self, agent_identifier: str,
                 plugin_configuration: PluginConfiguration = None) -> None:
        self._agent_identifier = agent_identifier
        self._plugin_configuration = plugin_configuration
        self._plugins = {}
        self._logger = logging.getLogger("ccai.agentkit.plugins")
        return

    @property
    def agent_identifier(self) -> str:
        """
            The identifier of the agent this manager belongs to.

            :returns: The agent identifier string.
        """
        return self._agent_identifier

    @property
    def loaded_count(self) -> int:
        """
            The count of plugins with status LOADED or ACTIVE.

            :returns: The number of loaded or active plugins.
        """
        count = 0
        for entry in self._plugins.values():
            descriptor = entry["descriptor"]
            status = descriptor.status
            if status is PluginStatus.LOADED or status is PluginStatus.ACTIVE:
                count = count + 1
        return count

    @property
    def active_count(self) -> int:
        """
            The count of plugins with status ACTIVE.

            :returns: The number of active plugins.
        """
        count = 0
        for entry in self._plugins.values():
            descriptor = entry["descriptor"]
            if descriptor.status is PluginStatus.ACTIVE:
                count = count + 1
        return count

    def discover(self) -> list:
        """
            Scans configured search paths and the codecraftai-extension registry
            for available plugins. For now, returns an empty list as the
            codecraftai-extension integration is not yet available.

            :returns: A list of PluginDescriptor objects.
        """
        discovered = []
        return discovered

    def load_plugin(self, descriptor: PluginDescriptor,
                    hook: PluginLifecycleHook = None) -> None:
        """
            Loads a plugin given its descriptor and optional lifecycle hook.
            Transitions status to LOADING, invokes on_load hook if provided,
            then transitions to LOADED. On failure, transitions to FAILED
            and raises PluginLoadError.

            :param descriptor: The PluginDescriptor for the plugin.
            :param hook: An optional PluginLifecycleHook implementation.

            :raises: PluginLoadError
        """
        plugin_name = descriptor.name

        loading_descriptor = PluginDescriptor(
            name=descriptor.name,
            version=descriptor.version,
            description=descriptor.description,
            author=descriptor.author,
            extension_points=descriptor.extension_points,
            dependencies=descriptor.dependencies,
            status=PluginStatus.LOADING
        )

        self._plugins[plugin_name] = {
            "descriptor": loading_descriptor,
            "hook": hook
        }

        if hook is not None:
            try:
                hook.on_load()
            except Exception as err:
                self._logger.warning(
                    "Plugin '%s' on_load hook raised an exception for agent '%s': %s",
                    plugin_name, self._agent_identifier, str(err)
                )

        loaded_descriptor = PluginDescriptor(
            name=descriptor.name,
            version=descriptor.version,
            description=descriptor.description,
            author=descriptor.author,
            extension_points=descriptor.extension_points,
            dependencies=descriptor.dependencies,
            status=PluginStatus.LOADED
        )

        self._plugins[plugin_name] = {
            "descriptor": loaded_descriptor,
            "hook": hook
        }

        self._logger.info(
            "Plugin '%s' loaded for agent '%s'",
            plugin_name, self._agent_identifier
        )
        return

    def activate_plugin(self, plugin_name: str) -> None:
        """
            Activates a loaded plugin. Validates dependencies are satisfied,
            invokes on_activate hook, and transitions status to ACTIVE.
            On failure, transitions to FAILED and raises PluginLoadError.

            :param plugin_name: Name of the plugin to activate.

            :raises: PluginLoadError
        """
        if plugin_name not in self._plugins:
            errmsg = "Plugin '{}' is not loaded.".format(plugin_name)
            raise PluginLoadError(plugin_name=plugin_name, message=errmsg)

        entry = self._plugins[plugin_name]
        descriptor = entry["descriptor"]
        hook = entry["hook"]

        dependencies = descriptor.dependencies
        for dependency in dependencies:
            is_satisfied = False

            for other_name, other_entry in self._plugins.items():
                other_descriptor = other_entry["descriptor"]
                other_status = other_descriptor.status

                if other_status is PluginStatus.LOADED or other_status is PluginStatus.ACTIVE:
                    if dependency.is_satisfied_by(other_descriptor.name, other_descriptor.version) is True:
                        is_satisfied = True
                        break

            if is_satisfied is not True:
                failed_descriptor = PluginDescriptor(
                    name=descriptor.name,
                    version=descriptor.version,
                    description=descriptor.description,
                    author=descriptor.author,
                    extension_points=descriptor.extension_points,
                    dependencies=descriptor.dependencies,
                    status=PluginStatus.FAILED
                )

                self._plugins[plugin_name] = {
                    "descriptor": failed_descriptor,
                    "hook": hook
                }

                errmsg = "Unsatisfied dependency '{}' for plugin '{}'.".format(
                    dependency.name, plugin_name
                )
                self._logger.warning(
                    "Plugin '%s' failed to activate for agent '%s': %s",
                    plugin_name, self._agent_identifier, errmsg
                )
                raise PluginLoadError(plugin_name=plugin_name, message=errmsg)

        if hook is not None:
            try:
                hook.on_activate()
            except Exception as err:
                self._logger.warning(
                    "Plugin '%s' on_activate hook raised an exception for agent '%s': %s",
                    plugin_name, self._agent_identifier, str(err)
                )

        active_descriptor = PluginDescriptor(
            name=descriptor.name,
            version=descriptor.version,
            description=descriptor.description,
            author=descriptor.author,
            extension_points=descriptor.extension_points,
            dependencies=descriptor.dependencies,
            status=PluginStatus.ACTIVE
        )

        self._plugins[plugin_name] = {
            "descriptor": active_descriptor,
            "hook": hook
        }

        self._logger.info(
            "Plugin '%s' activated for agent '%s'",
            plugin_name, self._agent_identifier
        )
        return

    def deactivate_plugin(self, plugin_name: str) -> None:
        """
            Deactivates an active plugin. Invokes on_deactivate hook
            and transitions status to LOADED.

            :param plugin_name: Name of the plugin to deactivate.
        """
        if plugin_name not in self._plugins:
            return

        entry = self._plugins[plugin_name]
        descriptor = entry["descriptor"]
        hook = entry["hook"]

        if hook is not None:
            try:
                hook.on_deactivate()
            except Exception as err:
                self._logger.warning(
                    "Plugin '%s' on_deactivate hook raised an exception for agent '%s': %s",
                    plugin_name, self._agent_identifier, str(err)
                )

        loaded_descriptor = PluginDescriptor(
            name=descriptor.name,
            version=descriptor.version,
            description=descriptor.description,
            author=descriptor.author,
            extension_points=descriptor.extension_points,
            dependencies=descriptor.dependencies,
            status=PluginStatus.LOADED
        )

        self._plugins[plugin_name] = {
            "descriptor": loaded_descriptor,
            "hook": hook
        }

        self._logger.info(
            "Plugin '%s' deactivated for agent '%s'",
            plugin_name, self._agent_identifier
        )
        return

    def unload_plugin(self, plugin_name: str) -> None:
        """
            Unloads a plugin: deactivates if active, invokes on_unload hook,
            and removes from the manager.

            :param plugin_name: Name of the plugin to unload.
        """
        if plugin_name not in self._plugins:
            return

        entry = self._plugins[plugin_name]
        descriptor = entry["descriptor"]
        hook = entry["hook"]

        if descriptor.status is PluginStatus.ACTIVE:
            self.deactivate_plugin(plugin_name)

        if hook is not None:
            try:
                hook.on_unload()
            except Exception as err:
                self._logger.warning(
                    "Plugin '%s' on_unload hook raised an exception for agent '%s': %s",
                    plugin_name, self._agent_identifier, str(err)
                )

        del self._plugins[plugin_name]

        self._logger.info(
            "Plugin '%s' unloaded for agent '%s'",
            plugin_name, self._agent_identifier
        )
        return

    def get_plugin(self, plugin_name: str) -> PluginDescriptor:
        """
            Returns the PluginDescriptor for a loaded plugin, or None.

            :param plugin_name: Name of the plugin to look up.

            :returns: The PluginDescriptor or None.
        """
        if plugin_name not in self._plugins:
            return None

        entry = self._plugins[plugin_name]
        descriptor = entry["descriptor"]
        return descriptor

    def list_all(self) -> list:
        """
            Returns a list of all PluginDescriptor objects managed by this manager.

            :returns: A list of PluginDescriptor objects.
        """
        descriptors = []
        for entry in self._plugins.values():
            descriptors.append(entry["descriptor"])
        return descriptors

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, loaded count, and active count.

            :returns: A repr string for debugging.
        """
        repr_str = "PluginManager(agent_identifier={!r}, loaded_count={}, active_count={})".format(
            self._agent_identifier, self.loaded_count, self.active_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent identifier,
            loaded count, and active count.

            :returns: A human-readable string.
        """
        str_val = "PluginManager for agent '{}' (loaded={}, active={})".format(
            self._agent_identifier, self.loaded_count, self.active_count
        )
        return str_val
