"""
    Defines the WebSocketTransport class, a concrete Transport
    implementation that uses WebSocket protocol semantics for
    persistent bidirectional communication between agents.

    The WebSocketTransport maintains a persistent WebSocket connection
    to the configured endpoint. It constructs ws:// or wss:// URLs
    from the TransportConfiguration (host, port, path), serializes
    messages to JSON, and sends them as WebSocket text frames.

    TLS is supported via wss:// URL scheme when the configuration
    options include ``{"tls": True}``.

    The transport exposes a connection_state property that tracks
    the current state of the WebSocket connection as one of
    "disconnected", "connecting", "connected", or "closing".

    The transport raises TransportError for connection loss, send
    failures, and receive failures.

    Structured logging is performed under the
    ccai.agentkit.messaging.transport.websocket logger hierarchy.

    The transport is designed to work with any WebSocket client that
    provides connect, send, recv, and close methods. The actual
    WebSocket client library (such as the ``websockets`` package) is
    not imported directly; instead, the transport wraps whatever
    client is provided or attempts to import ``websockets.sync.client``
    at connect time.

    .. module:: ccai.agentkit.transports.websockettransport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: WebSocket transport implementation for persistent
        bidirectional agent messaging.

    Requirements: 17.1-17.8
"""

import json
import logging
import ssl

from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messagingerrors import TransportError
from ccai.agentkit.transport import Transport
from ccai.agentkit.transportconfiguration import TransportConfiguration


class WebSocketTransport(Transport):
    """
        Transport implementation using WebSocket protocol semantics
        with persistent bidirectional connections.

        Uses a WebSocket client that provides connect, send, recv,
        and close methods. The transport constructs the target URL
        from the TransportConfiguration host, port, and optional
        path fields. TLS is supported via wss:// URL scheme when
        the configuration options include ``{"tls": True}``.

        The connect method establishes a persistent WebSocket
        connection to the configured endpoint. The disconnect method
        gracefully closes the connection. The send method serializes
        the message to JSON and sends it as a WebSocket text frame.
        The receive method reads a WebSocket text frame and
        deserializes it to a Message.

        The connection_state property tracks the current state of
        the WebSocket connection as one of "disconnected",
        "connecting", "connected", or "closing".

        TransportError is raised for connection loss, send failures,
        and receive failures.

        :param name: The transport name string.
        :param configuration: The TransportConfiguration instance
            defining WebSocket connection parameters.
        :param credential_names: An optional list of credential
            reference names required for authentication.
        :param tags: An optional dictionary of tags for categorization
            and discovery.
    """

    VALID_CONNECTION_STATES = {"disconnected", "connecting", "connected", "closing"}

    def __init__(self, name: str, configuration: TransportConfiguration,
                 credential_names: Optional[List[str]] = None,
                 tags: Optional[Dict[str, str]] = None) -> None:

        super().__init__(
            name=name,
            protocol_type="websocket",
            configuration=configuration,
            credential_names=credential_names,
            tags=tags
        )

        self._ws_logger = logging.getLogger(
            "ccai.agentkit.messaging.transport.websocket"
        )
        self._connection_state = "disconnected"
        self._ws_client = None
        self._ws_url = None
        self._ssl_context = None

        return

    @property
    def connection_state(self) -> str:
        """
            The current state of the WebSocket connection.

            Valid states are "disconnected", "connecting", "connected",
            and "closing".

            :returns: The connection state string.
        """
        return self._connection_state

    def _build_ws_url(self) -> str:
        """
            Constructs the WebSocket URL from the TransportConfiguration
            host, port, and optional path fields.

            The URL scheme is determined by the TLS setting in the
            configuration options. When ``options["tls"]`` is True,
            the scheme is "wss"; otherwise it is "ws".

            :returns: The WebSocket URL string.
        """
        config = self._configuration
        options = config.options

        use_tls = options.get("tls", False)
        scheme = "wss" if use_tls else "ws"

        host = config.host
        port = config.port
        path = config.path

        ws_url = "{}://{}:{}".format(scheme, host, port)

        if path is not None and len(path.strip()) > 0:
            clean_path = path.strip()
            if not clean_path.startswith("/"):
                clean_path = "/" + clean_path
            ws_url = ws_url + clean_path

        return ws_url

    def _build_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
            Builds an SSL context when TLS is enabled in the
            configuration options.

            :returns: An ssl.SSLContext instance or None if TLS is
                not enabled.
        """
        options = self._configuration.options
        use_tls = options.get("tls", False)

        if not use_tls:
            return None

        ssl_context = ssl.create_default_context()

        return ssl_context

    def connect(self) -> None:
        """
            Establishes a persistent WebSocket connection to the
            configured endpoint.

            Constructs the ws:// or wss:// URL from the configuration,
            builds an SSL context if TLS is enabled, and attempts to
            connect using the ``websockets.sync.client.connect``
            function.

            Sets the connection_state to "connecting" during the
            connection attempt, "connected" upon success, and
            "disconnected" if the connection fails.

            :raises TransportError: If the WebSocket connection cannot
                be established.
        """
        self._connection_state = "connecting"

        try:
            self._ws_url = self._build_ws_url()
            self._ssl_context = self._build_ssl_context()

            try:
                import websockets.sync.client as ws_sync_client
            except ImportError as import_err:
                self._connection_state = "disconnected"
                self._ws_logger.warning(
                    "WebSocket transport connect failed: name=%s, "
                    "error=websockets package not installed",
                    self._name
                )
                raise TransportError(
                    transport_name=self._name,
                    operation="connect",
                    cause=import_err
                )

            if self._ssl_context is not None:
                self._ws_client = ws_sync_client.connect(
                    self._ws_url,
                    ssl=self._ssl_context
                )
            else:
                self._ws_client = ws_sync_client.connect(
                    self._ws_url
                )

            self._connected = True
            self._connection_state = "connected"

            self._ws_logger.info(
                "WebSocket transport connected: name=%s, endpoint=%s",
                self._name, self._ws_url
            )

        except TransportError:
            raise

        except Exception as ex:
            self._connection_state = "disconnected"
            self._connected = False
            self._ws_client = None

            self._ws_logger.warning(
                "WebSocket transport connect failed: name=%s, "
                "endpoint=%s, error=%s",
                self._name, self._ws_url, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="connect",
                cause=ex
            )

        return

    def disconnect(self) -> None:
        """
            Gracefully closes the WebSocket connection.

            Sets the connection_state to "closing" during the close
            operation and "disconnected" upon completion.

            :raises TransportError: If the disconnection fails.
        """
        self._connection_state = "closing"

        try:
            if self._ws_client is not None:
                self._ws_client.close()
                self._ws_client = None

            self._connected = False
            self._connection_state = "disconnected"
            self._ssl_context = None

            self._ws_logger.info(
                "WebSocket transport disconnected: name=%s",
                self._name
            )

        except Exception as ex:
            self._connection_state = "disconnected"
            self._connected = False
            self._ws_client = None

            self._ws_logger.warning(
                "WebSocket transport disconnect failed: name=%s, error=%s",
                self._name, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="disconnect",
                cause=ex
            )

        return

    def send(self, message: Message) -> MessageEnvelope:
        """
            Sends a Message as a JSON-encoded WebSocket text frame.

            The message is serialized to JSON via its as_dict method
            and sent as a text frame over the persistent WebSocket
            connection.

            :param message: The Message to send.

            :returns: A MessageEnvelope with delivery metadata.

            :raises TransportError: If the transport is not connected,
                if the WebSocket connection is lost, or if the send
                operation fails.
        """
        if not self._connected or self._ws_client is None:
            errmsg = "Transport '{}' is not connected.".format(self._name)
            self._ws_logger.warning(
                "WebSocket transport send failed: name=%s, "
                "reason=not connected",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ConnectionError(errmsg)
            )

        try:
            message_data = message.as_dict()
            json_payload = json.dumps(message_data)

            self._ws_client.send(json_payload)

            self._ws_logger.info(
                "WebSocket transport message sent: name=%s, "
                "message_id=%s, sender=%s, recipient=%s, pattern=%s",
                self._name, message.identifier,
                message.sender.agent_identifier,
                message.recipient.agent_identifier,
                message.pattern.value
            )

            envelope = MessageEnvelope(
                message=message,
                transport_name=self._name,
                attempt_count=1,
                delivery_status="delivered"
            )

            return envelope

        except Exception as ex:
            self._connection_state = "disconnected"
            self._connected = False

            self._ws_logger.warning(
                "WebSocket transport send failed (connection loss): "
                "name=%s, message_id=%s, endpoint=%s, error=%s",
                self._name, message.identifier, self._ws_url, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ex
            )

    def receive(self) -> Message:
        """
            Receives a Message from the WebSocket connection.

            Reads a text frame from the persistent WebSocket connection
            and deserializes the JSON payload into a Message instance.

            :returns: The received Message.

            :raises TransportError: If the transport is not connected,
                if the WebSocket connection is lost, or if the received
                data cannot be deserialized.
        """
        if not self._connected or self._ws_client is None:
            errmsg = "Transport '{}' is not connected.".format(self._name)
            self._ws_logger.warning(
                "WebSocket transport receive failed: name=%s, "
                "reason=not connected",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="receive",
                cause=ConnectionError(errmsg)
            )

        try:
            raw_data = self._ws_client.recv()

            message_data = json.loads(raw_data)
            message = Message.from_dict(message_data)

            self._ws_logger.info(
                "WebSocket transport message received: name=%s, "
                "message_id=%s, sender=%s, pattern=%s",
                self._name, message.identifier,
                message.sender.agent_identifier,
                message.pattern.value
            )

            return message

        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as parse_err:
            self._ws_logger.warning(
                "WebSocket transport receive failed (deserialization): "
                "name=%s, error=%s",
                self._name, parse_err
            )
            raise TransportError(
                transport_name=self._name,
                operation="receive",
                cause=parse_err
            )

        except Exception as ex:
            self._connection_state = "disconnected"
            self._connected = False

            self._ws_logger.warning(
                "WebSocket transport receive failed (connection loss): "
                "name=%s, endpoint=%s, error=%s",
                self._name, self._ws_url, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="receive",
                cause=ex
            )
