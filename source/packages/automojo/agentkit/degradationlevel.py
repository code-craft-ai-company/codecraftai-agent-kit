"""
    Defines the DegradationLevel enum representing the severity of
    degradation in the Error Handling & Resilience feature.
"""

import enum

from automojo.agentkit.errors import SemanticError


class DegradationLevel(enum.Enum):
    """
        Enumeration defining the severity of degradation.

        NORMAL: All dependencies available.
        DEGRADED: Some dependencies unavailable, fallback behavior active.
        CRITICAL: Essential dependencies unavailable, minimal operation only.
    """

    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_string(cls, value: str) -> "DegradationLevel":
        """
            Returns the DegradationLevel member matching the given string.

            :param value: The string value to match.

            :returns: The matching DegradationLevel member.
            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = [m.value for m in cls]
        errmsg = "Invalid DegradationLevel value '{}'. Valid values are: {}.".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)
