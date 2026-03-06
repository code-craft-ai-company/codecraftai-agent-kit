"""
    Defines the ToolChainExecutor class for sequential execution of tool chains.

    ToolChainExecutor runs each step in a ToolChain in sequence through the
    ToolExecutor, applying input-output mappings between steps, and returns
    a ToolChainResult with the overall outcome.
"""

import time

from automojo.agentkit.toolchain import ToolChain
from automojo.agentkit.toolchainresult import ToolChainResult
from automojo.agentkit.toolexecutor import ToolExecutor
from automojo.agentkit.toolresult import ToolResult


class ToolChainExecutor:
    """
        Executes a ToolChain by running each step in sequence through the ToolExecutor.

        For each step in the chain, the executor looks up the tool from the chain's
        registry, applies input-output mappings from the previous step's output,
        and invokes the tool via the ToolExecutor. If any step fails, execution
        stops and a failure result is returned. If all steps succeed, a success
        result is returned with the final step's output.

        :param tool_executor: The ToolExecutor instance used to execute each step.
    """

    def __init__(self, tool_executor: ToolExecutor) -> None:
        self._tool_executor = tool_executor
        return

    def execute(self, chain: ToolChain, initial_inputs: dict,
                agent_identifier: str = None) -> ToolChainResult:
        """
            Executes the chain steps in order, applying mappings between steps.

            For each step, the tool is looked up from the chain's registry.
            If the step has mappings and is not the first step, the previous
            step's output fields are mapped to the current step's input fields.
            If no mappings are defined, the previous step's output is passed
            directly as the current step's inputs.

            :param chain: The ToolChain to execute.
            :param initial_inputs: Input dictionary for the first step.
            :param agent_identifier: Optional agent identifier for logging.

            :returns: A ToolChainResult with the overall outcome.
        """
        start_time = time.time()

        step_results = []
        current_inputs = initial_inputs
        current_output = None

        steps = chain._steps

        for step_index, step in enumerate(steps):
            tool_name = step["tool_name"]
            tool = chain._registry.lookup(tool_name=tool_name)

            is_first_step = step_index == 0

            if is_first_step is not True:
                mappings = step.get("mappings", None)
                current_inputs = self._apply_mappings(
                    mappings=mappings,
                    previous_output=current_output,
                )

            result = self._tool_executor.execute(
                tool=tool,
                inputs=current_inputs,
                agent_identifier=agent_identifier,
            )

            step_results.append(result)

            if result.is_success is not True:
                end_time = time.time()
                duration = end_time - start_time

                rtnval = ToolChainResult(
                    chain_name=chain.name,
                    status=ToolChainResult.STATUS_FAILURE,
                    step_results=step_results,
                    duration=duration,
                    error=result.error,
                )
                return rtnval

            current_output = result.output

        end_time = time.time()
        duration = end_time - start_time

        rtnval = ToolChainResult(
            chain_name=chain.name,
            status=ToolChainResult.STATUS_SUCCESS,
            output=current_output,
            step_results=step_results,
            duration=duration,
        )
        return rtnval

    def _apply_mappings(self, mappings: dict, previous_output: dict) -> dict:
        """
            Applies input-output mappings to transform the previous step's
            output into the current step's inputs.

            If mappings is None or empty, the previous output is passed
            directly as the current inputs. Otherwise, a new dictionary
            is constructed where each target input field is populated from
            the corresponding source output field.

            :param mappings: A dictionary mapping output field names to input
                field names, or None for pass-through.
            :param previous_output: The output dictionary from the previous step.

            :returns: The input dictionary for the current step.
        """
        has_mappings = mappings is not None and len(mappings) > 0

        if has_mappings is not True:
            rtnval = previous_output
            return rtnval

        mapped_inputs = {}

        for output_field, input_field in mappings.items():
            mapped_inputs[input_field] = previous_output[output_field]

        rtnval = mapped_inputs
        return rtnval
