"""
    Exception classes for the Tool & Capability System.

    Provides ToolValidationError for input/output schema validation failures
    and ToolExecutionError for tool runtime execution failures.
"""

import os

from typing import List

from automojo.agentkit.errors import AgentKitError


class ToolValidationError(AgentKitError):
    """
        Raised when input or output validation against a ToolSchema fails.

        :param tool_name: The name of the tool that failed validation.
        :param direction: The validation direction, either "input" or "output".
        :param errors: A list of validation error strings.
    """

    def __init__(self, tool_name: str, direction: str, errors: List[str]) -> None:
        self._tool_name = tool_name
        self._direction = direction
        self._errors = list(errors)

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def tool_name(self) -> str:
        """
            The name of the tool that failed validation.

            :returns: The tool name string.
        """
        return self._tool_name

    @property
    def direction(self) -> str:
        """
            The validation direction, either "input" or "output".

            :returns: The direction string.
        """
        return self._direction

    @property
    def errors(self) -> List[str]:
        """
            The list of validation error strings.

            :returns: A list of error strings.
        """
        return list(self._errors)

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the tool name, direction,
            and errors list.

            :returns: A formatted error message string.
        """
        error_count = len(self._errors)

        msg_lines = [
            "Tool '{}' {} validation failed with {} error(s).".format(
                self._tool_name, self._direction, error_count
            )
        ]

        if len(self._errors) > 0:
            msg_lines.append("ERRORS:")
            for error_item in self._errors:
                msg_lines.append("    - {}".format(error_item))

        errmsg = os.linesep.join(msg_lines)

        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            tool name, direction, and error count.

            :returns: A repr string for debugging.
        """
        error_count = len(self._errors)
        repr_str = "{}(tool_name={!r}, direction={!r}, error_count={})".format(
            self.__class__.__name__, self._tool_name, self._direction, error_count
        )
        return repr_str


class ToolExecutionError(AgentKitError):
    """
        Raised when a Tool's execute method encounters a runtime error.

        :param tool_name: The name of the tool that failed execution.
        :param cause: The original exception that caused the failure.
    """

    def __init__(self, tool_name: str, cause: Exception) -> None:
        self._tool_name = tool_name
        self._cause = cause

        errmsg = self._format_message()
        super().__init__(errmsg, cause=cause)

        return

    @property
    def tool_name(self) -> str:
        """
            The name of the tool that failed execution.

            :returns: The tool name string.
        """
        return self._tool_name

    @property
    def cause(self) -> Exception:
        """
            The original exception that caused the failure.

            :returns: The cause exception.
        """
        return self._cause

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the tool name and the
            cause exception.

            :returns: A formatted error message string.
        """
        msg_lines = [
            "Tool '{}' execution failed.".format(self._tool_name),
            "CAUSE: {}".format(str(self._cause))
        ]

        errmsg = os.linesep.join(msg_lines)

        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            tool name, and cause.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(tool_name={!r}, cause={!r})".format(
            self.__class__.__name__, self._tool_name, self._cause
        )
        return repr_str
