"""
    automojo.agentkit.platform.services - Platform service abstractions and DTOs.

    Provides abstract base classes for platform services (compute, storage,
    messaging) and immutable data transfer objects (StorageObject,
    QueueMessage, InvocationResult) used across all platform adapters.

    .. module:: automojo.agentkit.platform.services
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Platform service abstractions and data transfer objects.
"""

from automojo.agentkit.platform.services.computeservice import ComputeService
from automojo.agentkit.platform.services.invocationresult import InvocationResult
from automojo.agentkit.platform.services.messagingservice import MessagingService
from automojo.agentkit.platform.services.platformservice import PlatformService
from automojo.agentkit.platform.services.queuemessage import QueueMessage
from automojo.agentkit.platform.services.storageobject import StorageObject
from automojo.agentkit.platform.services.storageservice import StorageService
