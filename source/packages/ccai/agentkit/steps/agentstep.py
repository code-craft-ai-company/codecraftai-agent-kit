"""
    Defines the AgentStep class, a concrete WorkflowStep that delegates
    execution to another Agent via the Communication & Messaging system.

    AgentStep constructs a request message from the WorkflowContext,
    sends the message to the target agent through the agent's messaging
    system, awaits a response, and returns a StepResult containing the
    response payload on success or a FAILED status on timeout or
    transport error.

    .. module:: ccai.agentkit.steps.agentstep
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Built-in workflow step for cross-agent delegation.
"""

import logging
import time

from typing import Optional

from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowstep import WorkflowStep


class AgentStep(WorkflowStep):
    """
        Delegates execution to another Agent via the Communication &
        Messaging system.

        AgentStep is a concrete WorkflowStep subclass that integrates
        with the Communication & Messaging system. At execution time,
        it constructs a request message payload from the WorkflowContext
        inputs and accumulated step outputs, sends the message to the
        target agent through the executing agent's send_message method,
        and wraps the response in a StepResult.

        The target_agent_id identifies the remote agent to delegate to.
        The optional transport_name specifies which communication
        transport to use. The optional timeout specifies the maximum
        number of seconds to wait for a response from the target agent.

        :param step_id: The unique identifier for this step within
            the workflow. Must not be None or empty.
        :param name: The human-readable name for this step. Must
            not be None or empty.
        :param target_agent_id: The identifier of the Agent to
            delegate execution to.
        :param transport_name: An optional string specifying the
            communication transport to use. Defaults to None, which
            uses the agent's default transport.
        :param timeout: An optional float specifying the maximum
            number of seconds to wait for a response. Defaults to
            None, which uses the agent's default timeout.
        :param kwargs: Additional keyword arguments passed to the
            WorkflowStep base class constructor (e.g. input_schema,
            output_schema, tags, retry_policy).
    """

    def __init__(self, step_id: str, name: str, target_agent_id: str,
                 transport_name: Optional[str] = None,
                 timeout: Optional[float] = None, **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type="agent", **kwargs)
        self._target_agent_id = target_agent_id
        self._transport_name = transport_name
        self._timeout = timeout
        self._logger = logging.getLogger("ccai.agentkit.workflow.steps.agent")
        return

    @property
    def target_agent_id(self) -> str:
        """
            The identifier of the Agent to delegate execution to.

            :returns: The target agent identifier string.
        """
        return self._target_agent_id

    @property
    def transport_name(self) -> Optional[str]:
        """
            The optional communication transport name to use when
            sending the message to the target agent.

            :returns: The transport name string or None when the
                agent's default transport should be used.
        """
        return self._transport_name

    @property
    def timeout(self) -> Optional[float]:
        """
            The optional maximum number of seconds to wait for a
            response from the target agent.

            :returns: The timeout in seconds as a float or None
                when the agent's default timeout should be used.
        """
        return self._timeout

    def _build_payload(self, context: WorkflowContext) -> dict:
        """
            Constructs the request message payload from the
            WorkflowContext.

            The payload contains the workflow inputs and all
            accumulated step outputs, providing the target agent
            with the full context needed to perform the delegated
            work.

            :param context: The WorkflowContext to build the
                payload from.

            :returns: A dictionary containing "inputs" and
                "step_outputs" keys.
        """
        payload = {
            "inputs": dict(context.inputs) if context.inputs is not None else {},
            "step_outputs": dict(context.step_outputs) if context.step_outputs is not None else {}
        }
        return payload

    def execute(self, context: WorkflowContext) -> StepResult:
        """
            Executes this AgentStep using the provided workflow context.

            Retrieves the Agent from the context, constructs a request
            message payload from the WorkflowContext inputs and step
            outputs, sends the message to the target agent through the
            agent's send_message method, and returns a StepResult with
            the execution outcome.

            If the Agent is None, a StepResult with FAILED status is
            returned. If the message send raises a timeout error, a
            StepResult with FAILED status and the timeout information
            is returned. If the message send raises any other transport
            error, a StepResult with FAILED status and the error
            message is returned.

            :param context: The WorkflowContext with inputs and prior
                step outputs.

            :returns: A StepResult with the execution outcome.
        """
        start_time = time.monotonic()

        agent = context.agent

        if agent is None:
            duration = time.monotonic() - start_time
            errmsg = "AgentStep '{}' failed: no agent available in the workflow context.".format(
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

        payload = self._build_payload(context)

        try:
            send_kwargs = {}

            if self._transport_name is not None:
                send_kwargs["transport_name"] = self._transport_name

            if self._timeout is not None:
                send_kwargs["timeout"] = self._timeout

            response = agent.send_message(
                self._target_agent_id, payload, **send_kwargs
            )

            duration = time.monotonic() - start_time

            output = response if isinstance(response, dict) else {"response": response}

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.COMPLETED,
                output=output,
                duration=duration
            )
            return result

        except Exception as exec_err:
            duration = time.monotonic() - start_time

            error_type_name = type(exec_err).__name__
            errmsg = "AgentStep '{}' failed sending message to agent '{}': [{}] {}".format(
                self._name, self._target_agent_id, error_type_name,
                str(exec_err)
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

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, step identifier, step name, and target agent
            identifier.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, name={!r}, target_agent_id={!r})".format(
            self.__class__.__name__, self._step_id, self._name,
            self._target_agent_id
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name
            and target agent identifier.

            :returns: A human-readable string describing the agent step.
        """
        str_val = "AgentStep: {} [target: {}]".format(
            self._name, self._target_agent_id
        )
        return str_val
