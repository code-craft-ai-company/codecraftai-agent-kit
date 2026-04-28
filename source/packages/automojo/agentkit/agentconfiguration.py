"""
    Defines the AgentConfiguration class for declarative agent configuration
    in the automojo-agent-kit framework.

    AgentConfiguration supports loading from dictionaries, JSON, and YAML,
    with validation of required fields, credential reference resolution,
    data profile reference resolution, and serialization that excludes
    resolved credential secret values.
"""

import json
import os

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import yaml

from automojo.agentkit.errors import ConfigurationError


class AgentConfiguration:
    """
        Declarative configuration for an agent.

        Supports loading from dict, JSON string, JSON file, YAML string,
        and YAML file. Validates required fields, resolves credential and
        data profile references through external packages, and provides
        serialization methods that exclude resolved credential secret values.
    """

    REQUIRED_FIELDS: List[str] = ["identity"]
    REQUIRED_IDENTITY_FIELDS: List[str] = ["name", "version"]

    def __init__(self, identity: dict, settings: Optional[dict] = None,
                 credentials: Optional[dict] = None,
                 data_profiles: Optional[dict] = None,
                 sub_agents: Optional[list] = None,
                 resolved_credentials: Optional[dict] = None,
                 resolved_data_profiles: Optional[dict] = None) -> None:
        """
            Initializes an AgentConfiguration instance.

            This constructor is not intended to be called directly.
            Use the class methods from_dict, from_json, from_yaml,
            from_json_file, or from_yaml_file instead.

            :param identity: Dictionary containing identity fields.
            :param settings: Optional dictionary of agent settings.
            :param credentials: Optional dictionary of credential references.
            :param data_profiles: Optional dictionary of data profile references.
            :param sub_agents: Optional list of sub-agent configuration dicts.
            :param resolved_credentials: Optional dictionary of resolved credential objects.
            :param resolved_data_profiles: Optional dictionary of resolved data profile objects.
        """
        self._identity = dict(identity)

        if settings is not None:
            self._settings = dict(settings)
        else:
            self._settings = {}

        if credentials is not None:
            self._credentials = dict(credentials)
        else:
            self._credentials = {}

        if data_profiles is not None:
            self._data_profiles = dict(data_profiles)
        else:
            self._data_profiles = {}

        if sub_agents is not None:
            self._sub_agents = list(sub_agents)
        else:
            self._sub_agents = []

        if resolved_credentials is not None:
            self._resolved_credentials = dict(resolved_credentials)
        else:
            self._resolved_credentials = {}

        if resolved_data_profiles is not None:
            self._resolved_data_profiles = dict(resolved_data_profiles)
        else:
            self._resolved_data_profiles = {}

        return

    @property
    def identity(self) -> dict:
        """
            A defensive copy of the identity configuration dictionary.

            :returns: A dictionary containing identity fields.
        """
        return dict(self._identity)

    @property
    def settings(self) -> dict:
        """
            A defensive copy of the settings dictionary.

            :returns: A dictionary containing agent settings.
        """
        return dict(self._settings)

    @property
    def credentials(self) -> dict:
        """
            A defensive copy of the credential reference dictionary.

            Contains reference names only, not resolved secret values.

            :returns: A dictionary of credential references.
        """
        return dict(self._credentials)

    @property
    def data_profiles(self) -> dict:
        """
            A defensive copy of the data profile reference dictionary.

            Contains reference names only, not resolved values.

            :returns: A dictionary of data profile references.
        """
        return dict(self._data_profiles)

    @property
    def sub_agents(self) -> list:
        """
            A defensive copy of the sub-agent configuration list.

            :returns: A list of sub-agent configuration dictionaries.
        """
        return list(self._sub_agents)

    @property
    def resolved_credentials(self) -> dict:
        """
            A defensive copy of the resolved credential objects.

            :returns: A dictionary of resolved credential objects.
        """
        return dict(self._resolved_credentials)

    @property
    def resolved_data_profiles(self) -> dict:
        """
            A defensive copy of the resolved data profile objects.

            :returns: A dictionary of resolved data profile objects.
        """
        return dict(self._resolved_data_profiles)

    @classmethod
    def _validate_config_data(cls, config_data: dict) -> None:
        """
            Validates that the configuration dictionary contains all required fields.

            :param config_data: The configuration dictionary to validate.

            :raises: ConfigurationError
        """
        if not isinstance(config_data, dict):
            err_msg_lines = [
                "Configuration data must be a dictionary."
            ]
            err_msg_lines.append("  Received type: {}".format(type(config_data).__name__))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        for field in cls.REQUIRED_FIELDS:
            has_field = field in config_data
            if has_field is not True:
                err_msg_lines = [
                    "Missing required configuration field."
                ]
                err_msg_lines.append("  Missing field: {!r}".format(field))
                err_msg_lines.append("  Required fields: {}".format(cls.REQUIRED_FIELDS))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

        identity_data = config_data["identity"]

        if not isinstance(identity_data, dict):
            err_msg_lines = [
                "The 'identity' field must be a dictionary."
            ]
            err_msg_lines.append("  Received type: {}".format(type(identity_data).__name__))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        for field in cls.REQUIRED_IDENTITY_FIELDS:
            has_field = field in identity_data
            if has_field is not True:
                err_msg_lines = [
                    "Missing required identity field."
                ]
                err_msg_lines.append("  Missing field: {!r}".format(field))
                err_msg_lines.append("  Required identity fields: {}".format(cls.REQUIRED_IDENTITY_FIELDS))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

        return

    @classmethod
    def _resolve_credentials(cls, credentials_data: dict, app_context: Any) -> dict:
        """
            Resolves credential references through the credential manager.

            :param credentials_data: Dictionary of credential reference entries.
            :param app_context: The application context providing credential manager access.

            :returns: A dictionary mapping credential names to resolved credential objects.
            :raises: ConfigurationError
        """
        resolved = {}

        for cred_name, cred_ref in credentials_data.items():
            provider = cred_ref.get("provider", "")
            key = cred_ref.get("key", "")

            try:
                credential_manager = app_context.credential_manager
                resolved_cred = credential_manager.lookup_credential(key)
            except Exception as exc:
                err_msg_lines = [
                    "Failed to resolve credential reference."
                ]
                err_msg_lines.append("  Credential name: {!r}".format(cred_name))
                err_msg_lines.append("  Provider: {!r}".format(provider))
                err_msg_lines.append("  Key: {!r}".format(key))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg, cause=exc)

            if resolved_cred is None:
                err_msg_lines = [
                    "Unresolvable credential reference."
                ]
                err_msg_lines.append("  Credential name: {!r}".format(cred_name))
                err_msg_lines.append("  Provider: {!r}".format(provider))
                err_msg_lines.append("  Key: {!r}".format(key))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

            resolved[cred_name] = resolved_cred

        return resolved

    @classmethod
    def _resolve_data_profiles(cls, data_profiles_data: dict, app_context: Any) -> dict:
        """
            Resolves data profile references through the data profile manager.

            :param data_profiles_data: Dictionary of data profile reference entries.
            :param app_context: The application context providing data profile manager access.

            :returns: A dictionary mapping data profile names to resolved data profile objects.
            :raises: ConfigurationError
        """
        resolved = {}

        for profile_name, profile_ref in data_profiles_data.items():
            provider = profile_ref.get("provider", "")
            key = profile_ref.get("key", "")

            try:
                data_profile_manager = app_context.data_profile_manager
                resolved_profile = data_profile_manager.lookup_data_profile(key)
            except Exception as exc:
                err_msg_lines = [
                    "Failed to resolve data profile reference."
                ]
                err_msg_lines.append("  Data profile name: {!r}".format(profile_name))
                err_msg_lines.append("  Provider: {!r}".format(provider))
                err_msg_lines.append("  Key: {!r}".format(key))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg, cause=exc)

            if resolved_profile is None:
                err_msg_lines = [
                    "Unresolvable data profile reference."
                ]
                err_msg_lines.append("  Data profile name: {!r}".format(profile_name))
                err_msg_lines.append("  Provider: {!r}".format(provider))
                err_msg_lines.append("  Key: {!r}".format(key))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

            resolved[profile_name] = resolved_profile

        return resolved

    @classmethod
    def from_dict(cls, config_data: dict, app_context: Any = None) -> "AgentConfiguration":
        """
            Creates an AgentConfiguration from a dictionary.

            Validates required fields, resolves credential and data profile
            references if present, and returns a configured instance.

            :param config_data: The configuration dictionary.
            :param app_context: Optional application context for resolving
                credentials, data profiles, file paths, and environment variables.

            :returns: An AgentConfiguration instance.
            :raises: ConfigurationError
        """
        cls._validate_config_data(config_data)

        identity_data = dict(config_data["identity"])
        settings_data = config_data.get("settings", None)
        credentials_data = config_data.get("credentials", None)
        data_profiles_data = config_data.get("data_profiles", None)
        sub_agents_data = config_data.get("sub_agents", None)

        resolved_credentials = {}
        resolved_data_profiles = {}

        has_credentials = credentials_data is not None and len(credentials_data) > 0
        has_data_profiles = data_profiles_data is not None and len(data_profiles_data) > 0

        needs_app_context = has_credentials or has_data_profiles

        if needs_app_context is True and app_context is None:
            err_msg_lines = [
                "Application context is required but was not provided."
            ]
            err_msg_lines.append("  automojo-this-app must be initialized before creating agents.")
            err_msg_lines.append("  App context is needed to resolve credential and data profile references.")
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        if has_credentials is True:
            resolved_credentials = cls._resolve_credentials(credentials_data, app_context)

        if has_data_profiles is True:
            resolved_data_profiles = cls._resolve_data_profiles(data_profiles_data, app_context)

        configuration = cls(
            identity=identity_data,
            settings=settings_data,
            credentials=credentials_data,
            data_profiles=data_profiles_data,
            sub_agents=sub_agents_data,
            resolved_credentials=resolved_credentials,
            resolved_data_profiles=resolved_data_profiles
        )
        return configuration

    @classmethod
    def from_json(cls, json_str: str, app_context: Any = None) -> "AgentConfiguration":
        """
            Creates an AgentConfiguration from a JSON string.

            :param json_str: A JSON string containing configuration data.
            :param app_context: Optional application context for resolving references.

            :returns: An AgentConfiguration instance.
            :raises: ConfigurationError
        """
        try:
            config_data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as exc:
            err_msg_lines = [
                "Failed to parse JSON configuration string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        configuration = cls.from_dict(config_data, app_context=app_context)
        return configuration

    @classmethod
    def from_json_file(cls, file_path: str, app_context: Any = None) -> "AgentConfiguration":
        """
            Creates an AgentConfiguration from a JSON file.

            If app_context is provided, the file path is resolved relative
            to the AppContext directory.

            :param file_path: Path to the JSON configuration file.
            :param app_context: Optional application context for resolving
                the file path and references.

            :returns: An AgentConfiguration instance.
            :raises: ConfigurationError
        """
        resolved_path = file_path

        if app_context is not None:
            try:
                base_dir = app_context.directory
                resolved_path = os.path.join(base_dir, file_path)
            except Exception:
                resolved_path = file_path

        try:
            with open(resolved_path, "r") as file_handle:
                json_str = file_handle.read()
        except (OSError, IOError) as exc:
            err_msg_lines = [
                "Failed to read JSON configuration file."
            ]
            err_msg_lines.append("  File path: {!r}".format(resolved_path))
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        configuration = cls.from_json(json_str, app_context=app_context)
        return configuration

    @classmethod
    def from_yaml(cls, yaml_str: str, app_context: Any = None) -> "AgentConfiguration":
        """
            Creates an AgentConfiguration from a YAML string.

            :param yaml_str: A YAML string containing configuration data.
            :param app_context: Optional application context for resolving references.

            :returns: An AgentConfiguration instance.
            :raises: ConfigurationError
        """
        try:
            config_data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:
            err_msg_lines = [
                "Failed to parse YAML configuration string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        configuration = cls.from_dict(config_data, app_context=app_context)
        return configuration

    @classmethod
    def from_yaml_file(cls, file_path: str, app_context: Any = None) -> "AgentConfiguration":
        """
            Creates an AgentConfiguration from a YAML file.

            If app_context is provided, the file path is resolved relative
            to the AppContext directory.

            :param file_path: Path to the YAML configuration file.
            :param app_context: Optional application context for resolving
                the file path and references.

            :returns: An AgentConfiguration instance.
            :raises: ConfigurationError
        """
        resolved_path = file_path

        if app_context is not None:
            try:
                base_dir = app_context.directory
                resolved_path = os.path.join(base_dir, file_path)
            except Exception:
                resolved_path = file_path

        try:
            with open(resolved_path, "r") as file_handle:
                yaml_str = file_handle.read()
        except (OSError, IOError) as exc:
            err_msg_lines = [
                "Failed to read YAML configuration file."
            ]
            err_msg_lines.append("  File path: {!r}".format(resolved_path))
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        configuration = cls.from_yaml(yaml_str, app_context=app_context)
        return configuration

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration.

            Excludes resolved credential secret values. Includes credential
            reference names but not resolved values.

            :returns: A dictionary containing the configuration data.
        """
        result = {
            "identity": dict(self._identity)
        }

        if len(self._settings) > 0:
            result["settings"] = dict(self._settings)

        if len(self._credentials) > 0:
            result["credentials"] = dict(self._credentials)

        if len(self._data_profiles) > 0:
            result["data_profiles"] = dict(self._data_profiles)

        if len(self._sub_agents) > 0:
            result["sub_agents"] = list(self._sub_agents)

        return result

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration.

            Excludes resolved credential secret values.

            :returns: A JSON string containing the configuration data.
        """
        data = self.as_dict()
        json_str = json.dumps(data)
        return json_str

    def to_yaml(self) -> str:
        """
            Returns a YAML string representation of the configuration.

            Excludes resolved credential secret values.

            :returns: A YAML string containing the configuration data.
        """
        data = self.as_dict()
        yaml_str = yaml.dump(data, default_flow_style=False)
        return yaml_str

    def get_platform_configuration(self):
        """
            Returns a PlatformConfiguration from the settings dictionary
            if a 'platform' key is present, otherwise returns None.

            The platform configuration is constructed from the 'platform'
            sub-dictionary within settings using PlatformConfiguration.from_dict.

            :returns: A PlatformConfiguration instance or None.
        """
        platform_data = self._settings.get("platform", None)
        if platform_data is None:
            rtnval = None
            return rtnval

        from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration

        rtnval = PlatformConfiguration.from_dict(platform_data)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and identity configuration. Excludes resolved credential values.

            :returns: A repr string for debugging.
        """
        repr_str = "AgentConfiguration(identity={!r})".format(self._identity)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the configuration.

            Excludes resolved credential values.

            :returns: A human-readable string.
        """
        identity_name = self._identity.get("name", "unknown")
        identity_version = self._identity.get("version", "unknown")
        cred_count = len(self._credentials)
        profile_count = len(self._data_profiles)
        settings_count = len(self._settings)

        str_val = "AgentConfiguration: {} v{} (credentials={}, data_profiles={}, settings={})".format(
            identity_name, identity_version, cred_count, profile_count, settings_count
        )
        return str_val
