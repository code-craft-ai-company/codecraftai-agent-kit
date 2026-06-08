"""
    Unit tests for the ccai.agentkit.toolfactory module.

    Contains unit tests for the create_tool factory function, verifying
    tool creation with various schema configurations, execute delegation,
    and metadata correctness.

    Feature: tool-capability-system
"""

from ccai.agentkit.tool import Tool
from ccai.agentkit.toolfactory import create_tool
from ccai.agentkit.toolschema import ToolSchema


# ---------------------------------------------------------------------------
# Unit tests for create_tool factory function
# Feature: tool-capability-system, Task 4.4
# **Validates: Requirements 12.6**
# ---------------------------------------------------------------------------


def _noop_execute(inputs, credentials):
    """
        A no-op execute callable for testing.

        :param inputs: The input dictionary.
        :param credentials: The credentials dictionary.

        :returns: An empty dictionary.
    """
    rtnval = {}
    return rtnval


def test_create_tool_returns_tool_instance():
    """
        create_tool returns an object that is an instance of Tool.

        **Validates: Requirements 12.6**
    """
    input_schema = {"parameters": []}
    output_schema = {"parameters": []}

    tool = create_tool(
        name="factory_tool",
        description="A factory-created tool",
        input_schema=input_schema,
        output_schema=output_schema,
        execute_fn=_noop_execute,
    )

    is_tool = isinstance(tool, Tool)
    assert is_tool is True, (
        "create_tool should return a Tool instance, got: {}".format(
            type(tool).__name__
        )
    )

    return


def test_create_tool_with_input_and_output_schemas():
    """
        create_tool correctly converts input and output schema dictionaries
        to ToolSchema instances.

        **Validates: Requirements 12.6**
    """
    input_schema = {
        "parameters": [
            {"name": "query", "type": "string", "required": True},
            {"name": "limit", "type": "integer", "required": False, "default": 10},
        ]
    }
    output_schema = {
        "parameters": [
            {"name": "results", "type": "list", "required": True},
            {"name": "count", "type": "integer", "required": True},
        ]
    }

    tool = create_tool(
        name="search_tool",
        description="Searches for items",
        input_schema=input_schema,
        output_schema=output_schema,
        execute_fn=_noop_execute,
    )

    assert isinstance(tool.input_schema, ToolSchema), (
        "input_schema should be a ToolSchema instance"
    )
    assert isinstance(tool.output_schema, ToolSchema), (
        "output_schema should be a ToolSchema instance"
    )
    assert tool.input_schema.parameter_count == 2, (
        "input_schema should have 2 parameters, got: {}".format(
            tool.input_schema.parameter_count
        )
    )
    assert tool.output_schema.parameter_count == 2, (
        "output_schema should have 2 parameters, got: {}".format(
            tool.output_schema.parameter_count
        )
    )

    return


def test_create_tool_with_empty_schemas():
    """
        create_tool works with empty parameter lists in schemas.

        **Validates: Requirements 12.6**
    """
    input_schema = {"parameters": []}
    output_schema = {"parameters": []}

    tool = create_tool(
        name="empty_schema_tool",
        description="Tool with empty schemas",
        input_schema=input_schema,
        output_schema=output_schema,
        execute_fn=_noop_execute,
    )

    assert tool.input_schema.parameter_count == 0, (
        "input_schema should have 0 parameters"
    )
    assert tool.output_schema.parameter_count == 0, (
        "output_schema should have 0 parameters"
    )

    return


def test_create_tool_metadata_matches_arguments():
    """
        create_tool produces a Tool whose name, description, and version
        match the provided arguments.

        **Validates: Requirements 12.6**
    """
    tool = create_tool(
        name="meta_tool",
        description="Metadata test tool",
        input_schema={"parameters": []},
        output_schema={"parameters": []},
        execute_fn=_noop_execute,
        version="2.5.0",
    )

    assert tool.name == "meta_tool", (
        "name mismatch: {!r}".format(tool.name)
    )
    assert tool.description == "Metadata test tool", (
        "description mismatch: {!r}".format(tool.description)
    )
    assert tool.version == "2.5.0", (
        "version mismatch: {!r}".format(tool.version)
    )

    return


def test_create_tool_default_version():
    """
        create_tool defaults the version to '1.0.0' when not specified.

        **Validates: Requirements 12.6**
    """
    tool = create_tool(
        name="default_version_tool",
        description="Default version test",
        input_schema={"parameters": []},
        output_schema={"parameters": []},
        execute_fn=_noop_execute,
    )

    assert tool.version == "1.0.0", (
        "Default version should be '1.0.0', got: {!r}".format(tool.version)
    )

    return


def test_create_tool_with_tags():
    """
        create_tool passes tags through to the Tool instance.

        **Validates: Requirements 12.6**
    """
    tags = {"category": "search", "priority": "high"}

    tool = create_tool(
        name="tagged_tool",
        description="Tagged tool",
        input_schema={"parameters": []},
        output_schema={"parameters": []},
        execute_fn=_noop_execute,
        tags=tags,
    )

    assert tool.tags == tags, (
        "tags mismatch: {!r}".format(tool.tags)
    )

    return


def test_create_tool_default_tags_is_empty():
    """
        create_tool defaults tags to an empty dict when not specified.

        **Validates: Requirements 12.6**
    """
    tool = create_tool(
        name="no_tags_tool",
        description="No tags",
        input_schema={"parameters": []},
        output_schema={"parameters": []},
        execute_fn=_noop_execute,
    )

    assert tool.tags == {}, (
        "Default tags should be empty dict, got: {!r}".format(tool.tags)
    )

    return


def test_create_tool_execute_delegates_to_callable():
    """
        The Tool created by create_tool delegates its execute method
        to the provided callable.

        **Validates: Requirements 12.6**
    """
    call_tracker = {"called": False}

    def tracking_execute(inputs, credentials):
        """
            Tracks invocation and returns inputs as output.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: The inputs dictionary as output.
        """
        call_tracker["called"] = True
        rtnval = {"echo": inputs.get("message", "")}
        return rtnval

    tool = create_tool(
        name="delegate_tool",
        description="Delegation test",
        input_schema={"parameters": [
            {"name": "message", "type": "string", "required": True}
        ]},
        output_schema={"parameters": [
            {"name": "echo", "type": "string", "required": True}
        ]},
        execute_fn=tracking_execute,
    )

    result = tool.execute(
        inputs={"message": "hello"},
        credentials=None,
    )

    assert call_tracker["called"] is True, (
        "execute_fn should have been called"
    )
    assert result == {"echo": "hello"}, (
        "execute should return the output from execute_fn, got: {!r}".format(result)
    )

    return


def test_create_tool_execute_passes_credentials():
    """
        The Tool created by create_tool passes credentials through to
        the execute callable.

        **Validates: Requirements 12.6**
    """
    received = {"credentials": None}

    def cred_execute(inputs, credentials):
        """
            Records the received credentials.

            :param inputs: The input dictionary.
            :param credentials: The credentials dictionary.

            :returns: An empty dictionary.
        """
        received["credentials"] = credentials
        rtnval = {}
        return rtnval

    tool = create_tool(
        name="cred_tool",
        description="Credential pass-through test",
        input_schema={"parameters": []},
        output_schema={"parameters": []},
        execute_fn=cred_execute,
    )

    test_creds = {"api_key": "secret123"}
    tool.execute(inputs={}, credentials=test_creds)

    assert received["credentials"] == test_creds, (
        "execute_fn should receive the credentials, got: {!r}".format(
            received["credentials"]
        )
    )

    return


def test_create_tool_with_complex_schema():
    """
        create_tool works with schemas containing multiple parameter types
        including string, integer, float, boolean, list, and dictionary.

        **Validates: Requirements 12.6**
    """
    input_schema = {
        "parameters": [
            {"name": "name", "type": "string", "required": True},
            {"name": "count", "type": "integer", "required": True},
            {"name": "ratio", "type": "float", "required": False, "default": 1.0},
            {"name": "enabled", "type": "boolean", "required": False, "default": True},
            {"name": "items", "type": "list", "required": False},
            {"name": "metadata", "type": "dictionary", "required": False},
        ]
    }
    output_schema = {
        "parameters": [
            {"name": "status", "type": "string", "required": True},
        ]
    }

    tool = create_tool(
        name="complex_tool",
        description="Complex schema tool",
        input_schema=input_schema,
        output_schema=output_schema,
        execute_fn=_noop_execute,
    )

    assert tool.input_schema.parameter_count == 6, (
        "input_schema should have 6 parameters, got: {}".format(
            tool.input_schema.parameter_count
        )
    )
    assert tool.output_schema.parameter_count == 1, (
        "output_schema should have 1 parameter, got: {}".format(
            tool.output_schema.parameter_count
        )
    )

    return
