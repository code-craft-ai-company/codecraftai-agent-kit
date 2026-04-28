"""
    Unit tests for the messaging error classes.

    Tests TransportError, MessageSerializationError, MessageRoutingError,
    and MessageTimeoutError including construction, property access, repr,
    and error messages.

    Requirements: 23.1-23.9
"""

from automojo.agentkit.errors import AgentKitError
from automojo.agentkit.messagingerrors import MessageRoutingError
from automojo.agentkit.messagingerrors import MessageSerializationError
from automojo.agentkit.messagingerrors import MessageTimeoutError
from automojo.agentkit.messagingerrors import TransportError


# =========================================================================
# TransportError tests (Requirements 23.1, 23.2, 23.9)
# =========================================================================

def test_transport_error_inherits_from_agentkit_error():
    """
        Verify that TransportError inherits from AgentKitError.
    """
    err = TransportError("http-transport", "connect")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "TransportError should inherit from AgentKitError"
    return


def test_transport_error_transport_name_property():
    """
        Verify that the transport_name property returns the provided name.
    """
    err = TransportError("ws-transport", "send")
    name = err.transport_name
    assert name == "ws-transport", "transport_name should be 'ws-transport'"
    return


def test_transport_error_operation_property():
    """
        Verify that the operation property returns the provided operation.
    """
    err = TransportError("grpc-transport", "receive")
    operation = err.operation
    assert operation == "receive", "operation should be 'receive'"
    return


def test_transport_error_cause_none_by_default():
    """
        Verify that cause is None when not provided.
    """
    err = TransportError("my-transport", "connect")
    cause = err.cause
    assert cause is None, "Cause should be None when not provided"
    return


def test_transport_error_cause_with_exception():
    """
        Verify that cause stores the provided exception.
    """
    original = ConnectionError("connection refused")
    err = TransportError("http-transport", "connect", cause=original)
    cause = err.cause
    assert cause is original, "Cause should be the original exception"
    return


def test_transport_error_message_without_cause():
    """
        Verify that the error message includes transport name and operation.
    """
    err = TransportError("ws-transport", "disconnect")
    msg = err.message
    has_name = "ws-transport" in msg
    has_op = "disconnect" in msg
    assert has_name is True, "Message should contain the transport name"
    assert has_op is True, "Message should contain the operation"
    return


def test_transport_error_message_with_cause():
    """
        Verify that the error message includes the cause when provided.
    """
    original = TimeoutError("timed out")
    err = TransportError("http-transport", "send", cause=original)
    msg = err.message
    has_cause = "timed out" in msg
    assert has_cause is True, "Message should contain the cause description"
    return


def test_transport_error_repr():
    """
        Verify that __repr__ includes class name, transport name, operation,
        and cause.
    """
    err = TransportError("grpc-transport", "connect", cause=RuntimeError("boom"))
    repr_str = repr(err)
    has_class = "TransportError" in repr_str
    has_name = "grpc-transport" in repr_str
    has_op = "connect" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_name is True, "repr should contain the transport name"
    assert has_op is True, "repr should contain the operation"
    return


def test_transport_error_str_contains_message():
    """
        Verify that str() produces a meaningful string with the error message.
    """
    err = TransportError("mq-transport", "send")
    str_val = str(err)
    has_name = "mq-transport" in str_val
    has_op = "send" in str_val
    assert has_name is True, "str should contain the transport name"
    assert has_op is True, "str should contain the operation"
    return


# =========================================================================
# MessageSerializationError tests (Requirements 23.3, 23.4, 23.9)
# =========================================================================

def test_serialization_error_inherits_from_agentkit_error():
    """
        Verify that MessageSerializationError inherits from AgentKitError.
    """
    err = MessageSerializationError("json", "serialize", "object not serializable")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "MessageSerializationError should inherit from AgentKitError"
    return


def test_serialization_error_format_name_property():
    """
        Verify that the format_name property returns the provided format name.
    """
    err = MessageSerializationError("msgpack", "deserialize", "invalid bytes")
    name = err.format_name
    assert name == "msgpack", "format_name should be 'msgpack'"
    return


def test_serialization_error_direction_property():
    """
        Verify that the direction property returns the provided direction.
    """
    err = MessageSerializationError("protobuf", "serialize", "missing field")
    direction = err.direction
    assert direction == "serialize", "direction should be 'serialize'"
    return


def test_serialization_error_detail_property():
    """
        Verify that the detail property returns the provided detail string.
    """
    err = MessageSerializationError("json", "deserialize", "unexpected token at position 5")
    detail = err.detail
    assert detail == "unexpected token at position 5", "detail should match the provided string"
    return


def test_serialization_error_message_format():
    """
        Verify that the error message includes format name, direction, and detail.
    """
    err = MessageSerializationError("json", "serialize", "type set is not serializable")
    msg = err.message
    has_format = "json" in msg
    has_direction = "serialize" in msg
    has_detail = "type set is not serializable" in msg
    assert has_format is True, "Message should contain the format name"
    assert has_direction is True, "Message should contain the direction"
    assert has_detail is True, "Message should contain the detail"
    return


def test_serialization_error_repr():
    """
        Verify that __repr__ includes class name, format name, direction,
        and detail.
    """
    err = MessageSerializationError("msgpack", "deserialize", "truncated data")
    repr_str = repr(err)
    has_class = "MessageSerializationError" in repr_str
    has_format = "msgpack" in repr_str
    has_direction = "deserialize" in repr_str
    has_detail = "truncated data" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_format is True, "repr should contain the format name"
    assert has_direction is True, "repr should contain the direction"
    assert has_detail is True, "repr should contain the detail"
    return


def test_serialization_error_str_contains_message():
    """
        Verify that str() produces a meaningful string with the error message.
    """
    err = MessageSerializationError("protobuf", "deserialize", "invalid wire type")
    str_val = str(err)
    has_format = "protobuf" in str_val
    has_detail = "invalid wire type" in str_val
    assert has_format is True, "str should contain the format name"
    assert has_detail is True, "str should contain the detail"
    return


# =========================================================================
# MessageRoutingError tests (Requirements 23.5, 23.6, 23.9)
# =========================================================================

def test_routing_error_inherits_from_agentkit_error():
    """
        Verify that MessageRoutingError inherits from AgentKitError.
    """
    err = MessageRoutingError(message_id="msg-1", target="agent-x", detail="no handler")
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "MessageRoutingError should inherit from AgentKitError"
    return


def test_routing_error_message_id_property():
    """
        Verify that the message_id property returns the provided message id.
    """
    err = MessageRoutingError(message_id="msg-abc", target="agent-y")
    mid = err.message_id
    assert mid == "msg-abc", "message_id should be 'msg-abc'"
    return


def test_routing_error_target_property():
    """
        Verify that the target property returns the provided target.
    """
    err = MessageRoutingError(target="events.user.created")
    target = err.target
    assert target == "events.user.created", "target should be 'events.user.created'"
    return


def test_routing_error_detail_property():
    """
        Verify that the detail property returns the provided detail string.
    """
    err = MessageRoutingError(detail="no matching handler found")
    detail = err.detail
    assert detail == "no matching handler found", "detail should match the provided string"
    return


def test_routing_error_optional_fields_default_to_none():
    """
        Verify that message_id, target, and detail default to None.
    """
    err = MessageRoutingError()
    assert err.message_id is None, "message_id should default to None"
    assert err.target is None, "target should default to None"
    assert err.detail is None, "detail should default to None"
    return


def test_routing_error_message_with_all_fields():
    """
        Verify that the error message includes target, message_id, and detail
        when all are provided.
    """
    err = MessageRoutingError(message_id="msg-1", target="agent-z", detail="transport not found")
    msg = err.message
    has_target = "agent-z" in msg
    has_mid = "msg-1" in msg
    has_detail = "transport not found" in msg
    assert has_target is True, "Message should contain the target"
    assert has_mid is True, "Message should contain the message_id"
    assert has_detail is True, "Message should contain the detail"
    return


def test_routing_error_message_with_only_target():
    """
        Verify that the error message includes the target when only target
        is provided.
    """
    err = MessageRoutingError(target="agent-q")
    msg = err.message
    has_target = "agent-q" in msg
    assert has_target is True, "Message should contain the target"
    return


def test_routing_error_repr():
    """
        Verify that __repr__ includes class name, message_id, target, and detail.
    """
    err = MessageRoutingError(message_id="msg-5", target="agent-w", detail="unresolvable")
    repr_str = repr(err)
    has_class = "MessageRoutingError" in repr_str
    has_mid = "msg-5" in repr_str
    has_target = "agent-w" in repr_str
    has_detail = "unresolvable" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_mid is True, "repr should contain the message_id"
    assert has_target is True, "repr should contain the target"
    assert has_detail is True, "repr should contain the detail"
    return


def test_routing_error_str_contains_message():
    """
        Verify that str() produces a meaningful string with the error message.
    """
    err = MessageRoutingError(target="agent-r", detail="no route")
    str_val = str(err)
    has_target = "agent-r" in str_val
    has_detail = "no route" in str_val
    assert has_target is True, "str should contain the target"
    assert has_detail is True, "str should contain the detail"
    return


# =========================================================================
# MessageTimeoutError tests (Requirements 23.7, 23.8, 23.9)
# =========================================================================

def test_timeout_error_inherits_from_agentkit_error():
    """
        Verify that MessageTimeoutError inherits from AgentKitError.
    """
    err = MessageTimeoutError("req-1", "corr-1", 30.0)
    is_agentkit_error = isinstance(err, AgentKitError)
    assert is_agentkit_error is True, "MessageTimeoutError should inherit from AgentKitError"
    return


def test_timeout_error_request_message_id_property():
    """
        Verify that the request_message_id property returns the provided id.
    """
    err = MessageTimeoutError("req-abc", "corr-xyz", 60.0)
    mid = err.request_message_id
    assert mid == "req-abc", "request_message_id should be 'req-abc'"
    return


def test_timeout_error_correlation_id_property():
    """
        Verify that the correlation_id property returns the provided id.
    """
    err = MessageTimeoutError("req-1", "corr-42", 15.5)
    cid = err.correlation_id
    assert cid == "corr-42", "correlation_id should be 'corr-42'"
    return


def test_timeout_error_timeout_property():
    """
        Verify that the timeout property returns the provided duration.
    """
    err = MessageTimeoutError("req-1", "corr-1", 45.0)
    timeout = err.timeout
    assert timeout == 45.0, "timeout should be 45.0"
    return


def test_timeout_error_message_format():
    """
        Verify that the error message includes request id, correlation id,
        and timeout duration.
    """
    err = MessageTimeoutError("req-7", "corr-7", 30.0)
    msg = err.message
    has_req = "req-7" in msg
    has_corr = "corr-7" in msg
    has_timeout = "30.0" in msg
    assert has_req is True, "Message should contain the request message id"
    assert has_corr is True, "Message should contain the correlation id"
    assert has_timeout is True, "Message should contain the timeout duration"
    return


def test_timeout_error_repr():
    """
        Verify that __repr__ includes class name, request message id,
        correlation id, and timeout.
    """
    err = MessageTimeoutError("req-9", "corr-9", 120.0)
    repr_str = repr(err)
    has_class = "MessageTimeoutError" in repr_str
    has_req = "req-9" in repr_str
    has_corr = "corr-9" in repr_str
    has_timeout = "120.0" in repr_str
    assert has_class is True, "repr should contain the class name"
    assert has_req is True, "repr should contain the request message id"
    assert has_corr is True, "repr should contain the correlation id"
    assert has_timeout is True, "repr should contain the timeout"
    return


def test_timeout_error_str_contains_message():
    """
        Verify that str() produces a meaningful string with the error message.
    """
    err = MessageTimeoutError("req-3", "corr-3", 10.0)
    str_val = str(err)
    has_req = "req-3" in str_val
    has_corr = "corr-3" in str_val
    assert has_req is True, "str should contain the request message id"
    assert has_corr is True, "str should contain the correlation id"
    return


# =========================================================================
# Cross-cutting: all errors catchable as AgentKitError (Requirement 23.9)
# =========================================================================

def test_all_messaging_errors_catchable_as_agentkit_error():
    """
        Verify that all messaging exceptions can be caught as AgentKitError.
    """
    exceptions = [
        TransportError("transport-a", "connect"),
        MessageSerializationError("json", "serialize", "bad object"),
        MessageRoutingError(target="agent-x", detail="no route"),
        MessageTimeoutError("req-1", "corr-1", 30.0),
    ]

    for exc in exceptions:
        caught = False
        try:
            raise exc
        except AgentKitError:
            caught = True

        assert caught is True, "{} should be catchable as AgentKitError".format(type(exc).__name__)

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
