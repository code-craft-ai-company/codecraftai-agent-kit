"""
    Defines the MessagingConfiguration class for declarative messaging
    system settings in the Communication & Messaging feature.

    A MessagingConfiguration contains the default transport name, default
    serialization format name, default request timeout, optional
    transport configurations, pub/sub settings, credential references,
    and additional options. The class provides JSON and YAML
    serialization and deserialization, including file-based loading
    with optional AppContext path resolution.

    Credential reference values are excluded from serialized output
    (as_dict, to_json) to prevent leaking secrets.

    Requirements: 20.1-20.15, 26.23, 26.24
"""

import json
import os

import yaml

from ccai.agentkit.errors import ConfigurationError


class MessagingConfiguration:
    """
        Configuration object defining default transport, serialization
        format, request timeout, transport configurations, pub/sub
        settings, credential references, and additional options for
        an Agent's messaging system.

        Validation is performed at construction time:
        - default_transport must be provided and non-empty
        - default_serialization_format must be provided and non-empty
        - default_request_timeout must be provided

        :param default_transport: The default transport name string.
        :param default_serialization_format: The default serialization
            format name string (e.g., "json").
        :param default_request_timeout: The default timeout in seconds
            for request/response exchanges as a float. Defaults to 30.0.
        :param transport_configurations: An optional dictionary mapping
            transport names to TransportConfiguration dictionaries.
            Defaults to an empty dictionary.
        :param pubsub_settings: An optional dictionary of pub/sub
            configuration settings. Defaults to an empty dictionary.
        :param credential_references: An optional dictionary of named
            credential references for authentication. Defaults to an
            empty dictionary.
        :param options: An optional dictionary of additional
            configuration options. Defaults to an empty dictionary.

        :raises ConfigurationError: If required fields are missing.
    """

    REQUIRED_FIELDS = ["default_transport", "default_serialization_format", "default_request_timeout"]

    def __init__(self, default_transport: str,
                 default_serialization_format: str,
                 default_request_timeout: float = 30.0,
                 transport_configurations: dict = None,
                 pubsub_settings: dict = None,
                 credential_references: dict = None,
                 options: dict = None) -> None:

        self._validate_required_fields(
            default_transport=default_transport,
            default_serialization_format=default_serialization_format,
            default_request_timeout=default_request_timeout
        )

        self._default_transport = default_transport
        self._default_serialization_format = default_serialization_format
        self._default_request_timeout = default_request_timeout
        self._transport_configurations = dict(transport_configurations) if transport_configurations is not None else {}
        self._pubsub_settings = dict(pubsub_settings) if pubsub_settings is not None else {}
        self._credential_references = dict(credential_references) if credential_references is not None else {}
        self._options = dict(options) if options is not None else {}

        return

    def _validate_required_fields(self, default_transport: str,
                                  default_serialization_format: str,
                                  default_request_timeout: float) -> None:
        """
            Validates that all required fields are present and non-empty.

            :param default_transport: The default transport name to validate.
            :param default_serialization_format: The default serialization
                format name to validate.
            :param default_request_timeout: The default request timeout
                to validate.

            :raises ConfigurationError: If any required field is missing
                or empty.
        """
        missing_fields = []

        if default_transport is None or (isinstance(default_transport, str) and len(default_transport.strip()) == 0):
            missing_fields.append("default_transport")

        if default_serialization_format is None or (isinstance(default_serialization_format, str) and len(default_serialization_format.strip()) == 0):
            missing_fields.append("default_serialization_format")

        if default_request_timeout is None:
            missing_fields.append("default_request_timeout")

        if len(missing_fields) > 0:
            errmsg = "MessagingConfiguration is missing required field(s): {}.".format(
                ", ".join(missing_fields)
            )
            raise ConfigurationError(errmsg)

        return

    @property
    def default_transport(self) -> str:
        """
            The default transport name string.

            :returns: The default transport name.
        """
        return self._default_transport

    @property
    def default_serialization_format(self) -> str:
        """
            The default serialization format name string.

            :returns: The default serialization format name.
        """
        return self._default_serialization_format

    @property
    def default_request_timeout(self) -> float:
        """
            The default request/response timeout in seconds.

            :returns: A float representing the timeout in seconds.
        """
        return self._default_request_timeout

    @property
    def transport_configurations(self) -> dict:
        """
            The transport configurations dictionary mapping transport
            names to TransportConfiguration dictionaries.

            :returns: A dictionary of transport configurations.
        """
        return dict(self._transport_configurations)

    @property
    def pubsub_settings(self) -> dict:
        """
            The pub/sub configuration settings dictionary.

            :returns: A dictionary of pub/sub settings.
        """
        return dict(self._pubsub_settings)

    @property
    def credential_references(self) -> dict:
        """
            The named credential references dictionary.

            :returns: A dictionary of credential reference names
                to their reference data.
        """
        return dict(self._credential_references)

    @property
    def options(self) -> dict:
        """
            The additional configuration options dictionary.

            :returns: A dictionary of option key-value pairs.
        """
        return dict(self._options)

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
            "default_transport": self._default_transport,
            "default_serialization_format": self._default_serialization_format,
            "default_request_timeout": self._default_request_timeout,
        }

        if len(self._transport_configurations) > 0:
            rtnval["transport_configurations"] = dict(self._transport_configurations)

        if len(self._pubsub_settings) > 0:
            rtnval["pubsub_settings"] = dict(self._pubsub_settings)

        if len(self._credential_references) > 0:
            rtnval["credential_references"] = sorted(self._credential_references.keys())

        if len(self._options) > 0:
            rtnval["options"] = dict(self._options)

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

    @classmethod
    def from_dict(cls, config_data: dict,
                  app_context=None) -> "MessagingConfiguration":
        """
            Constructs a MessagingConfiguration from a dictionary.

            :param config_data: A dictionary containing configuration
                fields.
            :param app_context: An optional AppContext for path
                resolution. Currently unused for from_dict but
                accepted for API consistency.

            :returns: A MessagingConfiguration instance.

            :raises ConfigurationError: If required fields are missing.
        """
        default_transport = config_data.get("default_transport", None)
        default_serialization_format = config_data.get("default_serialization_format", None)
        default_request_timeout = config_data.get("default_request_timeout", 30.0)
        transport_configurations = config_data.get("transport_configurations", None)
        pubsub_settings = config_data.get("pubsub_settings", None)
        credential_references = config_data.get("credential_references", None)
        if isinstance(credential_references, (list, tuple)):
            reference_names = credential_references
            credential_references = {name: None for name in reference_names}
        options = config_data.get("options", None)

        rtnval = cls(
            default_transport=default_transport,
            default_serialization_format=default_serialization_format,
            default_request_timeout=default_request_timeout,
            transport_configurations=transport_configurations,
            pubsub_settings=pubsub_settings,
            credential_references=credential_references,
            options=options
        )
        return rtnval

    @classmethod
    def from_json(cls, json_str: str,
                  app_context=None) -> "MessagingConfiguration":
        """
            Deserializes a JSON string into a MessagingConfiguration
            instance.

            :param json_str: A JSON string containing configuration
                fields.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A MessagingConfiguration instance.

            :raises ConfigurationError: If required fields are missing.
        """
        data = json.loads(json_str)
        rtnval = cls.from_dict(config_data=data, app_context=app_context)
        return rtnval

    @classmethod
    def from_json_file(cls, file_path: str,
                       app_context=None) -> "MessagingConfiguration":
        """
            Loads a MessagingConfiguration from a JSON file.

            When an app_context is provided, the file path is
            resolved relative to the AppContext directory.

            :param file_path: The path to the JSON configuration
                file.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A MessagingConfiguration instance.

            :raises ConfigurationError: If required fields are missing.
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
                  app_context=None) -> "MessagingConfiguration":
        """
            Deserializes a YAML string into a MessagingConfiguration
            instance.

            :param yaml_str: A YAML string containing configuration
                fields.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A MessagingConfiguration instance.

            :raises ConfigurationError: If required fields are missing.
        """
        data = yaml.safe_load(yaml_str)
        rtnval = cls.from_dict(config_data=data, app_context=app_context)
        return rtnval

    @classmethod
    def from_yaml_file(cls, file_path: str,
                       app_context=None) -> "MessagingConfiguration":
        """
            Loads a MessagingConfiguration from a YAML file.

            When an app_context is provided, the file path is
            resolved relative to the AppContext directory.

            :param file_path: The path to the YAML configuration
                file.
            :param app_context: An optional AppContext for path
                resolution.

            :returns: A MessagingConfiguration instance.

            :raises ConfigurationError: If required fields are missing.
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
            class name, default transport name, and default
            serialization format.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(default_transport={!r}, default_serialization_format={!r})".format(
            self.__class__.__name__, self._default_transport,
            self._default_serialization_format
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the default
            transport name, default serialization format, and default
            request timeout.

            :returns: A human-readable string describing the
                configuration.
        """
        str_val = (
            "MessagingConfiguration: default_transport={}, "
            "default_serialization_format={}, "
            "default_request_timeout={}s"
        ).format(
            self._default_transport,
            self._default_serialization_format,
            self._default_request_timeout
        )
        return str_val
