"""
    Defines the PlatformService abstract base class representing a cloud
    or local service that a platform provides. Concrete subclasses include
    ComputeService, StorageService, and MessagingService.

    .. module:: ccai.agentkit.platform.services.platformservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract base class for all platform services.
"""

import abc

from ccai.agentkit.platform.platformtype import PlatformType


class PlatformService(abc.ABC):
    """
        Abstract base class representing a cloud or local service that a
        platform provides. Concrete subclasses include ComputeService,
        StorageService, and MessagingService.

        All platform services expose a service name, service type, and
        platform type. Subclasses must implement the is_available and
        health_check methods.

        :param service_name: A string identifying this service instance.
        :param service_type: The type of service (e.g. "compute", "storage", "messaging").
        :param platform_type: The PlatformType this service targets.
        :param configuration: An optional PlatformConfiguration for service-specific settings.
    """

    def __init__(self, service_name: str, service_type: str,
                 platform_type: PlatformType,
                 configuration: "PlatformConfiguration" = None) -> None:
        self._service_name = service_name
        self._service_type = service_type
        self._platform_type = platform_type
        self._configuration = configuration
        return

    @property
    def service_name(self) -> str:
        """
            The string identifying this service instance.

            :returns: The service name string.
        """
        rtnval = self._service_name
        return rtnval

    @property
    def service_type(self) -> str:
        """
            The type of service (e.g. "compute", "storage", "messaging").

            :returns: The service type string.
        """
        rtnval = self._service_type
        return rtnval

    @property
    def platform_type(self) -> PlatformType:
        """
            The PlatformType this service targets.

            :returns: The PlatformType value.
        """
        rtnval = self._platform_type
        return rtnval

    @abc.abstractmethod
    def is_available(self) -> bool:
        """
            Checks whether the service is available.

            :returns: True if the service is available, False otherwise.
        """

    @abc.abstractmethod
    def health_check(self) -> bool:
        """
            Returns a boolean indicating service health.

            :returns: True if the service is healthy, False otherwise.
        """

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            service name, service type, and platform type.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(service_name={}, service_type={}, platform_type={})".format(
            self.__class__.__name__, self._service_name,
            self._service_type, self._platform_type.to_string()
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the service name,
            service type, and platform type.

            :returns: A human-readable string.
        """
        rtnval = "{}: name={}, type={}, platform={}".format(
            self.__class__.__name__, self._service_name,
            self._service_type, self._platform_type.to_string()
        )
        return rtnval
