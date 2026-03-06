"""
    Defines the PluginConfiguration class representing declarative plugin
    management settings for the automojo-agent-kit framework.

    A PluginConfiguration contains lists of enabled and disabled plugin names,
    plugin search paths, and an automatic discovery enabled flag.
"""

import json

from automojo.agentkit.errors import ConfigurationError

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class PluginConfiguration:
    """
        Configuration object defining plugin management settings including
        enabled/disabled plugin lists, search paths, and auto-discovery.

        :param enabled_plugins: An optional list of enabled plugin name strings.
        :param disabled_plugins: An optional list of disabled plugin name strings.
        :param search_paths: An optional list of plugin search path strings.
        :param automatic_discovery_enabled: Whether automatic plugin discovery is enabled.
    """

    def __init__(self, enabled_plugins: list = None, disabled_plugins: list = None,
                 search_paths: list = None, automatic_discovery_enabled: bool = True) -> None:

        if enabled_plugins is not None:
            self._enabled_plugins = list(enabled_plugins)
        else:
            self._enabled_plugins = []

        if disabled_plugins is not None:
            self._disabled_plugins = list(disabled_plugins)
        else:
            self._disabled_plugins = []

        if search_paths is not None:
            self._search_paths = list(search_paths)
        else:
            self._search_paths = []

        self._automatic_discovery_enabled = automatic_discovery_enabled
        return

    @property
    def enabled_plugins(self) -> list:
        """
            A defensive copy of the list of enabled plugin name strings.

            :returns: A list copy of the enabled plugin names.
        """
        return list(self._enabled_plugins)

    @property
    def disabled_plugins(self) -> list:
        """
            A defensive copy of the list of disabled plugin name strings.

            :returns: A list copy of the disabled plugin names.
        """
        return list(self._disabled_plugins)

    @property
    def search_paths(self) -> list:
        """
            A defensive copy of the list of plugin search path strings.

            :returns: A list copy of the search path strings.
        """
        return list(self._search_paths)

    @property
    def automatic_discovery_enabled(self) -> bool:
        """
            Whether automatic plugin discovery is enabled.

            :returns: True if automatic discovery is enabled, False otherwise.
        """
        return self._automatic_discovery_enabled

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration fields.

            :returns: A dictionary with enabled_plugins, disabled_plugins,
                search_paths, and automatic_discovery_enabled.
        """
        result = {
            "enabled_plugins": list(self._enabled_plugins),
            "disabled_plugins": list(self._disabled_plugins),
            "search_paths": list(self._search_paths),
            "automatic_discovery_enabled": self._automatic_discovery_enabled
        }
        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration fields.

            :returns: A JSON string containing all configuration fields.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    @classmethod
    def from_dict(cls, data: dict) -> "PluginConfiguration":
        """
            Constructs a PluginConfiguration from a dictionary.

            :param data: A dictionary containing enabled_plugins, disabled_plugins,
                search_paths, and automatic_discovery_enabled.

            :returns: A PluginConfiguration instance reconstructed from the dictionary.
        """
        enabled_plugins = data.get("enabled_plugins", None)
        disabled_plugins = data.get("disabled_plugins", None)
        search_paths = data.get("search_paths", None)
        automatic_discovery_enabled = data.get("automatic_discovery_enabled", True)

        config = cls(
            enabled_plugins=enabled_plugins,
            disabled_plugins=disabled_plugins,
            search_paths=search_paths,
            automatic_discovery_enabled=automatic_discovery_enabled
        )
        return config

    @classmethod
    def from_json(cls, json_str: str) -> "PluginConfiguration":
        """
            Deserializes a JSON string into a PluginConfiguration instance.

            :param json_str: A JSON string containing configuration fields.

            :returns: A PluginConfiguration instance reconstructed from the JSON data.
        """
        data = json.loads(json_str)
        config = cls.from_dict(data)
        return config

    @classmethod
    def from_json_file(cls, file_path: str) -> "PluginConfiguration":
        """
            Loads a PluginConfiguration from a JSON file.

            :param file_path: Path to the JSON file.

            :returns: A PluginConfiguration instance loaded from the file.
            :raises: ConfigurationError
        """
        try:
            with open(file_path, "r") as file_handle:
                content = file_handle.read()
        except (OSError, IOError) as err:
            errmsg = "Failed to read plugin configuration file '{}': {}".format(
                file_path, str(err)
            )
            raise ConfigurationError(errmsg, cause=err) from err

        try:
            data = json.loads(content)
        except json.JSONDecodeError as err:
            errmsg = "Failed to parse JSON plugin configuration file '{}': {}".format(
                file_path, str(err)
            )
            raise ConfigurationError(errmsg, cause=err) from err

        config = cls.from_dict(data)
        return config

    @classmethod
    def from_yaml_file(cls, file_path: str) -> "PluginConfiguration":
        """
            Loads a PluginConfiguration from a YAML file.

            :param file_path: Path to the YAML file.

            :returns: A PluginConfiguration instance loaded from the file.
            :raises: ConfigurationError
        """
        if YAML_AVAILABLE is not True:
            errmsg = "PyYAML is not available. Install PyYAML to load YAML plugin configuration."
            raise ConfigurationError(errmsg)

        try:
            with open(file_path, "r") as file_handle:
                content = file_handle.read()
        except (OSError, IOError) as err:
            errmsg = "Failed to read plugin configuration file '{}': {}".format(
                file_path, str(err)
            )
            raise ConfigurationError(errmsg, cause=err) from err

        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as err:
            errmsg = "Failed to parse YAML plugin configuration file '{}': {}".format(
                file_path, str(err)
            )
            raise ConfigurationError(errmsg, cause=err) from err

        if data is None:
            data = {}

        config = cls.from_dict(data)
        return config

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            enabled plugin count, and automatic discovery enabled status.

            :returns: A repr string for debugging.
        """
        enabled_count = len(self._enabled_plugins)
        repr_str = "PluginConfiguration(enabled_plugins={}, automatic_discovery_enabled={})".format(
            enabled_count, self._automatic_discovery_enabled
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the enabled plugin count,
            disabled plugin count, and automatic discovery enabled status.

            :returns: A human-readable string.
        """
        enabled_count = len(self._enabled_plugins)
        disabled_count = len(self._disabled_plugins)
        str_val = "PluginConfiguration (enabled={}, disabled={}, automatic_discovery_enabled={})".format(
            enabled_count, disabled_count, self._automatic_discovery_enabled
        )
        return str_val
