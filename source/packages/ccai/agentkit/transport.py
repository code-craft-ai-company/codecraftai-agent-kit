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
    - Serializer selection by format name through an attached
      MessageSerializerRegistry via resolve_serializer
    - Structured logging under ccai.agentkit.messaging.transport
    - Validation that name and protocol_type are non-empty

    .. module:: ccai.agentkit.transport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Abstract base class for transport communication channels.

    Requirements: 1.1-1.11, 26.1, 26.2
"""

import abc
import logging
import os

from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.jsonmessageserializer import JsonMessageSerializer
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messageserializer import MessageSerializer
from ccai.agentkit.messageserializerregistry import MessageSerializerRegistry
from ccai.agentkit.messagingerrors import MessageSerializationError
from ccai.agentkit.transportconfiguration import TransportConfiguration


# The serialization format used when neither the Message nor the
# TransportConfiguration names one. JSON is always available, even when no
# serializer is registered, because the JsonMessageSerializer is built in.
DEFAULT_SERIALIZATION_FORMAT = "json"

# The TransportConfiguration options key that names the serialization format
# a transport uses for messages that do not name one, including every message
# it receives.
SERIALIZATION_FORMAT_OPTION = "serialization_format"


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

        Subclasses encode each Message with the MessageSerializer
        returned by resolve_serializer for the Message's
        serialization_format, and decode received data with the
        serializer for the transport's own format. Serializers are
        looked up by format name in the MessageSerializerRegistry
        attached with attach_serializer_registry; the Agent attaches
        its registry when the transport is registered. The built-in
        JsonMessageSerializer is used for the 'json' format when no
        registered serializer provides it.

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
        self._serializer_registry: Optional[MessageSerializerRegistry] = None
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

    @property
    def serializer_registry(self) -> Optional[MessageSerializerRegistry]:
        """
            The MessageSerializerRegistry used to look up serializers by
            format name, or None when no registry is attached.

            :returns: The attached MessageSerializerRegistry or None.
        """
        return self._serializer_registry

    def attach_serializer_registry(self, serializer_registry: MessageSerializerRegistry) -> None:
        """
            Attaches the MessageSerializerRegistry that resolve_serializer
            uses to look up serializers by format name. The Agent attaches
            its own registry so the serializers registered with the Agent,
            including serializer plugins, are available to the transport.

            :param serializer_registry: The MessageSerializerRegistry to use.
        """
        self._serializer_registry = serializer_registry
        return

    def resolve_serializer(self, format_name: Optional[str] = None,
                           direction: str = "serialize") -> MessageSerializer:
        """
            Returns the MessageSerializer for a serialization format name.

            When format_name is None, the format named by the
            ``serialization_format`` option of the TransportConfiguration
            is used, and when that is not set either, the default 'json'
            format is used. The serializer is looked up in the attached
            MessageSerializerRegistry. The built-in JsonMessageSerializer
            is returned for the 'json' format when the registry does not
            provide one.

            :param format_name: The serialization format name, typically a
                Message's serialization_format, or None to use the transport
                default.
            :param direction: The direction the serializer is needed for,
                'serialize' or 'deserialize', reported in the error when no
                serializer is available.

            :returns: The MessageSerializer for the format.

            :raises MessageSerializationError: If no serializer is available
                for the format.
        """
        effective_format_name = format_name

        if effective_format_name is None and self._configuration is not None:
            options = self._configuration.options
            effective_format_name = options.get(SERIALIZATION_FORMAT_OPTION, None)

        if effective_format_name is None:
            effective_format_name = DEFAULT_SERIALIZATION_FORMAT

        serializer = None
        if self._serializer_registry is not None:
            serializer = self._serializer_registry.lookup(effective_format_name)

        if serializer is None and effective_format_name == DEFAULT_SERIALIZATION_FORMAT:
            serializer = JsonMessageSerializer()

        if serializer is None:
            registered_formats = []
            if self._serializer_registry is not None:
                for registered in self._serializer_registry.list_all():
                    registered_formats.append(registered.format_name)
            registered_formats.sort()

            errmsg_lines = [
                "No message serializer is registered for format '{}' on transport '{}'.".format(
                    effective_format_name, self._name
                ),
                "    REGISTERED FORMATS: {}".format(registered_formats),
                "    The '{}' format is always available.".format(DEFAULT_SERIALIZATION_FORMAT),
            ]
            if self._serializer_registry is None:
                errmsg_lines.append(
                    "    No MessageSerializerRegistry is attached; register the transport "
                    "with an Agent or call attach_serializer_registry."
                )
            detail = os.linesep.join(errmsg_lines)
            raise MessageSerializationError(
                format_name=effective_format_name,
                direction=direction,
                detail=detail
            )

        return serializer

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

    @abc.abstractmethod
    def disconnect(self) -> None:
        """
            Closes the transport connection.

            Concrete implementations should set self._connected to
            False upon successful disconnection and log the
            disconnection at INFO level.

            :raises TransportError: If the disconnection fails.
        """

    @abc.abstractmethod
    def send(self, message: Message) -> MessageEnvelope:
        """
            Sends a Message through the transport.

            :param message: The Message to send.

            :returns: A MessageEnvelope with delivery metadata.

            :raises TransportError: If the send operation fails.
        """

    @abc.abstractmethod
    def receive(self) -> Message:
        """
            Receives a Message from the transport.

            :returns: The received Message.

            :raises TransportError: If the receive operation fails.
        """

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
