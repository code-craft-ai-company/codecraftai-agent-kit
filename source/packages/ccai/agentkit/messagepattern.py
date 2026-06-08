"""
    Defines the MessagePattern enum representing the communication patterns
    for messages in the Communication & Messaging feature.

    .. module:: ccai.agentkit.messagepattern
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Enumeration of message communication patterns.
"""

import enum

from ccai.agentkit.errors import SemanticError


class MessagePattern(enum.Enum):
    """
        Enumeration of message communication patterns.

        REQUEST: Expects a correlated response from the recipient.
        RESPONSE: Reply to a previously received request.
        FIRE_AND_FORGET: No response expected from the recipient.
        EVENT: Pub/sub broadcast to all topic subscribers.
    """

    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"
    FIRE_AND_FORGET = "FIRE_AND_FORGET"
    EVENT = "EVENT"

    @classmethod
    def from_string(cls, value: str) -> "MessagePattern":
        """
            Returns the MessagePattern member matching the given string value.

            :param value: The string value to match.

            :returns: The matching MessagePattern member.
            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = [m.value for m in cls]
        errmsg = "Invalid MessagePattern value '{}'. Valid values are: {}.".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)
