"""
    Defines the ApprovalStep class, a concrete WorkflowStep that
    creates an ApprovalRequest via the Agent's ApprovalGate and
    pauses workflow execution until the approval is resolved.

    ApprovalStep retrieves the ApprovalGate from the executing
    Agent, creates a pending ApprovalRequest with the step's
    description, and inspects the request status after handler
    invocation. If the request is approved, a StepResult with
    COMPLETED status and the approval metadata is returned. If
    the request is rejected, a StepResult with FAILED status and
    the rejection reason is returned. If the request remains
    pending and a timeout is configured, an ApprovalTimeoutError
    is raised. If the request remains pending with no timeout, a
    StepResult with PENDING_APPROVAL status is returned.

    .. module:: ccai.agentkit.steps.approvalstep
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Built-in workflow step for human-in-the-loop approval gates.
"""

import logging
import time

from typing import Optional

from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowerrors import ApprovalTimeoutError
from ccai.agentkit.workflowstep import WorkflowStep


class ApprovalStep(WorkflowStep):
    """
        Creates an ApprovalRequest and pauses workflow execution
        until the approval is resolved.

        ApprovalStep is a concrete WorkflowStep subclass that
        integrates with the ApprovalGate system. At execution
        time, it retrieves the ApprovalGate from the executing
        Agent, creates a pending ApprovalRequest with the step's
        description and the requesting agent's identity, and
        inspects the resulting request status.

        If a registered ApprovalHandler immediately approves or
        rejects the request during creation, the step returns a
        StepResult reflecting that resolution. If the request
        remains pending and a timeout is configured, an
        ApprovalTimeoutError is raised. If the request remains
        pending with no timeout, a StepResult with
        PENDING_APPROVAL status is returned to signal that the
        workflow should pause.

        :param step_id: The unique identifier for this step within
            the workflow. Must not be None or empty.
        :param name: The human-readable name for this step. Must
            not be None or empty.
        :param description: A human-readable description of what
            is being approved.
        :param timeout: An optional timeout in seconds as a float.
            When set and the request remains pending after handler
            invocation, an ApprovalTimeoutError is raised. Defaults
            to None, meaning no timeout is enforced at the step
            level.
        :param kwargs: Additional keyword arguments passed to the
            WorkflowStep base class constructor (e.g. input_schema,
            output_schema, tags, retry_policy).
    """

    def __init__(self, step_id: str, name: str, description: str,
                 timeout: Optional[float] = None, **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type="approval", **kwargs)
        self._description = description
        self._timeout = timeout
        self._logger = logging.getLogger("ccai.agentkit.workflow.steps.approval")
        return

    @property
    def description(self) -> str:
        """
            A human-readable description of what is being approved.

            :returns: The description string.
        """
        return self._description

    @property
    def timeout(self) -> Optional[float]:
        """
            The optional timeout in seconds for the approval request.

            When set and the request remains pending after handler
            invocation, an ApprovalTimeoutError is raised.

            :returns: The timeout in seconds as a float or None when
                no timeout is configured at the step level.
        """
        return self._timeout

    def execute(self, context: WorkflowContext) -> StepResult:
        """
            Executes this ApprovalStep using the provided workflow
            context.

            Retrieves the Agent from the context, obtains the
            ApprovalGate from the Agent, extracts the execution
            identifier from the context metadata, and creates an
            ApprovalRequest via the ApprovalGate. The ApprovalGate
            invokes all registered handlers during request creation,
            which may immediately approve or reject the request.

            After request creation, the step inspects the request
            status in the ApprovalGate's internal store:

            - If "approved", returns a StepResult with COMPLETED
              status and the approval metadata in the output.
            - If "rejected", returns a StepResult with FAILED
              status and the rejection reason in the error field.
            - If still "pending" and a timeout is configured,
              raises an ApprovalTimeoutError.
            - If still "pending" with no timeout, returns a
              StepResult with PENDING_APPROVAL status.

            If the Agent is None, a StepResult with FAILED status
            is returned.

            :param context: The WorkflowContext with inputs and
                prior step outputs.

            :returns: A StepResult with the execution outcome.

            :raises ApprovalTimeoutError: When the request remains
                pending and a timeout is configured.
        """
        start_time = time.monotonic()

        agent = context.agent

        if agent is None:
            duration = time.monotonic() - start_time
            errmsg = "ApprovalStep '{}' failed: no agent available in the workflow context.".format(
                self._name
            )
            self._logger.warning(errmsg)

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.FAILED,
                duration=duration,
                error=errmsg
            )
            return result

        # Retrieve the ApprovalGate from the Agent
        approval_gate = agent.approval_gate

        # Extract execution context information
        execution_id = context.get_metadata("execution_id", "unknown")
        requesting_agent_id = str(agent.identity.identifier)

        # Create the ApprovalRequest via the ApprovalGate
        self._logger.info(
            "ApprovalStep '%s' creating approval request for step '%s' "
            "in execution '%s'.",
            self._name, self._step_id, execution_id
        )

        request = approval_gate.create_request(
            execution_id=execution_id,
            step_id=self._step_id,
            description=self._description,
            requesting_agent_id=requesting_agent_id
        )

        request_id = request.identifier

        # After handler invocation, check the resolved status.
        # The ApprovalGate stores the updated request internally
        # under the same identifier. Retrieve the current state
        # from the gate's internal store.
        current_request = approval_gate._pending_requests.get(request_id, request)
        current_status = current_request.status

        if current_status == "approved":
            duration = time.monotonic() - start_time
            output = dict(current_request.metadata)
            output["approval_request_id"] = request_id

            self._logger.info(
                "ApprovalStep '%s' approved for request '%s'.",
                self._name, request_id
            )

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.COMPLETED,
                output=output,
                duration=duration
            )
            return result

        if current_status == "rejected":
            duration = time.monotonic() - start_time
            rejection_reason = current_request.rejection_reason
            errmsg = "ApprovalStep '{}' rejected for request '{}': {}".format(
                self._name, request_id,
                rejection_reason if rejection_reason is not None else "No reason provided."
            )
            self._logger.warning(errmsg)

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.FAILED,
                duration=duration,
                error=errmsg
            )
            return result

        # Request is still pending
        if self._timeout is not None:
            self._logger.warning(
                "ApprovalStep '%s' timed out for request '%s' after %s seconds.",
                self._name, request_id, self._timeout
            )
            raise ApprovalTimeoutError(
                request_id=request_id,
                step_id=self._step_id,
                timeout=self._timeout
            )

        # No timeout configured, return PENDING_APPROVAL status
        duration = time.monotonic() - start_time

        self._logger.info(
            "ApprovalStep '%s' pending approval for request '%s'.",
            self._name, request_id
        )

        result = StepResult(
            step_id=self._step_id,
            step_name=self._name,
            status=StepExecutionStatus.PENDING_APPROVAL,
            output={"approval_request_id": request_id},
            duration=duration
        )
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, step identifier, step name, and description.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, name={!r}, description={!r})".format(
            self.__class__.__name__, self._step_id, self._name,
            self._description
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name
            and description.

            :returns: A human-readable string describing the approval
                step.
        """
        str_val = "ApprovalStep: {} [description: {}]".format(
            self._name, self._description
        )
        return str_val
