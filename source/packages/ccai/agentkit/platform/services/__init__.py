"""
    ccai.agentkit.platform.services - Platform service abstractions and DTOs.

    Provides abstract base classes for platform services (compute, storage,
    messaging) and immutable data transfer objects (StorageObject,
    QueueMessage, InvocationResult) used across all platform adapters.

    .. module:: ccai.agentkit.platform.services
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Platform service abstractions and data transfer objects.
"""

from ccai.agentkit.platform.services.computeservice import ComputeService
from ccai.agentkit.platform.services.invocationresult import InvocationResult
from ccai.agentkit.platform.services.messagingservice import MessagingService
from ccai.agentkit.platform.services.platformservice import PlatformService
from ccai.agentkit.platform.services.queuemessage import QueueMessage
from ccai.agentkit.platform.services.storageobject import StorageObject
from ccai.agentkit.platform.services.storageservice import StorageService
