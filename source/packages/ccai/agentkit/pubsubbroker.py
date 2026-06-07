"""
    Defines the PubSubBroker class for managing topic-based publish/subscribe
    messaging with wildcard support.

    PubSubBroker maintains a list of Subscription objects and routes
    published messages to all subscribers whose topic pattern matches
    the publish topic. Wildcard topic matching follows MQTT/AMQP
    conventions: '*' matches exactly one segment, '#' matches zero or
    more segments, and '.' is the segment separator.

    Subscriber handlers are invoked in registration order. If a handler
    raises an exception, the exception is logged at WARNING level and
    delivery continues to remaining subscribers.

    .. module:: ccai.agentkit.pubsubbroker
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Topic-based pub/sub messaging with wildcard support.

    Requirements: 14.1-14.12, 26.15, 26.16
"""

import logging

from typing import Callable
from typing import List
from typing import Optional

from ccai.agentkit.message import Message
from ccai.agentkit.subscription import Subscription


SINGLE_LEVEL_WILDCARD = "*"
MULTI_LEVEL_WILDCARD = "#"
TOPIC_SEPARATOR = "."


class PubSubBroker:
    """
        Manages topic-based publish/subscribe messaging with wildcard support.

        Maintains an ordered list of Subscription objects. When a message
        is published to a topic, the broker invokes the handler of each
        subscription whose topic pattern matches the publish topic, in
        registration order.

        Wildcard topic matching rules:
        - '.' is the segment separator
        - '*' matches exactly one segment
        - '#' matches zero or more segments

        If a subscriber handler raises an exception during invocation,
        the exception is logged at WARNING level and delivery continues
        to the remaining subscribers.
    """

    def __init__(self) -> None:
        self._subscriptions: List[Subscription] = []
        self._logger = logging.getLogger("ccai.agentkit.messaging.pubsub")
        return

    def subscribe(self, topic: str, subscriber_agent_id: str,
                  handler: Callable, message_filter: Optional[Callable] = None) -> Subscription:
        """
            Creates a subscription for a topic.

            Constructs a Subscription object and appends it to the
            internal subscription list. Logs the subscription creation
            at INFO level.

            :param topic: The topic string (supports wildcard patterns).
            :param subscriber_agent_id: The subscriber agent identifier.
            :param handler: The MessageHandler callback.
            :param message_filter: Optional filter callable for additional
                message filtering.

            :returns: A Subscription object.
        """
        subscription = Subscription(
            subscriber_agent_id=subscriber_agent_id,
            topic=topic,
            handler=handler,
            message_filter=message_filter,
        )

        self._subscriptions.append(subscription)

        self._logger.info(
            "Subscription created: topic='%s', subscriber='%s'",
            topic, subscriber_agent_id
        )

        return subscription

    def unsubscribe(self, subscription: Subscription) -> None:
        """
            Removes a subscription.

            Removes the subscription from the internal list by matching
            the subscription identifier. If the subscription is not found,
            the operation is a no-op. Logs the removal at INFO level.

            :param subscription: The Subscription to remove.
        """
        updated_subscriptions = []

        for existing in self._subscriptions:
            is_target = existing.identifier == subscription.identifier

            if is_target is not True:
                updated_subscriptions.append(existing)

        self._subscriptions = updated_subscriptions

        self._logger.info(
            "Subscription removed: topic='%s', subscriber='%s'",
            subscription.topic, subscription.subscriber_agent_id
        )

        return

    def publish(self, topic: str, message: Message) -> None:
        """
            Publishes a message to all subscribers whose topic pattern matches.

            Iterates through all subscriptions in registration order and
            invokes the handler of each subscription whose topic pattern
            matches the publish topic. If a handler raises an exception,
            the exception is logged at WARNING level and delivery continues
            to the remaining subscribers.

            :param topic: The topic string.
            :param message: The Message to publish.
        """
        matched_count = 0

        for subscription in self._subscriptions:
            is_match = self.topic_matches(subscription.topic, topic)

            if is_match is True:
                if subscription.message_filter is not None:
                    try:
                        filter_result = subscription.message_filter(message)
                    except Exception:
                        filter_result = False

                    if filter_result is not True:
                        continue

                matched_count = matched_count + 1
                handler = subscription.handler

                try:
                    handler(message)
                except Exception as exc:
                    self._logger.warning(
                        "Handler exception: topic='%s', subscriber='%s', "
                        "message='%s': %s",
                        topic, subscription.subscriber_agent_id,
                        message.identifier, exc
                    )

        self._logger.info(
            "Message published: topic='%s', message='%s', subscriber_count=%d",
            topic, message.identifier, matched_count
        )

        return

    def topic_matches(self, subscription_topic: str, publish_topic: str) -> bool:
        """
            Checks if a subscription topic pattern matches a publish topic.

            Supports wildcard matching following MQTT/AMQP conventions:
            - '.' is the segment separator
            - '*' matches exactly one segment
            - '#' matches zero or more segments

            :param subscription_topic: The subscription topic pattern.
            :param publish_topic: The actual publish topic.

            :returns: True if the pattern matches, False otherwise.
        """
        sub_segments = subscription_topic.split(TOPIC_SEPARATOR)
        pub_segments = publish_topic.split(TOPIC_SEPARATOR)

        return self._match_segments(sub_segments, 0, pub_segments, 0)

    def _match_segments(self, sub_segments: list, sub_index: int,
                        pub_segments: list, pub_index: int) -> bool:
        """
            Recursively matches subscription topic segments against
            publish topic segments with wildcard support.

            :param sub_segments: The subscription topic segments.
            :param sub_index: The current index in subscription segments.
            :param pub_segments: The publish topic segments.
            :param pub_index: The current index in publish segments.

            :returns: True if the segments match, False otherwise.
        """
        sub_len = len(sub_segments)
        pub_len = len(pub_segments)

        while sub_index < sub_len:
            current_sub = sub_segments[sub_index]

            if current_sub == MULTI_LEVEL_WILDCARD:
                # '#' must be the last segment in the subscription pattern
                # It matches zero or more remaining segments
                return True

            if pub_index >= pub_len:
                # No more publish segments to match against
                return False

            if current_sub == SINGLE_LEVEL_WILDCARD:
                # '*' matches exactly one segment
                sub_index = sub_index + 1
                pub_index = pub_index + 1
                continue

            # Exact segment match required
            current_pub = pub_segments[pub_index]
            if current_sub != current_pub:
                return False

            sub_index = sub_index + 1
            pub_index = pub_index + 1

        # All subscription segments consumed; check if all publish segments consumed
        is_complete = pub_index >= pub_len
        return is_complete

    @property
    def active_topics(self) -> list:
        """
            Returns a list of unique topic strings from active subscriptions.

            :returns: A list of unique topic strings.
        """
        topics = []

        for subscription in self._subscriptions:
            topic = subscription.topic
            is_duplicate = topic in topics

            if is_duplicate is not True:
                topics.append(topic)

        return topics

    def get_subscriber_count(self, topic: str) -> int:
        """
            Returns the count of subscribers for an exact topic match.

            :param topic: The topic string to count subscribers for.

            :returns: The count of subscribers with the exact topic.
        """
        count = 0

        for subscription in self._subscriptions:
            if subscription.topic == topic:
                count = count + 1

        return count

    def get_subscriber_ids(self, topic: str) -> list:
        """
            Returns a list of subscriber agent identifiers for an exact
            topic match.

            :param topic: The topic string to get subscriber IDs for.

            :returns: A list of subscriber agent identifier strings.
        """
        subscriber_ids = []

        for subscription in self._subscriptions:
            if subscription.topic == topic:
                subscriber_ids.append(subscription.subscriber_agent_id)

        return subscriber_ids

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name and the count of active topics.

            :returns: A repr string for debugging.
        """
        topic_count = len(self.active_topics)
        repr_str = "{}(active_topics={})".format(
            self.__class__.__name__, topic_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of
            active topics and total subscription count.

            :returns: A human-readable string describing the broker state.
        """
        topic_count = len(self.active_topics)
        subscription_count = len(self._subscriptions)

        str_val = "PubSubBroker: {} active topic(s), {} subscription(s)".format(
            topic_count, subscription_count
        )
        return str_val
