"""
    Defines the WorkflowEdge class representing an immutable directed
    connection between two WorkflowStep nodes in a WorkflowDefinition.

    A WorkflowEdge carries a source step identifier, a target step identifier,
    an optional condition expression string for conditional branching, and an
    optional priority integer for ordering when multiple edges leave a step.
"""

from typing import Optional


class WorkflowEdge:
    """
        Immutable directed connection between two WorkflowStep nodes
        in a WorkflowDefinition.

        A WorkflowEdge connects a source step to a target step. When a
        condition expression is provided, the edge is only traversed if
        the condition evaluates to True against the WorkflowContext. When
        no condition is provided, the edge is unconditional and always
        traversed. The priority integer controls evaluation order when
        multiple conditional edges leave the same step; lower values
        are evaluated first.

        :param source_step_id: The identifier of the step where the edge originates.
        :param target_step_id: The identifier of the step where the edge terminates.
        :param condition: An optional condition expression string evaluated
            against the WorkflowContext to determine traversal.
        :param priority: An optional integer controlling evaluation order
            among sibling edges. Lower values are evaluated first. Defaults to 0.
    """

    def __init__(self, source_step_id: str, target_step_id: str,
                 condition: Optional[str] = None, priority: int = 0) -> None:
        self._source_step_id = source_step_id
        self._target_step_id = target_step_id
        self._condition = condition
        self._priority = priority
        return

    @property
    def source_step_id(self) -> str:
        """
            The identifier of the step where the edge originates.

            :returns: The source step identifier string.
        """
        return self._source_step_id

    @property
    def target_step_id(self) -> str:
        """
            The identifier of the step where the edge terminates.

            :returns: The target step identifier string.
        """
        return self._target_step_id

    @property
    def condition(self) -> Optional[str]:
        """
            The optional condition expression string for this edge.

            When None, the edge is unconditional and always traversed.

            :returns: The condition expression string or None.
        """
        return self._condition

    @property
    def priority(self) -> int:
        """
            The priority integer controlling evaluation order among
            sibling edges originating from the same step.

            Lower values are evaluated first.

            :returns: The priority integer.
        """
        return self._priority

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the edge fields.

            :returns: A dictionary containing source_step_id, target_step_id,
                condition, and priority.
        """
        rtnval = {
            "source_step_id": self._source_step_id,
            "target_step_id": self._target_step_id,
            "condition": self._condition,
            "priority": self._priority
        }
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            source step identifier, target step identifier, and whether a
            condition is present.

            :returns: A repr string for debugging.
        """
        has_condition = self._condition is not None
        repr_str = "{}(source_step_id={!r}, target_step_id={!r}, has_condition={})".format(
            self.__class__.__name__, self._source_step_id, self._target_step_id, has_condition
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the source step,
            target step, and condition expression.

            :returns: A human-readable string describing the edge.
        """
        if self._condition is not None:
            str_val = "Edge: {} -> {} [condition: {}, priority: {}]".format(
                self._source_step_id, self._target_step_id,
                self._condition, self._priority
            )
        else:
            str_val = "Edge: {} -> {} [unconditional, priority: {}]".format(
                self._source_step_id, self._target_step_id, self._priority
            )
        return str_val
