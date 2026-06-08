"""
    Defines the SubWorkflowStep class, a concrete WorkflowStep that
    executes a nested WorkflowDefinition as a sub-workflow within
    the parent workflow execution.

    SubWorkflowStep resolves an input mapping against the parent
    WorkflowContext, creates a new WorkflowExecutor for independent
    execution, runs the sub-workflow, and returns a StepResult
    containing the sub-workflow's final output on success or a
    FAILED status on failure.

    .. module:: ccai.agentkit.steps.subworkflowstep
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Built-in workflow step for sub-workflow execution.
"""

import logging
import time

from typing import Optional

from ccai.agentkit.stepexecutionstatus import StepExecutionStatus
from ccai.agentkit.stepresult import StepResult
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowdefinition import WorkflowDefinition
from ccai.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from ccai.agentkit.workflowexecutor import WorkflowExecutor
from ccai.agentkit.workflowstep import WorkflowStep


class SubWorkflowStep(WorkflowStep):
    """
        Executes a nested WorkflowDefinition as a sub-workflow.

        SubWorkflowStep is a concrete WorkflowStep subclass that
        composes workflows hierarchically. At execution time, it
        resolves the input mapping against the parent WorkflowContext
        to build the sub-workflow input dictionary, creates a new
        WorkflowExecutor instance for independent execution, runs
        the sub-workflow, and wraps the result in a StepResult.

        The sub-workflow gets its own WorkflowExecutor instance,
        which supports independent checkpointing of the sub-workflow
        execution separately from the parent workflow.

        The input_mapping dictionary maps sub-workflow input names
        to context references. Each value in the mapping is a string
        of the form "inputs.<field_name>" or
        "steps.<step_id>.<field_name>", which is resolved against
        the parent WorkflowContext at execution time.

        :param step_id: The unique identifier for this step within
            the workflow. Must not be None or empty.
        :param name: The human-readable name for this step. Must
            not be None or empty.
        :param sub_workflow: The WorkflowDefinition representing
            the nested sub-workflow to execute.
        :param input_mapping: An optional dictionary mapping
            sub-workflow input names to parent WorkflowContext
            reference strings. Defaults to an empty dictionary.
        :param kwargs: Additional keyword arguments passed to the
            WorkflowStep base class constructor (e.g. input_schema,
            output_schema, tags, retry_policy).
    """

    def __init__(self, step_id: str, name: str,
                 sub_workflow: WorkflowDefinition,
                 input_mapping: Optional[dict] = None, **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type="sub_workflow", **kwargs)
        self._sub_workflow = sub_workflow
        self._input_mapping = dict(input_mapping) if input_mapping is not None else {}
        self._logger = logging.getLogger("ccai.agentkit.workflow.steps.subworkflow")
        return

    @property
    def sub_workflow(self) -> WorkflowDefinition:
        """
            The WorkflowDefinition representing the nested
            sub-workflow to execute.

            :returns: The sub-workflow WorkflowDefinition instance.
        """
        return self._sub_workflow

    @property
    def input_mapping(self) -> dict:
        """
            The dictionary mapping sub-workflow input names to parent
            WorkflowContext reference strings.

            Each key is a sub-workflow input parameter name. Each
            value is a string of the form "inputs.<field_name>" or
            "steps.<step_id>.<field_name>" that is resolved against
            the parent WorkflowContext at execution time.

            :returns: A dictionary of input mapping entries.
        """
        return self._input_mapping

    def _resolve_input_mapping(self, context: WorkflowContext) -> dict:
        """
            Resolves the input mapping against the parent
            WorkflowContext.

            For each entry in the input_mapping dictionary, the
            context reference string is parsed and the corresponding
            value is retrieved from the parent WorkflowContext.
            References of the form "inputs.<field_name>" are resolved
            via context.get_input. References of the form
            "steps.<step_id>.<field_name>" are resolved via
            context.get_step_output.

            :param context: The parent WorkflowContext to resolve
                references against.

            :returns: A dictionary of resolved sub-workflow input
                values.
        """
        resolved_inputs = {}

        for param_name, reference in self._input_mapping.items():
            parts = reference.split(".")

            if len(parts) >= 2 and parts[0] == "inputs":
                field_name = ".".join(parts[1:])
                resolved_value = context.get_input(field_name)
                resolved_inputs[param_name] = resolved_value

            elif len(parts) >= 3 and parts[0] == "steps":
                step_id = parts[1]
                field_name = ".".join(parts[2:])
                step_output = context.get_step_output(step_id)

                if step_output is not None:
                    resolved_value = step_output.get(field_name, None)
                    resolved_inputs[param_name] = resolved_value
                else:
                    resolved_inputs[param_name] = None

            else:
                resolved_inputs[param_name] = None

        return resolved_inputs

    def execute(self, context: WorkflowContext) -> StepResult:
        """
            Executes this SubWorkflowStep using the provided parent
            workflow context.

            Resolves the input mapping against the parent
            WorkflowContext, creates a new WorkflowExecutor for
            independent sub-workflow execution, runs the sub-workflow
            with the resolved inputs and the agent from the parent
            context, and returns a StepResult with the execution
            outcome.

            If the sub-workflow completes successfully, the StepResult
            contains COMPLETED status and the sub-workflow's
            final_output. If the sub-workflow fails, the StepResult
            contains FAILED status and the sub-workflow's error
            information.

            :param context: The parent WorkflowContext with inputs
                and prior step outputs.

            :returns: A StepResult with the execution outcome.
        """
        start_time = time.monotonic()

        # Resolve input mapping against the parent WorkflowContext
        resolved_inputs = self._resolve_input_mapping(context)

        # Retrieve the agent from the parent context
        agent = context.agent

        # Create a new WorkflowExecutor for independent sub-workflow
        # execution. This supports independent checkpointing of the
        # sub-workflow separately from the parent workflow.
        sub_executor = WorkflowExecutor()

        self._logger.info(
            "SubWorkflowStep '%s' executing sub-workflow '%s'.",
            self._name, self._sub_workflow.name
        )

        try:
            workflow_result = sub_executor.execute(
                workflow=self._sub_workflow,
                inputs=resolved_inputs,
                agent=agent
            )
        except Exception as exec_err:
            duration = time.monotonic() - start_time
            errmsg = "SubWorkflowStep '{}' failed during execution of sub-workflow '{}': {}".format(
                self._name, self._sub_workflow.name, str(exec_err)
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

        duration = time.monotonic() - start_time

        if workflow_result.status == WorkflowExecutionStatus.COMPLETED:
            self._logger.info(
                "SubWorkflowStep '%s' sub-workflow '%s' completed "
                "successfully in %.3fs.",
                self._name, self._sub_workflow.name, duration
            )

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.COMPLETED,
                output=workflow_result.final_output,
                duration=duration
            )
            return result
        else:
            error_detail = workflow_result.error if workflow_result.error is not None else (
                "Sub-workflow '{}' finished with status '{}'.".format(
                    self._sub_workflow.name, workflow_result.status.value
                )
            )
            self._logger.warning(
                "SubWorkflowStep '%s' sub-workflow '%s' failed: %s",
                self._name, self._sub_workflow.name, error_detail
            )

            result = StepResult(
                step_id=self._step_id,
                step_name=self._name,
                status=StepExecutionStatus.FAILED,
                duration=duration,
                error=error_detail
            )
            return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including the
            class name, step identifier, step name, and sub-workflow
            name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, name={!r}, sub_workflow={!r})".format(
            self.__class__.__name__, self._step_id, self._name,
            self._sub_workflow.name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name
            and sub-workflow name.

            :returns: A human-readable string describing the
                sub-workflow step.
        """
        str_val = "SubWorkflowStep: {} [sub_workflow: {}]".format(
            self._name, self._sub_workflow.name
        )
        return str_val
