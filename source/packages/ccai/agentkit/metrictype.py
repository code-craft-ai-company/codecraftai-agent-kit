"""
    Defines the MetricType enumeration for classifying metrics as
    COUNTER, GAUGE, or HISTOGRAM.

    MetricType provides a from_string class method for converting
    string values to enum members, raising SemanticError for invalid
    values.
"""

import enum

from ccai.agentkit.errors import SemanticError


class MetricType(enum.Enum):
    """
        Enumeration defining the type of a metric.

        COUNTER represents a monotonically increasing value.
        GAUGE represents a value that can increase or decrease.
        HISTOGRAM represents a distribution of values.
    """

    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"

    @classmethod
    def from_string(cls, value: str) -> "MetricType":
        """
            Converts a string value to the corresponding MetricType member.

            The comparison is case-sensitive against the enum value strings.

            :param value: A string representing the metric type.

            :returns: The corresponding MetricType member.

            :raises SemanticError: If the value does not match any valid
                metric type.
        """
        for member in cls:
            if member.value == value:
                return member

        valid_values = [m.value for m in cls]
        raise SemanticError(
            "Invalid metric type value: {!r}. Valid values are: {}".format(
                value, valid_values
            )
        )
