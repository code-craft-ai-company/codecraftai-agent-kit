"""
    Unit tests for the ccai.agentkit.toolerrors module.

    Contains unit tests for ToolValidationError and ToolExecutionError,
    verifying field storage, property access, and __repr__ output.

    Feature: tool-capability-system
"""

from ccai.agentkit.errors import AgentKitError
from ccai.agentkit.toolerrors import ToolExecutionError
from ccai.agentkit.toolerrors import ToolValidationError


# ---------------------------------------------------------------------------
# Unit tests for ToolValidationError
# Feature: tool-capability-system, Task 1.4
# **Validates: Requirements 15.1, 15.2, 15.3, 15.5**
# ---------------------------------------------------------------------------


def test_tool_validation_error_inherits_from_agentkit_error():
    """
        ToolValidationError inherits from AgentKitError.

        **Validates: Requirements 15.1**
    """
    error = ToolValidationError(
        tool_name="test_tool",
        direction="input",
        errors=["Missing required parameter: 'name'"]
    )

    is_agentkit_error = isinstance(error, AgentKitError)
    assert is_agentkit_error is True, (
        "ToolValidationError should inherit from AgentKitError"
    )

    return


def test_tool_validation_error_fields():
    """
        ToolValidationError stores and exposes tool_name, direction, and
        errors through read-only properties.

        **Validates: Requirements 15.2**
    """
    error_list = [
        "Missing required parameter: 'name'",
        "Parameter 'age': expected type 'integer', got 'str'"
    ]
    error = ToolValidationError(
        tool_name="my_tool",
        direction="input",
        errors=error_list
    )

    assert error.tool_name == "my_tool", (
        "tool_name mismatch: {!r}".format(error.tool_name)
    )
    assert error.direction == "input", (
        "direction mismatch: {!r}".format(error.direction)
    )
    assert error.errors == error_list, (
        "errors mismatch: {!r}".format(error.errors)
    )

    return


def test_tool_validation_error_output_direction():
    """
        ToolValidationError works correctly with the 'output' direction.

        **Validates: Requirements 15.2**
    """
    error = ToolValidationError(
        tool_name="output_tool",
        direction="output",
        errors=["Parameter 'result': expected type 'string', got 'int'"]
    )

    assert error.direction == "output", (
        "direction should be 'output', got: {!r}".format(error.direction)
    )
    assert error.tool_name == "output_tool", (
        "tool_name mismatch: {!r}".format(error.tool_name)
    )

    return


def test_tool_validation_error_repr():
    """
        ToolValidationError __repr__ returns a string containing the class
        name, tool_name, direction, and error_count.

        **Validates: Requirements 15.5**
    """
    error = ToolValidationError(
        tool_name="repr_tool",
        direction="input",
        errors=["error one", "error two", "error three"]
    )

    repr_str = repr(error)
    expected = "ToolValidationError(tool_name='repr_tool', direction='input', error_count=3)"
    assert repr_str == expected, (
        "ToolValidationError repr mismatch: {!r}".format(repr_str)
    )

    return


def test_tool_validation_error_repr_empty_errors():
    """
        ToolValidationError __repr__ shows error_count=0 when no errors
        are provided.

        **Validates: Requirements 15.5**
    """
    error = ToolValidationError(
        tool_name="empty_tool",
        direction="output",
        errors=[]
    )

    repr_str = repr(error)
    expected = "ToolValidationError(tool_name='empty_tool', direction='output', error_count=0)"
    assert repr_str == expected, (
        "ToolValidationError repr with empty errors mismatch: {!r}".format(repr_str)
    )

    return


def test_tool_validation_error_errors_is_defensive_copy():
    """
        The errors property returns a copy of the internal errors list,
        so modifying the returned list does not affect the error object.

        **Validates: Requirements 15.2**
    """
    original_errors = ["error one"]
    error = ToolValidationError(
        tool_name="copy_tool",
        direction="input",
        errors=original_errors
    )

    returned_errors = error.errors
    returned_errors.append("extra error")

    assert len(error.errors) == 1, (
        "Modifying returned errors should not affect internal state, got length: {}".format(
            len(error.errors)
        )
    )

    return


# ---------------------------------------------------------------------------
# Unit tests for ToolExecutionError
# Feature: tool-capability-system, Task 1.4
# **Validates: Requirements 15.3, 15.4, 15.5**
# ---------------------------------------------------------------------------


def test_tool_execution_error_inherits_from_agentkit_error():
    """
        ToolExecutionError inherits from AgentKitError.

        **Validates: Requirements 15.3**
    """
    cause = RuntimeError("something went wrong")
    error = ToolExecutionError(tool_name="exec_tool", cause=cause)

    is_agentkit_error = isinstance(error, AgentKitError)
    assert is_agentkit_error is True, (
        "ToolExecutionError should inherit from AgentKitError"
    )

    return


def test_tool_execution_error_fields():
    """
        ToolExecutionError stores and exposes tool_name and cause through
        read-only properties.

        **Validates: Requirements 15.4**
    """
    cause = ValueError("invalid input value")
    error = ToolExecutionError(tool_name="field_tool", cause=cause)

    assert error.tool_name == "field_tool", (
        "tool_name mismatch: {!r}".format(error.tool_name)
    )
    assert error.cause is cause, (
        "cause should be the same exception instance"
    )

    return


def test_tool_execution_error_repr():
    """
        ToolExecutionError __repr__ returns a string containing the class
        name, tool_name, and cause.

        **Validates: Requirements 15.5**
    """
    cause = FileNotFoundError("file.txt not found")
    error = ToolExecutionError(tool_name="file_tool", cause=cause)

    repr_str = repr(error)
    expected = "ToolExecutionError(tool_name='file_tool', cause={!r})".format(cause)
    assert repr_str == expected, (
        "ToolExecutionError repr mismatch: {!r}".format(repr_str)
    )

    return


def test_tool_execution_error_message_contains_tool_name_and_cause():
    """
        ToolExecutionError message string includes both the tool name
        and the cause description.

        **Validates: Requirements 15.3, 15.5**
    """
    cause = PermissionError("access denied")
    error = ToolExecutionError(tool_name="perm_tool", cause=cause)

    error_message = str(error)

    tool_name_in_message = "perm_tool" in error_message
    assert tool_name_in_message is True, (
        "Error message should contain tool name, got: {!r}".format(error_message)
    )

    cause_in_message = "access denied" in error_message
    assert cause_in_message is True, (
        "Error message should contain cause text, got: {!r}".format(error_message)
    )

    return


def test_tool_validation_error_message_contains_tool_name():
    """
        ToolValidationError message string includes the tool name and
        direction.

        **Validates: Requirements 15.1, 15.5**
    """
    error = ToolValidationError(
        tool_name="msg_tool",
        direction="input",
        errors=["Missing required parameter: 'x'"]
    )

    error_message = str(error)

    tool_name_in_message = "msg_tool" in error_message
    assert tool_name_in_message is True, (
        "Error message should contain tool name, got: {!r}".format(error_message)
    )

    direction_in_message = "input" in error_message
    assert direction_in_message is True, (
        "Error message should contain direction, got: {!r}".format(error_message)
    )

    return
