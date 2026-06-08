"""
    Unit tests for the ccai.agentkit.llmtoolbridge module.

    Tests LLMToolBridge descriptors_to_functions, message_to_tool_calls,
    and tool_result_to_message methods with various ToolDescriptor schemas,
    valid and invalid LLMMessage metadata, and ToolResult conversions.

    Feature: llm-integration, Task 14.3
    **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**
"""

import json

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.llmtoolbridge import LLMToolBridge
from ccai.agentkit.tooldescriptor import ToolDescriptor
from ccai.agentkit.toolresult import ToolResult
from ccai.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _make_descriptor(name, description, params=None):
    """
        Creates a ToolDescriptor with the given name, description, and
        optional parameter definitions for the input schema.
    """
    if params is not None:
        input_schema = ToolSchema(parameters=params)
    else:
        input_schema = None

    rtnval = ToolDescriptor(
        name=name,
        description=description,
        version="1.0.0",
        input_schema=input_schema,
        output_schema=None,
    )
    return rtnval


# ---------------------------------------------------------------------------
# descriptors_to_functions - empty list
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_empty_list():
    """
        Converting an empty descriptor list returns an empty function list.

        **Validates: Requirements 11.1**
    """
    bridge = LLMToolBridge()

    result = bridge.descriptors_to_functions([])

    assert result == [], (
        "Expected empty list, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - string parameter
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_string_param():
    """
        A descriptor with a string parameter converts to JSON Schema type "string".

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [{"name": "query", "type": "string", "required": True, "description": "Search query"}]
    descriptor = _make_descriptor("search", "Search tool", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    assert len(result) == 1, "Expected 1 function definition"

    func_def = result[0]
    assert func_def["type"] == "function"
    assert func_def["function"]["name"] == "search"
    assert func_def["function"]["description"] == "Search tool"

    props = func_def["function"]["parameters"]["properties"]
    assert "query" in props, "Expected 'query' in properties"
    assert props["query"]["type"] == "string"
    assert props["query"]["description"] == "Search query"

    required = func_def["function"]["parameters"]["required"]
    assert "query" in required, "Expected 'query' in required list"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - integer parameter
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_integer_param():
    """
        A descriptor with an integer parameter converts to JSON Schema type "integer".

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [{"name": "count", "type": "integer", "required": True}]
    descriptor = _make_descriptor("counter", "Count tool", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    props = func_def["function"]["parameters"]["properties"]
    assert props["count"]["type"] == "integer"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - float parameter
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_float_param():
    """
        A descriptor with a float parameter converts to JSON Schema type "number".

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [{"name": "temperature", "type": "float", "required": True}]
    descriptor = _make_descriptor("sampler", "Sampler tool", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    props = func_def["function"]["parameters"]["properties"]
    assert props["temperature"]["type"] == "number"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - boolean parameter
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_boolean_param():
    """
        A descriptor with a boolean parameter converts to JSON Schema type "boolean".

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [{"name": "verbose", "type": "boolean", "required": False}]
    descriptor = _make_descriptor("logger", "Logger tool", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    props = func_def["function"]["parameters"]["properties"]
    assert props["verbose"]["type"] == "boolean"

    required = func_def["function"]["parameters"]["required"]
    assert "verbose" not in required, "Optional param should not be in required"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - list parameter
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_list_param():
    """
        A descriptor with a list parameter converts to JSON Schema type "array".

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [{"name": "items", "type": "list", "required": True}]
    descriptor = _make_descriptor("batch", "Batch tool", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    props = func_def["function"]["parameters"]["properties"]
    assert props["items"]["type"] == "array"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - dictionary parameter
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_dictionary_param():
    """
        A descriptor with a dictionary parameter converts to JSON Schema type "object".

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [{"name": "config", "type": "dictionary", "required": True}]
    descriptor = _make_descriptor("configurator", "Config tool", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    props = func_def["function"]["parameters"]["properties"]
    assert props["config"]["type"] == "object"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - no input schema (None)
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_no_input_schema():
    """
        A descriptor with no input schema produces a function definition
        with empty properties and required lists.

        **Validates: Requirements 11.1, 11.4**
    """
    bridge = LLMToolBridge()
    descriptor = _make_descriptor("simple", "Simple tool", params=None)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    assert func_def["function"]["name"] == "simple"
    assert func_def["function"]["parameters"]["properties"] == {}
    assert func_def["function"]["parameters"]["required"] == []

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - multiple parameters
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_multiple_params():
    """
        A descriptor with multiple parameters of different types converts
        all parameter names and types correctly.

        **Validates: Requirements 11.1, 11.4, 11.6**
    """
    bridge = LLMToolBridge()
    params = [
        {"name": "query", "type": "string", "required": True, "description": "The query"},
        {"name": "limit", "type": "integer", "required": False},
        {"name": "exact", "type": "boolean", "required": True},
    ]
    descriptor = _make_descriptor("search", "Multi-param search", params=params)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    props = func_def["function"]["parameters"]["properties"]
    required = func_def["function"]["parameters"]["required"]

    assert len(props) == 3, "Expected 3 properties"
    assert props["query"]["type"] == "string"
    assert props["limit"]["type"] == "integer"
    assert props["exact"]["type"] == "boolean"

    assert "query" in required
    assert "exact" in required
    assert "limit" not in required

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - multiple descriptors
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_multiple_descriptors():
    """
        Converting multiple descriptors returns one function definition per descriptor.

        **Validates: Requirements 11.1, 11.6**
    """
    bridge = LLMToolBridge()
    desc_a = _make_descriptor("tool_a", "Tool A", params=[{"name": "x", "type": "string", "required": True}])
    desc_b = _make_descriptor("tool_b", "Tool B", params=[{"name": "y", "type": "integer", "required": True}])

    result = bridge.descriptors_to_functions([desc_a, desc_b])

    assert len(result) == 2, "Expected 2 function definitions"
    assert result[0]["function"]["name"] == "tool_a"
    assert result[1]["function"]["name"] == "tool_b"

    return


# ---------------------------------------------------------------------------
# descriptors_to_functions - preserves name and description
# ---------------------------------------------------------------------------


def test_descriptors_to_functions_preserves_name_and_description():
    """
        The function definition preserves the tool name and description
        from the original ToolDescriptor.

        **Validates: Requirements 11.6**
    """
    bridge = LLMToolBridge()
    descriptor = _make_descriptor("my_tool", "A detailed description of my tool", params=None)

    result = bridge.descriptors_to_functions([descriptor])

    func_def = result[0]
    assert func_def["function"]["name"] == "my_tool", (
        "Function name should match descriptor name"
    )
    assert func_def["function"]["description"] == "A detailed description of my tool", (
        "Function description should match descriptor description"
    )

    return


# ---------------------------------------------------------------------------
# message_to_tool_calls - valid tool calls
# ---------------------------------------------------------------------------


def test_message_to_tool_calls_valid():
    """
        Extracting tool calls from a message with valid tool_calls metadata
        returns the correct tool name and arguments.

        **Validates: Requirements 11.2**
    """
    bridge = LLMToolBridge()
    metadata = {
        "tool_calls": [
            {
                "function": {
                    "name": "search",
                    "arguments": {"query": "hello"}
                }
            }
        ]
    }
    message = LLMMessage(role="assistant", content="", metadata=metadata)

    result = bridge.message_to_tool_calls(message)

    assert len(result) == 1, "Expected 1 tool call"
    assert result[0]["tool_name"] == "search"
    assert result[0]["arguments"] == {"query": "hello"}

    return


# ---------------------------------------------------------------------------
# message_to_tool_calls - multiple tool calls
# ---------------------------------------------------------------------------


def test_message_to_tool_calls_multiple():
    """
        Extracting tool calls from a message with multiple tool_calls
        returns all tool calls in order.

        **Validates: Requirements 11.2**
    """
    bridge = LLMToolBridge()
    metadata = {
        "tool_calls": [
            {"function": {"name": "tool_a", "arguments": {"x": 1}}},
            {"function": {"name": "tool_b", "arguments": {"y": "abc"}}},
        ]
    }
    message = LLMMessage(role="assistant", content="", metadata=metadata)

    result = bridge.message_to_tool_calls(message)

    assert len(result) == 2, "Expected 2 tool calls"
    assert result[0]["tool_name"] == "tool_a"
    assert result[1]["tool_name"] == "tool_b"

    return


# ---------------------------------------------------------------------------
# message_to_tool_calls - missing arguments defaults to empty dict
# ---------------------------------------------------------------------------


def test_message_to_tool_calls_missing_arguments():
    """
        When a tool call has no 'arguments' key, the result defaults
        to an empty dictionary.

        **Validates: Requirements 11.2**
    """
    bridge = LLMToolBridge()
    metadata = {
        "tool_calls": [
            {"function": {"name": "no_args_tool"}}
        ]
    }
    message = LLMMessage(role="assistant", content="", metadata=metadata)

    result = bridge.message_to_tool_calls(message)

    assert result[0]["arguments"] == {}, (
        "Missing arguments should default to empty dict"
    )

    return


# ---------------------------------------------------------------------------
# message_to_tool_calls - no tool_calls raises SemanticError
# ---------------------------------------------------------------------------


def test_message_to_tool_calls_no_tool_calls_raises():
    """
        Calling message_to_tool_calls on a message without tool_calls
        metadata raises SemanticError.

        **Validates: Requirements 11.5**
    """
    bridge = LLMToolBridge()
    message = LLMMessage(role="assistant", content="Hello", metadata={})

    caught = False
    try:
        bridge.message_to_tool_calls(message)
    except SemanticError:
        caught = True

    assert caught is True, (
        "Expected SemanticError for message without tool_calls"
    )

    return


# ---------------------------------------------------------------------------
# message_to_tool_calls - empty tool_calls list raises SemanticError
# ---------------------------------------------------------------------------


def test_message_to_tool_calls_empty_list_raises():
    """
        Calling message_to_tool_calls on a message with an empty tool_calls
        list raises SemanticError.

        **Validates: Requirements 11.5**
    """
    bridge = LLMToolBridge()
    metadata = {"tool_calls": []}
    message = LLMMessage(role="assistant", content="", metadata=metadata)

    caught = False
    try:
        bridge.message_to_tool_calls(message)
    except SemanticError:
        caught = True

    assert caught is True, (
        "Expected SemanticError for empty tool_calls list"
    )

    return


# ---------------------------------------------------------------------------
# message_to_tool_calls - no metadata raises SemanticError
# ---------------------------------------------------------------------------


def test_message_to_tool_calls_no_metadata_raises():
    """
        Calling message_to_tool_calls on a message with no metadata
        (defaults to empty dict) raises SemanticError.

        **Validates: Requirements 11.5**
    """
    bridge = LLMToolBridge()
    message = LLMMessage(role="assistant", content="Hello")

    caught = False
    try:
        bridge.message_to_tool_calls(message)
    except SemanticError:
        caught = True

    assert caught is True, (
        "Expected SemanticError for message with no metadata"
    )

    return


# ---------------------------------------------------------------------------
# tool_result_to_message - success result with output
# ---------------------------------------------------------------------------


def test_tool_result_to_message_success():
    """
        Converting a successful ToolResult produces an LLMMessage with
        role "tool", JSON content from as_dict, and tool_name in metadata.

        **Validates: Requirements 11.3**
    """
    bridge = LLMToolBridge()
    result = ToolResult(
        tool_name="search",
        status=ToolResult.STATUS_SUCCESS,
        output={"results": ["a", "b"]},
        duration=0.5,
    )

    message = bridge.tool_result_to_message("search", result)

    assert message.role == "tool", (
        "Expected role 'tool', got: {!r}".format(message.role)
    )
    assert message.metadata.get("tool_name") == "search", (
        "Expected tool_name 'search' in metadata"
    )

    content_data = json.loads(message.content)
    assert content_data["tool_name"] == "search"
    assert content_data["status"] == "success"
    assert content_data["output"] == {"results": ["a", "b"]}

    return


# ---------------------------------------------------------------------------
# tool_result_to_message - failure result
# ---------------------------------------------------------------------------


def test_tool_result_to_message_failure():
    """
        Converting a failed ToolResult produces an LLMMessage with
        role "tool" and the error information in the content.

        **Validates: Requirements 11.3**
    """
    bridge = LLMToolBridge()
    result = ToolResult(
        tool_name="broken",
        status=ToolResult.STATUS_FAILURE,
        output={"error_detail": "something went wrong"},
        duration=1.0,
        error=RuntimeError("something went wrong"),
    )

    message = bridge.tool_result_to_message("broken", result)

    assert message.role == "tool"
    assert message.metadata.get("tool_name") == "broken"

    content_data = json.loads(message.content)
    assert content_data["status"] == "failure"

    return


# ---------------------------------------------------------------------------
# tool_result_to_message - None output
# ---------------------------------------------------------------------------


def test_tool_result_to_message_none_output():
    """
        Converting a ToolResult with None output produces an LLMMessage
        with empty string content.

        **Validates: Requirements 11.3**
    """
    bridge = LLMToolBridge()
    result = ToolResult(
        tool_name="void_tool",
        status=ToolResult.STATUS_SUCCESS,
        output=None,
        duration=0.1,
    )

    message = bridge.tool_result_to_message("void_tool", result)

    assert message.role == "tool"
    assert message.content == "", (
        "Expected empty content for None output, got: {!r}".format(message.content)
    )
    assert message.metadata.get("tool_name") == "void_tool"

    return


# ---------------------------------------------------------------------------
# TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA mapping completeness
# ---------------------------------------------------------------------------


def test_type_mapping_covers_all_tool_schema_types():
    """
        The TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA mapping covers all types
        defined in ToolSchema.SUPPORTED_TYPES.

        **Validates: Requirements 11.4**
    """
    bridge = LLMToolBridge()
    mapping = bridge.TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA

    expected_types = {"string", "integer", "float", "boolean", "list", "dictionary"}

    for tool_type in expected_types:
        assert tool_type in mapping, (
            "Missing mapping for tool type: {!r}".format(tool_type)
        )

    return


def test_type_mapping_values():
    """
        Each tool schema type maps to the correct JSON Schema type.

        **Validates: Requirements 11.4**
    """
    bridge = LLMToolBridge()
    mapping = bridge.TOOL_SCHEMA_TYPE_TO_JSON_SCHEMA

    expected = {
        "string": "string",
        "integer": "integer",
        "float": "number",
        "boolean": "boolean",
        "list": "array",
        "dictionary": "object",
    }

    for tool_type, json_type in expected.items():
        assert mapping[tool_type] == json_type, (
            "Expected {!r} -> {!r}, got {!r}".format(tool_type, json_type, mapping[tool_type])
        )

    return
