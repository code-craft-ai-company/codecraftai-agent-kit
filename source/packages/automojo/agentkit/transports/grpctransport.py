"""
    Defines the GrpcTransport class, a concrete Transport implementation
    that uses gRPC protocol semantics for sending messages between agents.

    The GrpcTransport creates a gRPC channel to the configured endpoint
    and sends messages as gRPC unary calls with JSON-serialized payloads.
    The channel is constructed from the TransportConfiguration host and
    port fields.

    TLS is supported via secure channels when the configuration options
    include ``{"tls": True}``. Credential resolution for channel
    credentials is supported through the credential_references in the
    TransportConfiguration.

    The ``grpc`` package is imported at connect time since it may not
    be installed in all environments. If the package is not available,
    a TransportError is raised.

    The transport raises TransportError for connection errors and
    deadline exceeded conditions (grpc.RpcError).

    The receive method raises TransportError because gRPC receive is
    handled via the unary call response in the send method.

    Structured logging is performed under the
    automojo.agentkit.messaging.transport.grpc logger hierarchy.

    .. module:: automojo.agentkit.transports.grpctransport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: gRPC transport implementation for agent messaging.

    Requirements: 18.1-18.8
"""

import json
import logging

from typing import Dict
from typing import List
from typing import Optional

from automojo.agentkit.message import Message
from automojo.agentkit.messageenvelope import MessageEnvelope
from automojo.agentkit.messagingerrors import TransportError
from automojo.agentkit.transport import Transport
from automojo.agentkit.transportconfiguration import TransportConfiguration


class GrpcTransport(Transport):
    """
        Transport implementation using gRPC protocol semantics for
        sending messages between agents via unary calls.

        Uses the ``grpc`` package for channel management and RPC
        calls. The package is imported at connect time since it may
        not be installed in all environments.

        The transport constructs the target endpoint string from the
        TransportConfiguration host and port fields in the format
        ``host:port``. TLS is supported via secure channels when the
        configuration options include ``{"tls": True}``. Credential
        resolution for channel credentials is supported through the
        credential_references in the TransportConfiguration.

        The connect method establishes a gRPC channel (insecure or
        secure based on TLS configuration). The disconnect method
        closes the channel. The send method serializes the message
        to JSON bytes and sends it via a generic unary call, returning
        a MessageEnvelope.

        The receive method raises TransportError because gRPC receive
        is handled via the unary call response in the send method.

        TransportError is raised for connection errors and deadline
        exceeded conditions.

        :param name: The transport name string.
        :param configuration: The TransportConfiguration instance
            defining gRPC connection parameters.
        :param credential_names: An optional list of credential
            reference names required for authentication.
        :param tags: An optional dictionary of tags for categorization
            and discovery.
    """

    def __init__(self, name: str, configuration: TransportConfiguration,
                 credential_names: Optional[List[str]] = None,
                 tags: Optional[Dict[str, str]] = None) -> None:

        super().__init__(
            name=name,
            protocol_type="grpc",
            configuration=configuration,
            credential_names=credential_names,
            tags=tags
        )

        self._grpc_logger = logging.getLogger(
            "automojo.agentkit.messaging.transport.grpc"
        )
        self._channel = None
        self._target = None
        self._grpc_module = None

        return

    def _build_target(self) -> str:
        """
            Constructs the gRPC target string from the
            TransportConfiguration host and port fields.

            The target string is in the format ``host:port``.

            :returns: The gRPC target string.
        """
        config = self._configuration
        host = config.host
        port = config.port

        target = "{}:{}".format(host, port)

        return target

    def _resolve_channel_credentials(self):
        """
            Resolves channel credentials from the credential references
            in the TransportConfiguration.

            Looks for a credential reference named "root_certificates"
            in the configuration's credential_references dictionary.
            If found, creates gRPC SSL channel credentials using the
            root certificates value.

            :returns: A grpc.ChannelCredentials instance or None if
                no channel credentials are configured.
        """
        cred_refs = self._configuration.credential_references

        root_certs = cred_refs.get("root_certificates", None)

        if root_certs is not None:
            grpc = self._grpc_module
            root_certs_bytes = root_certs
            if isinstance(root_certs_bytes, str):
                root_certs_bytes = root_certs_bytes.encode("utf-8")
            channel_credentials = grpc.ssl_channel_credentials(
                root_certificates=root_certs_bytes
            )
            return channel_credentials

        return None

    def connect(self) -> None:
        """
            Establishes a gRPC channel to the configured endpoint.

            Imports the ``grpc`` package at connect time. If the
            package is not installed, raises a TransportError.

            Creates an insecure channel by default. When the
            configuration options include ``{"tls": True}``, creates
            a secure channel with SSL channel credentials. Credential
            resolution for channel credentials is supported through
            the credential_references in the TransportConfiguration.

            Sets the transport to connected status upon success.

            :raises TransportError: If the grpc package is not
                installed or if the channel cannot be created.
        """
        try:
            try:
                import grpc as grpc_module
                self._grpc_module = grpc_module
            except ImportError as import_err:
                self._grpc_logger.warning(
                    "gRPC transport connect failed: name=%s, "
                    "error=grpc package not installed",
                    self._name
                )
                raise TransportError(
                    transport_name=self._name,
                    operation="connect",
                    cause=import_err
                )

            self._target = self._build_target()

            options = self._configuration.options
            use_tls = options.get("tls", False)

            if use_tls:
                channel_credentials = self._resolve_channel_credentials()

                if channel_credentials is None:
                    channel_credentials = grpc_module.ssl_channel_credentials()

                self._channel = grpc_module.secure_channel(
                    self._target, channel_credentials
                )
            else:
                self._channel = grpc_module.insecure_channel(self._target)

            self._connected = True

            self._grpc_logger.info(
                "gRPC transport connected: name=%s, endpoint=%s, tls=%s",
                self._name, self._target, use_tls
            )

        except TransportError:
            raise

        except Exception as ex:
            self._connected = False
            self._channel = None

            self._grpc_logger.warning(
                "gRPC transport connect failed: name=%s, "
                "endpoint=%s, error=%s",
                self._name, self._target, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="connect",
                cause=ex
            )

        return

    def disconnect(self) -> None:
        """
            Closes the gRPC channel gracefully.

            Sets the transport to disconnected status.

            :raises TransportError: If the disconnection fails.
        """
        try:
            if self._channel is not None:
                self._channel.close()
                self._channel = None

            self._connected = False

            self._grpc_logger.info(
                "gRPC transport disconnected: name=%s",
                self._name
            )

        except Exception as ex:
            self._connected = False
            self._channel = None

            self._grpc_logger.warning(
                "gRPC transport disconnect failed: name=%s, error=%s",
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
            Sends a Message as a gRPC unary call with JSON-serialized
            payload.

            The message is serialized to JSON bytes via its as_dict
            method and sent as a generic unary-unary call over the
            gRPC channel. The call uses the configured timeout from
            the TransportConfiguration.

            :param message: The Message to send.

            :returns: A MessageEnvelope with delivery metadata.

            :raises TransportError: If the transport is not connected,
                if a connection error occurs, or if the deadline is
                exceeded.
        """
        if not self._connected or self._channel is None:
            errmsg = "Transport '{}' is not connected.".format(self._name)
            self._grpc_logger.warning(
                "gRPC transport send failed: name=%s, "
                "reason=not connected",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ConnectionError(errmsg)
            )

        try:
            grpc_module = self._grpc_module

            message_data = message.as_dict()
            body_bytes = json.dumps(message_data).encode("utf-8")

            timeout_seconds = self._configuration.timeout

            method = "/automojo.agentkit.messaging/Send"

            response = self._channel.unary_unary(
                method,
                request_serializer=lambda x: x,
                response_deserializer=lambda x: x
            )(body_bytes, timeout=timeout_seconds)

            self._grpc_logger.info(
                "gRPC transport message sent: name=%s, message_id=%s, "
                "sender=%s, recipient=%s, pattern=%s",
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
            grpc_module = self._grpc_module

            if grpc_module is not None and hasattr(grpc_module, "RpcError"):
                if isinstance(ex, grpc_module.RpcError):
                    status_code = None
                    if hasattr(ex, "code") and callable(ex.code):
                        status_code = ex.code()

                    if (status_code is not None and
                            hasattr(grpc_module, "StatusCode") and
                            status_code == grpc_module.StatusCode.DEADLINE_EXCEEDED):
                        self._grpc_logger.warning(
                            "gRPC transport send failed (deadline exceeded): "
                            "name=%s, message_id=%s, endpoint=%s, "
                            "timeout=%s",
                            self._name, message.identifier,
                            self._target, self._configuration.timeout
                        )
                        raise TransportError(
                            transport_name=self._name,
                            operation="send",
                            cause=ex
                        )

                    self._grpc_logger.warning(
                        "gRPC transport send failed (rpc error): "
                        "name=%s, message_id=%s, endpoint=%s, "
                        "status_code=%s",
                        self._name, message.identifier,
                        self._target, status_code
                    )
                    raise TransportError(
                        transport_name=self._name,
                        operation="send",
                        cause=ex
                    )

            self._grpc_logger.warning(
                "gRPC transport send failed: name=%s, "
                "message_id=%s, error=%s",
                self._name, message.identifier, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ex
            )

    def receive(self) -> Message:
        """
            Receives a Message from the transport.

            gRPC receive is handled via the unary call response in
            the send method. This method always raises a TransportError
            indicating that standalone receive is not supported for
            gRPC transports.

            :returns: Never returns; always raises TransportError.

            :raises TransportError: Always raised because gRPC does
                not support standalone passive receive.
        """
        self._grpc_logger.warning(
            "gRPC transport receive not supported: name=%s",
            self._name
        )
        raise TransportError(
            transport_name=self._name,
            operation="receive",
            cause=NotImplementedError(
                "gRPC transport does not support standalone receive. "
                "gRPC responses are returned via the unary call in send."
            )
        )
