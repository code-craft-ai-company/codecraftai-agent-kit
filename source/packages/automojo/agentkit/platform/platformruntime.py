"""
    Defines the PlatformRuntime class that manages the active platform
    environment for an Agent, providing access to platform services through
    a single entry point. Supports auto-configuration via platform detection
    and extension point integration for plugin adapters.

    .. module:: automojo.agentkit.platform.platformruntime
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Entry point for agents to access platform services with auto-configuration.
"""

import logging
import os

from typing import Optional

from automojo.agentkit.platform.errors import PlatformError
from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration
from automojo.agentkit.platform.platformdetector import PlatformDetector
from automojo.agentkit.platform.platformserviceregistry import PlatformServiceRegistry
from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.computeservice import ComputeService
from automojo.agentkit.platform.services.messagingservice import MessagingService
from automojo.agentkit.platform.services.platformservice import PlatformService
from automojo.agentkit.platform.services.storageservice import StorageService


logger = logging.getLogger("automojo.agentkit.platform.runtime")


class PlatformRuntime:
    """
        Manages the active platform environment for an Agent, providing
        access to platform services through a single entry point.

        The PlatformRuntime accepts a PlatformConfiguration and a
        PlatformAdapter at construction, registers all adapter services
        into a PlatformServiceRegistry, and exposes convenience methods
        for accessing compute, storage, and messaging services.

        The create_auto class method provides auto-configuration by
        detecting the current platform, building a default configuration
        from the environment when needed, and selecting the appropriate
        adapter (checking extension points for plugin adapters first,
        then falling back to built-in adapters).

        :param configuration: The PlatformConfiguration for the runtime.
        :param adapter: The PlatformAdapter providing platform services.
    """

    def __init__(self, configuration: PlatformConfiguration,
                 adapter: "PlatformAdapter") -> None:
        self._configuration = configuration
        self._adapter = adapter
        self._registry = PlatformServiceRegistry()
        self._initialize_services()
        logger.info(
            "PlatformRuntime initialized: platform=%s, region=%s, services=%s",
            configuration.platform_type.to_string(),
            configuration.region,
            [s.service_name for s in self._registry.list_all()]
        )
        return

    def _initialize_services(self) -> None:
        """
            Registers all services from the adapter into the service registry.
        """
        services = self._adapter.get_all_services()
        for service in services:
            self._registry.register(service)
        return

    @property
    def platform_type(self) -> PlatformType:
        """
            Returns the PlatformType of the active platform.

            :returns: The PlatformType value.
        """
        rtnval = self._configuration.platform_type
        return rtnval

    @property
    def configuration(self) -> PlatformConfiguration:
        """
            Returns the PlatformConfiguration for this runtime.

            :returns: The PlatformConfiguration instance.
        """
        rtnval = self._configuration
        return rtnval

    @property
    def adapter(self) -> "PlatformAdapter":
        """
            Returns the PlatformAdapter for this runtime.

            :returns: The PlatformAdapter instance.
        """
        rtnval = self._adapter
        return rtnval

    def get_compute_service(self) -> ComputeService:
        """
            Returns the ComputeService from the active adapter.

            :returns: A ComputeService instance.
        """
        rtnval = self._adapter.get_compute_service()
        return rtnval

    def get_storage_service(self) -> StorageService:
        """
            Returns the StorageService from the active adapter.

            :returns: A StorageService instance.
        """
        rtnval = self._adapter.get_storage_service()
        return rtnval

    def get_messaging_service(self) -> MessagingService:
        """
            Returns the MessagingService from the active adapter.

            :returns: A MessagingService instance.
        """
        rtnval = self._adapter.get_messaging_service()
        return rtnval

    def get_service(self, service_name: str) -> Optional[PlatformService]:
        """
            Returns a PlatformService by name from the registry.

            :param service_name: Name of the service to look up.

            :returns: The PlatformService instance or None.
        """
        rtnval = self._registry.lookup_by_name(service_name)
        return rtnval

    def health_check(self) -> dict:
        """
            Delegates to the adapter health_check and logs the results
            at INFO level.

            :returns: Dictionary of service name to health boolean.
        """
        rtnval = self._adapter.health_check()
        logger.info(
            "PlatformRuntime health check: platform=%s, results=%s",
            self.platform_type.to_string(), rtnval
        )
        return rtnval

    @classmethod
    def create_auto(cls, configuration: Optional[PlatformConfiguration] = None) -> "PlatformRuntime":
        """
            Auto-configures a PlatformRuntime by detecting the current platform
            and creating the appropriate adapter.

            When no configuration is provided, a default PlatformConfiguration
            is built from the detected platform type. When a partial
            configuration is provided (with platform_type as None), the
            detected platform type is merged with the provided settings.

            The method checks the automojo-extension ExtensionPoint for
            plugin adapters before falling back to built-in adapters.

            :param configuration: Optional PlatformConfiguration. If None or
                partial, environment-derived defaults are used.

            :returns: A configured PlatformRuntime instance.
            :raises: PlatformError
        """
        try:
            detector = PlatformDetector()
            detected_type = detector.detect(configuration=configuration)

            if configuration is None:
                configuration = PlatformConfiguration(platform_type=detected_type)
            elif configuration.platform_type is None:
                configuration = PlatformConfiguration(
                    platform_type=detected_type,
                    region=configuration.region,
                    credential_references=configuration.credential_references,
                    service_endpoint_overrides=configuration.service_endpoint_overrides,
                    options=configuration.options
                )

            # Check extension point for plugin adapters
            adapter = cls._load_adapter_from_extensions(detected_type, configuration)
            if adapter is None:
                adapter = cls._create_builtin_adapter(detected_type, configuration)

            rtnval = cls(configuration=configuration, adapter=adapter)
            return rtnval

        except PlatformError:
            raise
        except Exception as ex:
            err_msg_lines = [
                "Auto-configuration failed for platform runtime.",
                "Reason: {}".format(str(ex))
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise PlatformError(err_msg, cause=ex)

    @classmethod
    def _load_adapter_from_extensions(cls, platform_type: PlatformType,
                                       configuration: PlatformConfiguration) -> Optional["PlatformAdapter"]:
        """
            Discovers and loads PlatformAdapter implementations from the
            "automojo.agentkit.platform.adapters" extension point.

            Returns the first adapter whose platform_type matches the
            target platform type. If no plugin adapter matches, returns None.

            Plugin load failures are logged at WARNING level and remaining
            plugins continue loading.

            :param platform_type: The target PlatformType.
            :param configuration: The PlatformConfiguration.

            :returns: A PlatformAdapter instance or None.
        """
        try:
            from automojo.extension import ExtensionPoint
            extension_point = ExtensionPoint("automojo.agentkit.platform.adapters")
            discovered_adapters = extension_point.query()

            for adapter_entry in discovered_adapters:
                try:
                    if hasattr(adapter_entry, "platform_type"):
                        adapter_platform = adapter_entry.platform_type
                    else:
                        adapter_instance = adapter_entry(configuration=configuration)
                        adapter_platform = adapter_instance.platform_type

                        if adapter_platform == platform_type:
                            rtnval = adapter_instance
                            return rtnval
                        continue

                    if adapter_platform == platform_type:
                        adapter_instance = adapter_entry(configuration=configuration)
                        rtnval = adapter_instance
                        return rtnval

                except Exception as plugin_err:
                    logger.warning(
                        "Failed to load platform adapter plugin '%s': %s",
                        str(adapter_entry), str(plugin_err)
                    )

        except ImportError:
            logger.info(
                "automojo-extension not available; skipping platform adapter "
                "plugin discovery."
            )
        except Exception as discovery_err:
            logger.warning(
                "Platform adapter plugin discovery failed: %s",
                str(discovery_err)
            )

        return None

    @classmethod
    def _create_builtin_adapter(cls, platform_type: PlatformType,
                                 configuration: PlatformConfiguration) -> "PlatformAdapter":
        """
            Creates a built-in PlatformAdapter for the given platform type.

            :param platform_type: The target PlatformType.
            :param configuration: The PlatformConfiguration.

            :returns: A PlatformAdapter instance.
            :raises: PlatformError
        """
        from automojo.agentkit.platform.adapters.awsplatformadapter import AwsPlatformAdapter
        from automojo.agentkit.platform.adapters.azureplatformadapter import AzurePlatformAdapter
        from automojo.agentkit.platform.adapters.gcpplatformadapter import GcpPlatformAdapter
        from automojo.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter

        adapter_map = {
            PlatformType.AWS: AwsPlatformAdapter,
            PlatformType.AZURE: AzurePlatformAdapter,
            PlatformType.GCP: GcpPlatformAdapter,
            PlatformType.LOCAL: LocalPlatformAdapter,
        }

        adapter_cls = adapter_map.get(platform_type)
        if adapter_cls is None:
            err_msg_lines = [
                "No built-in adapter for platform type '{}'.".format(platform_type.to_string()),
                "Supported platform types: {}".format(
                    [pt.to_string() for pt in adapter_map.keys()]
                )
            ]
            err_msg = os.linesep.join(err_msg_lines)
            raise PlatformError(err_msg, platform_type=platform_type)

        rtnval = adapter_cls(configuration=configuration)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name and platform type.

            :returns: A repr string for debugging.
        """
        rtnval = "PlatformRuntime(platform_type={})".format(
            self._configuration.platform_type.to_string()
        )
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the platform type,
            region, and the count of available services.

            :returns: A human-readable string.
        """
        rtnval = "PlatformRuntime: platform={}, region={}, services={}".format(
            self._configuration.platform_type.to_string(),
            self._configuration.region,
            self._registry.count
        )
        return rtnval
