"""
    Defines the Subscription class representing an immutable agent
    subscription to a topic in the pub/sub messaging system.

    A Subscription contains a unique identifier, the subscriber agent
    identifier, the topic string, a MessageHandler callback, and an
    optional message filter callable. The identifier is auto-generated
    as a UUID when not provided explicitly.

    .. module:: automojo.agentkit.subscription
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable subscription object for pub/sub messaging.

    Requirements: 15.1-15.6, 26.19, 26.20
"""

import uuid

from typing import Callable
from typing import Optional


class Subscription:
    """
        Immutable object representing an agent's subscription to a topic.

        Contains a unique identifier, the subscriber agent identifier,
        the topic string (which may include wildcard patterns), a
        MessageHandler callback, and an optional message filter callable.

        When created without an explicit identifier, a UUID-based
        identifier is generated automatically.

        :param subscriber_agent_id: The identifier of the subscribing agent.
        :param topic: The topic string (supports wildcard patterns).
        :param handler: The MessageHandler callback to invoke on matching messages.
        :param message_filter: Optional filter callable for additional message filtering.
        :param identifier: Optional unique identifier. If not provided, a UUID is generated.
    """

    def __init__(self, subscriber_agent_id: str, topic: str,
                 handler: Callable, message_filter: Optional[Callable] = None,
                 identifier: Optional[str] = None) -> None:

        if identifier is not None:
            self._identifier = identifier
        else:
            self._identifier = str(uuid.uuid4())

        self._subscriber_agent_id = subscriber_agent_id
        self._topic = topic
        self._handler = handler
        self._message_filter = message_filter
        return

    @property
    def identifier(self) -> str:
        """
            The unique identifier of the subscription.

            :returns: The identifier string.
        """
        return self._identifier

    @property
    def subscriber_agent_id(self) -> str:
        """
            The identifier of the subscribing agent.

            :returns: The subscriber agent identifier string.
        """
        return self._subscriber_agent_id

    @property
    def topic(self) -> str:
        """
            The topic string for this subscription.

            :returns: The topic string.
        """
        return self._topic

    @property
    def handler(self) -> Callable:
        """
            The MessageHandler callback for this subscription.

            :returns: The handler callable.
        """
        return self._handler

    @property
    def message_filter(self) -> Optional[Callable]:
        """
            The optional message filter callable for this subscription.

            :returns: The filter callable or None.
        """
        return self._message_filter

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation containing the identifier,
            subscriber agent identifier, and topic string.

            The handler and message filter callables are excluded from
            the dictionary representation as they are not serializable.

            :returns: A dictionary with subscription metadata fields.
        """
        result = {
            "identifier": self._identifier,
            "subscriber_agent_id": self._subscriber_agent_id,
            "topic": self._topic,
        }
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class
            name, identifier, subscriber agent identifier, and topic.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(identifier={!r}, subscriber_agent_id={!r}, topic={!r})".format(
            self.__class__.__name__, self._identifier,
            self._subscriber_agent_id, self._topic
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the subscriber
            agent identifier and topic.

            :returns: A human-readable string describing the subscription.
        """
        str_val = "Subscription: subscriber={}, topic={}".format(
            self._subscriber_agent_id, self._topic
        )
        return str_val
