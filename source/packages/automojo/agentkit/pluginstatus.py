"""
    Defines the PluginStatus enum representing the lifecycle status
    of a plugin in the automojo-agent-kit framework.
"""

import enum

from automojo.agentkit.errors import SemanticError


class PluginStatus(enum.Enum):
    """
        Enumeration defining the lifecycle status of a plugin.

        Plugins transition through these states during their lifecycle:
        DISCOVERED, LOADING, LOADED, ACTIVE, FAILED, and DISABLED.
    """

    DISCOVERED = "DISCOVERED"
    LOADING = "LOADING"
    LOADED = "LOADED"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    DISABLED = "DISABLED"

    @classmethod
    def from_string(cls, value: str) -> "PluginStatus":
        """
            Returns the PluginStatus member matching the given string.

            :param value: The string value to match.

            :returns: The matching PluginStatus member.

            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = ", ".join(sorted(member.value for member in cls))
        errmsg = "Invalid PluginStatus value '{}'. Valid values: {}".format(
            value, valid_values
        )
        raise SemanticError(errmsg)
