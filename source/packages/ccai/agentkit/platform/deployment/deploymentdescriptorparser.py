"""
    Defines the DeploymentDescriptorParser class for parsing
    DeploymentDescriptor objects from JSON strings, YAML strings,
    or files. Validates required fields and detects file format
    from extension.

    .. module:: ccai.agentkit.platform.deployment.deploymentdescriptorparser
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Parser for deployment descriptors from JSON/YAML/files.
"""

import json
import logging
import os

import yaml

from ccai.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from ccai.agentkit.platform.errors import DeploymentDescriptorError


logger = logging.getLogger("ccai.agentkit.platform.deployment")


class DeploymentDescriptorParser:
    """
        Parses DeploymentDescriptor objects from JSON, YAML, or files.
        Validates descriptors against required fields and resolves
        platform-specific defaults.
    """

    SUPPORTED_EXTENSIONS = (".json", ".yaml", ".yml")
    REQUIRED_FIELDS = ["name", "target_platform"]

    def parse_json(self, json_str: str) -> DeploymentDescriptor:
        """
            Parses a JSON string into a DeploymentDescriptor.

            :param json_str: A JSON string containing descriptor fields.

            :returns: A DeploymentDescriptor instance.
            :raises: DeploymentDescriptorError
        """
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as exc:
            err_msg_lines = [
                "Failed to parse JSON deployment descriptor string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise DeploymentDescriptorError(err_msg)

        self._validate_schema(data)
        rtnval = DeploymentDescriptor.from_dict(data)
        logger.debug("Parsed deployment descriptor from JSON: name=%s, platform=%s",
                      rtnval.name, rtnval.target_platform.to_string())
        return rtnval

    def parse_yaml(self, yaml_str: str) -> DeploymentDescriptor:
        """
            Parses a YAML string into a DeploymentDescriptor.

            :param yaml_str: A YAML string containing descriptor fields.

            :returns: A DeploymentDescriptor instance.
            :raises: DeploymentDescriptorError
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:
            err_msg_lines = [
                "Failed to parse YAML deployment descriptor string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise DeploymentDescriptorError(err_msg)

        self._validate_schema(data)
        rtnval = DeploymentDescriptor.from_dict(data)
        logger.debug("Parsed deployment descriptor from YAML: name=%s, platform=%s",
                      rtnval.name, rtnval.target_platform.to_string())
        return rtnval

    def parse_file(self, file_path: str, app_context=None) -> DeploymentDescriptor:
        """
            Parses a deployment descriptor from a file, detecting format
            from the file extension.

            :param file_path: Path to the descriptor file.
            :param app_context: Optional AppContext for path resolution.

            :returns: A DeploymentDescriptor instance.
            :raises: DeploymentDescriptorError
        """
        resolved_path = self._resolve_path(file_path, app_context)
        ext = os.path.splitext(resolved_path)[1].lower()

        if ext == ".json":
            try:
                with open(resolved_path, "r") as file_handle:
                    content = file_handle.read()
            except (OSError, IOError) as exc:
                err_msg_lines = [
                    "Failed to read deployment descriptor file."
                ]
                err_msg_lines.append("  File path: {!r}".format(resolved_path))
                err_msg_lines.append("  Error: {}".format(str(exc)))
                err_msg = os.linesep.join(err_msg_lines)
                raise DeploymentDescriptorError(err_msg)
            rtnval = self.parse_json(content)
            return rtnval

        if ext in (".yaml", ".yml"):
            try:
                with open(resolved_path, "r") as file_handle:
                    content = file_handle.read()
            except (OSError, IOError) as exc:
                err_msg_lines = [
                    "Failed to read deployment descriptor file."
                ]
                err_msg_lines.append("  File path: {!r}".format(resolved_path))
                err_msg_lines.append("  Error: {}".format(str(exc)))
                err_msg = os.linesep.join(err_msg_lines)
                raise DeploymentDescriptorError(err_msg)
            rtnval = self.parse_yaml(content)
            return rtnval

        err_msg_lines = [
            "Unrecognized file extension '{}'.".format(ext),
            "Supported extensions: {}".format(list(self.SUPPORTED_EXTENSIONS))
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise DeploymentDescriptorError(err_msg)

    def _validate_schema(self, data: dict) -> None:
        """
            Validates the descriptor data against the required schema.

            :param data: Dictionary to validate.

            :raises: DeploymentDescriptorError
        """
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                err_msg = "Missing required field '{}' in deployment descriptor.".format(field)
                raise DeploymentDescriptorError(err_msg)
        return

    def _resolve_path(self, file_path: str, app_context) -> str:
        """
            Resolves the file path relative to the AppContext directory.

            :param file_path: The file path to resolve.
            :param app_context: Optional AppContext.

            :returns: The resolved absolute file path.
        """
        resolved_path = file_path

        if app_context is not None:
            try:
                base_dir = app_context.directory
                resolved_path = os.path.join(base_dir, file_path)
            except Exception:
                resolved_path = file_path

        rtnval = resolved_path
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a string representation including the class name.

            :returns: A repr string for debugging.
        """
        rtnval = "DeploymentDescriptorParser()"
        return rtnval
