"""
    ccai.agentkit.platform - Cross-platform runtime abstraction layer.

    Provides platform type enumeration, platform detection, configuration,
    abstract service base classes, data transfer objects, platform adapters,
    deployment descriptors, service registry, platform runtime, and the
    platform-specific exception hierarchy.

    .. module:: ccai.agentkit.platform
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Cross-platform runtime for the codecraftai-agent-kit SDK.
"""

from ccai.agentkit.platform.errors import ComputeError
from ccai.agentkit.platform.errors import DeploymentDescriptorError
from ccai.agentkit.platform.errors import MessagingError
from ccai.agentkit.platform.errors import PlatformDetectionError
from ccai.agentkit.platform.errors import PlatformError
from ccai.agentkit.platform.errors import StorageError

from ccai.agentkit.platform.platformtype import PlatformType
from ccai.agentkit.platform.platformdetector import PlatformDetector
from ccai.agentkit.platform.platformconfiguration import PlatformConfiguration
from ccai.agentkit.platform.platformserviceregistry import PlatformServiceRegistry
from ccai.agentkit.platform.platformruntime import PlatformRuntime

from ccai.agentkit.platform.services.platformservice import PlatformService
from ccai.agentkit.platform.services.computeservice import ComputeService
from ccai.agentkit.platform.services.storageservice import StorageService
from ccai.agentkit.platform.services.messagingservice import MessagingService
from ccai.agentkit.platform.services.storageobject import StorageObject
from ccai.agentkit.platform.services.queuemessage import QueueMessage
from ccai.agentkit.platform.services.invocationresult import InvocationResult

from ccai.agentkit.platform.adapters.platformadapter import PlatformAdapter
from ccai.agentkit.platform.adapters.awsplatformadapter import AwsPlatformAdapter
from ccai.agentkit.platform.adapters.azureplatformadapter import AzurePlatformAdapter
from ccai.agentkit.platform.adapters.gcpplatformadapter import GcpPlatformAdapter
from ccai.agentkit.platform.adapters.localplatformadapter import LocalPlatformAdapter

from ccai.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from ccai.agentkit.platform.deployment.deploymentdescriptorparser import DeploymentDescriptorParser
from ccai.agentkit.platform.deployment.deploymentdescriptorprinter import DeploymentDescriptorPrinter
