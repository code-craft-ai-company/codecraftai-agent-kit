"""
    Defines the ConfigurationManager class that manages the complete
    configuration lifecycle for an Agent in the automojo-agent-kit framework.

    The ConfigurationManager coordinates hierarchical configuration loading,
    schema validation, change notification, and hot-reload monitoring.
    It maintains an ordered list of ConfigurationLayer objects merged in
    ascending priority order where higher-priority layers override
    lower-priority values.
"""

import copy
import json
import logging
import os

from datetime import datetime
from datetime import timezone

from automojo.agentkit.configurationchangeevent import ConfigurationChangeEvent
from automojo.agentkit.configurationerrors import ConfigurationValidationError
from automojo.agentkit.configurationlayer import ConfigurationLayer
from automojo.agentkit.configurationlayersource import ConfigurationLayerSource
from automojo.agentkit.errors import ConfigurationError

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


PRIORITY_DEFAULTS = 0
PRIORITY_FILE = 100
PRIORITY_ENVIRONMENT = 200
PRIORITY_RUNTIME = 300
PRIORITY_OVERRIDE = 400


class ConfigurationManager:
    """
        Manages the complete configuration lifecycle for an Agent.

        Coordinates hierarchical configuration loading, schema validation,
        change notification, and hot-reload monitoring. Maintains an ordered
        list of ConfigurationLayer objects merged in ascending priority order.

        :param agent_identifier: The identifier string for the agent.
        :param schema: An optional ConfigurationSchema for validation.
    """

    def __init__(self, agent_identifier: str, schema=None) -> None:
        self._agent_identifier = agent_identifier
        self._schema = schema
        self._layers = []
        self._merged_configuration = {}
        self._change_listeners = []
        self._logger = logging.getLogger("automojo.agentkit.configuration")
        return

    @property
    def agent_identifier(self) -> str:
        """
            The identifier string for the agent.

            :returns: The agent identifier string.
        """
        return self._agent_identifier

    @property
    def schema(self):
        """
            The optional ConfigurationSchema used for validation.

            :returns: The ConfigurationSchema instance, or None.
        """
        return self._schema

    @property
    def merged_configuration(self) -> dict:
        """
            A defensive copy of the merged configuration dictionary.

            :returns: A deep copy of the merged configuration dictionary.
        """
        result = copy.deepcopy(self._merged_configuration)
        return result

    @property
    def layers(self) -> list:
        """
            A defensive copy of the list of ConfigurationLayer objects
            in priority order.

            :returns: A list of ConfigurationLayer objects.
        """
        result = list(self._layers)
        return result

    def get(self, field_path: str, default=None):
        """
            Returns the resolved configuration value at the given dot-separated
            field path, or the default value when not found.

            :param field_path: Dot-separated path string.
            :param default: Value to return when the field path is not found.

            :returns: The resolved configuration value or default.
        """
        value = self._resolve_field_path(self._merged_configuration, field_path)

        if value is None:
            return default

        return value

    def set(self, field_path: str, value) -> None:
        """
            Stores a value in the RUNTIME ConfigurationLayer at the given
            field path. Creates a RUNTIME layer if one does not exist.
            Re-merges configuration, detects changes, and notifies listeners.

            :param field_path: Dot-separated path string.
            :param value: The value to store.
        """
        runtime_layer = self._find_runtime_layer()

        if runtime_layer is None:
            runtime_config = {}
            self._set_nested_value(runtime_config, field_path, value)

            runtime_layer = ConfigurationLayer(
                name="runtime",
                priority=PRIORITY_RUNTIME,
                source=ConfigurationLayerSource.RUNTIME,
                configuration=runtime_config
            )
            self._layers.append(runtime_layer)
        else:
            layer_config = runtime_layer.configuration
            self._set_nested_value(layer_config, field_path, value)

            layer_index = self._layers.index(runtime_layer)
            updated_layer = ConfigurationLayer(
                name=runtime_layer.name,
                priority=runtime_layer.priority,
                source=runtime_layer.source,
                configuration=layer_config
            )
            self._layers[layer_index] = updated_layer

        old_merged = copy.deepcopy(self._merged_configuration)
        self._merge_layers()
        self._validate_if_schema_present()
        self._detect_and_notify_changes(old_merged, self._merged_configuration, ConfigurationLayerSource.RUNTIME)
        return

    def load_defaults(self, defaults: dict) -> None:
        """
            Loads default configuration values as the lowest-priority layer.

            :param defaults: Dictionary of default configuration values.
        """
        layer = ConfigurationLayer(
            name="defaults",
            priority=PRIORITY_DEFAULTS,
            source=ConfigurationLayerSource.DEFAULTS,
            configuration=defaults
        )

        old_merged = copy.deepcopy(self._merged_configuration)
        self._layers.append(layer)
        self._merge_layers()
        self._validate_if_schema_present()
        self._detect_and_notify_changes(old_merged, self._merged_configuration, ConfigurationLayerSource.DEFAULTS)
        return

    def load_from_dict(self, data: dict, layer_name: str = None) -> None:
        """
            Loads configuration from a dictionary as a RUNTIME layer.

            :param data: Configuration dictionary.
            :param layer_name: Optional layer name.
        """
        if layer_name is None:
            layer_name = "dict-runtime"

        layer = ConfigurationLayer(
            name=layer_name,
            priority=PRIORITY_RUNTIME,
            source=ConfigurationLayerSource.RUNTIME,
            configuration=data
        )

        old_merged = copy.deepcopy(self._merged_configuration)
        self._layers.append(layer)
        self._merge_layers()
        self._validate_if_schema_present()
        self._detect_and_notify_changes(old_merged, self._merged_configuration, ConfigurationLayerSource.RUNTIME)
        return

    def load_from_file(self, file_path: str) -> None:
        """
            Loads configuration from a JSON or YAML file as a FILE layer.
            Raises ConfigurationError for missing files or invalid syntax.

            :param file_path: Path to the configuration file.

            :raises ConfigurationError: If the file does not exist or contains
                invalid syntax.
        """
        if os.path.isfile(file_path) is False:
            errmsg = "Configuration file not found: '{}'".format(file_path)
            raise ConfigurationError(errmsg)

        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == ".json":
            data = self._load_json_file(file_path)
        elif file_extension in (".yaml", ".yml"):
            data = self._load_yaml_file(file_path)
        else:
            errmsg = "Unsupported configuration file format: '{}'. Supported formats: .json, .yaml, .yml".format(
                file_extension
            )
            raise ConfigurationError(errmsg)

        layer_name = os.path.basename(file_path)
        layer = ConfigurationLayer(
            name=layer_name,
            priority=PRIORITY_FILE,
            source=ConfigurationLayerSource.FILE,
            configuration=data
        )

        old_merged = copy.deepcopy(self._merged_configuration)
        self._layers.append(layer)
        self._merge_layers()
        self._validate_if_schema_present()
        self._detect_and_notify_changes(old_merged, self._merged_configuration, ConfigurationLayerSource.FILE)
        return

    def load_from_environment(self, prefix: str = None) -> None:
        """
            Loads configuration from environment variables as an ENVIRONMENT layer.
            Strips the prefix and converts underscores to dots for field paths.

            :param prefix: Optional prefix to filter environment variables.
        """
        env_config = {}

        for env_key, env_value in os.environ.items():
            if prefix is not None:
                if env_key.startswith(prefix) is False:
                    continue

                stripped_key = env_key[len(prefix):]
            else:
                stripped_key = env_key

            field_path = stripped_key.replace("_", ".").lower()

            if len(field_path) > 0:
                self._set_nested_value(env_config, field_path, env_value)

        layer_name = "environment"
        if prefix is not None:
            layer_name = "environment-{}".format(prefix)

        layer = ConfigurationLayer(
            name=layer_name,
            priority=PRIORITY_ENVIRONMENT,
            source=ConfigurationLayerSource.ENVIRONMENT,
            configuration=env_config
        )

        old_merged = copy.deepcopy(self._merged_configuration)
        self._layers.append(layer)
        self._merge_layers()
        self._validate_if_schema_present()
        self._detect_and_notify_changes(old_merged, self._merged_configuration, ConfigurationLayerSource.ENVIRONMENT)
        return

    def reload(self) -> None:
        """
            Re-reads all file-based and environment-based layers and re-merges.
            Detects changes and notifies listeners. Logs at INFO level.
        """
        self._logger.info("Reloading configuration for agent '%s'", self._agent_identifier)

        old_merged = copy.deepcopy(self._merged_configuration)
        reloaded_layers = []

        for layer in self._layers:
            if layer.source is ConfigurationLayerSource.FILE:
                reloaded_layer = self._reload_file_layer(layer)
                reloaded_layers.append(reloaded_layer)
            elif layer.source is ConfigurationLayerSource.ENVIRONMENT:
                reloaded_layer = self._reload_environment_layer(layer)
                reloaded_layers.append(reloaded_layer)
            else:
                reloaded_layers.append(layer)

        self._layers = reloaded_layers
        self._merge_layers()
        self._detect_and_notify_changes(old_merged, self._merged_configuration, ConfigurationLayerSource.RUNTIME)

        self._logger.info("Configuration reload complete for agent '%s'", self._agent_identifier)
        return

    def register_change_listener(self, listener) -> None:
        """
            Registers a ConfigurationChangeListener callback.

            :param listener: Callable that accepts a ConfigurationChangeEvent.
        """
        self._change_listeners.append(listener)
        return

    def deregister_change_listener(self, listener) -> None:
        """
            Deregisters a previously registered ConfigurationChangeListener.

            :param listener: The listener to remove.
        """
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

        return

    # ---- Private Helper Methods ----

    def _find_runtime_layer(self):
        """
            Finds the first RUNTIME layer in the layers list.

            :returns: The ConfigurationLayer with RUNTIME source, or None.
        """
        for layer in self._layers:
            if layer.source is ConfigurationLayerSource.RUNTIME:
                if layer.name == "runtime":
                    return layer

        return None

    def _merge_layers(self) -> None:
        """
            Merges all layers in ascending priority order. Higher-priority
            layers override lower-priority values using deep dictionary merge.
        """
        sorted_layers = sorted(self._layers, key=lambda layer: layer.priority)
        merged = {}

        for layer in sorted_layers:
            self._deep_merge(merged, layer.configuration)

        self._merged_configuration = merged
        return

    def _deep_merge(self, base: dict, override: dict) -> None:
        """
            Recursively merges the override dictionary into the base dictionary.
            Nested dictionaries are merged recursively; other values are overwritten.

            :param base: The base dictionary to merge into.
            :param override: The override dictionary to merge from.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) is True and isinstance(value, dict) is True:
                self._deep_merge(base[key], value)
            else:
                base[key] = value

        return

    def _resolve_field_path(self, configuration: dict, field_path: str):
        """
            Traverses a configuration dictionary using a dot-separated field path.

            :param configuration: The configuration dictionary to traverse.
            :param field_path: The dot-separated path string.

            :returns: The resolved value, or None if not found.
        """
        parts = field_path.split(".")
        current = configuration

        for part in parts:
            if isinstance(current, dict) is False:
                return None

            if part not in current:
                return None

            current = current[part]

        return current

    def _set_nested_value(self, configuration: dict, field_path: str, value) -> None:
        """
            Sets a value in a nested dictionary using a dot-separated field path.
            Creates intermediate dictionaries as needed.

            :param configuration: The configuration dictionary to modify.
            :param field_path: The dot-separated path string.
            :param value: The value to set.
        """
        parts = field_path.split(".")
        current = configuration

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif isinstance(current[part], dict) is False:
                current[part] = {}

            current = current[part]

        last_part = parts[-1]
        current[last_part] = value
        return

    def _validate_if_schema_present(self) -> None:
        """
            Validates the merged configuration against the schema if a schema
            is provided. Raises ConfigurationValidationError if validation fails.
            Logs validation failures at WARNING level.

            :raises ConfigurationValidationError: If validation fails.
        """
        if self._schema is None:
            return

        validation_result = self._schema.validate(self._merged_configuration)

        if validation_result.is_valid is False:
            self._logger.warning(
                "Configuration validation failed for agent '%s' against schema '%s' with %d error(s)",
                self._agent_identifier,
                self._schema.name,
                len(validation_result.errors)
            )
            raise ConfigurationValidationError(
                schema_name=self._schema.name,
                errors=validation_result.errors,
                warnings=validation_result.warnings
            )

        return

    def _detect_and_notify_changes(self, old_config: dict, new_config: dict,
                                   source: ConfigurationLayerSource) -> None:
        """
            Compares old and new merged configurations, creates
            ConfigurationChangeEvent for each changed field, and notifies
            all registered listeners.

            :param old_config: The previous merged configuration.
            :param new_config: The new merged configuration.
            :param source: The ConfigurationLayerSource that triggered the change.
        """
        changes = []
        self._collect_changes(old_config, new_config, "", changes)

        timestamp = datetime.now(tz=timezone.utc)

        for field_path, previous_value, new_value in changes:
            event = ConfigurationChangeEvent(
                field_path=field_path,
                previous_value=previous_value,
                new_value=new_value,
                source=source,
                timestamp=timestamp
            )
            self._notify_listeners(event)

        return

    def _collect_changes(self, old_config: dict, new_config: dict,
                         prefix: str, changes: list) -> None:
        """
            Recursively collects changed fields between old and new configurations.

            :param old_config: The previous configuration dictionary.
            :param new_config: The new configuration dictionary.
            :param prefix: The current dot-separated path prefix.
            :param changes: The list to append (field_path, old_value, new_value) tuples to.
        """
        all_keys = set()

        if isinstance(old_config, dict) is True:
            all_keys.update(old_config.keys())

        if isinstance(new_config, dict) is True:
            all_keys.update(new_config.keys())

        for key in sorted(all_keys):
            if len(prefix) > 0:
                field_path = "{}.{}".format(prefix, key)
            else:
                field_path = key

            old_value = old_config.get(key) if isinstance(old_config, dict) is True else None
            new_value = new_config.get(key) if isinstance(new_config, dict) is True else None

            if isinstance(old_value, dict) is True and isinstance(new_value, dict) is True:
                self._collect_changes(old_value, new_value, field_path, changes)
            elif old_value != new_value:
                changes.append((field_path, old_value, new_value))

        return

    def _notify_listeners(self, event: ConfigurationChangeEvent) -> None:
        """
            Invokes all registered change listeners with the given event.
            Catches exceptions from listeners, logs at WARNING level, and
            continues invoking remaining listeners.

            :param event: The ConfigurationChangeEvent to pass to listeners.
        """
        for listener in self._change_listeners:
            try:
                listener(event)
            except Exception as listener_exc:
                self._logger.warning(
                    "Change listener exception for agent '%s' on field '%s': %s",
                    self._agent_identifier,
                    event.field_path,
                    str(listener_exc)
                )

        return

    def _load_json_file(self, file_path: str) -> dict:
        """
            Loads and parses a JSON configuration file.

            :param file_path: Path to the JSON file.

            :returns: The parsed configuration dictionary.

            :raises ConfigurationError: If the file contains invalid JSON.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                data = json.load(file_handle)
        except json.JSONDecodeError as json_err:
            errmsg = "Invalid JSON syntax in configuration file '{}': {}".format(
                file_path, str(json_err)
            )
            raise ConfigurationError(errmsg, cause=json_err)

        return data

    def _load_yaml_file(self, file_path: str) -> dict:
        """
            Loads and parses a YAML configuration file.

            :param file_path: Path to the YAML file.

            :returns: The parsed configuration dictionary.

            :raises ConfigurationError: If YAML is not available or the file
                contains invalid YAML.
        """
        if YAML_AVAILABLE is False:
            errmsg = "YAML support is not available. Install PyYAML to load YAML configuration files."
            raise ConfigurationError(errmsg)

        try:
            with open(file_path, "r", encoding="utf-8") as file_handle:
                data = yaml.safe_load(file_handle)
        except yaml.YAMLError as yaml_err:
            errmsg = "Invalid YAML syntax in configuration file '{}': {}".format(
                file_path, str(yaml_err)
            )
            raise ConfigurationError(errmsg, cause=yaml_err)

        if data is None:
            data = {}

        return data

    def _reload_file_layer(self, layer: ConfigurationLayer) -> ConfigurationLayer:
        """
            Re-reads a file-based configuration layer from disk.

            :param layer: The existing FILE layer to reload.

            :returns: A new ConfigurationLayer with the re-read configuration.
        """
        file_path = layer.name
        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            if file_extension == ".json":
                data = self._load_json_file(file_path)
            elif file_extension in (".yaml", ".yml"):
                data = self._load_yaml_file(file_path)
            else:
                data = layer.configuration
        except ConfigurationError:
            self._logger.warning(
                "Failed to reload file layer '%s' for agent '%s', retaining previous configuration",
                layer.name, self._agent_identifier
            )
            data = layer.configuration

        reloaded_layer = ConfigurationLayer(
            name=layer.name,
            priority=layer.priority,
            source=layer.source,
            configuration=data
        )
        return reloaded_layer

    def _reload_environment_layer(self, layer: ConfigurationLayer) -> ConfigurationLayer:
        """
            Re-reads an environment-based configuration layer from os.environ.

            :param layer: The existing ENVIRONMENT layer to reload.

            :returns: A new ConfigurationLayer with the re-read configuration.
        """
        layer_name = layer.name
        prefix = None

        if layer_name.startswith("environment-"):
            prefix = layer_name[len("environment-"):]

        env_config = {}

        for env_key, env_value in os.environ.items():
            if prefix is not None:
                if env_key.startswith(prefix) is False:
                    continue

                stripped_key = env_key[len(prefix):]
            else:
                stripped_key = env_key

            field_path = stripped_key.replace("_", ".").lower()

            if len(field_path) > 0:
                self._set_nested_value(env_config, field_path, env_value)

        reloaded_layer = ConfigurationLayer(
            name=layer.name,
            priority=layer.priority,
            source=layer.source,
            configuration=env_config
        )
        return reloaded_layer

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            agent identifier, and layer count.

            :returns: A repr string for debugging.
        """
        layer_count = len(self._layers)
        repr_str = "ConfigurationManager(agent_identifier={!r}, layer_count={})".format(
            self._agent_identifier, layer_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the agent identifier,
            layer count, and whether a schema is configured.

            :returns: A human-readable string.
        """
        layer_count = len(self._layers)
        has_schema = self._schema is not None
        str_val = "ConfigurationManager for agent '{}' ({} layers, schema={})".format(
            self._agent_identifier, layer_count, has_schema
        )
        return str_val
