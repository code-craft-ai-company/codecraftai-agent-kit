"""
    Defines the PlatformServiceRegistry that tracks all available
    PlatformService instances within a PlatformRuntime, providing
    lookup by service name and service type.

    .. module:: ccai.agentkit.platform.platformserviceregistry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Registry for platform service discovery by name and type.
"""

import logging

from typing import List
from typing import Optional

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.platform.services.platformservice import PlatformService


logger = logging.getLogger("ccai.agentkit.platform.registry")


class PlatformServiceRegistry:
    """
        Registry that tracks all available PlatformService instances within
        a PlatformRuntime, providing lookup by service name and service type.

        Each PlatformRuntime owns its own registry instance. The registry
        is keyed by service name and supports lookup by name, lookup by
        service type, enumeration, and count.
    """

    def __init__(self) -> None:
        self._services: dict = {}
        return

    def register(self, service: PlatformService) -> None:
        """
            Registers a PlatformService instance using the service name as key.

            :param service: The PlatformService to register.

            :raises: SemanticError
        """
        name = service.service_name
        if name in self._services:
            err_msg = "Duplicate service name '{}' in PlatformServiceRegistry.".format(name)
            raise SemanticError(err_msg)
        self._services[name] = service
        logger.debug(
            "Registered service '%s' (type=%s, platform=%s) in PlatformServiceRegistry.",
            name, service.service_type, service.platform_type.to_string()
        )
        return

    def deregister(self, service_name: str) -> None:
        """
            Removes a PlatformService by name. If the name is not found,
            the method does nothing.

            :param service_name: Name of the service to remove.
        """
        if service_name in self._services:
            del self._services[service_name]
            logger.debug(
                "Deregistered service '%s' from PlatformServiceRegistry.",
                service_name
            )
        return

    def lookup_by_name(self, service_name: str) -> Optional[PlatformService]:
        """
            Returns the PlatformService with the given name, or None if
            no service with that name is registered.

            :param service_name: Name of the service to look up.

            :returns: The PlatformService instance or None.
        """
        rtnval = self._services.get(service_name)
        return rtnval

    def lookup_by_type(self, service_type: str) -> List[PlatformService]:
        """
            Returns a list of PlatformService instances matching the
            provided service type string.

            :param service_type: The service type string to filter by.

            :returns: List of matching PlatformService instances.
        """
        rtnval = []
        for service in self._services.values():
            if service.service_type == service_type:
                rtnval.append(service)
        return rtnval

    def list_all(self) -> List[PlatformService]:
        """
            Returns a list of all registered PlatformService instances.

            :returns: List of PlatformService instances.
        """
        rtnval = list(self._services.values())
        return rtnval

    @property
    def count(self) -> int:
        """
            Returns the count of currently registered services.

            :returns: Integer count.
        """
        rtnval = len(self._services)
        return rtnval

    def has_service(self, service_name: str) -> bool:
        """
            Returns whether a service with the given name is registered.

            :param service_name: Name of the service to check.

            :returns: True if registered, False otherwise.
        """
        rtnval = service_name in self._services
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name and the count of registered services.

            :returns: A repr string for debugging.
        """
        rtnval = "PlatformServiceRegistry(count={})".format(self.count)
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the registered
            service names and their service types.

            :returns: A human-readable string.
        """
        entries = []
        for name, service in self._services.items():
            entries.append("{}({})".format(name, service.service_type))
        rtnval = "PlatformServiceRegistry: [{}]".format(", ".join(entries))
        return rtnval
