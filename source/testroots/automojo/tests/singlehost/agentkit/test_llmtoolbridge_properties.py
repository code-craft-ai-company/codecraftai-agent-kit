"""
    Property-based tests for the automojo.agentkit.llmtoolbridge module.

    Uses automojo.testbase.properties to verify:
    - Property 34: LlmToolBridge preserves tool descriptor information
    - Property 35: LlmToolBridge tool_result_to_message produces tool role message
    - Property 36: LlmToolBridge rejects messages without tool calls

    **Validates: Requirements 11.1, 11.3, 11.4, 11.5, 11.6**
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmmessage import LlmMessage
from automojo.agentkit.llmtoolbridge import LlmToolBridge
from automojo.agentkit.tooldescriptor import ToolDescriptor
from automojo.agentkit.toolresult import ToolResult
from automojo.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_identifier = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=15,
)

_description_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ",
    min_size=1,
    max_size=40,
)

_version_text = st.text(
    alphabet="0123456789.",
    min_size=1,
    max_size=8,
)

_param_type = st.sampled_from(["string", "integer", "float", "boolean", "list", "dictionary"])


@composite
def _tool_param(draw):
    """
        Draws a single ToolSchema parameter definition dictionary.
    """
    name = draw(_identifier)
    ptype = draw(_param_type)
    required = draw(st.booleans())

    param = {
        "name": name,
        "type": ptype,
        "required": required,
    }

    return param


@composite
def _tool_schema_with_params(draw):
    """
        Draws a ToolSchema with at least one parameter, ensuring unique names.
    """
    params = draw(st.lists(_tool_param(), min_size=1, max_size=5))

    # Deduplicate by name, keeping the first occurrence
    seen_names = set()
    unique_params = []
    for p in params:
        if p["name"] not in seen_names:
            seen_names.add(p["name"])
            unique_params.append(p)

    schema = ToolSchema(parameters=unique_params)
    return schema


@composite
def _tool_descriptor_with_schema(draw):
    """
        Draws a ToolDescriptor with a non-None input schema containing parameters.
    """
    name = draw(_identifier)
    description = draw(_description_text)
    version = draw(_version_text)
    input_schema = draw(_tool_schema_with_params())

    descriptor = ToolDescriptor(
        name=name,
        description=description,
        version=version,
        input_schema=input_schema,
        output_schema=None,
    )

    return descriptor


_tool_result_status = st.sampled_from([ToolResult.STATUS_SUCCESS, ToolResult.STATUS_FAILURE])


@composite
def _tool_result(draw):
    """
        Draws a ToolResult with a random tool name, status, and optional output.
    """
    tool_name = draw(_identifier)
    status = draw(_tool_result_status)

    has_output = draw(st.booleans())
    if has_output is True:
        output = {"result": "value"}
    else:
        output = None

    duration = draw(st.floats(min_value=0.0, max_value=100.0))

    result = ToolResult(
        tool_name=tool_name,
        status=status,
        output=output,
        duration=duration,
    )

    return result


_non_tool_call_role = st.sampled_from(["system", "user", "assistant", "tool"])

_content_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ",
    min_size=0,
    max_size=30,
)


@composite
def _message_without_tool_calls(draw):
    """
        Draws an LlmMessage whose metadata does not contain a 'tool_calls' key
        or contains an empty list for 'tool_calls'.
    """
    role = draw(_non_tool_call_role)
    content = draw(_content_text)

    use_empty_list = draw(st.booleans())
    use_no_key = draw(st.booleans())

    if use_no_key is True:
        # Metadata without tool_calls key at all
        metadata = {"some_key": "some_value"}
    elif use_empty_list is True:
        # Metadata with empty tool_calls list
        metadata = {"tool_calls": []}
    else:
        # Empty metadata
        metadata = {}

    message = LlmMessage(role=role, content=content, metadata=metadata)
    return message


# ---------------------------------------------------------------------------
# Property 34: LlmToolBridge preserves tool descriptor information
# ---------------------------------------------------------------------------

@given(descriptor=_tool_descriptor_with_schema(), settings=settings(max_examples=50))
def test_llmtoolbridge_preserves_tool_name_and_description(
    descriptor: ToolDescriptor,
) -> None:
    """
        **Validates: Requirements 11.1, 11.4, 11.6**

        For any valid ToolDescriptor with a name, description, and input schema,
        converting to an LLM function definition via descriptors_to_functions()
        shall produce a dictionary whose function name equals the tool name
        and function description equals the tool description.
    """
    bridge = LlmToolBridge()

    functions = bridge.descriptors_to_functions([descriptor])

    assert len(functions) == 1, (
        "Expected 1 function definition, got {}".format(len(functions))
    )

    func_def = functions[0]
    func_info = func_def["function"]

    assert func_info["name"] == descriptor.name, (
        "Function name should be {!r}, got {!r}".format(
            descriptor.name, func_info["name"]
        )
    )

    assert func_info["description"] == descriptor.description, (
        "Function description should be {!r}, got {!r}".format(
            descriptor.description, func_info["description"]
        )
    )

    return


@given(descriptor=_tool_descriptor_with_schema(), settings=settings(max_examples=50))
def test_llmtoolbridge_preserves_parameter_names_and_types(
    descriptor: ToolDescriptor,
) -> None:
    """
        **Validates: Requirements 11.1, 11.4, 11.6**

        For any valid ToolDescriptor with an input schema, converting to an
        LLM function definition shall preserve the parameter names and types
        from the original ToolDescriptor.
    """
    bridge = LlmToolBridge()

    functions = bridge.descriptors_to_functions([descriptor])
    func_def = functions[0]
    func_params = func_def["function"]["parameters"]
    properties = func_params["properties"]

    expected_type_map = LlmToolBridge.TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA

    for param in descriptor.input_schema.parameters:
        pname = param["name"]
        ptype = param["type"]
        expected_json_type = expected_type_map.get(ptype, "string")

        assert pname in properties, (
            "Parameter {!r} should be in function properties".format(pname)
        )

        assert properties[pname]["type"] == expected_json_type, (
            "Parameter {!r} type should be {!r}, got {!r}".format(
                pname, expected_json_type, properties[pname]["type"]
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 35: LlmToolBridge tool_result_to_message produces tool role message
# ---------------------------------------------------------------------------

@given(tool_name=_identifier, result=_tool_result(), settings=settings(max_examples=50))
def test_llmtoolbridge_tool_result_to_message_produces_tool_role(
    tool_name: str,
    result: ToolResult,
) -> None:
    """
        **Validates: Requirements 11.3**

        For any tool name and ToolResult, tool_result_to_message() shall
        return an LlmMessage with role "tool" and metadata containing
        the tool name.
    """
    bridge = LlmToolBridge()

    message = bridge.tool_result_to_message(tool_name, result)

    assert message.role == "tool", (
        "Message role should be 'tool', got {!r}".format(message.role)
    )

    assert "tool_name" in message.metadata, (
        "Message metadata should contain 'tool_name' key"
    )

    assert message.metadata["tool_name"] == tool_name, (
        "Message metadata tool_name should be {!r}, got {!r}".format(
            tool_name, message.metadata["tool_name"]
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 36: LlmToolBridge rejects messages without tool calls
# ---------------------------------------------------------------------------

@given(message=_message_without_tool_calls(), settings=settings(max_examples=50))
def test_llmtoolbridge_rejects_messages_without_tool_calls(
    message: LlmMessage,
) -> None:
    """
        **Validates: Requirements 11.5**

        For any LlmMessage whose metadata does not contain a 'tool_calls'
        key or contains an empty list, message_to_tool_calls() shall raise
        SemanticError.
    """
    bridge = LlmToolBridge()

    raised = False
    try:
        bridge.message_to_tool_calls(message)
    except SemanticError:
        raised = True

    assert raised is True, (
        "message_to_tool_calls should raise SemanticError for message "
        "without valid tool calls, metadata was: {}".format(message.metadata)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
