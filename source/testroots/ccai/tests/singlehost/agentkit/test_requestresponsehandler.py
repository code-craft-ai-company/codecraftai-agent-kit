"""
    Unit tests for the ccai.agentkit.requestresponsehandler module.

    Tests RequestResponseHandler send_request, handle_response correlation
    matching, cancel, timeout behavior, pending_count, __repr__, __str__.
    Uses a minimal concrete Transport subclass for send operations.

    Requirements: 12.1-12.10
"""

import logging
import logging.handlers
import threading
import time

from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messagepattern import MessagePattern
from ccai.agentkit.messagingerrors import MessageTimeoutError
from ccai.agentkit.messagingerrors import TransportError
from ccai.agentkit.requestresponsehandler import RequestResponseHandler
from ccai.agentkit.transport import Transport
from ccai.agentkit.transportconfiguration import TransportConfiguration


# =========================================================================
# Test helpers
# =========================================================================

class RecordingTransport(Transport):
    """
        A minimal concrete Transport subclass that records sent messages
        for verification in tests.
    """

    def __init__(self):
        cfg = TransportConfiguration(
            protocol_type="http",
            host="localhost",
            port=8080,
        )
        super().__init__(
            name="test-transport",
            protocol_type="http",
            configuration=cfg,
        )
        self.sent_messages = []
        return

    def connect(self) -> None:
        self._connected = True
        return

    def disconnect(self) -> None:
        self._connected = False
        return

    def send(self, message: Message) -> MessageEnvelope:
        self.sent_messages.append(message)
        envelope = MessageEnvelope(
            message=message,
            transport_name=self.name,
            attempt_count=1,
            delivery_status="delivered",
        )
        return envelope

    def receive(self) -> Message:
        return None


def _create_request_message(identifier=None):
    """
        Creates a Message with MessagePattern.REQUEST for testing.
    """
    sender = AgentAddress(
        agent_identifier="requester-agent",
        transport_name="http",
    )
    recipient = AgentAddress(
        agent_identifier="responder-agent",
        transport_name="http",
    )
    message = Message(
        sender=sender,
        recipient=recipient,
        payload={"action": "get-status"},
        pattern=MessagePattern.REQUEST,
        identifier=identifier,
    )
    return message


def _create_response_message(correlation_id, identifier=None):
    """
        Creates a Message with MessagePattern.RESPONSE and a given
        correlation_id for testing.
    """
    sender = AgentAddress(
        agent_identifier="responder-agent",
        transport_name="http",
    )
    recipient = AgentAddress(
        agent_identifier="requester-agent",
        transport_name="http",
    )
    message = Message(
        sender=sender,
        recipient=recipient,
        payload={"status": "ok"},
        pattern=MessagePattern.RESPONSE,
        correlation_id=correlation_id,
        identifier=identifier,
    )
    return message


# =========================================================================
# Construction (Requirement 12.4)
# =========================================================================

def test_default_timeout():
    """
        Verify RequestResponseHandler uses 30.0 as the default timeout.
    """
    handler = RequestResponseHandler()

    assert handler._default_timeout == 30.0, \
        "Default timeout should be 30.0 seconds"
    return


def test_custom_default_timeout():
    """
        Verify RequestResponseHandler accepts a custom default timeout.
    """
    handler = RequestResponseHandler(default_timeout=10.0)

    assert handler._default_timeout == 10.0, \
        "Default timeout should match the provided value"
    return


# =========================================================================
# pending_count property (Requirement 12.7)
# =========================================================================

def test_pending_count_initially_zero():
    """
        Verify pending_count is zero when no requests are pending.
    """
    handler = RequestResponseHandler()

    assert handler.pending_count == 0, \
        "pending_count should be 0 initially"
    return


# =========================================================================
# send_request generates correlation_id (Requirement 12.2)
# =========================================================================

def test_send_request_generates_correlation_id():
    """
        Verify send_request generates a correlation_id and sets it on
        the message sent through the transport.
    """
    handler = RequestResponseHandler(default_timeout=1.0)
    transport = RecordingTransport()
    request = _create_request_message()

    # Send request in a thread so we can deliver the response
    result_holder = [None]
    error_holder = [None]

    def do_request():
        try:
            result_holder[0] = handler.send_request(request, transport, timeout=1.0)
        except Exception as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=do_request)
    thread.start()

    # Wait briefly for the request to be sent
    time.sleep(0.1)

    assert len(transport.sent_messages) == 1, \
        "Transport should have received one message"

    sent_msg = transport.sent_messages[0]
    assert sent_msg.correlation_id is not None, \
        "Sent message should have a correlation_id"
    assert len(sent_msg.correlation_id) > 0, \
        "correlation_id should be non-empty"

    # Deliver the response to unblock the caller
    response = _create_response_message(correlation_id=sent_msg.correlation_id)
    handler.handle_response(response)

    thread.join(timeout=2.0)

    assert error_holder[0] is None, \
        "send_request should not raise an error: {}".format(error_holder[0])
    assert result_holder[0] is response, \
        "send_request should return the response message"
    return


# =========================================================================
# send_request and handle_response correlation matching (Requirement 12.1, 12.3)
# =========================================================================

def test_send_request_returns_correlated_response():
    """
        Verify send_request returns the response message that matches
        the correlation_id.
    """
    handler = RequestResponseHandler(default_timeout=5.0)
    transport = RecordingTransport()
    request = _create_request_message()

    result_holder = [None]
    error_holder = [None]

    def do_request():
        try:
            result_holder[0] = handler.send_request(request, transport, timeout=5.0)
        except Exception as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=do_request)
    thread.start()

    time.sleep(0.1)

    sent_msg = transport.sent_messages[0]
    response = _create_response_message(
        correlation_id=sent_msg.correlation_id,
        identifier="response-001",
    )
    handler.handle_response(response)

    thread.join(timeout=2.0)

    assert error_holder[0] is None, \
        "send_request should not raise: {}".format(error_holder[0])
    assert result_holder[0] is not None, \
        "send_request should return a response"
    assert result_holder[0].identifier == "response-001", \
        "Response identifier should match"
    return


# =========================================================================
# Timeout behavior (Requirement 12.5)
# =========================================================================

def test_send_request_raises_timeout_error():
    """
        Verify send_request raises MessageTimeoutError when no response
        is received within the timeout.
    """
    handler = RequestResponseHandler(default_timeout=0.2)
    transport = RecordingTransport()
    request = _create_request_message(identifier="timeout-req-001")

    error_holder = [None]

    def do_request():
        try:
            handler.send_request(request, transport, timeout=0.2)
        except MessageTimeoutError as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=do_request)
    thread.start()
    thread.join(timeout=2.0)

    assert error_holder[0] is not None, \
        "send_request should raise MessageTimeoutError on timeout"

    err = error_holder[0]
    assert err.request_message_id == "timeout-req-001", \
        "MessageTimeoutError should contain the request message id"
    assert err.correlation_id is not None, \
        "MessageTimeoutError should contain the correlation_id"
    assert err.timeout == 0.2, \
        "MessageTimeoutError should contain the timeout value"
    return


def test_send_request_uses_default_timeout():
    """
        Verify send_request uses the default timeout when none is provided.
    """
    handler = RequestResponseHandler(default_timeout=0.2)
    transport = RecordingTransport()
    request = _create_request_message()

    error_holder = [None]

    def do_request():
        try:
            handler.send_request(request, transport)
        except MessageTimeoutError as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=do_request)
    thread.start()
    thread.join(timeout=2.0)

    assert error_holder[0] is not None, \
        "send_request should raise MessageTimeoutError using default timeout"
    assert error_holder[0].timeout == 0.2, \
        "Timeout in error should match default_timeout"
    return


# =========================================================================
# Cancel pending request (Requirement 12.8)
# =========================================================================

def test_cancel_raises_timeout_error_to_waiting_caller():
    """
        Verify cancel causes the waiting caller to receive a
        MessageTimeoutError.
    """
    handler = RequestResponseHandler(default_timeout=5.0)
    transport = RecordingTransport()
    request = _create_request_message(identifier="cancel-req-001")

    error_holder = [None]

    def do_request():
        try:
            handler.send_request(request, transport, timeout=5.0)
        except MessageTimeoutError as exc:
            error_holder[0] = exc

    thread = threading.Thread(target=do_request)
    thread.start()

    time.sleep(0.1)

    sent_msg = transport.sent_messages[0]
    correlation_id = sent_msg.correlation_id

    handler.cancel(correlation_id)

    thread.join(timeout=2.0)

    assert error_holder[0] is not None, \
        "cancel should cause MessageTimeoutError for the waiting caller"
    assert error_holder[0].correlation_id == correlation_id, \
        "Error correlation_id should match the cancelled request"
    return


def test_cancel_unknown_correlation_id_is_noop():
    """
        Verify cancel with an unknown correlation_id does not raise.
    """
    handler = RequestResponseHandler()

    # Should not raise
    handler.cancel("nonexistent-correlation-id")
    return


# =========================================================================
# Multiple concurrent pending requests (Requirement 12.6)
# =========================================================================

def test_multiple_concurrent_requests():
    """
        Verify multiple concurrent requests can be tracked and resolved
        independently.
    """
    handler = RequestResponseHandler(default_timeout=5.0)
    transport = RecordingTransport()

    request_a = _create_request_message(identifier="req-a")
    request_b = _create_request_message(identifier="req-b")

    result_a = [None]
    result_b = [None]
    error_a = [None]
    error_b = [None]

    def do_request_a():
        try:
            result_a[0] = handler.send_request(request_a, transport, timeout=5.0)
        except Exception as exc:
            error_a[0] = exc

    def do_request_b():
        try:
            result_b[0] = handler.send_request(request_b, transport, timeout=5.0)
        except Exception as exc:
            error_b[0] = exc

    thread_a = threading.Thread(target=do_request_a)
    thread_b = threading.Thread(target=do_request_b)
    thread_a.start()
    thread_b.start()

    time.sleep(0.2)

    assert len(transport.sent_messages) == 2, \
        "Transport should have received two messages"
    assert handler.pending_count == 2, \
        "pending_count should be 2 with two concurrent requests"

    # The two threads race to send, so the sent messages are looked up by
    # request identifier rather than by position. Deliver B's response first.
    sent_by_identifier = {msg.identifier: msg for msg in transport.sent_messages}
    sent_b = sent_by_identifier["req-b"]
    response_b = _create_response_message(
        correlation_id=sent_b.correlation_id,
        identifier="resp-b",
    )
    handler.handle_response(response_b)

    time.sleep(0.1)

    sent_a = sent_by_identifier["req-a"]
    response_a = _create_response_message(
        correlation_id=sent_a.correlation_id,
        identifier="resp-a",
    )
    handler.handle_response(response_a)

    thread_a.join(timeout=2.0)
    thread_b.join(timeout=2.0)

    assert error_a[0] is None, \
        "Request A should not raise: {}".format(error_a[0])
    assert error_b[0] is None, \
        "Request B should not raise: {}".format(error_b[0])
    assert result_a[0].identifier == "resp-a", \
        "Request A should receive response A"
    assert result_b[0].identifier == "resp-b", \
        "Request B should receive response B"
    return


# =========================================================================
# handle_response with no matching pending request
# =========================================================================

def test_handle_response_no_matching_request():
    """
        Verify handle_response silently ignores a response with no
        matching pending request.
    """
    handler = RequestResponseHandler()
    response = _create_response_message(
        correlation_id="orphan-correlation-id",
        identifier="orphan-resp",
    )

    # Should not raise
    handler.handle_response(response)
    return


# =========================================================================
# pending_count decreases after response or timeout (Requirement 12.7)
# =========================================================================

def test_pending_count_decreases_after_response():
    """
        Verify pending_count decreases after a response is delivered.
    """
    handler = RequestResponseHandler(default_timeout=5.0)
    transport = RecordingTransport()
    request = _create_request_message()

    result_holder = [None]

    def do_request():
        try:
            result_holder[0] = handler.send_request(request, transport, timeout=5.0)
        except Exception:
            # Worker-thread exceptions cannot reach the test thread; a failed send_request
            # is detected by the pending_count assertions below.
            pass

    thread = threading.Thread(target=do_request)
    thread.start()

    time.sleep(0.1)

    assert handler.pending_count == 1, \
        "pending_count should be 1 while request is pending"

    sent_msg = transport.sent_messages[0]
    response = _create_response_message(correlation_id=sent_msg.correlation_id)
    handler.handle_response(response)

    thread.join(timeout=2.0)

    assert handler.pending_count == 0, \
        "pending_count should be 0 after response is delivered"
    return


def test_pending_count_decreases_after_timeout():
    """
        Verify pending_count decreases after a request times out.
    """
    handler = RequestResponseHandler(default_timeout=0.2)
    transport = RecordingTransport()
    request = _create_request_message()

    def do_request():
        try:
            handler.send_request(request, transport, timeout=0.2)
        except MessageTimeoutError:
            # Expected: the request is meant to time out; the test verifies pending_count afterward.
            pass

    thread = threading.Thread(target=do_request)
    thread.start()
    thread.join(timeout=2.0)

    assert handler.pending_count == 0, \
        "pending_count should be 0 after timeout"
    return


# =========================================================================
# __repr__ (Requirement 12.9, 26.17)
# =========================================================================

class _FailingTransport(RecordingTransport):
    """
        RecordingTransport whose send raises a TransportError.
    """

    def send(self, message: Message) -> MessageEnvelope:
        raise TransportError(
            transport_name=self.name,
            operation="send",
            cause=ConnectionError("broker unreachable"),
        )


def test_send_request_failed_send_is_not_left_pending():
    """
        Verify that when the transport send fails, send_request raises the
        send error and no longer tracks the request as pending.
    """
    handler = RequestResponseHandler(default_timeout=5.0)
    transport = _FailingTransport()
    request_message = _create_request_message()

    caught = None
    try:
        handler.send_request(message=request_message, transport=transport, timeout=5.0)
    except TransportError as err:
        caught = err

    assert caught is not None, \
        "The send error should propagate to the caller"
    assert handler.pending_count == 0, \
        "A request whose send failed should not stay pending, got {}".format(
            handler.pending_count)
    return


def test_repr_includes_class_name_and_pending_count():
    """
        Verify __repr__ includes the class name and pending count.
    """
    handler = RequestResponseHandler()
    repr_str = repr(handler)

    assert "RequestResponseHandler" in repr_str, \
        "repr should contain the class name"
    assert "pending_count=0" in repr_str, \
        "repr should contain the pending count"
    return


# =========================================================================
# __str__ (Requirement 12.10, 26.18)
# =========================================================================

def test_str_includes_pending_count_and_default_timeout():
    """
        Verify __str__ includes the pending count and default timeout.
    """
    handler = RequestResponseHandler(default_timeout=15.0)
    str_val = str(handler)

    assert "0 pending request(s)" in str_val, \
        "str should contain the pending count"
    assert "15.0" in str_val, \
        "str should contain the default timeout"
    return


# =========================================================================
# Structured logging (Requirement 26.17, 26.18)
# =========================================================================

def test_timeout_logs_warning():
    """
        Verify that a timeout logs a WARNING message with the request
        message identifier, correlation identifier, and timeout duration.
    """
    handler = RequestResponseHandler(default_timeout=0.2)
    transport = RecordingTransport()
    request = _create_request_message(identifier="log-timeout-req")

    logger = logging.getLogger("ccai.agentkit.messaging.requestresponse")
    log_handler = logging.handlers.MemoryHandler(capacity=100)
    logger.addHandler(log_handler)
    original_level = logger.level
    logger.setLevel(logging.DEBUG)

    try:
        error_holder = [None]

        def do_request():
            try:
                handler.send_request(request, transport, timeout=0.2)
            except MessageTimeoutError as exc:
                error_holder[0] = exc

        thread = threading.Thread(target=do_request)
        thread.start()
        thread.join(timeout=2.0)

        log_handler.flush()
        log_records = log_handler.buffer

        warning_records = [r for r in log_records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1, \
            "At least one WARNING log record should be emitted on timeout"

        warning_msg = warning_records[0].getMessage()
        assert "log-timeout-req" in warning_msg, \
            "Warning log should contain the request message identifier"
    finally:
        logger.removeHandler(log_handler)
        logger.setLevel(original_level)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
