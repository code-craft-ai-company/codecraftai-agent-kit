"""
    Defines the PlatformConfiguration class for declarative platform-specific
    settings including platform type, region, credential references, service
    endpoint overrides, and platform-specific options.

    Supports serialization to and from dictionary, JSON, and YAML
    representations. Integrates with automojo-credentials for credential
    resolution and automojo-this-app for file path resolution.

    .. module:: automojo.agentkit.platform.platformconfiguration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Declarative platform configuration with JSON/YAML serialization.
"""

import json
import logging
import os

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import yaml

from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.platform.platformtype import PlatformType


logger = logging.getLogger("automojo.agentkit.platform.configuration")


class PlatformConfiguration:
    """
        Configuration object defining platform-specific settings including
        platform type, region, credential references, service endpoint
        overrides, and platform-specific options.

        :param platform_type: The target PlatformType value.
        :param region: An optional region string.
        :param credential_references: An optional list of credential reference names.
        :param service_endpoint_overrides: An optional dictionary mapping service
            names to endpoint URLs.
        :param options: An optional dictionary of platform-specific options.
    """

    REQUIRED_FIELDS = ["platform_type"]

    def __init__(self, platform_type: PlatformType, region: Optional[str] = None,
                 credential_references: Optional[List[str]] = None,
                 service_endpoint_overrides: Optional[Dict[str, str]] = None,
                 options: Optional[Dict[str, Any]] = None) -> None:
        self._platform_type = platform_type
        self._region = region
        self._credential_references = list(credential_references) if credential_references is not None else []
        self._service_endpoint_overrides = dict(service_endpoint_overrides) if service_endpoint_overrides is not None else {}
        self._options = dict(options) if options is not None else {}
        self._resolved_credentials = {}
        return

    @property
    def platform_type(self) -> PlatformType:
        """
            The target platform type.

            :returns: The PlatformType value.
        """
        rtnval = self._platform_type
        return rtnval

    @property
    def region(self) -> Optional[str]:
        """
            The optional region string.

            :returns: The region string or None.
        """
        rtnval = self._region
        return rtnval

    @property
    def credential_references(self) -> List[str]:
        """
            A defensive copy of the credential reference names list.

            :returns: A list of credential reference name strings.
        """
        rtnval = list(self._credential_references)
        return rtnval

    @property
    def service_endpoint_overrides(self) -> Dict[str, str]:
        """
            A defensive copy of the service endpoint overrides dictionary.

            :returns: A dictionary mapping service names to endpoint URLs.
        """
        rtnval = dict(self._service_endpoint_overrides)
        return rtnval

    @property
    def options(self) -> Dict[str, Any]:
        """
            A defensive copy of the platform-specific options dictionary.

            :returns: A dictionary of platform-specific options.
        """
        rtnval = dict(self._options)
        return rtnval

    @property
    def resolved_credentials(self) -> dict:
        """
            A defensive copy of the resolved credentials dictionary.

            :returns: A dictionary mapping credential names to resolved values.
        """
        rtnval = dict(self._resolved_credentials)
        return rtnval

    def resolve_credentials(self, credential_resolver) -> None:
        """
            Resolves each credential reference through the credential resolver.

            The credential_resolver is expected to provide a lookup_credential
            method that accepts a credential name and returns the resolved
            credential object.

            :param credential_resolver: The credential resolution service.

            :raises: ConfigurationError
        """
        resolved = {}

        for cred_name in self._credential_references:
            try:
                resolved_cred = credential_resolver.lookup_credential(cred_name)
            except Exception as exc:
                err_msg_lines = [
                    "Failed to resolve credential reference."
                ]
                err_msg_lines.append("  Credential name: {!r}".format(cred_name))
                err_msg_lines.append("  Platform type: {!r}".format(self._platform_type.to_string()))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg, cause=exc)

            if resolved_cred is None:
                err_msg_lines = [
                    "Unresolvable credential reference."
                ]
                err_msg_lines.append("  Credential name: {!r}".format(cred_name))
                err_msg_lines.append("  Platform type: {!r}".format(self._platform_type.to_string()))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

            resolved[cred_name] = resolved_cred

        self._resolved_credentials = resolved
        logger.info(
            "Resolved %d credential reference(s) for platform '%s'.",
            len(resolved), self._platform_type.to_string()
        )
        return

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration,
            excluding resolved credential values.

            :returns: A dictionary containing the configuration fields.
        """
        rtnval = {
            "platform_type": self._platform_type.to_string(),
        }

        if self._region is not None:
            rtnval["region"] = self._region

        if len(self._credential_references) > 0:
            rtnval["credential_references"] = list(self._credential_references)

        if len(self._service_endpoint_overrides) > 0:
            rtnval["service_endpoint_overrides"] = dict(self._service_endpoint_overrides)

        if len(self._options) > 0:
            rtnval["options"] = dict(self._options)

        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration,
            excluding resolved credential values.

            :returns: A JSON string.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    def to_yaml(self) -> str:
        """
            Returns a YAML string representation of the configuration,
            excluding resolved credential values.

            :returns: A YAML string.
        """
        data = self.as_dict()
        rtnval = yaml.dump(data, default_flow_style=False)
        return rtnval

    @classmethod
    def from_dict(cls, data: dict) -> "PlatformConfiguration":
        """
            Constructs a PlatformConfiguration from a dictionary.

            Validates that all required fields are present and raises
            ConfigurationError when required fields are missing.

            :param data: Dictionary containing configuration fields.

            :returns: A PlatformConfiguration instance.
            :raises: ConfigurationError
        """
        for field_name in cls.REQUIRED_FIELDS:
            if field_name not in data:
                err_msg_lines = [
                    "Missing required field in platform configuration."
                ]
                err_msg_lines.append("  Required field: {!r}".format(field_name))
                err_msg_lines.append("  Required fields: {}".format(cls.REQUIRED_FIELDS))
                err_msg = os.linesep.join(err_msg_lines)
                raise ConfigurationError(err_msg)

        platform_type_str = data["platform_type"]
        try:
            platform_type = PlatformType.from_string(platform_type_str)
        except Exception as exc:
            err_msg_lines = [
                "Invalid platform_type value in configuration."
            ]
            err_msg_lines.append("  Value: {!r}".format(platform_type_str))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        region = data.get("region", None)
        credential_references = data.get("credential_references", None)
        service_endpoint_overrides = data.get("service_endpoint_overrides", None)
        options = data.get("options", None)

        rtnval = cls(
            platform_type=platform_type,
            region=region,
            credential_references=credential_references,
            service_endpoint_overrides=service_endpoint_overrides,
            options=options
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "PlatformConfiguration":
        """
            Deserializes a JSON string into a PlatformConfiguration instance.

            :param json_str: A JSON string containing configuration fields.

            :returns: A PlatformConfiguration instance.
            :raises: ConfigurationError
        """
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as exc:
            err_msg_lines = [
                "Failed to parse JSON platform configuration string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        rtnval = cls.from_dict(data)
        return rtnval

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "PlatformConfiguration":
        """
            Deserializes a YAML string into a PlatformConfiguration instance.

            :param yaml_str: A YAML string containing configuration fields.

            :returns: A PlatformConfiguration instance.
            :raises: ConfigurationError
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:
            err_msg_lines = [
                "Failed to parse YAML platform configuration string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        rtnval = cls.from_dict(data)
        return rtnval

    @classmethod
    def from_json_file(cls, file_path: str, app_context=None) -> "PlatformConfiguration":
        """
            Loads configuration from a JSON file, resolving the path relative
            to the AppContext directory when provided.

            :param file_path: Path to the JSON configuration file.
            :param app_context: Optional AppContext for path resolution.

            :returns: A PlatformConfiguration instance.
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
                "Failed to read JSON platform configuration file."
            ]
            err_msg_lines.append("  File path: {!r}".format(resolved_path))
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        rtnval = cls.from_json(json_str)
        logger.info(
            "Loaded PlatformConfiguration from JSON file: path=%s, platform=%s",
            resolved_path, rtnval.platform_type.to_string()
        )
        return rtnval

    @classmethod
    def from_yaml_file(cls, file_path: str, app_context=None) -> "PlatformConfiguration":
        """
            Loads configuration from a YAML file, resolving the path relative
            to the AppContext directory when provided.

            :param file_path: Path to the YAML configuration file.
            :param app_context: Optional AppContext for path resolution.

            :returns: A PlatformConfiguration instance.
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
                "Failed to read YAML platform configuration file."
            ]
            err_msg_lines.append("  File path: {!r}".format(resolved_path))
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        rtnval = cls.from_yaml(yaml_str)
        logger.info(
            "Loaded PlatformConfiguration from YAML file: path=%s, platform=%s",
            resolved_path, rtnval.platform_type.to_string()
        )
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            platform type, and region.

            :returns: A repr string for debugging.
        """
        rtnval = "PlatformConfiguration(platform_type={}, region={})".format(
            self._platform_type.to_string(), self._region
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the platform type,
            region, and the count of service endpoint overrides.

            :returns: A human-readable string.
        """
        override_count = len(self._service_endpoint_overrides)
        rtnval = "PlatformConfiguration(platform_type={}, region={}, endpoint_overrides={})".format(
            self._platform_type.to_string(), self._region, override_count
        )
        return rtnval
