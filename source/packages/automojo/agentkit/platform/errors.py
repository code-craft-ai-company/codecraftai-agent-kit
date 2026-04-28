"""
    Exception hierarchy for the cross-platform runtime feature.

    Provides PlatformError as the base platform exception with specialized
    subclasses for detection, storage, compute, messaging, and deployment
    descriptor errors.

    .. module:: automojo.agentkit.platform.errors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Platform-specific exception hierarchy inheriting from AgentKitError.
"""

from typing import Optional

from automojo.agentkit.errors import AgentKitError


class PlatformError(AgentKitError):
    """
        Raised for general platform operation failures.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
        :param platform_type: An optional PlatformType indicating the platform.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None,
                 platform_type=None) -> None:
        super().__init__(message, cause=cause)
        self._platform_type = platform_type
        return

    @property
    def platform_type(self):
        """
            The optional platform type associated with this error.

            :returns: The PlatformType or None.
        """
        rtnval = self._platform_type
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            message, and platform type.

            :returns: A repr string for debugging.
        """
        platform_str = self._platform_type.to_string() if self._platform_type is not None else "unknown"
        rtnval = "PlatformError(message={}, platform_type={})".format(
            str(self), platform_str
        )
        return rtnval


class PlatformDetectionError(PlatformError):
    """
        Raised when platform detection fails or produces ambiguous results.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
        :param platform_type: An optional PlatformType indicating the platform.
    """
    pass


class StorageError(PlatformError):
    """
        Raised when a storage operation fails.

        :param message: A descriptive error message.
        :param operation_name: The name of the storage operation that failed.
        :param container_name: The name of the storage container involved.
        :param object_key: The optional object key involved.
        :param cause: An optional exception that caused this error.
        :param platform_type: An optional PlatformType indicating the platform.
    """

    def __init__(self, message: str, operation_name: str = None,
                 container_name: str = None, object_key: str = None,
                 cause: Optional[Exception] = None,
                 platform_type=None) -> None:
        super().__init__(message, cause=cause, platform_type=platform_type)
        self._operation_name = operation_name
        self._container_name = container_name
        self._object_key = object_key
        return

    @property
    def operation_name(self) -> str:
        """
            The name of the storage operation that failed.

            :returns: The operation name string or None.
        """
        rtnval = self._operation_name
        return rtnval

    @property
    def container_name(self) -> str:
        """
            The name of the storage container involved.

            :returns: The container name string or None.
        """
        rtnval = self._container_name
        return rtnval

    @property
    def object_key(self) -> str:
        """
            The optional object key involved in the failed operation.

            :returns: The object key string or None.
        """
        rtnval = self._object_key
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            message, operation, container, and platform type.

            :returns: A repr string for debugging.
        """
        platform_str = self._platform_type.to_string() if self._platform_type is not None else "unknown"
        rtnval = "StorageError(message={}, operation={}, container={}, platform_type={})".format(
            str(self), self._operation_name, self._container_name, platform_str
        )
        return rtnval


class ComputeError(PlatformError):
    """
        Raised when a compute operation fails.

        :param message: A descriptive error message.
        :param function_name: The name of the function that failed.
        :param cause: An optional exception that caused this error.
        :param platform_type: An optional PlatformType indicating the platform.
    """

    def __init__(self, message: str, function_name: str = None,
                 cause: Optional[Exception] = None,
                 platform_type=None) -> None:
        super().__init__(message, cause=cause, platform_type=platform_type)
        self._function_name = function_name
        return

    @property
    def function_name(self) -> str:
        """
            The name of the function that failed.

            :returns: The function name string or None.
        """
        rtnval = self._function_name
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            message, function name, and platform type.

            :returns: A repr string for debugging.
        """
        platform_str = self._platform_type.to_string() if self._platform_type is not None else "unknown"
        rtnval = "ComputeError(message={}, function_name={}, platform_type={})".format(
            str(self), self._function_name, platform_str
        )
        return rtnval


class MessagingError(PlatformError):
    """
        Raised when a messaging operation fails.

        :param message: A descriptive error message.
        :param queue_name: The name of the queue involved.
        :param cause: An optional exception that caused this error.
        :param platform_type: An optional PlatformType indicating the platform.
    """

    def __init__(self, message: str, queue_name: str = None,
                 cause: Optional[Exception] = None,
                 platform_type=None) -> None:
        super().__init__(message, cause=cause, platform_type=platform_type)
        self._queue_name = queue_name
        return

    @property
    def queue_name(self) -> str:
        """
            The name of the queue involved in the failed operation.

            :returns: The queue name string or None.
        """
        rtnval = self._queue_name
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            message, queue name, and platform type.

            :returns: A repr string for debugging.
        """
        platform_str = self._platform_type.to_string() if self._platform_type is not None else "unknown"
        rtnval = "MessagingError(message={}, queue_name={}, platform_type={})".format(
            str(self), self._queue_name, platform_str
        )
        return rtnval


class DeploymentDescriptorError(PlatformError):
    """
        Raised when a deployment descriptor is invalid or cannot be parsed.

        :param message: A descriptive error message.
        :param cause: An optional exception that caused this error.
        :param platform_type: An optional PlatformType indicating the platform.
    """
    pass
