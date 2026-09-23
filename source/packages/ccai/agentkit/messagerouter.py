"""
    Defines the MessageRouter class for routing incoming messages to
    registered MessageHandler callbacks based on topic, pattern, or
    custom filter criteria.

    MessageRouter supports three registration modes: by topic string,
    by MessagePattern value, and by custom filter callable. Handlers
    are invoked in registration order. If a handler raises an exception,
    the exception is logged at WARNING and remaining handlers continue
    to be invoked. If no handler matches an incoming message, a
    MessageRoutingError is raised.

    .. module:: ccai.agentkit.messagerouter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Message routing to registered handler callbacks.

    Requirements: 11.1-11.11, 26.13, 26.14
"""

import logging

from typing import Callable
from typing import List

from ccai.agentkit.message import Message
from ccai.agentkit.messagepattern import MessagePattern
from ccai.agentkit.messagingerrors import MessageRoutingError


_MATCH_TYPE_TOPIC = "topic"
_MATCH_TYPE_PATTERN = "pattern"
_MATCH_TYPE_FILTER = "filter"


class MessageRouter:
    """
        Routes incoming messages to registered MessageHandler callbacks
        based on topic, pattern, or custom filter criteria.

        Handlers are registered with one of three matching strategies:
        topic string matching (against message headers), MessagePattern
        matching (against message.pattern), or custom filter callable
        matching. Each registration returns a unique registration
        identifier string that can be used for deregistration.

        When routing a message, all matching handlers are invoked in
        the order they were registered. If a handler raises an exception,
        the exception is logged at WARNING level and the remaining
        handlers continue to be invoked. If no handler matches, a
        MessageRoutingError is raised.
    """

    def __init__(self) -> None:
        self._handlers: List[dict] = []
        self._next_registration_id: int = 0
        self._logger = logging.getLogger("ccai.agentkit.messaging.router")
        return

    def _allocate_registration_id(self) -> str:
        """
            Allocates and returns the next unique registration identifier.

            :returns: A registration identifier string.
        """
        registration_id = "handler-{}".format(self._next_registration_id)
        self._next_registration_id = self._next_registration_id + 1
        return registration_id

    def register_by_topic(self, topic: str, handler: Callable) -> str:
        """
            Registers a handler for a specific topic string.

            The handler will be invoked when a routed message has a
            headers entry with key "topic" matching the registered
            topic string.

            :param topic: The topic string to match.
            :param handler: The MessageHandler callback.

            :returns: A registration identifier string.
        """
        registration_id = self._allocate_registration_id()

        entry = {
            "registration_id": registration_id,
            "match_type": _MATCH_TYPE_TOPIC,
            "match_value": topic,
            "handler": handler,
        }
        self._handlers.append(entry)

        return registration_id

    def register_by_pattern(self, pattern: MessagePattern, handler: Callable) -> str:
        """
            Registers a handler for a specific MessagePattern value.

            The handler will be invoked when a routed message has a
            pattern matching the registered MessagePattern.

            :param pattern: The MessagePattern to match.
            :param handler: The MessageHandler callback.

            :returns: A registration identifier string.
        """
        registration_id = self._allocate_registration_id()

        entry = {
            "registration_id": registration_id,
            "match_type": _MATCH_TYPE_PATTERN,
            "match_value": pattern,
            "handler": handler,
        }
        self._handlers.append(entry)

        return registration_id

    def register_by_filter(self, filter_fn: Callable, handler: Callable) -> str:
        """
            Registers a handler with a custom filter callable.

            The handler will be invoked when the filter callable
            returns True for a routed message.

            :param filter_fn: A callable accepting a Message and returning bool.
            :param handler: The MessageHandler callback.

            :returns: A registration identifier string.
        """
        registration_id = self._allocate_registration_id()

        entry = {
            "registration_id": registration_id,
            "match_type": _MATCH_TYPE_FILTER,
            "match_value": filter_fn,
            "handler": handler,
        }
        self._handlers.append(entry)

        return registration_id

    def deregister(self, registration_id: str) -> None:
        """
            Removes a handler by its registration identifier.

            If the registration identifier is not found, the operation
            is a no-op.

            :param registration_id: The registration identifier returned
                at registration time.
        """
        updated_handlers = []

        for entry in self._handlers:
            entry_id = entry["registration_id"]
            is_target = entry_id == registration_id

            if is_target is not True:
                updated_handlers.append(entry)

        self._handlers = updated_handlers

        return

    def _matches(self, entry: dict, message: Message) -> bool:
        """
            Determines whether a handler entry matches the given message.

            :param entry: The handler registration entry dictionary.
            :param message: The incoming Message.

            :returns: True if the entry matches the message, False otherwise.
        """
        match_type = entry["match_type"]
        match_value = entry["match_value"]

        if match_type == _MATCH_TYPE_TOPIC:
            message_topic = message.headers.get("topic", None)
            is_match = message_topic == match_value
            return is_match

        if match_type == _MATCH_TYPE_PATTERN:
            is_match = message.pattern == match_value
            return is_match

        if match_type == _MATCH_TYPE_FILTER:
            filter_fn = match_value
            is_match = filter_fn(message)
            return is_match

        return False

    def route(self, message: Message) -> None:
        """
            Routes a message to all matching handlers.

            Invokes all registered handlers whose topic, pattern, or
            custom filter matches the incoming message, in registration
            order. If a handler raises an exception, the exception is
            logged at WARNING level and remaining handlers continue to
            be invoked.

            :param message: The incoming Message.

            :raises MessageRoutingError: If no handler matches the message.
        """
        matched_count = 0

        for entry in self._handlers:
            is_match = self._matches(entry, message)

            if is_match is True:
                matched_count = matched_count + 1
                handler = entry["handler"]
                registration_id = entry["registration_id"]

                try:
                    handler(message)
                except Exception as exc:
                    self._logger.warning(
                        "Handler '%s' raised exception while processing "
                        "message '%s': %s",
                        registration_id, message.identifier, exc
                    )

        if matched_count == 0:
            topic = message.headers.get("topic", None)
            pattern_value = message.pattern.value if message.pattern is not None else None

            raise MessageRoutingError(
                message_id=message.identifier,
                target=topic,
                detail="No handler matched message with pattern '{}' and topic '{}'".format(
                    pattern_value, topic
                )
            )

        return

    @property
    def handler_count(self) -> int:
        """
            The number of currently registered handlers.

            :returns: The count of registered handlers.
        """
        rtnval = len(self._handlers)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name and the count of registered handlers.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(handler_count={})".format(
            self.__class__.__name__, self.handler_count
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of
            registered handlers and the list of registered topics.

            :returns: A human-readable string describing the router state.
        """
        topics = []

        for entry in self._handlers:
            match_type = entry["match_type"]

            if match_type == _MATCH_TYPE_TOPIC:
                topic_value = entry["match_value"]
                is_duplicate = topic_value in topics

                if is_duplicate is not True:
                    topics.append(topic_value)

        if len(topics) == 0:
            str_val = "MessageRouter: {} handler(s) registered, no topics".format(
                self.handler_count
            )
        else:
            str_val = "MessageRouter: {} handler(s) registered, topics=[{}]".format(
                self.handler_count, ", ".join(topics)
            )

        return str_val
