"""
    Defines the ComputeService abstract base class representing a compute
    service that can invoke functions, manage execution contexts, and report
    execution status. Concrete implementations wrap AWS Lambda, Azure
    Functions, GCP Cloud Functions, and local process execution.

    .. module:: ccai.agentkit.platform.services.computeservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract compute service interface for platform compute services.
"""

import abc

from typing import Optional

from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.services.platformservice import PlatformService


class ComputeService(PlatformService, abc.ABC):
    """
        Abstract base class representing a compute service that can invoke
        functions, manage execution contexts, and report execution status.

        Inherits from PlatformService with service_type fixed to "compute".
        Subclasses must implement invoke, invoke_async, get_invocation_status,
        and list_functions in addition to is_available and health_check.

        :param service_name: A string identifying this compute service instance.
        :param platform_type: The PlatformType this service targets.
        :param configuration: An optional PlatformConfiguration for service-specific settings.
    """

    def __init__(self, service_name: str, platform_type: PlatformType,
                 configuration: "PlatformConfiguration" = None) -> None:
        super().__init__(
            service_name=service_name,
            service_type="compute",
            platform_type=platform_type,
            configuration=configuration
        )
        return

    @abc.abstractmethod
    def invoke(self, function_name: str, payload: dict,
               timeout: float = None) -> "InvocationResult":
        """
            Invokes a function synchronously.

            :param function_name: Name of the function to invoke.
            :param payload: Dictionary payload to pass to the function.
            :param timeout: Optional timeout in seconds.

            :returns: An InvocationResult with the execution outcome.
            :raises: ComputeError
        """
        ...

    @abc.abstractmethod
    def invoke_async(self, function_name: str, payload: dict) -> str:
        """
            Invokes a function asynchronously.

            :param function_name: Name of the function to invoke.
            :param payload: Dictionary payload to pass to the function.

            :returns: A request identifier string for tracking.
            :raises: ComputeError
        """
        ...

    @abc.abstractmethod
    def get_invocation_status(self, request_id: str) -> "InvocationResult":
        """
            Returns the current status of an asynchronous invocation.

            :param request_id: The request identifier from invoke_async.

            :returns: An InvocationResult representing the current status.
            :raises: ComputeError
        """
        ...

    @abc.abstractmethod
    def list_functions(self) -> list:
        """
            Returns a list of available function name strings.

            :returns: List of function name strings.
            :raises: ComputeError
        """
        ...

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            service name, and platform type.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(service_name={}, platform_type={})".format(
            self.__class__.__name__, self._service_name,
            self._platform_type.to_string()
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the service name
            and platform type.

            :returns: A human-readable string.
        """
        rtnval = "{}: name={}, platform={}".format(
            self.__class__.__name__, self._service_name,
            self._platform_type.to_string()
        )
        return rtnval
