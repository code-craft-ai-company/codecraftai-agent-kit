"""
    Exception hierarchy for the codecraftai-agent-kit framework.

    Provides AgentKitError as the base exception, with ConfigurationError,
    SemanticError, and LifecycleError as specialized subclasses.
"""

import os

from typing import Optional


class AgentKitError(Exception):
    """
        Base exception for all codecraftai-agent-kit framework errors.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        self._message = message
        self._cause = cause

        if cause is not None:
            super().__init__(message)
            self.__cause__ = cause
        else:
            super().__init__(message)

        return

    @property
    def message(self) -> str:
        """
            The descriptive error message.

            :returns: The error message string.
        """
        return self._message

    @property
    def cause(self) -> Optional[Exception]:
        """
            The optional cause exception.

            :returns: The cause exception or None.
        """
        return self._cause

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name and message.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(message={!r})".format(self.__class__.__name__, self._message)
        return repr_str


class ConfigurationError(AgentKitError):
    """
        Raised for configuration-related problems in the agent framework.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message, cause=cause)
        return


class SemanticError(AgentKitError):
    """
        Raised for API misuse in the agent framework.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message, cause=cause)
        return


class LifecycleError(AgentKitError):
    """
        Raised for errors that occur during lifecycle transitions.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message, cause=cause)
        return
