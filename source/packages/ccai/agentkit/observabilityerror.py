"""
    Exception class for observability operation failures.

    Provides ObservabilityError as a specialized subclass of AgentKitError,
    raised when an observability operation fails due to an exporter error,
    recording error, or pipeline configuration error.
"""

from typing import Optional

from ccai.agentkit.errors import AgentKitError


class ObservabilityError(AgentKitError):
    """
        Raised when an observability operation fails due to an exporter
        error, recording error, or pipeline configuration error.

        :param component_name: The name of the component where the failure occurred
            (e.g., exporter class name, recorder name).
        :param operation_name: The name of the operation that failed.
        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
    """

    def __init__(self, component_name: str, operation_name: str, message: str,
                 cause: Optional[Exception] = None) -> None:
        self._component_name = component_name
        self._operation_name = operation_name

        super().__init__(message, cause=cause)
        return

    @property
    def component_name(self) -> str:
        """
            The name of the component where the failure occurred.

            :returns: The component name string.
        """
        return self._component_name

    @property
    def operation_name(self) -> str:
        """
            The name of the operation that failed.

            :returns: The operation name string.
        """
        return self._operation_name

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            component name, operation name, and message.

            :returns: A repr string for debugging.
        """
        repr_str = (
            "{}(component_name={!r}, operation_name={!r}, message={!r})"
        ).format(
            self.__class__.__name__,
            self._component_name,
            self._operation_name,
            self._message
        )
        return repr_str
