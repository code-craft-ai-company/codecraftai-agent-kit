"""
    Defines the MessagingService abstract base class representing a message
    queuing service that can send messages, receive messages, and manage
    queue subscriptions. Concrete implementations wrap AWS SQS, Azure
    Service Bus, GCP Pub/Sub, and local in-memory queuing.

    .. module:: automojo.agentkit.platform.services.messagingservice
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract messaging service interface for platform messaging services.
"""

import abc

from typing import Optional

from automojo.agentkit.platform.platformtype import PlatformType
from automojo.agentkit.platform.services.platformservice import PlatformService


class MessagingService(PlatformService, abc.ABC):
    """
        Abstract base class representing a message queuing service that can
        send messages, receive messages, and manage queue subscriptions.

        Inherits from PlatformService with service_type fixed to "messaging".
        Subclasses must implement send_message, receive_messages,
        acknowledge_message, create_queue, delete_queue, and list_queues
        in addition to is_available and health_check.

        :param service_name: A string identifying this messaging service instance.
        :param platform_type: The PlatformType this service targets.
        :param configuration: An optional PlatformConfiguration for service-specific settings.
    """

    def __init__(self, service_name: str, platform_type: PlatformType,
                 configuration: "PlatformConfiguration" = None) -> None:
        super().__init__(
            service_name=service_name,
            service_type="messaging",
            platform_type=platform_type,
            configuration=configuration
        )
        return

    @abc.abstractmethod
    def send_message(self, queue_name: str, body: object,
                     attributes: dict = None) -> str:
        """
            Sends a message to the specified queue.

            :param queue_name: Name of the target queue.
            :param body: Message body as a Python object.
            :param attributes: Optional message attributes dictionary.

            :returns: A message identifier string.
            :raises: MessagingError
        """
        ...

    @abc.abstractmethod
    def receive_messages(self, queue_name: str, max_count: int = 1,
                         wait_time: float = None) -> list:
        """
            Receives messages from the specified queue.

            :param queue_name: Name of the source queue.
            :param max_count: Maximum number of messages to receive.
            :param wait_time: Optional wait time in seconds.

            :returns: A list of QueueMessage objects.
            :raises: MessagingError
        """
        ...

    @abc.abstractmethod
    def acknowledge_message(self, queue_name: str, receipt_handle: str) -> None:
        """
            Acknowledges a message for deletion from the queue.

            :param queue_name: Name of the queue.
            :param receipt_handle: Receipt handle string for the message.

            :raises: MessagingError
        """
        ...

    @abc.abstractmethod
    def create_queue(self, queue_name: str) -> None:
        """
            Creates a message queue.

            :param queue_name: Name of the queue to create.

            :raises: MessagingError
        """
        ...

    @abc.abstractmethod
    def delete_queue(self, queue_name: str) -> None:
        """
            Removes a message queue.

            :param queue_name: Name of the queue to remove.

            :raises: MessagingError
        """
        ...

    @abc.abstractmethod
    def list_queues(self) -> list:
        """
            Returns a list of queue name strings.

            :returns: List of queue name strings.
            :raises: MessagingError
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
