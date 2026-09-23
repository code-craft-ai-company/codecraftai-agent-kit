"""
    Defines the HttpTransport class, a concrete Transport implementation
    that uses HTTP POST semantics for sending messages between agents.

    The HttpTransport uses Python's standard library urllib.request module
    for HTTP operations. It constructs URLs from the TransportConfiguration
    (host, port, path), serializes messages to JSON, and sends them via
    HTTP POST. Configurable headers, TLS (via https:// URLs), and
    credential resolution for Authorization headers are supported.

    The transport raises TransportError for connection errors, timeouts,
    and HTTP 5xx server error responses.

    Structured logging is performed under the
    ccai.agentkit.messaging.transport.http logger hierarchy.

    .. module:: ccai.agentkit.transports.httptransport
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: HTTP transport implementation using urllib for agent messaging.

    Requirements: 16.1-16.8, 13.1-13.4, 25.2, 25.3, 25.4, 25.5, 25.6
"""

import json
import logging
import ssl
import urllib.error
import urllib.request

from typing import Dict
from typing import List
from typing import Optional

from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messagingerrors import TransportError
from ccai.agentkit.transport import Transport
from ccai.agentkit.transportconfiguration import TransportConfiguration


class HttpTransport(Transport):
    """
        Transport implementation using HTTP POST semantics for sending
        messages between agents.

        Uses Python's standard library urllib.request for all HTTP
        operations. The transport constructs the target URL from the
        TransportConfiguration host, port, and optional path fields.
        TLS is supported via https:// URL scheme when the configuration
        options include ``{"tls": True}`` or the host starts with
        "https://".

        Configurable default headers are taken from the
        TransportConfiguration headers dictionary. Credential resolution
        for the Authorization header is supported through the
        credential_references in the TransportConfiguration.

        The connect method establishes a logical HTTP session by
        validating the configuration and preparing the base URL and
        default headers. The disconnect method tears down the session.

        The send method serializes the message to JSON and sends it
        via HTTP POST to the recipient endpoint. For FIRE_AND_FORGET
        pattern messages, the transport sends and returns immediately
        with a "delivered" status envelope.

        The receive method raises TransportError because HTTP is a
        request-driven protocol and does not support passive message
        reception.

        TransportError is raised for connection errors, timeouts, and
        HTTP 5xx server error responses.

        :param name: The transport name string.
        :param configuration: The TransportConfiguration instance
            defining HTTP connection parameters.
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
            protocol_type="http",
            configuration=configuration,
            credential_names=credential_names,
            tags=tags
        )

        self._http_logger = logging.getLogger(
            "ccai.agentkit.messaging.transport.http"
        )
        self._base_url = None
        self._default_headers = {}
        self._ssl_context = None

        return

    def _build_base_url(self) -> str:
        """
            Constructs the base URL from the TransportConfiguration
            host, port, and optional path fields.

            The URL scheme is determined by the TLS setting in the
            configuration options. When ``options["tls"]`` is True,
            the scheme is "https"; otherwise it is "http".

            :returns: The base URL string.
        """
        config = self._configuration
        options = config.options

        use_tls = options.get("tls", False)
        scheme = "https" if use_tls else "http"

        host = config.host
        port = config.port
        path = config.path

        base_url = "{}://{}:{}".format(scheme, host, port)

        if path is not None and len(path.strip()) > 0:
            clean_path = path.strip()
            if not clean_path.startswith("/"):
                clean_path = "/" + clean_path
            base_url = base_url + clean_path

        return base_url

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

    def _resolve_auth_header(self) -> Optional[str]:
        """
            Resolves the Authorization header value from the
            credential references in the TransportConfiguration.

            Looks for a credential reference named "authorization"
            in the configuration's credential_references dictionary.
            The credential reference value is used directly as the
            Authorization header value.

            :returns: The Authorization header value string or None
                if no authorization credential is configured.
        """
        cred_refs = self._configuration.credential_references

        if "authorization" in cred_refs:
            auth_value = cred_refs["authorization"]
            return auth_value

        return None

    def connect(self) -> None:
        """
            Establishes a logical HTTP session by validating the
            configuration and preparing the base URL, default headers,
            and optional SSL context.

            Sets the transport to connected status upon success.

            :raises TransportError: If the connection setup fails.
        """
        try:
            self._base_url = self._build_base_url()
            self._ssl_context = self._build_ssl_context()

            self._default_headers = dict(self._configuration.headers)
            self._default_headers["Content-Type"] = "application/json"

            auth_header = self._resolve_auth_header()
            if auth_header is not None:
                self._default_headers["Authorization"] = auth_header

            self._connected = True

            self._http_logger.info(
                "HTTP transport connected: name=%s, endpoint=%s",
                self._name, self._base_url
            )

        except Exception as ex:
            self._http_logger.warning(
                "HTTP transport connect failed: name=%s, error=%s",
                self._name, ex
            )
            raise TransportError(
                transport_name=self._name,
                operation="connect",
                cause=ex
            )

        return

    def disconnect(self) -> None:
        """
            Closes the logical HTTP session by clearing the base URL,
            default headers, and SSL context.

            Sets the transport to disconnected status.

            :raises TransportError: If the disconnection fails.
        """
        try:
            self._base_url = None
            self._default_headers = {}
            self._ssl_context = None
            self._connected = False

            self._http_logger.info(
                "HTTP transport disconnected: name=%s",
                self._name
            )

        except Exception as ex:
            self._http_logger.warning(
                "HTTP transport disconnect failed: name=%s, error=%s",
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
            Sends a Message via HTTP POST to the recipient endpoint.

            The message is serialized to JSON and sent as the request
            body. The target URL is the base URL of this transport.
            Default headers and any configured Authorization header
            are included in the request.

            For FIRE_AND_FORGET pattern messages, the transport sends
            the message and returns immediately with a "delivered"
            status envelope upon successful send.

            :param message: The Message to send.

            :returns: A MessageEnvelope with delivery metadata.

            :raises TransportError: If the transport is not connected,
                if a connection error occurs, if the request times out,
                or if the server returns an HTTP 5xx response.
        """
        if not self._connected:
            errmsg = "Transport '{}' is not connected.".format(self._name)
            self._http_logger.warning(
                "HTTP transport send failed: name=%s, reason=not connected",
                self._name
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=ConnectionError(errmsg)
            )

        try:
            message_data = message.as_dict()
            body_bytes = json.dumps(message_data).encode("utf-8")

            request = urllib.request.Request(
                url=self._base_url,
                data=body_bytes,
                method="POST"
            )

            for header_name, header_value in self._default_headers.items():
                request.add_header(header_name, header_value)

            timeout_seconds = self._configuration.timeout

            if self._ssl_context is not None:
                urllib.request.urlopen(
                    request,
                    timeout=timeout_seconds,
                    context=self._ssl_context
                )
            else:
                urllib.request.urlopen(
                    request,
                    timeout=timeout_seconds
                )

            self._http_logger.info(
                "HTTP transport message sent: name=%s, message_id=%s, "
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

        except urllib.error.HTTPError as http_err:
            if http_err.code >= 500:
                self._http_logger.warning(
                    "HTTP transport send failed (5xx): name=%s, "
                    "message_id=%s, status_code=%s",
                    self._name, message.identifier, http_err.code
                )
                raise TransportError(
                    transport_name=self._name,
                    operation="send",
                    cause=http_err
                )

            self._http_logger.warning(
                "HTTP transport send failed: name=%s, "
                "message_id=%s, status_code=%s",
                self._name, message.identifier, http_err.code
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=http_err
            )

        except urllib.error.URLError as url_err:
            self._http_logger.warning(
                "HTTP transport send failed (connection error): name=%s, "
                "message_id=%s, error=%s",
                self._name, message.identifier, url_err
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=url_err
            )

        except TimeoutError as timeout_err:
            self._http_logger.warning(
                "HTTP transport send failed (timeout): name=%s, "
                "message_id=%s, error=%s",
                self._name, message.identifier, timeout_err
            )
            raise TransportError(
                transport_name=self._name,
                operation="send",
                cause=timeout_err
            )

        except Exception as ex:
            self._http_logger.warning(
                "HTTP transport send failed: name=%s, "
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

            HTTP is a request-driven protocol and does not support
            passive message reception. This method always raises a
            TransportError indicating that receive is not supported
            for HTTP transports.

            :returns: Never returns; always raises TransportError.

            :raises TransportError: Always raised because HTTP does
                not support passive receive.
        """
        self._http_logger.warning(
            "HTTP transport receive not supported: name=%s",
            self._name
        )
        raise TransportError(
            transport_name=self._name,
            operation="receive",
            cause=NotImplementedError(
                "HTTP transport does not support passive receive. "
                "HTTP is a request-driven protocol."
            )
        )
