"""
    Defines the StepExecutionStatus enum representing the possible
    states of a single step execution in the Workflow & Orchestration feature.
"""

import enum

from ccai.agentkit.errors import SemanticError


class StepExecutionStatus(enum.Enum):
    """
        Enumeration of step execution states.

        PENDING: The step has not yet started execution.
        RUNNING: The step is currently executing.
        COMPLETED: The step has finished successfully.
        FAILED: The step has stopped due to an error.
        SKIPPED: The step was skipped because its condition was not met.
        PENDING_APPROVAL: The step is paused awaiting external approval.
        CANCELLED: The step was cancelled before completion.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    CANCELLED = "CANCELLED"

    @classmethod
    def from_string(cls, value: str) -> "StepExecutionStatus":
        """
            Returns the StepExecutionStatus member matching the given string.

            :param value: The string value to match.

            :returns: The matching StepExecutionStatus member.
            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = [m.value for m in cls]
        errmsg = "Invalid StepExecutionStatus value '{}'. Valid values are: {}.".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)
