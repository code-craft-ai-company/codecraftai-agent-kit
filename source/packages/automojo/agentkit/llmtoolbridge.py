"""
    Defines the LlmToolBridge class for converting between Tool system types
    and LLM function calling format.

    LlmToolBridge is a stateless utility class that converts ToolDescriptor
    objects into OpenAI-compatible function definition dictionaries, extracts
    tool call requests from LlmMessage metadata, and converts ToolResult
    objects into LlmMessage instances with role "tool".
"""

import json

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmmessage import LlmMessage
from automojo.agentkit.tooldescriptor import ToolDescriptor
from automojo.agentkit.toolresult import ToolResult


class LlmToolBridge:
    """
        Converts between Tool system types and LLM function calling format.
        Stateless utility class.
    """

    TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA = {
        "string": "string",
        "integer": "integer",
        "float": "number",
        "boolean": "boolean",
        "list": "array",
        "dictionary": "object",
    }

    def descriptors_to_functions(self, descriptors: list) -> list:
        """
            Converts a list of ToolDescriptor objects into LLM-compatible
            function definition dictionaries (OpenAI function calling format).

            :param descriptors: A list of ToolDescriptor objects.

            :returns: A list of function definition dictionaries.
        """
        rtnval = []

        for descriptor in descriptors:
            func_def = self._descriptor_to_function(descriptor)
            rtnval.append(func_def)

        return rtnval

    def _descriptor_to_function(self, descriptor: ToolDescriptor) -> dict:
        """
            Converts a single ToolDescriptor to an OpenAI function definition.

            :param descriptor: The ToolDescriptor to convert.

            :returns: A function definition dictionary.
        """
        properties = {}
        required = []

        if descriptor.input_schema is not None:
            for param in descriptor.input_schema.parameters:
                pname = param["name"]
                ptype = param["type"]
                json_type = self.TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA.get(ptype, "string")
                properties[pname] = {"type": json_type}

                has_description = param.get("description") is not None
                if has_description is True:
                    description_value = param["description"]
                    if len(description_value) > 0:
                        properties[pname]["description"] = description_value

                is_required = param.get("required", True)
                if is_required is True:
                    required.append(pname)

        rtnval = {
            "type": "function",
            "function": {
                "name": descriptor.name,
                "description": descriptor.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }

        return rtnval

    def message_to_tool_calls(self, message: LlmMessage) -> list:
        """
            Extracts tool call requests from an LlmMessage.

            :param message: An LlmMessage with tool call metadata.

            :returns: A list of dicts with 'tool_name' and 'arguments' keys.

            :raises: SemanticError if message does not contain tool calls.
        """
        metadata = message.metadata
        tool_calls = metadata.get("tool_calls")

        has_tool_calls = tool_calls is not None
        if has_tool_calls is False:
            errmsg = "LlmMessage does not contain tool call information."
            raise SemanticError(errmsg)

        is_empty = len(tool_calls) == 0
        if is_empty is True:
            errmsg = "LlmMessage does not contain tool call information."
            raise SemanticError(errmsg)

        rtnval = []

        for tc in tool_calls:
            function_info = tc["function"]
            tool_name = function_info["name"]
            arguments = function_info.get("arguments", {})

            entry = {
                "tool_name": tool_name,
                "arguments": arguments
            }
            rtnval.append(entry)

        return rtnval

    def tool_result_to_message(self, tool_name: str,
                                result: ToolResult) -> LlmMessage:
        """
            Converts a ToolResult into an LlmMessage with role "tool".

            :param tool_name: The name of the tool that was executed.
            :param result: The ToolResult from tool execution.

            :returns: An LlmMessage with role "tool".
        """
        has_output = result.output is not None
        if has_output is True:
            content = json.dumps(result.as_dict())
        else:
            content = ""

        rtnval = LlmMessage(
            role="tool",
            content=content,
            metadata={"tool_name": tool_name}
        )

        return rtnval
