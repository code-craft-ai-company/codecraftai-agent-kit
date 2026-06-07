"""
    Unit tests for the ccai.agentkit.subscription and
    ccai.agentkit.pubsubbroker modules.

    Tests Subscription construction, auto-generated ID, property access,
    as_dict, __repr__, __str__. Tests PubSubBroker subscribe, unsubscribe,
    publish, wildcard matching, handler exception handling, active_topics,
    get_subscriber_count, get_subscriber_ids, __repr__, __str__.

    Requirements: 14.1-14.12, 15.1-15.6
"""

import logging
import uuid

from ccai.agentkit.agentaddress import AgentAddress
from ccai.agentkit.message import Message
from ccai.agentkit.messagepattern import MessagePattern
from ccai.agentkit.pubsubbroker import PubSubBroker
from ccai.agentkit.subscription import Subscription


# =========================================================================
# Test helpers
# =========================================================================

def _create_event_message(payload="test-payload", identifier=None):
    """
        Creates a Message with MessagePattern.EVENT for testing.
    """
    sender = AgentAddress(
        agent_identifier="publisher-agent",
        transport_name="http",
    )
    recipient = AgentAddress(
        agent_identifier="broadcast",
        transport_name="http",
    )

    message = Message(
        sender=sender,
        recipient=recipient,
        payload=payload,
        pattern=MessagePattern.EVENT,
        identifier=identifier,
    )
    return message


# =========================================================================
# Subscription construction and auto-generated ID (Requirement 15.1, 15.2)
# =========================================================================


def test_subscription_auto_generates_uuid_identifier():
    """
        Verify Subscription generates a UUID-based identifier when none
        is provided.
    """
    handler = lambda msg: None

    sub = Subscription(
        subscriber_agent_id="agent-1",
        topic="events.user.created",
        handler=handler,
    )

    assert isinstance(sub.identifier, str), \
        "Identifier should be a string"
    # Validate it is a valid UUID
    parsed = uuid.UUID(sub.identifier)
    assert str(parsed) == sub.identifier, \
        "Identifier should be a valid UUID string"
    return


def test_subscription_uses_explicit_identifier():
    """
        Verify Subscription uses the provided identifier when given.
    """
    handler = lambda msg: None

    sub = Subscription(
        subscriber_agent_id="agent-1",
        topic="events.user.created",
        handler=handler,
        identifier="custom-id-123",
    )

    assert sub.identifier == "custom-id-123", \
        "Identifier should match the explicitly provided value"
    return


def test_subscription_unique_identifiers():
    """
        Verify two Subscriptions created without explicit identifiers
        have different auto-generated identifiers.
    """
    handler = lambda msg: None

    sub_a = Subscription(subscriber_agent_id="agent-1", topic="t1", handler=handler)
    sub_b = Subscription(subscriber_agent_id="agent-2", topic="t2", handler=handler)

    assert sub_a.identifier != sub_b.identifier, \
        "Auto-generated identifiers should be unique"
    return


# =========================================================================
# Subscription property access (Requirement 15.3)
# =========================================================================

def test_subscription_property_access():
    """
        Verify all read-only properties return the correct values.
    """
    handler = lambda msg: None
    filter_fn = lambda msg: True

    sub = Subscription(
        subscriber_agent_id="agent-42",
        topic="orders.shipped",
        handler=handler,
        message_filter=filter_fn,
        identifier="sub-id-001",
    )

    assert sub.identifier == "sub-id-001", \
        "identifier property mismatch"
    assert sub.subscriber_agent_id == "agent-42", \
        "subscriber_agent_id property mismatch"
    assert sub.topic == "orders.shipped", \
        "topic property mismatch"
    assert sub.handler is handler, \
        "handler property should reference the original callable"
    assert sub.message_filter is filter_fn, \
        "message_filter property should reference the original callable"
    return


def test_subscription_message_filter_defaults_to_none():
    """
        Verify message_filter defaults to None when not provided.
    """
    handler = lambda msg: None

    sub = Subscription(
        subscriber_agent_id="agent-1",
        topic="events.test",
        handler=handler,
    )

    assert sub.message_filter is None, \
        "message_filter should default to None"
    return


# =========================================================================
# Subscription as_dict (Requirement 15.4)
# =========================================================================

def test_subscription_as_dict():
    """
        Verify as_dict returns a dictionary with identifier,
        subscriber_agent_id, and topic. Handler and filter are excluded.
    """
    handler = lambda msg: None

    sub = Subscription(
        subscriber_agent_id="agent-7",
        topic="metrics.cpu",
        handler=handler,
        identifier="dict-test-id",
    )

    result = sub.as_dict()

    assert isinstance(result, dict), \
        "as_dict should return a dictionary"
    assert result["identifier"] == "dict-test-id", \
        "identifier key mismatch"
    assert result["subscriber_agent_id"] == "agent-7", \
        "subscriber_agent_id key mismatch"
    assert result["topic"] == "metrics.cpu", \
        "topic key mismatch"
    assert "handler" not in result, \
        "handler should not be in the dictionary"
    assert "message_filter" not in result, \
        "message_filter should not be in the dictionary"
    return


# =========================================================================
# Subscription __repr__ (Requirement 15.5)
# =========================================================================

def test_subscription_repr():
    """
        Verify __repr__ includes class name, identifier, subscriber_agent_id,
        and topic.
    """
    handler = lambda msg: None

    sub = Subscription(
        subscriber_agent_id="agent-repr",
        topic="events.repr.test",
        handler=handler,
        identifier="repr-id-001",
    )

    repr_str = repr(sub)

    assert "Subscription" in repr_str, \
        "repr should contain class name"
    assert "repr-id-001" in repr_str, \
        "repr should contain the identifier"
    assert "agent-repr" in repr_str, \
        "repr should contain the subscriber_agent_id"
    assert "events.repr.test" in repr_str, \
        "repr should contain the topic"
    return


# =========================================================================
# Subscription __str__ (Requirement 15.6)
# =========================================================================

def test_subscription_str():
    """
        Verify __str__ returns a human-readable summary including
        subscriber_agent_id and topic.
    """
    handler = lambda msg: None

    sub = Subscription(
        subscriber_agent_id="agent-str",
        topic="events.str.test",
        handler=handler,
    )

    str_val = str(sub)

    assert "agent-str" in str_val, \
        "str should contain the subscriber_agent_id"
    assert "events.str.test" in str_val, \
        "str should contain the topic"
    return


# =========================================================================
# PubSubBroker subscribe (Requirement 14.1)
# =========================================================================

def test_subscribe_returns_subscription():
    """
        Verify subscribe returns a Subscription object with the correct
        topic and subscriber_agent_id.
    """
    broker = PubSubBroker()
    invocations = []

    sub = broker.subscribe(
        topic="events.user.created",
        subscriber_agent_id="agent-sub-1",
        handler=lambda msg: invocations.append(msg),
    )

    assert isinstance(sub, Subscription), \
        "subscribe should return a Subscription instance"
    assert sub.topic == "events.user.created", \
        "Subscription topic should match"
    assert sub.subscriber_agent_id == "agent-sub-1", \
        "Subscription subscriber_agent_id should match"
    return


def test_subscribe_with_message_filter():
    """
        Verify subscribe accepts an optional message_filter.
    """
    broker = PubSubBroker()
    filter_fn = lambda msg: True

    sub = broker.subscribe(
        topic="events.test",
        subscriber_agent_id="agent-filter",
        handler=lambda msg: None,
        message_filter=filter_fn,
    )

    assert sub.message_filter is filter_fn, \
        "Subscription should store the message_filter"
    return


# =========================================================================
# PubSubBroker unsubscribe (Requirement 14.2)
# =========================================================================

def test_unsubscribe_removes_subscription():
    """
        Verify unsubscribe removes the subscription so the handler
        is no longer invoked on publish.
    """
    broker = PubSubBroker()
    invocations = []

    sub = broker.subscribe(
        topic="events.test",
        subscriber_agent_id="agent-unsub",
        handler=lambda msg: invocations.append(msg),
    )

    broker.unsubscribe(sub)

    message = _create_event_message()
    broker.publish("events.test", message)

    assert len(invocations) == 0, \
        "Handler should not be invoked after unsubscribe"
    return


def test_unsubscribe_nonexistent_is_noop():
    """
        Verify unsubscribing a subscription that was already removed
        does not raise an error.
    """
    broker = PubSubBroker()

    sub = broker.subscribe(
        topic="events.test",
        subscriber_agent_id="agent-noop",
        handler=lambda msg: None,
    )

    broker.unsubscribe(sub)
    # Second unsubscribe should be a no-op
    broker.unsubscribe(sub)
    return


def test_unsubscribe_only_removes_target():
    """
        Verify unsubscribe only removes the targeted subscription,
        leaving other subscriptions intact.
    """
    broker = PubSubBroker()
    invocations_a = []
    invocations_b = []

    sub_a = broker.subscribe(
        topic="events.test",
        subscriber_agent_id="agent-a",
        handler=lambda msg: invocations_a.append(msg),
    )
    sub_b = broker.subscribe(
        topic="events.test",
        subscriber_agent_id="agent-b",
        handler=lambda msg: invocations_b.append(msg),
    )

    broker.unsubscribe(sub_a)

    message = _create_event_message()
    broker.publish("events.test", message)

    assert len(invocations_a) == 0, \
        "Removed subscription handler should not be invoked"
    assert len(invocations_b) == 1, \
        "Remaining subscription handler should still be invoked"
    return


# =========================================================================
# PubSubBroker publish (Requirement 14.3, 14.4)
# =========================================================================

def test_publish_delivers_to_matching_subscribers():
    """
        Verify publish delivers the message to all subscribers of the topic.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe(
        topic="events.order.placed",
        subscriber_agent_id="agent-1",
        handler=lambda msg: invocations.append(("agent-1", msg)),
    )
    broker.subscribe(
        topic="events.order.placed",
        subscriber_agent_id="agent-2",
        handler=lambda msg: invocations.append(("agent-2", msg)),
    )

    message = _create_event_message(payload="order-data")
    broker.publish("events.order.placed", message)

    assert len(invocations) == 2, \
        "Both subscribers should receive the message"
    assert invocations[0][0] == "agent-1", \
        "First subscriber should be invoked first"
    assert invocations[1][0] == "agent-2", \
        "Second subscriber should be invoked second"
    assert invocations[0][1] is message, \
        "Handler should receive the published message"
    return


def test_publish_does_not_deliver_to_non_matching_topic():
    """
        Verify publish does not deliver to subscribers of a different topic.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe(
        topic="events.order.placed",
        subscriber_agent_id="agent-1",
        handler=lambda msg: invocations.append(msg),
    )

    message = _create_event_message()
    broker.publish("events.user.created", message)

    assert len(invocations) == 0, \
        "Handler should not be invoked for non-matching topic"
    return


# =========================================================================
# PubSubBroker handler invocation order (Requirement 14.5)
# =========================================================================

def test_publish_invokes_handlers_in_registration_order():
    """
        Verify handlers are invoked in the order subscriptions were registered.
    """
    broker = PubSubBroker()
    order = []

    broker.subscribe("events.test", "agent-1", lambda msg: order.append(1))
    broker.subscribe("events.test", "agent-2", lambda msg: order.append(2))
    broker.subscribe("events.test", "agent-3", lambda msg: order.append(3))

    message = _create_event_message()
    broker.publish("events.test", message)

    assert order == [1, 2, 3], \
        "Handlers should be invoked in registration order"
    return


# =========================================================================
# PubSubBroker handler exception handling (Requirement 14.6)
# =========================================================================

def test_publish_continues_after_handler_exception():
    """
        Verify that if a handler raises an exception, delivery continues
        to remaining subscribers.
    """
    broker = PubSubBroker()
    invocations = []

    def failing_handler(msg):
        raise RuntimeError("handler failure")

    broker.subscribe("events.test", "agent-fail", failing_handler)
    broker.subscribe("events.test", "agent-ok", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.test", message)

    assert len(invocations) == 1, \
        "Second handler should still be invoked after first handler exception"
    assert invocations[0] is message, \
        "Second handler should receive the published message"
    return


def test_publish_logs_handler_exception_at_warning():
    """
        Verify that handler exceptions are logged at WARNING level
        with topic, subscriber agent ID, and message identifier.
    """
    broker = PubSubBroker()
    logger = logging.getLogger("ccai.agentkit.messaging.pubsub")

    log_records = []
    test_handler = logging.Handler()
    test_handler.emit = lambda record: log_records.append(record)
    logger.addHandler(test_handler)
    original_level = logger.level
    logger.setLevel(logging.WARNING)

    try:
        def failing_handler(msg):
            raise ValueError("test error detail")

        broker.subscribe("events.log.test", "agent-log", failing_handler)

        message = _create_event_message(identifier="msg-log-001")
        broker.publish("events.log.test", message)

        warning_records = [r for r in log_records if r.levelno == logging.WARNING]
        assert len(warning_records) >= 1, \
            "At least one WARNING log record should be emitted"

        warning_msg = warning_records[0].getMessage()
        assert "events.log.test" in warning_msg, \
            "Warning log should contain the topic"
        assert "agent-log" in warning_msg, \
            "Warning log should contain the subscriber agent ID"
        assert "msg-log-001" in warning_msg, \
            "Warning log should contain the message identifier"
    finally:
        logger.removeHandler(test_handler)
        logger.setLevel(original_level)

    return


# =========================================================================
# PubSubBroker wildcard matching (Requirement 14.10)
# =========================================================================

def test_wildcard_single_segment_match():
    """
        Verify '*' matches exactly one segment.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.*.created", "agent-wc", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user.created", message)

    assert len(invocations) == 1, \
        "'*' should match exactly one segment"
    return


def test_wildcard_single_segment_no_match_zero_segments():
    """
        Verify '*' does not match zero segments.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.*.created", "agent-wc", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.created", message)

    assert len(invocations) == 0, \
        "'*' should not match zero segments"
    return


def test_wildcard_single_segment_no_match_multiple_segments():
    """
        Verify '*' does not match more than one segment.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.*.created", "agent-wc", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user.admin.created", message)

    assert len(invocations) == 0, \
        "'*' should not match multiple segments"
    return


def test_wildcard_multi_level_match_zero_segments():
    """
        Verify '#' matches zero remaining segments.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.#", "agent-ml", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events", message)

    assert len(invocations) == 1, \
        "'#' should match zero remaining segments"
    return


def test_wildcard_multi_level_match_one_segment():
    """
        Verify '#' matches one remaining segment.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.#", "agent-ml", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user", message)

    assert len(invocations) == 1, \
        "'#' should match one remaining segment"
    return


def test_wildcard_multi_level_match_many_segments():
    """
        Verify '#' matches multiple remaining segments.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.#", "agent-ml", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user.admin.created", message)

    assert len(invocations) == 1, \
        "'#' should match multiple remaining segments"
    return


def test_exact_topic_match():
    """
        Verify exact topic strings match themselves.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.user.created", "agent-exact", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user.created", message)

    assert len(invocations) == 1, \
        "Exact topic should match itself"
    return


def test_exact_topic_no_match():
    """
        Verify exact topic strings do not match different topics.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("events.user.created", "agent-exact", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user.deleted", message)

    assert len(invocations) == 0, \
        "Different exact topic should not match"
    return


def test_wildcard_hash_only_matches_everything():
    """
        Verify '#' alone matches any topic.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe("#", "agent-all", lambda msg: invocations.append(msg))

    message = _create_event_message()
    broker.publish("events.user.created", message)

    assert len(invocations) == 1, \
        "'#' alone should match any topic"
    return


# =========================================================================
# PubSubBroker message_filter in publish (Requirement 14.4)
# =========================================================================

def test_publish_respects_message_filter():
    """
        Verify publish skips subscribers whose message_filter returns False.
    """
    broker = PubSubBroker()
    invocations = []

    broker.subscribe(
        topic="events.test",
        subscriber_agent_id="agent-filtered",
        handler=lambda msg: invocations.append(msg),
        message_filter=lambda msg: msg.payload == "accepted",
    )

    rejected_msg = _create_event_message(payload="rejected")
    broker.publish("events.test", rejected_msg)

    assert len(invocations) == 0, \
        "Handler should not be invoked when filter returns False"

    accepted_msg = _create_event_message(payload="accepted")
    broker.publish("events.test", accepted_msg)

    assert len(invocations) == 1, \
        "Handler should be invoked when filter returns True"
    return


# =========================================================================
# PubSubBroker active_topics (Requirement 14.7)
# =========================================================================

def test_active_topics_empty():
    """
        Verify active_topics returns an empty list when no subscriptions exist.
    """
    broker = PubSubBroker()

    assert broker.active_topics == [], \
        "active_topics should be empty with no subscriptions"
    return


def test_active_topics_returns_unique_topics():
    """
        Verify active_topics returns unique topic strings.
    """
    broker = PubSubBroker()

    broker.subscribe("events.a", "agent-1", lambda msg: None)
    broker.subscribe("events.b", "agent-2", lambda msg: None)
    broker.subscribe("events.a", "agent-3", lambda msg: None)

    topics = broker.active_topics

    assert len(topics) == 2, \
        "active_topics should return unique topics"
    assert "events.a" in topics, \
        "active_topics should contain 'events.a'"
    assert "events.b" in topics, \
        "active_topics should contain 'events.b'"
    return


# =========================================================================
# PubSubBroker get_subscriber_count (Requirement 14.8)
# =========================================================================

def test_get_subscriber_count_zero():
    """
        Verify get_subscriber_count returns 0 for a topic with no subscribers.
    """
    broker = PubSubBroker()

    count = broker.get_subscriber_count("events.nonexistent")

    assert count == 0, \
        "Subscriber count should be 0 for nonexistent topic"
    return


def test_get_subscriber_count_multiple():
    """
        Verify get_subscriber_count returns the correct count for a topic.
    """
    broker = PubSubBroker()

    broker.subscribe("events.test", "agent-1", lambda msg: None)
    broker.subscribe("events.test", "agent-2", lambda msg: None)
    broker.subscribe("events.other", "agent-3", lambda msg: None)

    count = broker.get_subscriber_count("events.test")

    assert count == 2, \
        "Subscriber count should be 2 for 'events.test'"
    return


# =========================================================================
# PubSubBroker get_subscriber_ids (Requirement 14.9)
# =========================================================================

def test_get_subscriber_ids_empty():
    """
        Verify get_subscriber_ids returns an empty list for a topic
        with no subscribers.
    """
    broker = PubSubBroker()

    ids = broker.get_subscriber_ids("events.nonexistent")

    assert ids == [], \
        "Subscriber IDs should be empty for nonexistent topic"
    return


def test_get_subscriber_ids_returns_correct_ids():
    """
        Verify get_subscriber_ids returns the subscriber agent identifiers
        for the given topic.
    """
    broker = PubSubBroker()

    broker.subscribe("events.test", "agent-alpha", lambda msg: None)
    broker.subscribe("events.test", "agent-beta", lambda msg: None)
    broker.subscribe("events.other", "agent-gamma", lambda msg: None)

    ids = broker.get_subscriber_ids("events.test")

    assert len(ids) == 2, \
        "Should return 2 subscriber IDs"
    assert "agent-alpha" in ids, \
        "Should contain 'agent-alpha'"
    assert "agent-beta" in ids, \
        "Should contain 'agent-beta'"
    assert "agent-gamma" not in ids, \
        "Should not contain 'agent-gamma' (different topic)"
    return


# =========================================================================
# PubSubBroker __repr__ (Requirement 14.11, 26.15)
# =========================================================================

def test_pubsubbroker_repr_empty():
    """
        Verify __repr__ includes class name and active topic count
        when broker is empty.
    """
    broker = PubSubBroker()

    repr_str = repr(broker)

    assert "PubSubBroker" in repr_str, \
        "repr should contain class name"
    assert "0" in repr_str, \
        "repr should indicate 0 active topics"
    return


def test_pubsubbroker_repr_with_topics():
    """
        Verify __repr__ includes the correct active topic count.
    """
    broker = PubSubBroker()

    broker.subscribe("events.a", "agent-1", lambda msg: None)
    broker.subscribe("events.b", "agent-2", lambda msg: None)

    repr_str = repr(broker)

    assert "PubSubBroker" in repr_str, \
        "repr should contain class name"
    assert "2" in repr_str, \
        "repr should indicate 2 active topics"
    return


# =========================================================================
# PubSubBroker __str__ (Requirement 14.12, 26.16)
# =========================================================================

def test_pubsubbroker_str_empty():
    """
        Verify __str__ returns a human-readable summary with 0 topics
        and 0 subscriptions.
    """
    broker = PubSubBroker()

    str_val = str(broker)

    assert "0" in str_val, \
        "str should indicate 0 topics/subscriptions"
    assert "PubSubBroker" in str_val, \
        "str should contain class name"
    return


def test_pubsubbroker_str_with_subscriptions():
    """
        Verify __str__ includes the count of active topics and total
        subscription count.
    """
    broker = PubSubBroker()

    broker.subscribe("events.a", "agent-1", lambda msg: None)
    broker.subscribe("events.a", "agent-2", lambda msg: None)
    broker.subscribe("events.b", "agent-3", lambda msg: None)

    str_val = str(broker)

    assert "2" in str_val, \
        "str should indicate 2 active topics"
    assert "3" in str_val, \
        "str should indicate 3 subscriptions"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
