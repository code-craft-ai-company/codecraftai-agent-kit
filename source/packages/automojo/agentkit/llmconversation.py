"""
    Defines the LLMConversation class for managing ordered sequences of
    LLMMessage objects.

    LLMConversation is a mutable collection that supports appending messages,
    truncating to a maximum count while preserving system messages, and
    serialization to and from JSON.
"""

import json

from automojo.agentkit.llmmessage import LLMMessage


class LLMConversation:
    """
        An ordered, mutable sequence of LLMMessage objects representing
        a conversation history.

        Provides methods for appending messages, truncating the conversation
        while preserving system messages, and serializing to and from JSON.

        :param messages: Optional initial list of LLMMessage objects.
    """

    def __init__(self, messages: list = None) -> None:
        self._messages = list(messages) if messages is not None else []
        return

    @property
    def count(self) -> int:
        """
            The number of messages in the conversation.

            :returns: The message count as an integer.
        """
        rtnval = len(self._messages)
        return rtnval

    @property
    def messages(self) -> list:
        """
            Returns a copy of the message list.

            :returns: A list of LLMMessage objects.
        """
        rtnval = list(self._messages)
        return rtnval

    def append(self, message: "LLMMessage") -> None:
        """
            Adds an LLMMessage to the end of the conversation.

            :param message: The LLMMessage to append.
        """
        self._messages.append(message)
        return

    def truncate(self, max_messages: int) -> None:
        """
            Removes the oldest non-system messages to fit within the limit,
            preserving all system messages.

            System messages are always retained. When the total message count
            exceeds max_messages, the oldest non-system messages are removed
            first. If the number of system messages alone exceeds max_messages,
            all non-system messages are removed.

            :param max_messages: The maximum number of messages to retain.
        """
        if len(self._messages) <= max_messages:
            return

        system_messages = [m for m in self._messages if m.role == "system"]
        non_system_messages = [m for m in self._messages if m.role != "system"]

        available_slots = max_messages - len(system_messages)
        if available_slots < 0:
            available_slots = 0

        kept_non_system = non_system_messages[-available_slots:] if available_slots > 0 else []

        self._messages = system_messages + kept_non_system
        return

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the conversation.

            :returns: A dictionary with a messages key containing a list of
                      message dictionaries.
        """
        rtnval = {
            "messages": [m.as_dict() for m in self._messages]
        }
        return rtnval

    def to_json(self) -> str:
        """
            Returns a JSON string representation of the conversation.

            :returns: A JSON string.
        """
        rtnval = json.dumps(self.as_dict())
        return rtnval

    @classmethod
    def from_json(cls, json_str: str) -> "LLMConversation":
        """
            Deserializes a JSON string into an LLMConversation.

            :param json_str: A JSON string.

            :returns: An LLMConversation instance.
        """
        data = json.loads(json_str)
        messages = [LLMMessage.from_dict(m) for m in data["messages"]]
        rtnval = cls(messages=messages)
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name
            and message count.

            :returns: A repr string for debugging.
        """
        rtnval = "{}(count={})".format(self.__class__.__name__, len(self._messages))
        return rtnval

    def __str__(self) -> str:
        """
            Returns a human-readable summary listing the message roles in order.

            :returns: A human-readable string.
        """
        roles = [m.role for m in self._messages]
        rtnval = "LLMConversation: [{}]".format(", ".join(roles))
        return rtnval

    def __eq__(self, other) -> bool:
        """
            Checks equality based on the message list.

            :param other: The object to compare against.

            :returns: True if all messages are equal, False otherwise.
        """
        if not isinstance(other, LLMConversation):
            return False

        rtnval = self._messages == other._messages
        return rtnval
