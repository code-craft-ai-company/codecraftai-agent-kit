"""
    Defines the ParallelBranch class representing an immutable grouping
    construct that identifies a set of WorkflowStep nodes that can execute
    concurrently, bounded by a fork step and a join step within a
    WorkflowDefinition.

    A ParallelBranch declares the boundaries of parallel execution by
    specifying the fork step identifier where concurrent execution begins
    and the join step identifier where parallel branches converge.
"""


class ParallelBranch:
    """
        Immutable grouping construct identifying a set of steps that can
        execute concurrently, bounded by a fork step and a join step.

        A ParallelBranch makes parallel execution boundaries visible in
        the WorkflowDefinition rather than inferred, improving
        debuggability. The fork step identifier marks where concurrent
        execution begins and the join step identifier marks where all
        parallel branches must converge before execution continues.

        :param fork_step_id: The identifier of the step where parallel
            execution begins.
        :param join_step_id: The identifier of the step where parallel
            branches converge.
    """

    def __init__(self, fork_step_id: str, join_step_id: str) -> None:
        self._fork_step_id = fork_step_id
        self._join_step_id = join_step_id
        return

    @property
    def fork_step_id(self) -> str:
        """
            The identifier of the step where parallel execution begins.

            :returns: The fork step identifier string.
        """
        return self._fork_step_id

    @property
    def join_step_id(self) -> str:
        """
            The identifier of the step where parallel branches converge.

            :returns: The join step identifier string.
        """
        return self._join_step_id

    def as_dict(self) -> dict:
        """
            Returns a dictionary representation of the parallel branch fields.

            :returns: A dictionary containing fork_step_id and join_step_id.
        """
        rtnval = {
            "fork_step_id": self._fork_step_id,
            "join_step_id": self._join_step_id
        }
        return rtnval

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the class name,
            fork step identifier, and join step identifier.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(fork_step_id={!r}, join_step_id={!r})".format(
            self.__class__.__name__, self._fork_step_id, self._join_step_id
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the fork and join
            step identifiers.

            :returns: A human-readable string describing the parallel branch.
        """
        str_val = "ParallelBranch: fork={} -> join={}".format(
            self._fork_step_id, self._join_step_id
        )
        return str_val
