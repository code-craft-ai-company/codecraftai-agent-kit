"""
    Unit tests for the automojo.agentkit.messagerouter module.

    Tests MessageRouter register_by_topic, register_by_pattern,
    register_by_filter, deregister, route, handler_count, __repr__,
    and __str__. Verifies handler invocation order, exception logging
    and continuation, and MessageRoutingError on no match.

    Requirements: 11.1-11.11
"""

import logging

from automojo.agentkit.agentaddress import AgentAddress
from automojo.agentkit.message import Message
from automojo.agentkit.messagepattern import MessagePattern
from automojo.agentkit.messagerouter import MessageRouter
from automojo.agentkit.messagingerrors import MessageRoutingError


# =========================================================================
# Test helpers
# =========================================================================

def _create_message(topic=None, pattern=MessagePattern.FIRE_AND_FORGET,
                    payload="test-payload"):
    """
        Creates a Message with optional topic header for testing.
    """
    sender = AgentAddress(
        agent_identifier="sender-agent",
        transport_name="http",
    )
    recipient = AgentAddress(
        agent_identifier="recipient-agent",
        transport_name="http",
    )

    headers = {}
    if topic is not None:
        headers["topic"] = topic

    message = Message(
        sender=sender,
        recipient=recipient,
        payload=payload,
        pattern=pattern,
        headers=headers,
    )
    return message


# =========================================================================
# register_by_topic (Requirement 11.1)
# =========================================================================

def test_register_by_topic_returns_registration_id():
    """
        Verify register_by_topic returns a registration identifier string.
    """
    router = MessageRouter()
    invocations = []

    reg_id = router.register_by_topic("orders.created", lambda msg: invocations.append(msg))

    assert isinstance(reg_id, str), \
        "Registration ID should be a string"
    assert len(reg_id) > 0, \
        "Registration ID should not be empty"
    return


def test_register_by_topic_routes_matching_message():
    """
        Verify a handler registered by topic is invoked when the
        message topic matches.
    """
    router = MessageRouter()
    invocations = []

    router.register_by_topic("orders.created", lambda msg: invocations.append(msg))

    message = _create_message(topic="orders.created")
    router.route(message)

    assert len(invocations) == 1, \
        "Handler should be invoked once for matching topic"
    assert invocations[0] is message, \
        "Handler should receive the routed message"
    return


def test_register_by_topic_does_not_route_non_matching():
    """
        Verify a handler registered by topic is not invoked when the
        message topic does not match.
    """
    router = MessageRouter()
    invocations = []

    router.register_by_topic("orders.created", lambda msg: invocations.append(msg))

    message = _create_message(topic="orders.deleted")

    raised = False
    try:
        router.route(message)
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised when no handler matches"
    assert len(invocations) == 0, \
        "Handler should not be invoked for non-matching topic"
    return


# =========================================================================
# register_by_pattern (Requirement 11.2)
# =========================================================================

def test_register_by_pattern_returns_registration_id():
    """
        Verify register_by_pattern returns a registration identifier string.
    """
    router = MessageRouter()

    reg_id = router.register_by_pattern(MessagePattern.REQUEST, lambda msg: None)

    assert isinstance(reg_id, str), \
        "Registration ID should be a string"
    return


def test_register_by_pattern_routes_matching_message():
    """
        Verify a handler registered by pattern is invoked when the
        message pattern matches.
    """
    router = MessageRouter()
    invocations = []

    router.register_by_pattern(
        MessagePattern.REQUEST,
        lambda msg: invocations.append(msg)
    )

    message = _create_message(pattern=MessagePattern.REQUEST)
    router.route(message)

    assert len(invocations) == 1, \
        "Handler should be invoked once for matching pattern"
    return


def test_register_by_pattern_does_not_route_non_matching():
    """
        Verify a handler registered by pattern is not invoked when the
        message pattern does not match.
    """
    router = MessageRouter()
    invocations = []

    router.register_by_pattern(
        MessagePattern.REQUEST,
        lambda msg: invocations.append(msg)
    )

    message = _create_message(pattern=MessagePattern.EVENT)

    raised = False
    try:
        router.route(message)
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised when no handler matches"
    assert len(invocations) == 0, \
        "Handler should not be invoked for non-matching pattern"
    return


# =========================================================================
# register_by_filter (Requirement 11.3)
# =========================================================================

def test_register_by_filter_returns_registration_id():
    """
        Verify register_by_filter returns a registration identifier string.
    """
    router = MessageRouter()

    reg_id = router.register_by_filter(
        lambda msg: True,
        lambda msg: None
    )

    assert isinstance(reg_id, str), \
        "Registration ID should be a string"
    return


def test_register_by_filter_routes_when_filter_returns_true():
    """
        Verify a handler registered by filter is invoked when the
        filter callable returns True.
    """
    router = MessageRouter()
    invocations = []

    router.register_by_filter(
        lambda msg: msg.payload == "important",
        lambda msg: invocations.append(msg)
    )

    message = _create_message(payload="important")
    router.route(message)

    assert len(invocations) == 1, \
        "Handler should be invoked when filter returns True"
    return


def test_register_by_filter_does_not_route_when_filter_returns_false():
    """
        Verify a handler registered by filter is not invoked when the
        filter callable returns False.
    """
    router = MessageRouter()
    invocations = []

    router.register_by_filter(
        lambda msg: msg.payload == "important",
        lambda msg: invocations.append(msg)
    )

    message = _create_message(payload="not-important")

    raised = False
    try:
        router.route(message)
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised when no handler matches"
    assert len(invocations) == 0, \
        "Handler should not be invoked when filter returns False"
    return


# =========================================================================
# route invokes matching handlers in order (Requirement 11.4, 11.5)
# =========================================================================

def test_route_invokes_multiple_matching_handlers_in_order():
    """
        Verify route invokes all matching handlers in registration order.
    """
    router = MessageRouter()
    call_order = []

    router.register_by_topic("events.user", lambda msg: call_order.append("first"))
    router.register_by_topic("events.user", lambda msg: call_order.append("second"))
    router.register_by_topic("events.user", lambda msg: call_order.append("third"))

    message = _create_message(topic="events.user")
    router.route(message)

    assert call_order == ["first", "second", "third"], \
        "Handlers should be invoked in registration order, got: {}".format(call_order)
    return


def test_route_invokes_mixed_match_types():
    """
        Verify route invokes handlers registered by different match types
        when all match the same message.
    """
    router = MessageRouter()
    call_order = []

    router.register_by_topic("events.user", lambda msg: call_order.append("topic"))
    router.register_by_pattern(
        MessagePattern.FIRE_AND_FORGET,
        lambda msg: call_order.append("pattern")
    )
    router.register_by_filter(
        lambda msg: True,
        lambda msg: call_order.append("filter")
    )

    message = _create_message(topic="events.user", pattern=MessagePattern.FIRE_AND_FORGET)
    router.route(message)

    assert call_order == ["topic", "pattern", "filter"], \
        "All matching handlers should be invoked in order, got: {}".format(call_order)
    return


# =========================================================================
# route raises MessageRoutingError on no match (Requirement 11.6)
# =========================================================================

def test_route_raises_routing_error_when_no_handler_matches():
    """
        Verify MessageRoutingError is raised when no handler matches.
    """
    router = MessageRouter()
    router.register_by_topic("orders.created", lambda msg: None)

    message = _create_message(topic="orders.deleted")

    raised = False
    error = None
    try:
        router.route(message)
    except MessageRoutingError as exc:
        raised = True
        error = exc

    assert raised is True, \
        "MessageRoutingError should be raised when no handler matches"
    assert error.message_id == message.identifier, \
        "Error should contain the message identifier"
    return


def test_route_raises_routing_error_on_empty_router():
    """
        Verify MessageRoutingError is raised when routing with no handlers.
    """
    router = MessageRouter()
    message = _create_message(topic="anything")

    raised = False
    try:
        router.route(message)
    except MessageRoutingError:
        raised = True

    assert raised is True, \
        "MessageRoutingError should be raised on empty router"
    return


# =========================================================================
# deregister (Requirement 11.7)
# =========================================================================

def test_deregister_removes_handler():
    """
        Verify deregister removes the handler by registration ID.
    """
    router = MessageRouter()
    invocations = []

    reg_id = router.register_by_topic("events.user", lambda msg: invocations.append(msg))

    assert router.handler_count == 1, \
        "Should have 1 handler after registration"

    router.deregister(reg_id)

    assert router.handler_count == 0, \
        "Should have 0 handlers after deregistration"
    return


def test_deregister_nonexistent_is_noop():
    """
        Verify deregister with unknown ID does not raise.
    """
    router = MessageRouter()
    router.register_by_topic("events.user", lambda msg: None)

    router.deregister("nonexistent-id")

    assert router.handler_count == 1, \
        "Handler count should remain unchanged"
    return


def test_deregister_only_removes_target_handler():
    """
        Verify deregister removes only the targeted handler.
    """
    router = MessageRouter()
    call_order = []

    reg_a = router.register_by_topic("events.user", lambda msg: call_order.append("a"))
    reg_b = router.register_by_topic("events.user", lambda msg: call_order.append("b"))

    router.deregister(reg_a)

    message = _create_message(topic="events.user")
    router.route(message)

    assert call_order == ["b"], \
        "Only handler 'b' should remain after deregistering 'a', got: {}".format(call_order)
    return


# =========================================================================
# handler_count (Requirement 11.8)
# =========================================================================

def test_handler_count_empty():
    """
        Verify handler_count is 0 on a new router.
    """
    router = MessageRouter()

    assert router.handler_count == 0, \
        "handler_count should be 0 on new router"
    return


def test_handler_count_after_registrations():
    """
        Verify handler_count reflects the number of registered handlers.
    """
    router = MessageRouter()

    router.register_by_topic("a", lambda msg: None)
    router.register_by_pattern(MessagePattern.REQUEST, lambda msg: None)
    router.register_by_filter(lambda msg: True, lambda msg: None)

    assert router.handler_count == 3, \
        "handler_count should be 3 after three registrations"
    return


# =========================================================================
# Handler exception logging and continuation (Requirement 11.9)
# =========================================================================

def test_route_continues_after_handler_exception():
    """
        Verify that when a handler raises an exception, the router
        logs the exception and continues invoking remaining handlers.
    """
    router = MessageRouter()
    call_order = []

    def failing_handler(msg):
        call_order.append("failing")
        raise ValueError("handler error")

    def succeeding_handler(msg):
        call_order.append("succeeding")

    router.register_by_topic("events.user", failing_handler)
    router.register_by_topic("events.user", succeeding_handler)

    message = _create_message(topic="events.user")
    router.route(message)

    assert call_order == ["failing", "succeeding"], \
        "Both handlers should be invoked despite exception, got: {}".format(call_order)
    return


def test_route_logs_handler_exception_at_warning():
    """
        Verify that handler exceptions are logged at WARNING level.
    """
    router = MessageRouter()
    logger = logging.getLogger("automojo.agentkit.messaging.router")
    log_records = []

    class RecordHandler(logging.Handler):
        def emit(self, record):
            log_records.append(record)

    record_handler = RecordHandler()
    logger.addHandler(record_handler)
    original_level = logger.level
    logger.setLevel(logging.WARNING)

    try:
        def failing_handler(msg):
            raise RuntimeError("test error")

        router.register_by_topic("events.user", failing_handler)

        message = _create_message(topic="events.user")
        router.route(message)

        assert len(log_records) == 1, \
            "Should have logged one warning, got: {}".format(len(log_records))

        record = log_records[0]
        assert record.levelno == logging.WARNING, \
            "Log level should be WARNING"
        assert "test error" in record.getMessage(), \
            "Log message should contain the exception detail"
    finally:
        logger.removeHandler(record_handler)
        logger.setLevel(original_level)

    return


# =========================================================================
# __repr__ (Requirement 11.10, 26.13)
# =========================================================================

def test_repr_contains_class_name_and_count():
    """
        Verify __repr__ includes class name and handler count.
    """
    router = MessageRouter()
    router.register_by_topic("a", lambda msg: None)
    router.register_by_topic("b", lambda msg: None)

    repr_str = repr(router)

    assert "MessageRouter" in repr_str, \
        "repr should contain class name"
    assert "2" in repr_str, \
        "repr should contain handler count"
    return


# =========================================================================
# __str__ (Requirement 11.11, 26.14)
# =========================================================================

def test_str_empty_router():
    """
        Verify __str__ for an empty router.
    """
    router = MessageRouter()

    str_val = str(router)

    assert "0" in str_val, \
        "str should indicate 0 handlers"
    assert "MessageRouter" in str_val, \
        "str should contain class name"
    return


def test_str_with_topics():
    """
        Verify __str__ includes registered topics.
    """
    router = MessageRouter()
    router.register_by_topic("orders.created", lambda msg: None)
    router.register_by_topic("orders.deleted", lambda msg: None)

    str_val = str(router)

    assert "orders.created" in str_val, \
        "str should contain registered topic 'orders.created'"
    assert "orders.deleted" in str_val, \
        "str should contain registered topic 'orders.deleted'"
    assert "2" in str_val, \
        "str should indicate 2 handlers"
    return


def test_str_with_non_topic_handlers():
    """
        Verify __str__ works when handlers are registered by pattern
        and filter (no topics).
    """
    router = MessageRouter()
    router.register_by_pattern(MessagePattern.REQUEST, lambda msg: None)
    router.register_by_filter(lambda msg: True, lambda msg: None)

    str_val = str(router)

    assert "2" in str_val, \
        "str should indicate 2 handlers"
    assert "no topics" in str_val, \
        "str should indicate no topics when only pattern/filter handlers"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
