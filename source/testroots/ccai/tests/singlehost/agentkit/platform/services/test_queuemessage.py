"""
    Tests for the ccai.agentkit.platform.services.queuemessage module.

    Contains unit tests for the QueueMessage immutable data transfer object
    including read-only properties, as_dict serialization, JSON round-trip,
    and __repr__/__str__ output with body truncation.

    Feature: cross-platform-runtime
"""

import json

from datetime import datetime

from ccai.agentkit.platform.services.queuemessage import QueueMessage


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _create_sample_queue_message() -> QueueMessage:
    """
        Creates a sample QueueMessage for testing.

        :returns: A QueueMessage instance with known test values.
    """
    msg = QueueMessage(
        identifier="msg-001",
        queue_name="task-queue",
        body={"action": "process", "item_id": 42},
        attributes={"priority": "high"},
        receipt_handle="receipt-abc-123",
        timestamp=datetime(2026, 2, 20, 14, 0, 0)
    )
    return msg


# ---------------------------------------------------------------------------
# Read-only property tests
# ---------------------------------------------------------------------------

def test_identifier_property_returns_correct_value():
    """
        Verify that the identifier property returns the value passed at construction.
    """
    msg = _create_sample_queue_message()

    actual = msg.identifier

    assert actual == "msg-001", (
        "identifier should be 'msg-001', got: {!r}".format(actual)
    )
    return


def test_queue_name_property_returns_correct_value():
    """
        Verify that the queue_name property returns the value passed at construction.
    """
    msg = _create_sample_queue_message()

    actual = msg.queue_name

    assert actual == "task-queue", (
        "queue_name should be 'task-queue', got: {!r}".format(actual)
    )
    return


def test_body_property_returns_correct_value():
    """
        Verify that the body property returns the object passed at construction.
    """
    msg = _create_sample_queue_message()

    actual = msg.body

    expected = {"action": "process", "item_id": 42}
    assert actual == expected, (
        "body should be {!r}, got: {!r}".format(expected, actual)
    )
    return


def test_attributes_property_returns_defensive_copy():
    """
        Verify that the attributes property returns a copy and modifying it
        does not affect the internal state.
    """
    msg = _create_sample_queue_message()

    attrs_copy = msg.attributes
    attrs_copy["injected"] = "bad-value"

    original_attrs = msg.attributes
    has_injected = "injected" in original_attrs

    assert has_injected is False, (
        "Modifying returned attributes should not affect internal state"
    )
    return


def test_receipt_handle_property_returns_correct_value():
    """
        Verify that the receipt_handle property returns the value passed
        at construction.
    """
    msg = _create_sample_queue_message()

    actual = msg.receipt_handle

    assert actual == "receipt-abc-123", (
        "receipt_handle should be 'receipt-abc-123', got: {!r}".format(actual)
    )
    return


def test_timestamp_property_returns_correct_value():
    """
        Verify that the timestamp property returns the datetime passed
        at construction.
    """
    msg = _create_sample_queue_message()

    actual = msg.timestamp

    expected = datetime(2026, 2, 20, 14, 0, 0)
    assert actual == expected, (
        "timestamp should be {!r}, got: {!r}".format(expected, actual)
    )
    return


def test_none_attributes_defaults_to_empty_dict():
    """
        Verify that passing None for attributes results in an empty dictionary.
    """
    msg = QueueMessage(
        identifier="msg-002",
        queue_name="q",
        body="simple",
        attributes=None,
        receipt_handle="rh",
        timestamp=datetime(2026, 1, 1)
    )

    attrs = msg.attributes

    assert attrs == {}, (
        "None attributes should default to empty dict, got: {!r}".format(attrs)
    )
    return


# ---------------------------------------------------------------------------
# as_dict tests
# ---------------------------------------------------------------------------

def test_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all expected keys.
    """
    msg = _create_sample_queue_message()

    result = msg.as_dict()

    expected_keys = {"identifier", "queue_name", "body", "attributes",
                     "receipt_handle", "timestamp"}
    actual_keys = set(result.keys())

    assert actual_keys == expected_keys, (
        "as_dict should contain keys {}, got: {}".format(expected_keys, actual_keys)
    )
    return


def test_as_dict_timestamp_is_isoformat():
    """
        Verify that as_dict serializes timestamp as an ISO format string.
    """
    msg = _create_sample_queue_message()

    result = msg.as_dict()

    actual = result["timestamp"]
    expected = datetime(2026, 2, 20, 14, 0, 0).isoformat()

    assert actual == expected, (
        "timestamp should be ISO format {!r}, got: {!r}".format(expected, actual)
    )
    return


# ---------------------------------------------------------------------------
# JSON round-trip tests
# ---------------------------------------------------------------------------

def test_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    msg = _create_sample_queue_message()

    json_str = msg.to_json()
    parsed = json.loads(json_str)

    has_identifier = "identifier" in parsed
    assert has_identifier is True, "JSON should contain 'identifier' field"
    return


def test_json_round_trip_preserves_all_fields():
    """
        Verify that serializing to JSON and deserializing back produces
        an equivalent QueueMessage.
    """
    original = _create_sample_queue_message()

    json_str = original.to_json()
    restored = QueueMessage.from_json(json_str)

    assert restored.identifier == original.identifier, (
        "Round-trip identifier mismatch: {!r} != {!r}".format(
            restored.identifier, original.identifier)
    )
    assert restored.queue_name == original.queue_name, (
        "Round-trip queue_name mismatch: {!r} != {!r}".format(
            restored.queue_name, original.queue_name)
    )
    assert restored.body == original.body, (
        "Round-trip body mismatch: {!r} != {!r}".format(
            restored.body, original.body)
    )
    assert restored.attributes == original.attributes, (
        "Round-trip attributes mismatch: {!r} != {!r}".format(
            restored.attributes, original.attributes)
    )
    assert restored.receipt_handle == original.receipt_handle, (
        "Round-trip receipt_handle mismatch: {!r} != {!r}".format(
            restored.receipt_handle, original.receipt_handle)
    )
    assert restored.timestamp == original.timestamp, (
        "Round-trip timestamp mismatch: {!r} != {!r}".format(
            restored.timestamp, original.timestamp)
    )
    return


def test_from_dict_with_string_body():
    """
        Verify that from_dict works correctly with a simple string body.
    """
    data = {
        "identifier": "msg-003",
        "queue_name": "simple-queue",
        "body": "plain text message",
        "attributes": {},
        "receipt_handle": "rh-xyz",
        "timestamp": "2026-06-01T08:00:00"
    }

    msg = QueueMessage.from_dict(data)

    assert msg.body == "plain text message", (
        "from_dict should preserve string body, got: {!r}".format(msg.body)
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_contains_class_name_identifier_queue_name():
    """
        Verify that __repr__ includes the class name, identifier, and
        queue name.
    """
    msg = _create_sample_queue_message()

    repr_str = repr(msg)

    has_class_name = "QueueMessage" in repr_str
    has_identifier = "msg-001" in repr_str
    has_queue_name = "task-queue" in repr_str

    assert has_class_name is True, "repr should contain 'QueueMessage'"
    assert has_identifier is True, "repr should contain the identifier"
    assert has_queue_name is True, "repr should contain the queue name"
    return


def test_str_contains_identifier_queue_name_body_preview():
    """
        Verify that __str__ returns a human-readable summary with identifier,
        queue name, and body preview.
    """
    msg = _create_sample_queue_message()

    str_val = str(msg)

    has_identifier = "msg-001" in str_val
    has_queue_name = "task-queue" in str_val

    assert has_identifier is True, "str should contain the identifier"
    assert has_queue_name is True, "str should contain the queue name"
    return


def test_str_truncates_long_body_at_50_chars():
    """
        Verify that __str__ truncates the body preview at 50 characters
        and appends an ellipsis.
    """
    long_body = "A" * 100
    msg = QueueMessage(
        identifier="msg-long",
        queue_name="q",
        body=long_body,
        attributes={},
        receipt_handle="rh",
        timestamp=datetime(2026, 1, 1)
    )

    str_val = str(msg)

    has_ellipsis = "..." in str_val
    assert has_ellipsis is True, (
        "str should truncate long body with '...', got: {!r}".format(str_val)
    )

    # The body preview should be at most 53 chars (50 + "...")
    # Verify the full 100-char body is NOT present
    has_full_body = long_body in str_val
    assert has_full_body is False, (
        "str should not contain the full 100-char body"
    )
    return


def test_str_does_not_truncate_short_body():
    """
        Verify that __str__ does not truncate a body shorter than 50 characters.
    """
    short_body = "short"
    msg = QueueMessage(
        identifier="msg-short",
        queue_name="q",
        body=short_body,
        attributes={},
        receipt_handle="rh",
        timestamp=datetime(2026, 1, 1)
    )

    str_val = str(msg)

    has_body = "short" in str_val
    has_ellipsis = "..." in str_val

    assert has_body is True, "str should contain the short body"
    assert has_ellipsis is False, "str should not truncate short body with '...'"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
