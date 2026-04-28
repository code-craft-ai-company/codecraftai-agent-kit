"""
    Defines the ToolStep class, a concrete WorkflowStep that executes
    a named Tool from the Agent's ToolRegistry during workflow
    execution.

    ToolStep resolves an input mapping against the WorkflowContext,
    looks up the tool by name in the Agent's ToolRegistry, executes
    the tool through the Agent's execute_tool method, and returns a
    StepResult containing the ToolResult output on success or a
    FAILED status on failure.

    .. module:: automojo.agentkit.steps.toolstep
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Built-in workflow step for tool execution.
"""

import logging
import time

from typing import Optional

from automojo.agentkit.stepexecutionstatus import StepExecutionStatus
from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.workflowstep import WorkflowStep


class ToolStep(WorkflowStep):
    """
        Executes a named Tool from the Agent's ToolRegistry.

        ToolStep is a concrete WorkflowStep subclass that integrates
        with the Tool & Capability System. At execution time, it
        resolves the input mapping against the WorkflowContext to
        build the tool input dictionary, looks up the tool by name
        in the Agent's ToolRegistry, executes the tool, and wraps
        the result in a StepResult.

        The input_mapping dictionary maps tool parameter names to
        context references. Each value in the mapping is a string
        of the form "inputs.<field_name>" or
        "steps.<step_id>.<field_name>", which is resolved against
        the WorkflowContext at execution time.

        :param step_id: The unique identifier for this step within
            the workflow. Must not be None or empty.
        :param name: The human-readable name for this step. Must
            not be None or empty.
        :param tool_name: The name of the Tool to look up in the
            Agent's ToolRegistry.
        :param input_mapping: An optional dictionary mapping tool
            parameter names to WorkflowContext reference strings.
            Defaults to an empty dictionary.
        :param kwargs: Additional keyword arguments passed to the
            WorkflowStep base class constructor (e.g. input_schema,
            output_schema, tags, retry_policy).
    """

    def __init__(self, step_id: str, name: str, tool_name: str,
                 input_mapping: Optional[dict] = None, **kwargs) -> None:
        super().__init__(step_id=step_id, name=name, step_type="tool", **kwargs)
        self._tool_name = tool_name
        self._input_mapping = dict(input_mapping) if input_mapping is not None else {}
        self._logger = logging.getLogger("automojo.agentkit.workflow.steps.tool")
        return

    @property
    def tool_name(self) -> str:
        """
            The name of the Tool to execute from the Agent's ToolRegistry.

            :returns: The tool name string.
        """
        return self._tool_name

    @property
    def input_mapping(self) -> dict:
        """
            The dictionary mapping tool parameter names to WorkflowContext
            reference strings.

            Each key is a tool input parameter name. Each value is a
            string of the form "inputs.<field_name>" or
            "steps.<step_id>.<field_name>" that is resolved against
            the WorkflowContext at execution time.

            :returns: A dictionary of input mapping entries.
        """
        return self._input_mapping

    def _resolve_input_mapping(self, context: WorkflowContext) -> dict:
        """
            Resolves the input mapping against the WorkflowContext.

            For each entry in the input_mapping dictionary, the
            context reference string is parsed and the corresponding
            value is retrieved from the WorkflowContext. References
            of the form "inputs.<field_name>" are resolved via
            context.get_input. References of the form
            "steps.<step_id>.<field_name>" are resolved via
            context.get_step_output.

            :param context: The WorkflowContext to resolve references
                against.

            :returns: A dictionary of resolved tool input values.
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
            Executes this ToolStep using the provided workflow context.

            Resolves the input mapping against the WorkflowContext,
            retrieves the Agent from the context, looks up the tool
            by name in the Agent's ToolRegistry, executes the tool
            through the Agent's execute_tool method, and returns a
            StepResult with the execution outcome.

            If the Agent is None or the tool is not found in the
            Agent's ToolRegistry, a StepResult with FAILED status
            is returned. If the tool execution raises an exception,
            a StepResult with FAILED status and the error message
            is returned.

            :param context: The WorkflowContext with inputs and prior
                step outputs.

            :returns: A StepResult with the execution outcome.
        """
        start_time = time.monotonic()

        agent = context.agent

        if agent is None:
            duration = time.monotonic() - start_time
            errmsg = "ToolStep '{}' failed: no agent available in the workflow context.".format(
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

        # Check that the tool exists in the Agent's ToolRegistry
        tool_registry = agent.tools
        tool = tool_registry.lookup(self._tool_name)

        if tool is None:
            duration = time.monotonic() - start_time
            errmsg = "ToolStep '{}' failed: tool '{}' not found in the agent's ToolRegistry.".format(
                self._name, self._tool_name
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

        # Resolve input mapping against the WorkflowContext
        resolved_inputs = self._resolve_input_mapping(context)

        # Execute the tool through the Agent
        try:
            tool_result = agent.execute_tool(self._tool_name, resolved_inputs)
            duration = time.monotonic() - start_time

            if tool_result.is_success:
                output = tool_result.output if tool_result.output is not None else {}

                result = StepResult(
                    step_id=self._step_id,
                    step_name=self._name,
                    status=StepExecutionStatus.COMPLETED,
                    output=output,
                    duration=duration
                )
                return result
            else:
                error_detail = str(tool_result.error) if tool_result.error is not None else "Tool execution failed."

                result = StepResult(
                    step_id=self._step_id,
                    step_name=self._name,
                    status=StepExecutionStatus.FAILED,
                    duration=duration,
                    error=error_detail
                )
                return result

        except Exception as exec_err:
            duration = time.monotonic() - start_time
            errmsg = "ToolStep '{}' failed during execution of tool '{}': {}".format(
                self._name, self._tool_name, str(exec_err)
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
            class name, step identifier, step name, and tool name.

            :returns: A repr string for debugging.
        """
        repr_str = "{}(step_id={!r}, name={!r}, tool_name={!r})".format(
            self.__class__.__name__, self._step_id, self._name,
            self._tool_name
        )
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the step name
            and tool name.

            :returns: A human-readable string describing the tool step.
        """
        str_val = "ToolStep: {} [tool: {}]".format(
            self._name, self._tool_name
        )
        return str_val
