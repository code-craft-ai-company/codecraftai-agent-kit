"""
    Exception classes for the Workflow & Orchestration feature.

    Provides WorkflowDefinitionError for structurally invalid workflow definitions,
    WorkflowExecutionError for runtime step execution failures,
    WorkflowCheckpointError for checkpoint save and restore failures,
    and ApprovalTimeoutError for approval request timeout conditions.
"""

from typing import Optional

from automojo.agentkit.errors import AgentKitError


class WorkflowDefinitionError(AgentKitError):
    """
        Raised when a WorkflowDefinition is structurally invalid.

        Structural problems include cycles in the DAG, a missing start step,
        unreachable steps, and invalid edge references.

        :param workflow_name: The name of the workflow that failed validation.
        :param detail: A descriptive string identifying the structural problem.
    """

    def __init__(self, workflow_name: str, detail: str) -> None:
        self._workflow_name = workflow_name
        self._detail = detail

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def workflow_name(self) -> str:
        """
            The name of the workflow that failed validation.

            :returns: The workflow name string.
        """
        return self._workflow_name

    @property
    def detail(self) -> str:
        """
            A descriptive string identifying the structural problem.

            :returns: The detail string.
        """
        return self._detail

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the workflow name and detail.

            :returns: A formatted error message string.
        """
        errmsg = "Workflow definition '{}' is invalid: {}".format(
            self._workflow_name, self._detail
        )
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            workflow name, and detail.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(workflow_name={!r}, detail={!r})".format(
            self.__class__.__name__, self._workflow_name, self._detail
        )
        return repr_str


class WorkflowExecutionError(AgentKitError):
    """
        Raised when a workflow execution fails during step execution.

        :param workflow_name: The name of the workflow that failed.
        :param step_id: The identifier of the step where the error occurred.
        :param cause: An optional exception that caused the failure.
    """

    def __init__(self, workflow_name: str, step_id: str, cause: Optional[Exception] = None) -> None:
        self._workflow_name = workflow_name
        self._step_id = step_id
        self._cause = cause

        errmsg = self._format_message()
        super().__init__(errmsg, cause=cause)

        return

    @property
    def workflow_name(self) -> str:
        """
            The name of the workflow that failed.

            :returns: The workflow name string.
        """
        return self._workflow_name

    @property
    def step_id(self) -> str:
        """
            The identifier of the step where the error occurred.

            :returns: The step identifier string.
        """
        return self._step_id

    @property
    def cause(self) -> Optional[Exception]:
        """
            The optional exception that caused the failure.

            :returns: The cause exception or None.
        """
        return self._cause

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the workflow name,
            step identifier, and optional cause.

            :returns: A formatted error message string.
        """
        errmsg = "Workflow '{}' execution failed at step '{}'".format(
            self._workflow_name, self._step_id
        )

        if self._cause is not None:
            errmsg = "{}: {}".format(errmsg, self._cause)

        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            workflow name, step identifier, and cause.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(workflow_name={!r}, step_id={!r}, cause={!r})".format(
            self.__class__.__name__, self._workflow_name, self._step_id, self._cause
        )
        return repr_str


class WorkflowCheckpointError(AgentKitError):
    """
        Raised when a checkpoint save or restore operation fails.

        :param execution_id: The workflow execution identifier.
        :param operation: The operation that failed (e.g. 'save' or 'load').
        :param cause: An optional exception that caused the failure.
    """

    def __init__(self, execution_id: str, operation: str, cause: Optional[Exception] = None) -> None:
        self._execution_id = execution_id
        self._operation = operation
        self._cause = cause

        errmsg = self._format_message()
        super().__init__(errmsg, cause=cause)

        return

    @property
    def execution_id(self) -> str:
        """
            The workflow execution identifier.

            :returns: The execution identifier string.
        """
        return self._execution_id

    @property
    def operation(self) -> str:
        """
            The checkpoint operation that failed.

            :returns: The operation string (e.g. 'save' or 'load').
        """
        return self._operation

    @property
    def cause(self) -> Optional[Exception]:
        """
            The optional exception that caused the failure.

            :returns: The cause exception or None.
        """
        return self._cause

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the execution identifier,
            operation, and optional cause.

            :returns: A formatted error message string.
        """
        errmsg = "Checkpoint {} failed for execution '{}'".format(
            self._operation, self._execution_id
        )

        if self._cause is not None:
            errmsg = "{}: {}".format(errmsg, self._cause)

        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            execution identifier, operation, and cause.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(execution_id={!r}, operation={!r}, cause={!r})".format(
            self.__class__.__name__, self._execution_id, self._operation, self._cause
        )
        return repr_str


class ApprovalTimeoutError(AgentKitError):
    """
        Raised when an ApprovalRequest exceeds the configured timeout duration.

        :param request_id: The approval request identifier.
        :param step_id: The step identifier where the timeout occurred.
        :param timeout: The timeout duration in seconds.
    """

    def __init__(self, request_id: str, step_id: str, timeout: float) -> None:
        self._request_id = request_id
        self._step_id = step_id
        self._timeout = timeout

        errmsg = self._format_message()
        super().__init__(errmsg)

        return

    @property
    def request_id(self) -> str:
        """
            The approval request identifier.

            :returns: The request identifier string.
        """
        return self._request_id

    @property
    def step_id(self) -> str:
        """
            The step identifier where the timeout occurred.

            :returns: The step identifier string.
        """
        return self._step_id

    @property
    def timeout(self) -> float:
        """
            The timeout duration in seconds.

            :returns: The timeout value as a float.
        """
        return self._timeout

    def _format_message(self) -> str:
        """
            Builds a descriptive error message from the request identifier,
            step identifier, and timeout duration.

            :returns: A formatted error message string.
        """
        errmsg = "Approval request '{}' for step '{}' timed out after {} seconds".format(
            self._request_id, self._step_id, self._timeout
        )
        return errmsg

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name,
            request identifier, step identifier, and timeout.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(request_id={!r}, step_id={!r}, timeout={!r})".format(
            self.__class__.__name__, self._request_id, self._step_id, self._timeout
        )
        return repr_str
