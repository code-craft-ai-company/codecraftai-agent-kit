"""
    Defines the ConfigurationLayerSource enum representing the origin
    of a ConfigurationLayer in the codecraftai-agent-kit framework.
"""

import enum

from ccai.agentkit.errors import SemanticError


class ConfigurationLayerSource(enum.Enum):
    """
        Enumeration defining the origin of a ConfigurationLayer.

        Configuration layers are classified by their source to support
        hierarchical merging and precedence management.
    """

    DEFAULTS = "DEFAULTS"
    FILE = "FILE"
    ENVIRONMENT = "ENVIRONMENT"
    RUNTIME = "RUNTIME"
    OVERRIDE = "OVERRIDE"

    @classmethod
    def from_string(cls, value: str) -> "ConfigurationLayerSource":
        """
            Returns the ConfigurationLayerSource member matching the given string.

            :param value: The string value to match.

            :returns: The matching ConfigurationLayerSource member.

            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = ", ".join(sorted(member.value for member in cls))
        errmsg = "Invalid ConfigurationLayerSource value '{}'. Valid values: {}".format(
            value, valid_values
        )
        raise SemanticError(errmsg)
