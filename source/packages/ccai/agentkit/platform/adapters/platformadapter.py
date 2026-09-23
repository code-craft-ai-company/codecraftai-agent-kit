"""
    Defines the PlatformAdapter abstract base class that bundles a complete
    set of platform service implementations (ComputeService, StorageService,
    MessagingService) for a specific platform. Concrete implementations
    provide AwsPlatformAdapter, AzurePlatformAdapter, GcpPlatformAdapter,
    and LocalPlatformAdapter.

    .. module:: ccai.agentkit.platform.adapters.platformadapter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract platform adapter base class bundling platform services.
"""

import abc
import logging

from ccai.agentkit.platform.platformconfiguration import PlatformConfiguration
from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.services.computeservice import ComputeService
from ccai.agentkit.platform.services.messagingservice import MessagingService
from ccai.agentkit.platform.services.storageservice import StorageService


logger = logging.getLogger("ccai.agentkit.platform.adapters")


class PlatformAdapter(abc.ABC):
    """
        Abstract base class that bundles a complete set of platform service
        implementations for a specific platform. Concrete implementations
        provide compute, storage, and messaging services as a unit.

        Swapping platforms means swapping one adapter, not three services.

        :param configuration: The PlatformConfiguration for initializing
            platform-specific service clients.
    """

    def __init__(self, configuration: PlatformConfiguration) -> None:
        self._configuration = configuration
        return

    @property
    @abc.abstractmethod
    def platform_type(self) -> PlatformType:
        """
            Returns the PlatformType for this adapter.

            :returns: The PlatformType value.
        """

    @abc.abstractmethod
    def get_compute_service(self) -> ComputeService:
        """
            Returns the ComputeService for this platform.

            :returns: A ComputeService instance.
        """

    @abc.abstractmethod
    def get_storage_service(self) -> StorageService:
        """
            Returns the StorageService for this platform.

            :returns: A StorageService instance.
        """

    @abc.abstractmethod
    def get_messaging_service(self) -> MessagingService:
        """
            Returns the MessagingService for this platform.

            :returns: A MessagingService instance.
        """

    def get_all_services(self) -> list:
        """
            Returns a list of all PlatformService instances provided by
            this adapter.

            :returns: List of PlatformService instances.
        """
        rtnval = [
            self.get_compute_service(),
            self.get_storage_service(),
            self.get_messaging_service()
        ]
        return rtnval

    def health_check(self) -> dict:
        """
            Invokes health_check on each service and returns a dictionary
            mapping service names to boolean health status values.

            If a service health check raises an exception, the failure is
            logged at WARNING level and the service is reported as unhealthy.

            :returns: Dictionary of service name to health boolean.
        """
        result = {}
        services = self.get_all_services()

        for service in services:
            try:
                healthy = service.health_check()
                result[service.service_name] = healthy
            except Exception as ex:
                logger.warning(
                    "Health check failed for service '%s' on platform '%s': %s",
                    service.service_name, self.platform_type.to_string(), str(ex)
                )
                result[service.service_name] = False

        rtnval = result
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and platform type.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(platform_type={})".format(
            self.__class__.__name__, self.platform_type.to_string()
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the platform type
            and the list of available service names.

            :returns: A human-readable string.
        """
        service_names = [s.service_name for s in self.get_all_services()]
        rtnval = "{}: platform={}, services={}".format(
            self.__class__.__name__, self.platform_type.to_string(), service_names
        )
        return rtnval
