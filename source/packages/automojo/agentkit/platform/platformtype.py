"""
    Defines the PlatformType enumeration representing the supported
    platform types for the cross-platform runtime feature.

    .. module:: automojo.agentkit.platform.platformtype
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Enumeration of supported platform types (AWS, Azure, GCP, Local).
"""

import enum
import os

from automojo.agentkit.errors import SemanticError


class PlatformType(enum.Enum):
    """
        Enumeration of supported platform types.

        Defines the cloud providers and local environment that the
        cross-platform runtime can target.
    """

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    LOCAL = "local"

    @classmethod
    def from_string(cls, value: str) -> "PlatformType":
        """
            Returns the PlatformType member matching the given case-insensitive string.

            :param value: A string representing the platform type.

            :returns: The matching PlatformType member.
            :raises: SemanticError
        """
        normalized = value.strip().lower()
        for member in cls:
            if member.value == normalized:
                rtnval = member
                return rtnval

        valid_values = [m.value for m in cls]
        err_msg_lines = [
            "Invalid platform type value '{}'.".format(value),
            "Valid platform types: {}".format(valid_values)
        ]
        err_msg = os.linesep.join(err_msg_lines)
        raise SemanticError(err_msg)

    def to_string(self) -> str:
        """
            Returns the lowercase string representation of the platform type.

            :returns: The lowercase string value.
        """
        rtnval = self.value
        return rtnval
