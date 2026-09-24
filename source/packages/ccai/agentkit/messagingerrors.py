"""
    Exception classes for the Communication & Messaging feature.

    Provides TransportError for transport operation failures,
    NoMessageAvailableError for a receive that finds no waiting message,
    MessageSerializationError for serialization and deserialization failures,
    MessageRoutingError for routing and address resolution failures,
    and MessageTimeoutError for request/response timeout conditions.
"""

from typing import Optional

from ccai.agentkit.errors import AgentKitError


class TransportError(AgentKitError):
    """
        Raised when a Transport operation fails due to a connection, send,
        or receive error.

        :param transport_name: The name of the transport where the error occurred.
        :param operation: The operation that failed (e.g. 'connect', 'disconnect',
            'send', 'receive').
        :param cause: An optional exception that caused the failure.
    """

    def __init__(self, transport_name: str, operation: str, cause: Optional[Exception] = None) -> None:
        self._transport_name = transport_name
        self._operation = operation
        self._cause_exception = cause

        errmsg = self._format_message()
        super().__init__(errmsg, cause=cause)

        return

    @property
    def transport_name(self) -> str:
        """
            The name of the transport where the error occurred.

            :returns: The transport name string.
        """
        return self._transport_name

    @property
    def operation(self) -> str:
        """
            The operation that failed.

            :returns: The operation string (e.g. 'connect', 'disconnect',
                'send', 'receive').
        """
        return self._operation

    @property
    def cause(self) -> Optional[Exception]:
        """
            The optional exception that caused the failure.

            :returns: The cause exception or None.
        """
        return self._cause_exception

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the transport name,
            operation, and optional cause.

            :returns: A formatted error message string.
        """
        errmsg = "Transport '{}' failed during {} operation".format(
            self._transport_name, self._operation
        )

        if self._cause_exception is not None:
            errmsg = "{}: {}".format(errmsg, self._cause_exception)

        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            transport name, operation, and cause.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(transport_name={!r}, operation={!r}, cause={!r})".format(
            self.__class__.__name__, self._transport_name, self._operation,
            self._cause_exception
        )
        return repr_str


class NoMessageAvailableError(TransportError):
    """
        Raised by the receive method of a pull-based Transport, such as the
        MessageQueueTransport, when no message is waiting to be received.

        It derives from TransportError so code that catches TransportError
        around receive keeps working. The Agent receive path treats it as
        "nothing received yet" instead of as a failure.

        :param transport_name: The name of the transport that had no message.
        :param operation: The operation that found no message, 'receive'.
        :param cause: An optional exception describing the empty source.
    """


class MessageSerializationError(AgentKitError):
    """
        Raised when a MessageSerializer fails to serialize or deserialize
        a message payload.

        :param format_name: The serializer format name (e.g. 'json', 'msgpack',
            'protobuf').
        :param direction: The serialization direction ('serialize' or 'deserialize').
        :param detail: A descriptive string identifying the serialization problem.
    """

    def __init__(self, format_name: str, direction: str, detail: str) -> None:
        self._format_name = format_name
        self._direction = direction
        self._detail = detail

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def format_name(self) -> str:
        """
            The serializer format name.

            :returns: The format name string (e.g. 'json', 'msgpack', 'protobuf').
        """
        return self._format_name

    @property
    def direction(self) -> str:
        """
            The serialization direction that failed.

            :returns: The direction string ('serialize' or 'deserialize').
        """
        return self._direction

    @property
    def detail(self) -> str:
        """
            A descriptive string identifying the serialization problem.

            :returns: The detail string.
        """
        return self._detail

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the format name,
            direction, and detail.

            :returns: A formatted error message string.
        """
        errmsg = "Serialization error in '{}' during {}: {}".format(
            self._format_name, self._direction, self._detail
        )
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            format name, direction, and detail.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(format_name={!r}, direction={!r}, detail={!r})".format(
            self.__class__.__name__, self._format_name, self._direction,
            self._detail
        )
        return repr_str


class MessageRoutingError(AgentKitError):
    """
        Raised when the MessageRouter or AddressResolver cannot route or resolve
        a message destination.

        :param message_id: The message identifier, when available.
        :param target: The target agent identifier or topic.
        :param detail: A descriptive string identifying the routing problem.
    """

    def __init__(self, message_id: Optional[str] = None, target: Optional[str] = None,
                 detail: Optional[str] = None) -> None:
        self._message_id = message_id
        self._target = target
        self._detail = detail

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def message_id(self) -> Optional[str]:
        """
            The message identifier, when available.

            :returns: The message identifier string or None.
        """
        return self._message_id

    @property
    def target(self) -> Optional[str]:
        """
            The target agent identifier or topic.

            :returns: The target string or None.
        """
        return self._target

    @property
    def detail(self) -> Optional[str]:
        """
            A descriptive string identifying the routing problem.

            :returns: The detail string or None.
        """
        return self._detail

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the message identifier,
            target, and detail.

            :returns: A formatted error message string.
        """
        parts = ["Message routing failed"]

        if self._target is not None:
            parts.append("for target '{}'".format(self._target))

        if self._message_id is not None:
            parts.append("(message_id='{}')".format(self._message_id))

        if self._detail is not None:
            parts.append(": {}".format(self._detail))

        errmsg = " ".join(parts)
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            message identifier, target, and detail.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(message_id={!r}, target={!r}, detail={!r})".format(
            self.__class__.__name__, self._message_id, self._target,
            self._detail
        )
        return repr_str


class MessageTimeoutError(AgentKitError):
    """
        Raised when a request/response exchange exceeds the configured timeout
        duration.

        :param request_message_id: The request message identifier.
        :param correlation_id: The correlation identifier for the request/response
            exchange.
        :param timeout: The timeout duration in seconds.
    """

    def __init__(self, request_message_id: str, correlation_id: str, timeout: float) -> None:
        self._request_message_id = request_message_id
        self._correlation_id = correlation_id
        self._timeout = timeout

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def request_message_id(self) -> str:
        """
            The request message identifier.

            :returns: The request message identifier string.
        """
        return self._request_message_id

    @property
    def correlation_id(self) -> str:
        """
            The correlation identifier for the request/response exchange.

            :returns: The correlation identifier string.
        """
        return self._correlation_id

    @property
    def timeout(self) -> float:
        """
            The timeout duration in seconds.

            :returns: The timeout value as a float.
        """
        return self._timeout

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the request message identifier,
            correlation identifier, and timeout duration.

            :returns: A formatted error message string.
        """
        errmsg = "Request '{}' with correlation '{}' timed out after {} seconds".format(
            self._request_message_id, self._correlation_id, self._timeout
        )
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            request message identifier, correlation identifier, and timeout.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(request_message_id={!r}, correlation_id={!r}, timeout={!r})".format(
            self.__class__.__name__, self._request_message_id,
            self._correlation_id, self._timeout
        )
        return repr_str
