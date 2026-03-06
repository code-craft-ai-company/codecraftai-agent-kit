"""
    Exception classes for the Configuration & Extensibility feature.

    Provides ConfigurationValidationError for schema validation failures
    and PluginLoadError for plugin loading and activation failures.
"""

import os

from typing import List
from typing import Optional

from automojo.agentkit.errors import AgentKitError


class ConfigurationValidationError(AgentKitError):
    """
        Raised when configuration validation against a ConfigurationSchema fails.

        :param schema_name: The name of the schema that failed validation.
        :param errors: A list of validation error strings.
        :param warnings: An optional list of validation warning strings.
    """

    def __init__(self, schema_name: str, errors: List[str], warnings: List[str] = None) -> None:
        self._schema_name = schema_name
        self._errors = list(errors)
        self._warnings = list(warnings) if warnings is not None else []

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def schema_name(self) -> str:
        """
            The name of the schema that failed validation.

            :returns: The schema name string.
        """
        return self._schema_name

    @property
    def errors(self) -> List[str]:
        """
            The list of validation error strings.

            :returns: A list of error strings.
        """
        return list(self._errors)

    @property
    def warnings(self) -> List[str]:
        """
            The list of validation warning strings.

            :returns: A list of warning strings.
        """
        return list(self._warnings)

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the schema name and errors list.

            :returns: A formatted error message string.
        """
        error_count = len(self._errors)

        msg_lines = [
            "Configuration validation failed for schema '{}' with {} error(s).".format(
                self._schema_name, error_count
            )
        ]

        if len(self._errors) > 0:
            msg_lines.append("ERRORS:")
            for error_item in self._errors:
                msg_lines.append("    - {}".format(error_item))

        if len(self._warnings) > 0:
            msg_lines.append("WARNINGS:")
            for warning_item in self._warnings:
                msg_lines.append("    - {}".format(warning_item))

        errmsg = os.linesep.join(msg_lines)

        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            schema name, and error count.

            :returns: A repr string for debugging.
        """
        error_count = len(self._errors)
        repr_str = "{}(schema_name={!r}, error_count={})".format(
            self.__class__.__name__, self._schema_name, error_count
        )
        return repr_str


class PluginLoadError(AgentKitError):
    """
        Raised when a plugin fails to load or activate.

        :param plugin_name: The name of the plugin that failed.
        :param message: A descriptive error message.
        :param cause: An optional exception that caused the failure.
    """

    def __init__(self, plugin_name: str, message: str, cause: Optional[Exception] = None) -> None:
        self._plugin_name = plugin_name

        errmsg = self._format_message(plugin_name=plugin_name, message=message)
        super().__init__(errmsg, cause=cause)

        return

    @property
    def plugin_name(self) -> str:
        """
            The name of the plugin that failed to load or activate.

            :returns: The plugin name string.
        """
        return self._plugin_name

    def _format_message(self, plugin_name: str, message: str) -> str:
        """
            Builds a descriptive error message from the plugin name and message.

            :param plugin_name: The name of the plugin that failed.
            :param message: The descriptive error message.

            :returns: A formatted error message string.
        """
        errmsg = "Plugin '{}' failed to load: {}".format(plugin_name, message)
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            plugin name, and message.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(plugin_name={!r}, message={!r})".format(
            self.__class__.__name__, self._plugin_name, self._message
        )
        return repr_str
