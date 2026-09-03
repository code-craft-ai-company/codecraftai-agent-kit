"""
    Declarative configuration for the observability system of an Agent.

    Provides the ObservabilityConfiguration class that defines logging format,
    log level, tracing enablement, metrics enablement, recording enablement,
    debug mode enablement, sampling rates, and exporter settings. Supports
    loading from dict, JSON string, JSON file, YAML string, and YAML file.
    Validates required fields and excludes resolved credential secret values
    from serialization output.
"""

import json
import os

from typing import Any, Optional

import yaml

from ccai.agentkit.errors import ConfigurationError


class ObservabilityConfiguration:
    """
        A configuration object that defines the observability system settings
        for an Agent.

        Supports loading from dict, JSON string, JSON file, YAML string,
        and YAML file. Validates log_level, log_format, and sampling_rate.
        Excludes resolved credential secret values from serialization output.
    """

    VALID_LOG_LEVELS = ("debug", "info", "warning", "error", "critical")
    VALID_LOG_FORMATS = ("json", "key_value", "human_readable")

    def __init__(self, log_level: str = "info", log_format: str = "human_readable",
                 tracing_enabled: bool = False, metrics_enabled: bool = False,
                 recording_enabled: bool = False, debug_mode_enabled: bool = False,
                 sampling_rate: float = 1.0, exporter_settings: Optional[dict] = None,
                 credentials: Optional[dict] = None,
                 resolved_credentials: Optional[dict] = None) -> None:
        """
            Initializes an ObservabilityConfiguration instance.

            :param log_level: The log level string, one of VALID_LOG_LEVELS.
            :param log_format: The log format string, one of VALID_LOG_FORMATS.
            :param tracing_enabled: Whether distributed tracing is enabled.
            :param metrics_enabled: Whether metrics collection is enabled.
            :param recording_enabled: Whether execution recording is enabled.
            :param debug_mode_enabled: Whether debug mode is enabled.
            :param sampling_rate: The sampling rate as a float between 0.0 and 1.0.
            :param exporter_settings: Optional dictionary of exporter settings.
            :param credentials: Optional dictionary of credential references.
            :param resolved_credentials: Optional dictionary of resolved credential objects.

            :raises: ConfigurationError
        """
        self._validate_log_level(log_level)
        self._validate_log_format(log_format)
        self._validate_sampling_rate(sampling_rate)

        self._log_level = log_level
        self._log_format = log_format
        self._tracing_enabled = tracing_enabled
        self._metrics_enabled = metrics_enabled
        self._recording_enabled = recording_enabled
        self._debug_mode_enabled = debug_mode_enabled
        self._sampling_rate = sampling_rate

        if exporter_settings is not None:
            self._exporter_settings = dict(exporter_settings)
        else:
            self._exporter_settings = {}

        if credentials is not None:
            self._credentials = dict(credentials)
        else:
            self._credentials = {}

        if resolved_credentials is not None:
            self._resolved_credentials = dict(resolved_credentials)
        else:
            self._resolved_credentials = {}

        return

    @classmethod
    def _validate_log_level(cls, log_level: str) -> None:
        """
            Validates that the log level is one of the valid log levels.

            :param log_level: The log level string to validate.

            :raises: ConfigurationError
        """
        is_valid = log_level in cls.VALID_LOG_LEVELS
        if is_valid is not True:
            err_msg_lines = [
                "Invalid log level provided."
            ]
            err_msg_lines.append("  Provided log level: {!r}".format(log_level))
            err_msg_lines.append("  Valid log levels: {}".format(list(cls.VALID_LOG_LEVELS)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        return

    @classmethod
    def _validate_log_format(cls, log_format: str) -> None:
        """
            Validates that the log format is one of the valid log formats.

            :param log_format: The log format string to validate.

            :raises: ConfigurationError
        """
        is_valid = log_format in cls.VALID_LOG_FORMATS
        if is_valid is not True:
            err_msg_lines = [
                "Invalid log format provided."
            ]
            err_msg_lines.append("  Provided log format: {!r}".format(log_format))
            err_msg_lines.append("  Valid log formats: {}".format(list(cls.VALID_LOG_FORMATS)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        return

    @classmethod
    def _validate_sampling_rate(cls, sampling_rate: float) -> None:
        """
            Validates that the sampling rate is between 0.0 and 1.0 inclusive.

            :param sampling_rate: The sampling rate to validate.

            :raises: ConfigurationError
        """
        is_valid = 0.0 <= sampling_rate <= 1.0
        if is_valid is not True:
            err_msg_lines = [
                "Invalid sampling rate provided."
            ]
            err_msg_lines.append("  Provided sampling rate: {!r}".format(sampling_rate))
            err_msg_lines.append("  Sampling rate must be between 0.0 and 1.0 inclusive.")
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        return

    @property
    def log_level(self) -> str:
        """
            The configured log level.

            :returns: The log level string.
        """
        return self._log_level

    @property
    def log_format(self) -> str:
        """
            The configured log format.

            :returns: The log format string.
        """
        return self._log_format

    @property
    def tracing_enabled(self) -> bool:
        """
            Whether distributed tracing is enabled.

            :returns: True if tracing is enabled, False otherwise.
        """
        return self._tracing_enabled

    @property
    def metrics_enabled(self) -> bool:
        """
            Whether metrics collection is enabled.

            :returns: True if metrics collection is enabled, False otherwise.
        """
        return self._metrics_enabled

    @property
    def recording_enabled(self) -> bool:
        """
            Whether execution recording is enabled.

            :returns: True if recording is enabled, False otherwise.
        """
        return self._recording_enabled

    @property
    def debug_mode_enabled(self) -> bool:
        """
            Whether debug mode is enabled.

            :returns: True if debug mode is enabled, False otherwise.
        """
        return self._debug_mode_enabled

    @property
    def sampling_rate(self) -> float:
        """
            The configured sampling rate.

            :returns: The sampling rate as a float between 0.0 and 1.0.
        """
        return self._sampling_rate

    @property
    def exporter_settings(self) -> dict:
        """
            A defensive copy of the exporter settings dictionary.

            :returns: A dictionary containing exporter settings.
        """
        return dict(self._exporter_settings)

    @property
    def credentials(self) -> dict:
        """
            A defensive copy of the credential reference dictionary.

            Contains reference names only, not resolved secret values.

            :returns: A dictionary of credential references.
        """
        return dict(self._credentials)

    @property
    def resolved_credentials(self) -> dict:
        """
            A defensive copy of the resolved credential objects.

            :returns: A dictionary of resolved credential objects.
        """
        return dict(self._resolved_credentials)

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the configuration.

            Excludes resolved credential secret values. Includes credential
            reference names but not resolved values.

            :returns: A dictionary containing the configuration data.
        """
        result = {
            "log_level": self._log_level,
            "log_format": self._log_format,
            "tracing_enabled": self._tracing_enabled,
            "metrics_enabled": self._metrics_enabled,
            "recording_enabled": self._recording_enabled,
            "debug_mode_enabled": self._debug_mode_enabled,
            "sampling_rate": self._sampling_rate,
        }

        if len(self._exporter_settings) > 0:
            result["exporter_settings"] = dict(self._exporter_settings)

        if len(self._credentials) > 0:
            result["credentials"] = dict(self._credentials)

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

    @classmethod
    def from_dict(cls, data: dict, app_context: Any = None) -> "ObservabilityConfiguration":
        """
            Creates an ObservabilityConfiguration from a dictionary.

            Validates fields, resolves credential references if present,
            and returns a configured instance.

            :param data: The configuration dictionary.
            :param app_context: Optional application context for resolving
                credentials and file paths.

            :returns: An ObservabilityConfiguration instance.
            :raises: ConfigurationError
        """
        if not isinstance(data, dict):
            err_msg_lines = [
                "Configuration data must be a dictionary."
            ]
            err_msg_lines.append("  Received type: {}".format(type(data).__name__))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg)

        log_level = data.get("log_level", "info")
        log_format = data.get("log_format", "human_readable")
        tracing_enabled = data.get("tracing_enabled", False)
        metrics_enabled = data.get("metrics_enabled", False)
        recording_enabled = data.get("recording_enabled", False)
        debug_mode_enabled = data.get("debug_mode_enabled", False)
        sampling_rate = data.get("sampling_rate", 1.0)
        exporter_settings = data.get("exporter_settings", None)
        credentials_data = data.get("credentials", None)

        resolved_credentials = {}

        has_credentials = credentials_data is not None and len(credentials_data) > 0

        if has_credentials is True and app_context is not None:
            resolved_credentials = cls._resolve_credentials(credentials_data, app_context)

        configuration = cls(
            log_level=log_level,
            log_format=log_format,
            tracing_enabled=tracing_enabled,
            metrics_enabled=metrics_enabled,
            recording_enabled=recording_enabled,
            debug_mode_enabled=debug_mode_enabled,
            sampling_rate=sampling_rate,
            exporter_settings=exporter_settings,
            credentials=credentials_data,
            resolved_credentials=resolved_credentials,
        )
        return configuration

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
            # A core ccai.errors ConfigurationError (e.g. a missing vault key)
            # derives from BaseException and deliberately passes through this
            # handler: a wrong configuration must terminate the run.
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
    def from_json(cls, json_str: str, app_context: Any = None) -> "ObservabilityConfiguration":
        """
            Creates an ObservabilityConfiguration from a JSON string.

            :param json_str: A JSON string containing configuration data.
            :param app_context: Optional application context for resolving references.

            :returns: An ObservabilityConfiguration instance.
            :raises: ConfigurationError
        """
        try:
            data = json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as exc:
            err_msg_lines = [
                "Failed to parse JSON configuration string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        configuration = cls.from_dict(data, app_context=app_context)
        return configuration

    @classmethod
    def from_yaml(cls, yaml_str: str, app_context: Any = None) -> "ObservabilityConfiguration":
        """
            Creates an ObservabilityConfiguration from a YAML string.

            :param yaml_str: A YAML string containing configuration data.
            :param app_context: Optional application context for resolving references.

            :returns: An ObservabilityConfiguration instance.
            :raises: ConfigurationError
        """
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as exc:
            err_msg_lines = [
                "Failed to parse YAML configuration string."
            ]
            err_msg_lines.append("  Error: {}".format(str(exc)))
            err_msg = os.linesep.join(err_msg_lines)
            raise ConfigurationError(err_msg, cause=exc)

        configuration = cls.from_dict(data, app_context=app_context)
        return configuration

    @classmethod
    def from_json_file(cls, file_path: str, app_context: Any = None) -> "ObservabilityConfiguration":
        """
            Creates an ObservabilityConfiguration from a JSON file.

            If app_context is provided, the file path is resolved relative
            to the AppContext directory.

            :param file_path: Path to the JSON configuration file.
            :param app_context: Optional application context for resolving
                the file path and references.

            :returns: An ObservabilityConfiguration instance.
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
    def from_yaml_file(cls, file_path: str, app_context: Any = None) -> "ObservabilityConfiguration":
        """
            Creates an ObservabilityConfiguration from a YAML file.

            If app_context is provided, the file path is resolved relative
            to the AppContext directory.

            :param file_path: Path to the YAML configuration file.
            :param app_context: Optional application context for resolving
                the file path and references.

            :returns: An ObservabilityConfiguration instance.
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

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            log level, log format, and tracing enabled status.

            :returns: A repr string for debugging.
        """
        repr_str = "ObservabilityConfiguration(log_level={!r}, log_format={!r}, tracing_enabled={!r})".format(
            self._log_level, self._log_format, self._tracing_enabled
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the configuration.

            :returns: A human-readable string.
        """
        str_val = (
            "ObservabilityConfiguration: log_level={}, log_format={}, "
            "tracing={}, metrics={}, recording={}, debug={}, sampling_rate={}".format(
                self._log_level, self._log_format,
                self._tracing_enabled, self._metrics_enabled,
                self._recording_enabled, self._debug_mode_enabled,
                self._sampling_rate
            )
        )
        return str_val