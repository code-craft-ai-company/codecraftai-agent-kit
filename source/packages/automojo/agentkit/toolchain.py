"""
    Defines the ToolChain class for composing ordered tool pipelines
    in the automojo-agent-kit framework.

    A ToolChain is an ordered sequence of tool references with optional
    input-output mappings that define how the output fields of one step
    map to the input fields of the next step. The chain validates tool
    existence and schema compatibility at construction time.
"""

import os

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.toolerrors import ToolValidationError
from automojo.agentkit.toolregistry import ToolRegistry


class ToolChain:
    """
        An ordered sequence of tool references with input-output mappings
        defining a pipeline.

        Each step is a dictionary with:
            - tool_name (str, required): Name of the tool to execute.
            - mappings (dict, optional): Maps output field names from the
              previous step to input field names for this step.

        :param name: Name of the chain.
        :param steps: List of dicts with 'tool_name' and optional 'mappings' keys.
        :param registry: The ToolRegistry to resolve tool names against.

        :raises: SemanticError if a tool name is not found.
        :raises: ToolValidationError if schema compatibility fails.
    """

    def __init__(self, name: str, steps: list, registry: ToolRegistry) -> None:
        self._name = name
        self._steps = list(steps)
        self._registry = registry

        self._validate_steps()

        return

    @property
    def name(self) -> str:
        """
            The name of this tool chain.

            :returns: The chain name string.
        """
        rtnval = self._name
        return rtnval

    @property
    def tool_names(self) -> list:
        """
            The ordered list of tool names in the chain.

            :returns: A list of tool name strings.
        """
        names = []

        for step in self._steps:
            tool_name = step["tool_name"]
            names.append(tool_name)

        rtnval = names
        return rtnval

    @property
    def step_count(self) -> int:
        """
            The number of steps in the chain.

            :returns: The count of steps.
        """
        rtnval = len(self._steps)
        return rtnval

    def _validate_steps(self) -> None:
        """
            Validates that all tool names exist in the registry and that
            schema compatibility holds between consecutive steps according
            to the provided mappings.

            :raises: SemanticError if a tool name is not found in the registry.
            :raises: ToolValidationError if schema compatibility fails between steps.
        """
        self._validate_tool_existence()
        self._validate_schema_compatibility()

        return

    def _validate_tool_existence(self) -> None:
        """
            Validates that every tool name referenced in the steps exists
            in the registry.

            :raises: SemanticError if a tool name is not found.
        """
        for step in self._steps:
            tool_name = step["tool_name"]
            tool = self._registry.lookup(tool_name=tool_name)

            if tool is None:
                errmsg_lines = [
                    "ToolChain '{}' references a tool that is not registered.".format(self._name),
                    "  Missing tool name: '{}'".format(tool_name),
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise SemanticError(errmsg)

        return

    def _validate_schema_compatibility(self) -> None:
        """
            Validates schema compatibility between consecutive steps based
            on the mappings defined in each step.

            For each consecutive pair of steps where the second step has
            mappings, checks that:
            1. Each source field in the mappings exists in the output schema
               of the previous step.
            2. The type of the source field in the output schema is compatible
               with the type of the target field in the input schema of the
               next step.

            :raises: ToolValidationError if schema compatibility fails.
        """
        step_count = len(self._steps)

        if step_count < 2:
            return

        for step_index in range(1, step_count):
            current_step = self._steps[step_index]
            previous_step = self._steps[step_index - 1]

            mappings = current_step.get("mappings", None)

            if mappings is None:
                continue

            has_mappings = len(mappings) > 0

            if has_mappings is not True:
                continue

            previous_tool_name = previous_step["tool_name"]
            current_tool_name = current_step["tool_name"]

            previous_tool = self._registry.lookup(tool_name=previous_tool_name)
            current_tool = self._registry.lookup(tool_name=current_tool_name)

            previous_output_schema = previous_tool.output_schema
            current_input_schema = current_tool.input_schema

            self._check_mapping_compatibility(
                previous_tool_name=previous_tool_name,
                current_tool_name=current_tool_name,
                previous_output_schema=previous_output_schema,
                current_input_schema=current_input_schema,
                mappings=mappings,
                step_index=step_index,
            )

        return

    def _check_mapping_compatibility(
        self,
        previous_tool_name: str,
        current_tool_name: str,
        previous_output_schema,
        current_input_schema,
        mappings: dict,
        step_index: int,
    ) -> None:
        """
            Checks that the mappings between two consecutive steps are
            compatible with the output schema of the previous step and
            the input schema of the next step.

            :param previous_tool_name: The name of the previous step's tool.
            :param current_tool_name: The name of the current step's tool.
            :param previous_output_schema: The output ToolSchema of the previous step.
            :param current_input_schema: The input ToolSchema of the current step.
            :param mappings: The mappings dict from the current step.
            :param step_index: The index of the current step in the chain.

            :raises: ToolValidationError if a mapping is incompatible.
        """
        output_params_by_name = self._build_param_lookup(schema=previous_output_schema)
        input_params_by_name = self._build_param_lookup(schema=current_input_schema)

        errors = []

        for source_field, target_field in mappings.items():
            source_exists = source_field in output_params_by_name
            target_exists = target_field in input_params_by_name

            if source_exists is not True:
                errmsg = "Mapping source field '{}' not found in output schema of tool '{}'.".format(
                    source_field, previous_tool_name
                )
                errors.append(errmsg)
                continue

            if target_exists is not True:
                errmsg = "Mapping target field '{}' not found in input schema of tool '{}'.".format(
                    target_field, current_tool_name
                )
                errors.append(errmsg)
                continue

            source_type = output_params_by_name[source_field]["type"]
            target_type = input_params_by_name[target_field]["type"]

            types_match = source_type == target_type

            if types_match is not True:
                errmsg = "Type mismatch in mapping '{}' -> '{}': output type '{}' from tool '{}' is incompatible with input type '{}' on tool '{}'.".format(
                    source_field, target_field, source_type, previous_tool_name, target_type, current_tool_name
                )
                errors.append(errmsg)

        has_errors = len(errors) > 0

        if has_errors is True:
            error_context_lines = [
                "Schema compatibility check failed between step {} ('{}') and step {} ('{}') in chain '{}'.".format(
                    step_index - 1, previous_tool_name, step_index, current_tool_name, self._name
                )
            ]

            for error_item in errors:
                error_context_lines.append("  - {}".format(error_item))

            direction = "input"
            raise ToolValidationError(
                tool_name=current_tool_name,
                direction=direction,
                errors=errors,
            )

        return

    def _build_param_lookup(self, schema) -> dict:
        """
            Builds a dictionary mapping parameter names to their definitions
            from a ToolSchema instance.

            :param schema: A ToolSchema instance, or None.

            :returns: A dictionary mapping parameter name strings to parameter
                definition dictionaries.
        """
        params_by_name = {}

        if schema is not None:
            parameters = schema.parameters

            for param_def in parameters:
                param_name = param_def["name"]
                params_by_name[param_name] = param_def

        rtnval = params_by_name
        return rtnval
