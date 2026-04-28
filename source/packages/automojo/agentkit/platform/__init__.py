"""
    automojo.agentkit.platform - Cross-platform runtime abstraction layer.

    Provides platform type enumeration, platform detection, configuration,
    abstract service base classes, data transfer objects, platform adapters,
    deployment descriptors, service registry, platform runtime, and the
    platform-specific exception hierarchy.

    .. module:: automojo.agentkit.platform
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Cross-platform runtime for the automojo-agent-kit SDK.
"""

from automojo.agentkit.platform.errors import ComputeError
from automojo.agentkit.platform.errors import DeploymentDescriptorError
from automojo.agentkit.platform.errors import MessagingError
from automojo.agentkit.platform.errors import PlatformDetectionError
from automojo.agentkit.platform.errors import PlatformError
from automojo.agentkit.platform.errors import StorageError

from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.platformdetector import PlatformDetector
from automojo.agentkit.platform.platformconfiguration import PlatformConfiguration
from automojo.agentkit.platform.platformserviceregistry import PlatformServiceRegistry
from automojo.agentkit.platform.platformruntime import PlatformRuntime

from automojo.agentkit.platform.services.platformservice import PlatformService
from automojo.agentkit.platform.services.computeservice import ComputeService
from automojo.agentkit.platform.services.storageservice import StorageService
from automojo.agentkit.platform.services.messagingservice import MessagingService
from automojo.agentkit.platform.services.storageobject import StorageObject
from automojo.agentkit.platform.services.queuemessage import QueueMessage
from automojo.agentkit.platform.services.invocationresult import InvocationResult

from automojo.agentkit.platform.adapters.platformadapter import PlatformAdapter
from automojo.agentkit.platform.adapters.awsplatformadapter import AwsPlatformAdapter
from automojo.agentkit.platform.adapters.azureplatformadapter import AzurePlatformAdapter
from automojo.agentkit.platform.adapters.gcpplatformadapter import GcpPlatformAdapter
from automojo.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter

from automojo.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from automojo.agentkit.platform.deployment.deploymentdescriptorparser import DeploymentDescriptorParser
from automojo.agentkit.platform.deployment.deploymentdescriptorprinter import DeploymentDescriptorPrinter
