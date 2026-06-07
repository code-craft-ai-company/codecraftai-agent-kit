"""
    Unit tests for the ccai.agentkit.message and
    ccai.agentkit.messageenvelope modules.

    Tests Message construction, auto-generated identifier and timestamp,
    property access, as_dict, to_json, from_dict, from_json, __repr__,
    and __str__.

    Tests MessageEnvelope construction, default values, property access,
    as_dict, __repr__, __str__, and delivery_status validation.

    Requirements: 4.1-4.11, 6.1-6.5, 26.3, 26.4, 26.5, 26.6
"""

import json
import uuid

from datetime import datetime
from datetime import timezone

from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.errors import SemanticError
from ccai.agentkit.message import Message
from ccai.agentkit.messageenvelope import MessageEnvelope
from ccai.agentkit.messagepattern import MessagePattern


# =========================================================================
# Helper factories
# =========================================================================

def _make_sender() -> AgentAddress:
    """
        Creates a sender AgentAddress for testing.
    """
    addr = AgentAddress(
        agent_identifier="sender-agent",
        transport_name="http",
        endpoint={"host": "sender.example.com", "port": "8080"},
    )
    return addr


def _make_recipient() -> AgentAddress:
    """
        Creates a recipient AgentAddress for testing.
    """
    addr = AgentAddress(
        agent_identifier="recipient-agent",
        transport_name="http",
        endpoint={"host": "recipient.example.com", "port": "9090"},
    )
    return addr


# =========================================================================
# Construction and auto-generated fields (Requirements 4.1, 4.2, 4.3)
# =========================================================================

def test_construction_with_all_fields():
    """
        Verify Message stores all fields when explicitly provided.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    payload = {"action": "greet", "data": "hello"}
    pattern = MessagePattern.REQUEST
    headers = {"content-type": "application/json"}
    correlation_id = "corr-001"
    identifier = "msg-001"
    timestamp = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload=payload,
        pattern=pattern,
        headers=headers,
        correlation_id=correlation_id,
        identifier=identifier,
        timestamp=timestamp,
    )

    assert msg.identifier == "msg-001", \
        "identifier should be 'msg-001'"
    assert msg.sender == sender, \
        "sender should match the provided AgentAddress"
    assert msg.recipient == recipient, \
        "recipient should match the provided AgentAddress"
    assert msg.payload == {"action": "greet", "data": "hello"}, \
        "payload should match the provided dictionary"
    assert msg.pattern == MessagePattern.REQUEST, \
        "pattern should be REQUEST"
    assert msg.headers == {"content-type": "application/json"}, \
        "headers should match the provided dictionary"
    assert msg.correlation_id == "corr-001", \
        "correlation_id should be 'corr-001'"
    assert msg.timestamp == timestamp, \
        "timestamp should match the provided datetime"
    return


def test_auto_generated_identifier():
    """
        Verify Message generates a UUID-based identifier when none is provided.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="test-payload",
        pattern=MessagePattern.FIRE_AND_FORGET,
    )

    identifier = msg.identifier
    assert identifier is not None, \
        "identifier should not be None"
    assert len(identifier) > 0, \
        "identifier should not be empty"

    # Verify it is a valid UUID string
    parsed_uuid = uuid.UUID(identifier)
    assert str(parsed_uuid) == identifier, \
        "identifier should be a valid UUID string"
    return


def test_auto_generated_timestamp():
    """
        Verify Message generates a UTC timestamp when none is provided.
    """
    before = datetime.now(timezone.utc)

    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="test-payload",
        pattern=MessagePattern.EVENT,
    )

    after = datetime.now(timezone.utc)

    assert msg.timestamp is not None, \
        "timestamp should not be None"
    assert msg.timestamp >= before, \
        "timestamp should be at or after the time before construction"
    assert msg.timestamp <= after, \
        "timestamp should be at or before the time after construction"
    assert msg.timestamp.tzinfo is not None, \
        "timestamp should be timezone-aware"
    return


def test_default_headers_empty_dict():
    """
        Verify Message defaults headers to an empty dict when not provided.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="test",
        pattern=MessagePattern.RESPONSE,
    )

    assert msg.headers == {}, \
        "headers should default to an empty dict"
    return


def test_default_correlation_id_none():
    """
        Verify Message defaults correlation_id to None when not provided.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="test",
        pattern=MessagePattern.FIRE_AND_FORGET,
    )

    assert msg.correlation_id is None, \
        "correlation_id should default to None"
    return


# =========================================================================
# Read-only properties (Requirement 4.4)
# =========================================================================

def test_headers_returns_defensive_copy():
    """
        Verify that the headers property returns a copy, so mutations
        do not affect the internal state.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    headers = {"x-trace": "abc123"}

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="test",
        pattern=MessagePattern.REQUEST,
        headers=headers,
    )

    copy = msg.headers
    copy["x-trace"] = "modified"

    assert msg.headers["x-trace"] == "abc123", \
        "Modifying the returned headers should not affect the original"
    return


# =========================================================================
# as_dict (Requirement 4.5)
# =========================================================================

def test_as_dict_returns_all_fields():
    """
        Verify as_dict returns a dictionary with all message fields,
        converting sender/recipient to dicts, pattern to string value,
        and timestamp to ISO format.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    timestamp = datetime(2025, 6, 1, 10, 30, 0, tzinfo=timezone.utc)

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload={"key": "value"},
        pattern=MessagePattern.REQUEST,
        headers={"h1": "v1"},
        correlation_id="corr-100",
        identifier="msg-100",
        timestamp=timestamp,
    )

    result = msg.as_dict()

    assert result["identifier"] == "msg-100", \
        "as_dict identifier mismatch"
    assert result["sender"] == sender.as_dict(), \
        "as_dict sender should match sender.as_dict()"
    assert result["recipient"] == recipient.as_dict(), \
        "as_dict recipient should match recipient.as_dict()"
    assert result["payload"] == {"key": "value"}, \
        "as_dict payload mismatch"
    assert result["pattern"] == "REQUEST", \
        "as_dict pattern should be the string value 'REQUEST'"
    assert result["headers"] == {"h1": "v1"}, \
        "as_dict headers mismatch"
    assert result["correlation_id"] == "corr-100", \
        "as_dict correlation_id mismatch"
    assert result["timestamp"] == timestamp.isoformat(), \
        "as_dict timestamp should be ISO format string"
    return


def test_as_dict_with_none_correlation_id():
    """
        Verify as_dict includes correlation_id as None when not set.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="simple",
        pattern=MessagePattern.FIRE_AND_FORGET,
        identifier="msg-101",
    )

    result = msg.as_dict()

    assert result["correlation_id"] is None, \
        "as_dict correlation_id should be None"
    return


# =========================================================================
# to_json (Requirement 4.6)
# =========================================================================

def test_to_json_returns_valid_json():
    """
        Verify to_json returns a valid JSON string containing all fields.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    timestamp = datetime(2025, 3, 20, 8, 0, 0, tzinfo=timezone.utc)

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload={"data": [1, 2, 3]},
        pattern=MessagePattern.EVENT,
        identifier="msg-200",
        timestamp=timestamp,
    )

    json_str = msg.to_json()
    parsed = json.loads(json_str)

    assert parsed["identifier"] == "msg-200", \
        "JSON identifier mismatch"
    assert parsed["pattern"] == "EVENT", \
        "JSON pattern mismatch"
    assert parsed["payload"] == {"data": [1, 2, 3]}, \
        "JSON payload mismatch"
    return


# =========================================================================
# from_dict (Requirement 4.7)
# =========================================================================

def test_from_dict_constructs_message():
    """
        Verify from_dict constructs a Message from a dictionary,
        reconstructing AgentAddress, MessagePattern, and timestamp.
    """
    timestamp = datetime(2025, 4, 10, 14, 30, 0, tzinfo=timezone.utc)

    data = {
        "identifier": "msg-300",
        "sender": {
            "agent_identifier": "agent-a",
            "transport_name": "http",
            "endpoint": {"host": "a.com"},
        },
        "recipient": {
            "agent_identifier": "agent-b",
            "transport_name": "http",
            "endpoint": {"host": "b.com"},
        },
        "payload": {"action": "ping"},
        "pattern": "REQUEST",
        "headers": {"x-id": "123"},
        "correlation_id": "corr-300",
        "timestamp": timestamp.isoformat(),
    }

    msg = Message.from_dict(data)

    assert msg.identifier == "msg-300", \
        "from_dict identifier mismatch"
    assert msg.sender.agent_identifier == "agent-a", \
        "from_dict sender agent_identifier mismatch"
    assert msg.recipient.agent_identifier == "agent-b", \
        "from_dict recipient agent_identifier mismatch"
    assert msg.payload == {"action": "ping"}, \
        "from_dict payload mismatch"
    assert msg.pattern == MessagePattern.REQUEST, \
        "from_dict pattern mismatch"
    assert msg.headers == {"x-id": "123"}, \
        "from_dict headers mismatch"
    assert msg.correlation_id == "corr-300", \
        "from_dict correlation_id mismatch"
    assert msg.timestamp == timestamp, \
        "from_dict timestamp mismatch"
    return


# =========================================================================
# from_json (Requirement 4.8)
# =========================================================================

def test_from_json_constructs_message():
    """
        Verify from_json deserializes a JSON string into a Message.
    """
    timestamp = datetime(2025, 5, 5, 16, 0, 0, tzinfo=timezone.utc)

    data = {
        "identifier": "msg-400",
        "sender": {
            "agent_identifier": "agent-x",
            "transport_name": "grpc",
            "endpoint": {},
        },
        "recipient": {
            "agent_identifier": "agent-y",
            "transport_name": "grpc",
            "endpoint": {},
        },
        "payload": "hello-world",
        "pattern": "FIRE_AND_FORGET",
        "headers": {},
        "correlation_id": None,
        "timestamp": timestamp.isoformat(),
    }
    json_str = json.dumps(data)

    msg = Message.from_json(json_str)

    assert msg.identifier == "msg-400", \
        "from_json identifier mismatch"
    assert msg.sender.agent_identifier == "agent-x", \
        "from_json sender agent_identifier mismatch"
    assert msg.pattern == MessagePattern.FIRE_AND_FORGET, \
        "from_json pattern mismatch"
    assert msg.payload == "hello-world", \
        "from_json payload mismatch"
    assert msg.correlation_id is None, \
        "from_json correlation_id should be None"
    return


# =========================================================================
# JSON round-trip (Requirement 4.9)
# =========================================================================

def test_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent
        Message object.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    timestamp = datetime(2025, 7, 4, 12, 0, 0, tzinfo=timezone.utc)

    original = Message(
        sender=sender,
        recipient=recipient,
        payload={"items": [1, "two", 3.0]},
        pattern=MessagePattern.RESPONSE,
        headers={"trace": "xyz"},
        correlation_id="corr-500",
        identifier="msg-500",
        timestamp=timestamp,
    )

    json_str = original.to_json()
    restored = Message.from_json(json_str)

    assert restored.identifier == original.identifier, \
        "Round-trip identifier mismatch"
    assert restored.sender == original.sender, \
        "Round-trip sender mismatch"
    assert restored.recipient == original.recipient, \
        "Round-trip recipient mismatch"
    assert restored.payload == original.payload, \
        "Round-trip payload mismatch"
    assert restored.pattern == original.pattern, \
        "Round-trip pattern mismatch"
    assert restored.headers == original.headers, \
        "Round-trip headers mismatch"
    assert restored.correlation_id == original.correlation_id, \
        "Round-trip correlation_id mismatch"
    assert restored.timestamp == original.timestamp, \
        "Round-trip timestamp mismatch"
    return


# =========================================================================
# __repr__ (Requirements 4.10, 26.3)
# =========================================================================

def test_repr_contains_class_name_and_fields():
    """
        Verify __repr__ includes the class name, identifier, pattern,
        and a payload preview.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload={"key": "value"},
        pattern=MessagePattern.REQUEST,
        identifier="msg-600",
    )

    repr_str = repr(msg)

    assert "Message" in repr_str, \
        "repr should contain 'Message'"
    assert "msg-600" in repr_str, \
        "repr should contain the identifier"
    assert "REQUEST" in repr_str, \
        "repr should contain the pattern value"
    return


def test_repr_truncates_long_payload():
    """
        Verify __repr__ truncates the payload preview for long payloads.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    long_payload = "x" * 200

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload=long_payload,
        pattern=MessagePattern.EVENT,
        identifier="msg-601",
    )

    repr_str = repr(msg)

    assert "..." in repr_str, \
        "repr should contain '...' for truncated payload"
    return


# =========================================================================
# __str__ (Requirements 4.11, 26.4)
# =========================================================================

def test_str_contains_human_readable_summary():
    """
        Verify __str__ returns a human-readable summary including the
        sender, recipient, pattern, and payload preview.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload={"action": "notify"},
        pattern=MessagePattern.FIRE_AND_FORGET,
        identifier="msg-700",
    )

    str_val = str(msg)

    assert "sender-agent" in str_val, \
        "str should contain the sender agent identifier"
    assert "recipient-agent" in str_val, \
        "str should contain the recipient agent identifier"
    assert "FIRE_AND_FORGET" in str_val, \
        "str should contain the pattern value"
    return


# =========================================================================
# Payload types (Requirement 4.1 - dict, list, string, bytes)
# =========================================================================

def test_payload_as_list():
    """
        Verify Message accepts a list as payload.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload=[1, 2, 3],
        pattern=MessagePattern.EVENT,
    )

    assert msg.payload == [1, 2, 3], \
        "payload should be the list [1, 2, 3]"
    return


def test_payload_as_string():
    """
        Verify Message accepts a string as payload.
    """
    sender = _make_sender()
    recipient = _make_recipient()

    msg = Message(
        sender=sender,
        recipient=recipient,
        payload="hello",
        pattern=MessagePattern.FIRE_AND_FORGET,
    )

    assert msg.payload == "hello", \
        "payload should be the string 'hello'"
    return


# =========================================================================
# MessageEnvelope - Helper factory
# =========================================================================

def _make_message() -> Message:
    """
        Creates a Message instance for MessageEnvelope testing.
    """
    sender = _make_sender()
    recipient = _make_recipient()
    msg = Message(
        sender=sender,
        recipient=recipient,
        payload={"action": "test"},
        pattern=MessagePattern.FIRE_AND_FORGET,
        identifier="msg-env-001",
    )
    return msg


# =========================================================================
# MessageEnvelope construction (Requirement 6.1)
# =========================================================================

def test_envelope_construction_with_all_fields():
    """
        Verify MessageEnvelope stores all fields when explicitly provided.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="http-transport",
        attempt_count=3,
        delivery_status="delivered",
    )

    assert envelope.message is msg, \
        "envelope.message should be the provided Message"
    assert envelope.transport_name == "http-transport", \
        "transport_name should be 'http-transport'"
    assert envelope.attempt_count == 3, \
        "attempt_count should be 3"
    assert envelope.delivery_status == "delivered", \
        "delivery_status should be 'delivered'"
    return


def test_envelope_default_attempt_count():
    """
        Verify MessageEnvelope defaults attempt_count to 1.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="ws-transport",
    )

    assert envelope.attempt_count == 1, \
        "attempt_count should default to 1"
    return


def test_envelope_default_delivery_status():
    """
        Verify MessageEnvelope defaults delivery_status to 'pending'.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="grpc-transport",
    )

    assert envelope.delivery_status == "pending", \
        "delivery_status should default to 'pending'"
    return


# =========================================================================
# MessageEnvelope property access (Requirement 6.2)
# =========================================================================

def test_envelope_property_access():
    """
        Verify all MessageEnvelope properties return the expected values.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="mq-transport",
        attempt_count=2,
        delivery_status="failed",
    )

    assert envelope.message.identifier == "msg-env-001", \
        "message identifier should be 'msg-env-001'"
    assert envelope.transport_name == "mq-transport", \
        "transport_name should be 'mq-transport'"
    assert envelope.attempt_count == 2, \
        "attempt_count should be 2"
    assert envelope.delivery_status == "failed", \
        "delivery_status should be 'failed'"
    return


# =========================================================================
# MessageEnvelope valid statuses (Requirement 6.1)
# =========================================================================

def test_envelope_valid_status_pending():
    """
        Verify MessageEnvelope accepts 'pending' as delivery_status.
    """
    msg = _make_message()
    envelope = MessageEnvelope(message=msg, transport_name="t1", delivery_status="pending")
    assert envelope.delivery_status == "pending", \
        "delivery_status should be 'pending'"
    return


def test_envelope_valid_status_delivered():
    """
        Verify MessageEnvelope accepts 'delivered' as delivery_status.
    """
    msg = _make_message()
    envelope = MessageEnvelope(message=msg, transport_name="t1", delivery_status="delivered")
    assert envelope.delivery_status == "delivered", \
        "delivery_status should be 'delivered'"
    return


def test_envelope_valid_status_failed():
    """
        Verify MessageEnvelope accepts 'failed' as delivery_status.
    """
    msg = _make_message()
    envelope = MessageEnvelope(message=msg, transport_name="t1", delivery_status="failed")
    assert envelope.delivery_status == "failed", \
        "delivery_status should be 'failed'"
    return


# =========================================================================
# MessageEnvelope invalid delivery_status (Requirement 6.1)
# =========================================================================

def test_envelope_invalid_delivery_status_raises_semantic_error():
    """
        Verify MessageEnvelope raises SemanticError for an invalid
        delivery_status value.
    """
    msg = _make_message()

    raised = False
    try:
        MessageEnvelope(
            message=msg,
            transport_name="http-transport",
            delivery_status="unknown",
        )
    except SemanticError:
        raised = True

    assert raised, \
        "MessageEnvelope should raise SemanticError for invalid delivery_status"
    return


def test_envelope_empty_delivery_status_raises_semantic_error():
    """
        Verify MessageEnvelope raises SemanticError for an empty
        delivery_status string.
    """
    msg = _make_message()

    raised = False
    try:
        MessageEnvelope(
            message=msg,
            transport_name="http-transport",
            delivery_status="",
        )
    except SemanticError:
        raised = True

    assert raised, \
        "MessageEnvelope should raise SemanticError for empty delivery_status"
    return


# =========================================================================
# MessageEnvelope as_dict (Requirement 6.3)
# =========================================================================

def test_envelope_as_dict():
    """
        Verify as_dict returns a dictionary with all envelope fields
        including the wrapped message as a dict.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="http-transport",
        attempt_count=2,
        delivery_status="delivered",
    )

    result = envelope.as_dict()

    assert result["transport_name"] == "http-transport", \
        "as_dict transport_name mismatch"
    assert result["attempt_count"] == 2, \
        "as_dict attempt_count mismatch"
    assert result["delivery_status"] == "delivered", \
        "as_dict delivery_status mismatch"
    assert result["message"] == msg.as_dict(), \
        "as_dict message should match msg.as_dict()"
    return


# =========================================================================
# MessageEnvelope __repr__ (Requirements 6.4, 26.5)
# =========================================================================

def test_envelope_repr():
    """
        Verify __repr__ includes class name, message identifier,
        transport name, and delivery status.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="http-transport",
        delivery_status="pending",
    )

    repr_str = repr(envelope)

    assert "MessageEnvelope" in repr_str, \
        "repr should contain 'MessageEnvelope'"
    assert "msg-env-001" in repr_str, \
        "repr should contain the message identifier"
    assert "http-transport" in repr_str, \
        "repr should contain the transport name"
    assert "pending" in repr_str, \
        "repr should contain the delivery status"
    return


# =========================================================================
# MessageEnvelope __str__ (Requirements 6.5, 26.6)
# =========================================================================

def test_envelope_str():
    """
        Verify __str__ returns a human-readable summary including
        message identifier, transport name, attempt count, and
        delivery status.
    """
    msg = _make_message()

    envelope = MessageEnvelope(
        message=msg,
        transport_name="ws-transport",
        attempt_count=3,
        delivery_status="failed",
    )

    str_val = str(envelope)

    assert "msg-env-001" in str_val, \
        "str should contain the message identifier"
    assert "ws-transport" in str_val, \
        "str should contain the transport name"
    assert "3" in str_val, \
        "str should contain the attempt count"
    assert "failed" in str_val, \
        "str should contain the delivery status"
    return


# =========================================================================
# Entrypoint
# =========================================================================

if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
