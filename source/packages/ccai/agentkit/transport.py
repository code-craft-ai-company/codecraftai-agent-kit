"""
    Defines the Transport abstract base class for the Communication &
    Messaging feature.

    A Transport represents a communication channel for sending and
    receiving messages. Concrete implementations wrap specific protocols
    such as HTTP, WebSocket, gRPC, or message queues.

    The base class provides:
    - Abstract methods for connect, disconnect, send, and receive
    - Concrete read-only properties for name, protocol_type,
      configuration, tags, and credential_names
    - Connection status tracking via is_connected
    - Structured logging under ccai.agentkit.messaging.transport
    - Validation that name and protocol_type are non-empty

    .. module:: ccai.agentkit.transport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract base class for transport communication channels.

    Requirements: 1.1-1.11, 26.1, 26.2
"""

import abc
import logging

from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.transportconfiguration import TransportConfiguration


class Transport(abc.ABC):
    """
        Abstract base class representing a communication channel for
        sending and receiving messages. Concrete implementations wrap
        specific protocols such as HTTP, WebSocket, gRPC, or message
        queues.

        Subclasses must implement the connect, disconnect, send, and
        receive abstract methods. The base class provides concrete
        read-only properties for name, protocol_type, configuration,
        tags, credential_names, and connection status.

        :param name: The transport name string. Must be non-empty.
        :param protocol_type: The protocol type string (e.g. "http",
            "websocket", "grpc", "message_queue"). Must be non-empty.
        :param configuration: The TransportConfiguration instance
            defining connection parameters.
        :param credential_names: An optional list of credential
            reference names required for authentication.
        :param tags: An optional dictionary of tags for categorization
            and discovery.

        :raises SemanticError: If name is missing or empty.
        :raises SemanticError: If protocol_type is missing or empty.
    """

    def __init__(self, name: str, protocol_type: str,
                 configuration: TransportConfiguration,
                 credential_names: Optional[List[str]] = None,
                 tags: Optional[Dict[str, str]] = None) -> None:

        if name is None or len(str(name).strip()) == 0:
            errmsg = "A transport name is required."
            raise SemanticError(errmsg)

        if protocol_type is None or len(str(protocol_type).strip()) == 0:
            errmsg = "A protocol type is required."
            raise SemanticError(errmsg)

        self._name = name
        self._protocol_type = protocol_type
        self._configuration = configuration
        self._credential_names = list(credential_names) if credential_names is not None else []
        self._tags = dict(tags) if tags is not None else {}
        self._connected = False
        self._logger = logging.getLogger("ccai.agentkit.messaging.transport")

        return

    @property
    def name(self) -> str:
        """
            The transport name string.

            :returns: The name of this transport.
        """
        return self._name

    @property
    def protocol_type(self) -> str:
        """
            The protocol type string.

            :returns: The protocol type (e.g. "http", "websocket",
                "grpc", "message_queue").
        """
        return self._protocol_type

    @property
    def configuration(self) -> TransportConfiguration:
        """
            The TransportConfiguration instance defining connection
            parameters for this transport.

            :returns: The TransportConfiguration object.
        """
        return self._configuration

    @property
    def tags(self) -> Dict[str, str]:
        """
            A defensive copy of the tags dictionary used for
            categorization and discovery.

            :returns: A dictionary of tag key-value pairs.
        """
        return dict(self._tags)

    @property
    def credential_names(self) -> List[str]:
        """
            A defensive copy of the credential reference names
            required for authentication.

            :returns: A list of credential name strings.
        """
        return list(self._credential_names)

    @abc.abstractmethod
    def connect(self) -> None:
        """
            Establishes a connection using the transport protocol.

            Concrete implementations should set self._connected to
            True upon successful connection and log the connection
            at INFO level.

            :raises TransportError: If the connection cannot be
                established.
        """
        ...

    @abc.abstractmethod
    def disconnect(self) -> None:
        """
            Closes the transport connection.

            Concrete implementations should set self._connected to
            False upon successful disconnection and log the
            disconnection at INFO level.

            :raises TransportError: If the disconnection fails.
        """
        ...

    @abc.abstractmethod
    def send(self, message: Message) -> MessageEnvelope:
        """
            Sends a Message through the transport.

            :param message: The Message to send.

            :returns: A MessageEnvelope with delivery metadata.

            :raises TransportError: If the send operation fails.
        """
        ...

    @abc.abstractmethod
    def receive(self) -> Message:
        """
            Receives a Message from the transport.

            :returns: The received Message.

            :raises TransportError: If the receive operation fails.
        """
        ...

    def is_connected(self) -> bool:
        """
            Returns whether the transport is currently connected.

            :returns: True if connected, False otherwise.
        """
        rtnval = self._connected
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, transport name, and protocol type.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(name={!r}, protocol_type={!r})".format(
            self.__class__.__name__, self._name, self._protocol_type
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the transport
            name, protocol type, and connection status.

            :returns: A human-readable string describing the transport.
        """
        connected_str = "connected" if self._connected else "disconnected"
        str_val = "Transport: name={}, protocol_type={}, status={}".format(
            self._name, self._protocol_type, connected_str
        )
        return str_val
