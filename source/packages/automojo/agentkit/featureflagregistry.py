"""
    Defines the FeatureFlagRegistry class that tracks FeatureFlag instances
    for an Agent in the automojo-agent-kit framework.

    The registry provides lookup, enumeration, runtime override, and
    file-based loading of feature flag definitions.
"""

import json
import logging

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.featureflag import FeatureFlag

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class FeatureFlagRegistry:
    """
        Registry tracking FeatureFlag instances for an Agent.

        Provides lookup, enumeration, runtime override, and file-based loading.
    """

    def __init__(self) -> None:
        self._flags = {}
        self._overrides = {}
        self._logger = logging.getLogger("automojo.agentkit.featureflags")
        return

    def register(self, flag: FeatureFlag) -> None:
        """
            Registers a FeatureFlag using its name as the key.

            :param flag: The FeatureFlag to register.

            :raises SemanticError: If a flag with the same name is already registered.
        """
        flag_name = flag.name

        if flag_name in self._flags:
            errmsg = "A FeatureFlag with name '{}' is already registered".format(flag_name)
            raise SemanticError(errmsg)

        self._flags[flag_name] = flag
        return

    def deregister(self, flag_name: str) -> None:
        """
            Deregisters a FeatureFlag by name.

            :param flag_name: The name of the flag to deregister.
        """
        if flag_name in self._flags:
            del self._flags[flag_name]

        if flag_name in self._overrides:
            del self._overrides[flag_name]

        return

    def lookup(self, flag_name: str) -> FeatureFlag:
        """
            Looks up a registered FeatureFlag by name.

            :param flag_name: The name of the flag to look up.

            :returns: The FeatureFlag instance, or None if not found.
        """
        result = self._flags.get(flag_name, None)
        return result

    def list_all(self) -> list:
        """
            Returns a list of all registered FeatureFlag instances.

            :returns: A list of FeatureFlag objects.
        """
        result = list(self._flags.values())
        return result

    def has_flag(self, flag_name: str) -> bool:
        """
            Checks whether a FeatureFlag with the given name is registered.

            :param flag_name: The flag name to check.

            :returns: True if the flag is registered, False otherwise.
        """
        result = flag_name in self._flags
        return result

    @property
    def count(self) -> int:
        """
            The count of currently registered flags.

            :returns: The number of registered flags.
        """
        result = len(self._flags)
        return result

    def is_enabled(self, flag_name: str) -> bool:
        """
            Returns whether the flag is enabled, considering runtime overrides
            and the default value in that precedence order.

            The registry's is_enabled checks: 1) runtime override, 2) default value.
            The evaluator adds the configuration layer.

            :param flag_name: The flag name to evaluate.

            :returns: True if the flag is enabled.
        """
        if flag_name in self._overrides:
            return self._overrides[flag_name]

        flag = self._flags.get(flag_name, None)

        if flag is not None:
            return flag.default_value

        return False

    def set_override(self, flag_name: str, value: bool) -> None:
        """
            Sets a runtime override for a flag.

            :param flag_name: The flag name to override.
            :param value: The override boolean value.
        """
        self._overrides[flag_name] = value
        effective_value = self.is_enabled(flag_name)
        self._logger.info(
            "Feature flag override set: flag='%s', override=%s, effective=%s",
            flag_name, value, effective_value
        )
        return

    def clear_override(self, flag_name: str) -> None:
        """
            Clears the runtime override for a flag.

            :param flag_name: The flag name to clear the override for.
        """
        if flag_name in self._overrides:
            del self._overrides[flag_name]

        effective_value = self.is_enabled(flag_name)
        self._logger.info(
            "Feature flag override cleared: flag='%s', effective=%s",
            flag_name, effective_value
        )
        return

    def clear_all_overrides(self) -> None:
        """
            Removes all runtime overrides.
        """
        self._overrides.clear()
        self._logger.info("All feature flag overrides cleared")
        return

    def load_from_json_file(self, file_path: str) -> None:
        """
            Loads FeatureFlag definitions from a JSON file.

            :param file_path: Path to the JSON file.
        """
        with open(file_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)

        self._load_flags_from_data(data)
        return

    def load_from_yaml_file(self, file_path: str) -> None:
        """
            Loads FeatureFlag definitions from a YAML file.

            :param file_path: Path to the YAML file.
        """
        if YAML_AVAILABLE is False:
            errmsg = "YAML support is not available. Install PyYAML to load YAML files."
            raise SemanticError(errmsg)

        with open(file_path, "r", encoding="utf-8") as file_handle:
            data = yaml.safe_load(file_handle)

        if data is None:
            data = {}

        self._load_flags_from_data(data)
        return

    def _load_flags_from_data(self, data) -> None:
        """
            Loads FeatureFlag definitions from a parsed data structure.
            Expects either a dict of flag_name -> flag_dict or a list of flag dicts.

            :param data: The parsed data structure.
        """
        if isinstance(data, dict) is True:
            for flag_name, flag_data in data.items():
                if isinstance(flag_data, dict) is True:
                    flag_data["name"] = flag_name
                    flag = FeatureFlag.from_dict(flag_data)
                elif isinstance(flag_data, bool) is True:
                    flag = FeatureFlag(name=flag_name, default_value=flag_data)
                else:
                    flag = FeatureFlag(name=flag_name, default_value=False)

                if flag_name not in self._flags:
                    self._flags[flag_name] = flag
        elif isinstance(data, list) is True:
            for flag_data in data:
                if isinstance(flag_data, dict) is True:
                    flag = FeatureFlag.from_dict(flag_data)
                    flag_name = flag.name

                    if flag_name not in self._flags:
                        self._flags[flag_name] = flag

        return

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and the count of registered flags.

            :returns: A repr string for debugging.
        """
        flag_count = len(self._flags)
        repr_str = "FeatureFlagRegistry(count={})".format(flag_count)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered flag
            names and their current enabled status.

            :returns: A human-readable string.
        """
        flag_entries = []

        for flag_name in sorted(self._flags.keys()):
            enabled = self.is_enabled(flag_name)
            entry = "{}={}".format(flag_name, enabled)
            flag_entries.append(entry)

        flags_summary = ", ".join(flag_entries)
        str_val = "FeatureFlagRegistry({} flags: {})".format(
            len(self._flags), flags_summary
        )
        return str_val
