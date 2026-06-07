"""
    Defines the WorkflowExecutionStatus enum representing the possible
    states of a workflow execution in the Workflow & Orchestration feature.
"""

import enum

from ccai.agentkit.errors import SemanticError


class WorkflowExecutionStatus(enum.Enum):
    """
        Enumeration of workflow execution states.

        RUNNING: The workflow is currently executing steps.
        COMPLETED: The workflow has finished all steps successfully.
        FAILED: The workflow has stopped due to a step failure.
        PAUSED: The workflow is paused, typically awaiting approval.
        CANCELLED: The workflow has been cancelled before completion.
    """

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"

    @classmethod
    def from_string(cls, value: str) -> "WorkflowExecutionStatus":
        """
            Returns the WorkflowExecutionStatus member matching the given string.

            :param value: The string value to match.

            :returns: The matching WorkflowExecutionStatus member.
            :raises SemanticError: If the value does not match any member.
        """
        upper_value = value.upper()

        for member in cls:
            if member.value == upper_value:
                return member

        valid_values = [m.value for m in cls]
        errmsg = "Invalid WorkflowExecutionStatus value '{}'. Valid values are: {}.".format(
            value, ", ".join(valid_values)
        )
        raise SemanticError(errmsg)
