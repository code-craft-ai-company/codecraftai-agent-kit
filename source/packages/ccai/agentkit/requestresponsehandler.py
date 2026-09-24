"""
    Defines the RequestResponseHandler class for managing the lifecycle
    of request/response message exchanges.

    The RequestResponseHandler tracks pending requests by correlation
    identifier, sends request messages through a Transport, and waits
    for correlated response messages. It supports configurable timeouts,
    cancellation of pending requests, and multiple concurrent pending
    requests using threading primitives.

    When a response message arrives with a matching correlation identifier,
    the handler delivers the response to the waiting caller. If no response
    arrives within the timeout duration, a MessageTimeoutError is raised.

    .. module:: ccai.agentkit.requestresponsehandler
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Correlated request/response management with timeout support.

    Requirements: 12.1-12.10, 26.17, 26.18
"""

import logging
import threading
import uuid

from typing import Optional

from ccai.agentkit.message import Message
from ccai.agentkit.messagingerrors import MessageTimeoutError
from ccai.agentkit.transport import Transport


class RequestResponseHandler:
    """
        Manages the lifecycle of request/response message exchanges
        including correlation tracking, timeout management, and
        response delivery.

        Each outgoing request is assigned a unique correlation identifier.
        The request is sent through a Transport and the caller blocks
        until a correlated response is received or the timeout expires.

        Pending requests are tracked in a dictionary keyed by correlation
        identifier. Each entry contains a threading.Event for signaling,
        a slot for the response message, and the original request message
        identifier.

        :param default_timeout: The default timeout in seconds for
            request/response exchanges. Defaults to 30.0.
    """

    def __init__(self, default_timeout: float = 30.0) -> None:
        self._pending_requests: dict = {}
        self._default_timeout = default_timeout
        self._lock = threading.Lock()
        self._logger = logging.getLogger("ccai.agentkit.messaging.requestresponse")
        return

    def send_request(self, message: Message, transport: Transport,
                     timeout: Optional[float] = None) -> Message:
        """
            Sends a request message and waits for a correlated response.

            Generates a unique correlation identifier for the request,
            constructs a new Message with the correlation identifier set,
            sends the message through the provided Transport, and blocks
            until a correlated response is received or the timeout expires.

            :param message: The request Message with MessagePattern.REQUEST.
            :param transport: The Transport to send through.
            :param timeout: Optional timeout in seconds. If not provided,
                the default_timeout is used.

            :returns: The correlated response Message.

            :raises MessageTimeoutError: If no response is received within
                the timeout duration.

            If the transport send raises, the request is no longer tracked
            as pending and the send error propagates to the caller.
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout

        correlation_id = str(uuid.uuid4())

        request_message = Message(
            sender=message.sender,
            recipient=message.recipient,
            payload=message.payload,
            pattern=message.pattern,
            headers=message.headers,
            correlation_id=correlation_id,
            identifier=message.identifier,
            timestamp=message.timestamp,
            serialization_format=message.serialization_format,
        )

        ready_event = threading.Event()

        pending_entry = {
            "event": ready_event,
            "response": None,
            "request_message_id": request_message.identifier,
            "correlation_id": correlation_id,
            "timeout": effective_timeout,
            "cancelled": False,
        }

        # The request is tracked before it is sent so a reply that arrives
        # while send is still returning is not lost.
        with self._lock:
            self._pending_requests[correlation_id] = pending_entry

        send_completed = False
        try:
            transport.send(request_message)
            send_completed = True
        finally:
            if send_completed is not True:
                # The request never left, so no reply can come; stop tracking
                # it so pending_count stays accurate.
                with self._lock:
                    self._pending_requests.pop(correlation_id, None)

        self._logger.info(
            "Request sent: message_id='%s', correlation_id='%s', "
            "timeout=%.1f",
            request_message.identifier, correlation_id, effective_timeout
        )

        response_received = ready_event.wait(timeout=effective_timeout)

        with self._lock:
            entry = self._pending_requests.pop(correlation_id, None)

        if entry is not None and entry.get("cancelled") is True:
            raise MessageTimeoutError(
                request_message_id=request_message.identifier,
                correlation_id=correlation_id,
                timeout=effective_timeout,
            )

        if response_received is not True:
            self._logger.warning(
                "Request timed out: message_id='%s', correlation_id='%s', "
                "timeout=%.1f",
                request_message.identifier, correlation_id, effective_timeout
            )
            raise MessageTimeoutError(
                request_message_id=request_message.identifier,
                correlation_id=correlation_id,
                timeout=effective_timeout,
            )

        response_message = entry["response"]

        self._logger.info(
            "Response received: request_message_id='%s', "
            "correlation_id='%s', response_message_id='%s'",
            request_message.identifier, correlation_id,
            response_message.identifier
        )

        return response_message

    def handle_response(self, message: Message) -> None:
        """
            Delivers a response message to the waiting caller by matching
            the correlation identifier.

            Looks up the pending request entry by the response message's
            correlation_id. If a matching entry is found, stores the
            response message and signals the waiting caller via the
            threading.Event.

            If no matching pending request is found, the response is
            silently ignored and logged at WARNING level.

            :param message: The response Message with a correlation_id
                matching a pending request.
        """
        correlation_id = message.correlation_id

        with self._lock:
            entry = self._pending_requests.get(correlation_id)

        if entry is None:
            self._logger.warning(
                "No pending request for correlation_id='%s', "
                "message_id='%s'",
                correlation_id, message.identifier
            )
            return

        entry["response"] = message
        entry["event"].set()

        self._logger.info(
            "Response matched: correlation_id='%s', "
            "response_message_id='%s'",
            correlation_id, message.identifier
        )

        return

    def cancel(self, correlation_id: str) -> None:
        """
            Cancels a pending request.

            Marks the pending request entry as cancelled and signals
            the waiting caller via the threading.Event. The waiting
            caller will then raise a MessageTimeoutError.

            If no pending request is found for the given correlation
            identifier, the operation is a no-op.

            :param correlation_id: The correlation identifier of the
                pending request to cancel.
        """
        with self._lock:
            entry = self._pending_requests.get(correlation_id)

        if entry is None:
            self._logger.warning(
                "Cancel requested for unknown correlation_id='%s'",
                correlation_id
            )
            return

        entry["cancelled"] = True
        entry["event"].set()

        self._logger.info(
            "Request cancelled: correlation_id='%s', "
            "request_message_id='%s'",
            correlation_id, entry["request_message_id"]
        )

        return

    @property
    def pending_count(self) -> int:
        """
            The count of currently pending requests.

            :returns: The number of pending requests as an integer.
        """
        with self._lock:
            count = len(self._pending_requests)
        return count

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name and the count of pending requests.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(pending_count={})".format(
            self.__class__.__name__, self.pending_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of
            pending requests and the default timeout.

            :returns: A human-readable string describing the handler state.
        """
        str_val = "RequestResponseHandler: {} pending request(s), default_timeout={:.1f}s".format(
            self.pending_count, self._default_timeout
        )
        return str_val
