"""
    Enumeration defining the visibility scope of a MemoryEntry.

    Provides AGENT, SHARED, and GLOBAL scope values for controlling
    memory entry visibility across agents.
"""

import enum

from ccai.agentkit.errors import SemanticError


class MemoryScope(enum.Enum):
    """
        Enumeration defining the visibility scope of a MemoryEntry.

        AGENT — visible only to the owning agent.
        SHARED — visible to all agents that reference the same MemoryStore instance.
        GLOBAL — visible to all agents in the runtime.
    """

    AGENT = "AGENT"
    SHARED = "SHARED"
    GLOBAL = "GLOBAL"

    @classmethod
    def from_string(cls, value: str) -> "MemoryScope":
        """
            Returns the MemoryScope member matching the given string value.

            :param value: A string value to match against MemoryScope members.

            :returns: The matching MemoryScope member.
            :raises: SemanticError if the value does not match any member.
        """
        upper_value = value.upper().strip()
        for member in cls:
            if member.value == upper_value:
                rtnval = member
                return rtnval

        valid_values = [m.value for m in cls]
        errmsg = "Invalid MemoryScope value {!r}. Valid values are: {}".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)

    def __repr__(self) -> str:
        rtnval = "{}({!r})".format(self.__class__.__name__, self.value)
        return rtnval

    def __str__(self) -> str:
        rtnval = self.value
        return rtnval
