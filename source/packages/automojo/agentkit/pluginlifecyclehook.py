"""
    Defines the PluginLifecycleHook abstract base class that plugins
    implement to receive lifecycle notifications from the PluginManager
    in the automojo-agent-kit framework.

    Plugins that implement this interface will be notified when they are
    loaded, activated, deactivated, and unloaded.
"""

import abc


class PluginLifecycleHook(abc.ABC):
    """
        Abstract callback interface that plugins implement to receive
        lifecycle notifications from the PluginManager.
    """

    @abc.abstractmethod
    def on_load(self) -> None:
        """
            Called when the plugin is being loaded.
        """
        ...

    @abc.abstractmethod
    def on_activate(self) -> None:
        """
            Called when the plugin is being activated.
        """
        ...

    @abc.abstractmethod
    def on_deactivate(self) -> None:
        """
            Called when the plugin is being deactivated.
        """
        ...

    @abc.abstractmethod
    def on_unload(self) -> None:
        """
            Called when the plugin is being unloaded.
        """
        ...
