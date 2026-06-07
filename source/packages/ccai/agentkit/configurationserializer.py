"""
    Defines the ConfigurationSerializer class for serializing and deserializing
    configuration dictionaries to and from JSON and YAML formats.

    The ConfigurationSerializer provides round-trip fidelity for configuration
    data and excludes resolved credential values from serialized output to
    prevent accidental credential leakage.
"""

import json

from ccai.agentkit.errors import ConfigurationError

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Keys containing any of these substrings (case-insensitive) are treated as
# credential keys and their values are redacted during serialization.
_CREDENTIAL_KEY_PATTERNS = ("credential", "secret", "password", "token")

# Placeholder string used to replace redacted credential values.
_REDACTED_PLACEHOLDER = "[REDACTED]"


class ConfigurationSerializer:
    """
        Serializes and deserializes configuration dictionaries to and from
        JSON and YAML formats with round-trip fidelity.
        Excludes resolved credential values from serialized output.
    """

    def to_json(self, configuration: dict) -> str:
        """
            Serializes a configuration dictionary to a JSON string.
            Credential values are filtered out and replaced with a
            redacted placeholder before serialization.

            :param configuration: The configuration dictionary.

            :returns: A JSON string representation.
        """
        filtered = self._filter_credentials(configuration)
        json_str = json.dumps(filtered)
        return json_str

    def from_json(self, json_str: str) -> dict:
        """
            Deserializes a JSON string to a configuration dictionary.

            :param json_str: The JSON string.

            :returns: A configuration dictionary.
            :raises: ConfigurationError
        """
        try:
            result = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as err:
            errmsg = "Failed to parse JSON configuration: {}".format(str(err))
            raise ConfigurationError(errmsg, cause=err) from err

        return result

    def to_yaml(self, configuration: dict) -> str:
        """
            Serializes a configuration dictionary to a YAML string.
            Credential values are filtered out and replaced with a
            redacted placeholder before serialization.

            :param configuration: The configuration dictionary.

            :returns: A YAML string representation.
            :raises: ConfigurationError
        """
        if YAML_AVAILABLE is not True:
            errmsg = "PyYAML is not available. Install PyYAML to use YAML serialization."
            raise ConfigurationError(errmsg)

        filtered = self._filter_credentials(configuration)
        yaml_str = yaml.dump(filtered, default_flow_style=False)
        return yaml_str

    def from_yaml(self, yaml_str: str) -> dict:
        """
            Deserializes a YAML string to a configuration dictionary.

            :param yaml_str: The YAML string.

            :returns: A configuration dictionary.
            :raises: ConfigurationError
        """
        if YAML_AVAILABLE is not True:
            errmsg = "PyYAML is not available. Install PyYAML to use YAML deserialization."
            raise ConfigurationError(errmsg)

        try:
            result = yaml.safe_load(yaml_str)
        except yaml.YAMLError as err:
            errmsg = "Failed to parse YAML configuration: {}".format(str(err))
            raise ConfigurationError(errmsg, cause=err) from err

        if result is None:
            result = {}

        return result

    def _filter_credentials(self, configuration: dict) -> dict:
        """
            Recursively filters credential values from a configuration dictionary.
            Keys containing credential-related substrings are replaced with a
            redacted placeholder. Values that are dicts containing a '_resolved'
            key are also replaced with the redacted placeholder.

            :param configuration: The configuration dictionary to filter.

            :returns: A new dictionary with credential values redacted.
        """
        filtered = {}

        for key, value in configuration.items():
            key_lower = key.lower()
            is_credential_key = False

            for pattern in _CREDENTIAL_KEY_PATTERNS:
                if pattern in key_lower:
                    is_credential_key = True
                    break

            if is_credential_key is True:
                filtered[key] = _REDACTED_PLACEHOLDER
                continue

            if isinstance(value, dict):
                if "_resolved" in value:
                    filtered[key] = _REDACTED_PLACEHOLDER
                else:
                    filtered[key] = self._filter_credentials(value)
                continue

            filtered[key] = value

        return filtered

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name.

            :returns: A repr string for debugging.
        """
        repr_str = "ConfigurationSerializer()"
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the supported format names.

            :returns: A human-readable string.
        """
        str_val = "ConfigurationSerializer (formats: json, yaml)"
        return str_val
