"""
    Enumeration defining the strategy for trimming context to fit
    within token limits.

    Provides FIFO, RELEVANCE, and SUMMARIZE strategy values for
    controlling how the ContextWindow manages content when the
    token limit is exceeded.
"""

import enum

from automojo.agentkit.errors import SemanticError


class ContextWindowStrategy(enum.Enum):
    """
        Enumeration defining the strategy for trimming context
        to fit within token limits.

        FIFO — remove oldest non-system messages first.
        RELEVANCE — remove least relevant memory entries first.
        SUMMARIZE — summarize older messages to reduce token count.
    """

    FIFO = "FIFO"
    RELEVANCE = "RELEVANCE"
    SUMMARIZE = "SUMMARIZE"

    @classmethod
    def from_string(cls, value: str) -> "ContextWindowStrategy":
        """
            Returns the ContextWindowStrategy member matching the given string value.

            :param value: A string value to match against ContextWindowStrategy members.

            :returns: The matching ContextWindowStrategy member.
            :raises: SemanticError if the value does not match any member.
        """
        upper_value = value.upper().strip()
        for member in cls:
            if member.value == upper_value:
                rtnval = member
                return rtnval

        valid_values = [m.value for m in cls]
        errmsg = "Invalid ContextWindowStrategy value {!r}. Valid values are: {}".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)

    def __repr__(self) -> str:
        rtnval = "{}({!r})".format(self.__class__.__name__, self.value)
        return rtnval

    def __str__(self) -> str:
        rtnval = self.value
        return rtnval
