"""
    Defines the TransportConfiguration class for declarative transport
    protocol settings in the Communication & Messaging feature.

    A TransportConfiguration contains the protocol type, host, port,
    optional path, headers, timeout, protocol-specific options, and
    credential references. The class provides JSON and YAML
    serialization and deserialization, including file-based loading
    with optional AppContext path resolution.

    Credential reference values are excluded from serialized output
    (as_dict, to_json, to_yaml) to prevent leaking secrets.

    Requirements: 2.1-2.19, 26.21, 26.22
"""

import json
import os

from typing import Optional

import yaml

from ccai.agentkit.errors import ConfigurationError


class TransportConfiguration:
    """
        Configuration object defining transport protocol type, connection
        parameters, authentication settings, and protocol-specific options.

        Validation is performed at construction time:
        - protocol_type must be one of the VALID_PROTOCOL_TYPES
        - host must be provided and non-empty
        - port must be provided

        :param protocol_type: The transport protocol type string. Must be
            one of "http", "websocket", "grpc", or "message_queue".
        :param host: The host address string.
        :param port: The port number integer.
        :param path: An optional URL path string. Defaults to None.
        :param headers: An optional dictionary of default headers.
            Defaults to an empty dictionary.
        :param timeout: The connection/request timeout in seconds as a
            float. Defaults to 30.0.
        :param options: An optional dictionary of protocol-specific
            options. Defaults to an empty dictionary.
        :param credential_references: An optional dictionary of named
            credential references for authentication. Defaults to an
            empty dictionary.

        :raises ConfigurationError: If protocol_type is not valid, or
            if required fields are missing.
    """

    VALID_PROTOCOL_TYPES = {"http", "websocket", "grpc", "message_queue"}
    REQUIRED_FIELDS = ["protocol_type", "host", "port"]

    def __init__(self, protocol_type: str, host: str, port: int,
                 path: str = None, headers: dict = None,
                 timeout: float = 30.0, options: dict = None,
                 credential_references: dict = None) -> None:

        self._validate_required_fields(
            protocol_type=protocol_type, host=host, port=port
        )
        self._validate_protocol_type(protocol_type=protocol_type)

        self._protocol_type = protocol_type
        self._host = host
        self._port = port
        self._path = path
        self._headers = dict(headers) if headers is not None else {}
        self._timeout = timeout
        self._options = dict(options) if options is not None else {}
        self._credential_references = dict(credential_references) if credential_references is not None else {}

        return

    def _validate_required_fields(self, protocol_type: str, host: str,
                                  port: int) -> None:
        """
            Validates that all required fields are present and non-empty.

            :param protocol_type: The protocol type value to validate.
            :param host: The host value to validate.
            :param port: The port value to validate.

            :raises ConfigurationError: If any required field is missing
                or empty.
        """
        missing_fields = []

        if protocol_type is None or (isinstance(protocol_type, str) and len(protocol_type.strip()) == 0):
            missing_fields.append("protocol_type")

        if host is None or (isinstance(host, str) and len(host.strip()) == 0):
            missing_fields.append("host")

        if port is None:
            missing_fields.append("port")

        if len(missing_fields) > 0:
            errmsg = "TransportConfiguration is missing required field(s): {}.".format(
                ", ".join(missing_fields)
            )
            raise ConfigurationError(errmsg)

        return

    def _validate_protocol_type(self, protocol_type: str) -> None:
        """
            Validates that the protocol type is one of the valid values.

            :param protocol_type: The protocol type string to validate.

            :raises ConfigurationError: If the protocol type is not valid.
        """
        if protocol_type not in self.VALID_PROTOCOL_TYPES:
            valid_types_str = ", ".join(sorted(self.VALID_PROTOCOL_TYPES))
            errmsg = (
                "Invalid protocol type '{}'. "
                "Valid protocol types are: {}."
            ).format(protocol_type, valid_types_str)
            raise ConfigurationError(errmsg)

        return

    @property
    def protocol_type(self) -> str:
        """
            The transport protocol type string.

            :returns: One of "http", "websocket", "grpc", or
                "message_queue".
        """
        return self._protocol_type

    @property
    def host(self) -> str:
        """
            The host address string.

            :returns: The host address.
        """
        return self._host

    @property
    def port(self) -> int:
        """
            The port number integer.

            :returns: The port number.
        """
        return self._port

    @property
    def path(self) -> Optional[str]:
        """
            The optional URL path string.

            :returns: The path string or None.
        """
        return self._path

    @property
    def headers(self) -> dict:
        """
            The default headers dictionary.

            :returns: A dictionary of header key-value pairs.
        """
        return dict(self._headers)

    @property
    def timeout(self) -> float:
        """
            The connection/request timeout in seconds.

            :returns: A float representing the timeout in seconds.
        """
        return self._timeout

    @property
    def options(self) -> dict:
        """
            The protocol-specific options dictionary.

            :returns: A dictionary of option key-value pairs.
        """
        return dict(self._options)

    @property
    def credential_references(self) -> dict:
        """
            The named credential references dictionary.

            :returns: A dictionary of credential reference names
                to their reference data.
        """
        return dict(self._credential_references)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration.

            Credential reference values are excluded from the output
            to prevent leaking secrets. Only the credential reference
            names are included.

            :returns: A dictionary containing all configuration fields
                except resolved credential values.
        """
        rtnval = {
            "protocol_type": self._protocol_type,
            "host": self._host,
            "port": self._port,
            "timeout": self._timeout,
        }

        if self._path is not None:
            rtnval["path"] = self._path

        if len(self._headers) > 0:
            rtnval["headers"] = dict(self._headers)

        if len(self._options) > 0:
            rtnval["options"] = dict(self._options)

        if len(self._credential_references) > 0:
            rtnval["credential_references"] = sorted(self._credential_references.keys())

        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the configuration.

            Credential reference values are excluded from the output
            to prevent leaking secrets.

            :returns: A JSON string containing all configuration fields
                except resolved credential values.
        """
        data = self.as_dict()
        rtnval = json.dumps(data)
        return rtnval

    def to_yaml(self) -> str:
        """
            Returns a YAML string representation of the configuration.

            Credential reference values are excluded from the output
            to prevent leaking secrets.

            :returns: A YAML string containing all configuration fields
                except resolved credential values.
        """
        data = self.as_dict()
        rtnval = yaml.dump(data, default_flow_style=False)
        return rtnval

    @classmethod
    def from_dict(cls, config_data: dict,
                  app_context=None) -> "TransportConfiguration":
        """
            Constructs a TransportConfiguration from a dictionary.

            :param config_data: A dictionary containing configuration
                fields.
            :param app_context: An optional AppContext for path
                resolution. Currently unused for from_dict but
                accepted for API consistency.

            :returns: A TransportConfiguration instance.

            :raises ConfigurationError: If required fields are missing
                or the protocol type is invalid.
        """
        protocol_type = config_data.get("protocol_type", None)
        host = config_data.get("host", None)
        port = config_data.get("port", None)
        path = config_data.get("path", None)
        headers = config_data.get("headers", None)
        timeout = config_data.get("timeout", 30.0)
        options = config_data.get("options", None)
        credential_references = config_data.get("credential_references", None)
        if isinstance(credential_references, (list, tuple)):
            reference_names = credential_references
            credential_references = {name: None for name in reference_names}

        rtnval = cls(
            protocol_type=protocol_type,
            host=host,
            port=port,
            path=path,
            headers=headers,
            timeout=timeout,
            options=options,
            credential_references=credential_references
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str,
                  app_context=None) -> "TransportConfiguration":
        """
            Deserializes a JSON string into a TransportConfiguration
            instance.

            :param json_str: A JSON string containing configuration
                fields.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A TransportConfiguration instance.

            :raises ConfigurationError: If required fields are missing
                or the protocol type is invalid.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(config_data=data, app_context=app_context)
        return rtnval

    @classmethod
    def from_json_file(cls, file_path: str,
                       app_context=None) -> "TransportConfiguration":
        """
            Loads a TransportConfiguration from a JSON file.

            When an app_context is provided, the file path is
            resolved relative to the AppContext directory.

            :param file_path: The path to the JSON configuration
                file.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A TransportConfiguration instance.

            :raises ConfigurationError: If required fields are missing
                or the protocol type is invalid.
        """
        resolved_path = file_path

        if app_context is not None:
            base_dir = app_context.home_directory
            resolved_path = os.path.join(base_dir, file_path)

        with open(resolved_path, "r") as fh:
            json_str = fh.read()

        rtnval = cls.from_json(json_str=json_str, app_context=app_context)
        return rtnval

    @classmethod
    def from_yaml(cls, yaml_str: str,
                  app_context=None) -> "TransportConfiguration":
        """
            Deserializes a YAML string into a TransportConfiguration
            instance.

            :param yaml_str: A YAML string containing configuration
                fields.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A TransportConfiguration instance.

            :raises ConfigurationError: If required fields are missing
                or the protocol type is invalid.
        """
        data = yaml.safe_load(yaml_str)
        rtnval = cls.from_dict(config_data=data, app_context=app_context)
        return rtnval

    @classmethod
    def from_yaml_file(cls, file_path: str,
                       app_context=None) -> "TransportConfiguration":
        """
            Loads a TransportConfiguration from a YAML file.

            When an app_context is provided, the file path is
            resolved relative to the AppContext directory.

            :param file_path: The path to the YAML configuration
                file.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A TransportConfiguration instance.

            :raises ConfigurationError: If required fields are missing
                or the protocol type is invalid.
        """
        resolved_path = file_path

        if app_context is not None:
            base_dir = app_context.home_directory
            resolved_path = os.path.join(base_dir, file_path)

        with open(resolved_path, "r") as fh:
            yaml_str = fh.read()

        rtnval = cls.from_yaml(yaml_str=yaml_str, app_context=app_context)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, protocol type, host, and port.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(protocol_type={!r}, host={!r}, port={})".format(
            self.__class__.__name__, self._protocol_type,
            self._host, self._port
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the protocol
            type, host, port, and timeout.

            :returns: A human-readable string describing the
                configuration.
        """
        str_val = (
            "TransportConfiguration: protocol_type={}, "
            "host={}, port={}, timeout={}s"
        ).format(
            self._protocol_type, self._host,
            self._port, self._timeout
        )
        return str_val
