"""
    Property-based tests for the ccai.agentkit.toolresult module.

    Contains property-based tests (using ccai.testbase.properties) for the ToolResult class,
    validating is_success status reflection and field/as_dict correctness.

    Feature: tool-capability-system
"""


from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.agentkit.toolresult import ToolResult


# ---------------------------------------------------------------------------
# testbase property strategies for generating ToolResult inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid tool name strings
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating status values
status_strategy = st.sampled_from([ToolResult.STATUS_SUCCESS, ToolResult.STATUS_FAILURE])

# Strategy for generating optional output dictionaries
output_strategy = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(
            alphabet=st.characters(categories=("L", "N")),
            min_size=1,
            max_size=15
        ),
        values=st.one_of(
            st.text(min_size=0, max_size=20),
            st.integers(min_value=-1000, max_value=1000),
            st.booleans()
        ),
        max_size=5
    )
)

# Strategy for generating non-negative duration floats
duration_strategy = st.floats(
    min_value=0.0,
    max_value=10000.0
)

# Strategy for generating optional exceptions
error_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=50).map(RuntimeError),
    st.text(min_size=1, max_size=50).map(ValueError),
    st.text(min_size=1, max_size=50).map(FileNotFoundError),
)


# ---------------------------------------------------------------------------
# Property 15: ToolResult is_success reflects status
# Feature: tool-capability-system, Property 15: ToolResult is_success reflects status
# **Validates: Requirements 6.3**
# ---------------------------------------------------------------------------

@given(
    tool_name=tool_name_strategy,
    status=status_strategy,
    output=output_strategy,
    duration=duration_strategy,
    constraints={"max_examples": 100})
def test_property_15_is_success_reflects_status(tool_name, status, output, duration):
    """
        Property 15: ToolResult is_success reflects status.

        For any ToolResult instance, is_success returns True when status
        is "success" and False when status is "failure".

        **Validates: Requirements 6.3**
    """
    if status == ToolResult.STATUS_SUCCESS:
        result = ToolResult(
            tool_name=tool_name,
            status=status,
            output=output,
            duration=duration,
            error=None,
        )
    else:
        error = RuntimeError("test failure")
        result = ToolResult(
            tool_name=tool_name,
            status=status,
            output=None,
            duration=duration,
            error=error,
        )

    if status == ToolResult.STATUS_SUCCESS:
        assert result.is_success is True, (
            "is_success should be True for status '{}', got: {!r}".format(
                status, result.is_success
            )
        )
    else:
        assert result.is_success is False, (
            "is_success should be False for status '{}', got: {!r}".format(
                status, result.is_success
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 16: ToolResult fields and as_dict correctness
# Feature: tool-capability-system, Property 16: ToolResult fields and as_dict correctness
# **Validates: Requirements 6.1, 6.2, 6.4**
# ---------------------------------------------------------------------------

@given(
    tool_name=tool_name_strategy,
    status=status_strategy,
    output=output_strategy,
    duration=duration_strategy,
    error=error_strategy,
    constraints={"max_examples": 100})
def test_property_16_fields_and_as_dict_correctness(tool_name, status, output, duration, error):
    """
        Property 16: ToolResult fields and as_dict correctness.

        For any ToolResult instance, all fields (tool_name, status, output,
        duration, error) are accessible as read-only properties, and as_dict()
        returns a dictionary containing these fields with matching values.

        **Validates: Requirements 6.1, 6.2, 6.4**
    """
    result = ToolResult(
        tool_name=tool_name,
        status=status,
        output=output,
        duration=duration,
        error=error,
    )

    # Verify all fields are accessible as properties
    assert result.tool_name == tool_name, (
        "tool_name mismatch: {!r} != {!r}".format(result.tool_name, tool_name)
    )
    assert result.status == status, (
        "status mismatch: {!r} != {!r}".format(result.status, status)
    )
    assert result.output == output, (
        "output mismatch: {!r} != {!r}".format(result.output, output)
    )
    assert result.duration == duration, (
        "duration mismatch: {!r} != {!r}".format(result.duration, duration)
    )
    assert result.error is error, (
        "error mismatch: {!r} is not {!r}".format(result.error, error)
    )

    # Verify as_dict returns correct values
    result_dict = result.as_dict()

    assert result_dict["tool_name"] == tool_name, (
        "as_dict tool_name mismatch: {!r} != {!r}".format(
            result_dict["tool_name"], tool_name
        )
    )
    assert result_dict["status"] == status, (
        "as_dict status mismatch: {!r} != {!r}".format(
            result_dict["status"], status
        )
    )
    assert result_dict["output"] == output, (
        "as_dict output mismatch: {!r} != {!r}".format(
            result_dict["output"], output
        )
    )
    assert result_dict["duration"] == duration, (
        "as_dict duration mismatch: {!r} != {!r}".format(
            result_dict["duration"], duration
        )
    )

    # Verify error serialization in as_dict
    if error is not None:
        expected_error_value = str(error)
        assert result_dict["error"] == expected_error_value, (
            "as_dict error mismatch: {!r} != {!r}".format(
                result_dict["error"], expected_error_value
            )
        )
    else:
        assert result_dict["error"] is None, (
            "as_dict error should be None when no error, got: {!r}".format(
                result_dict["error"]
            )
        )

    return


# ---------------------------------------------------------------------------
# Unit tests for ToolResult
# ---------------------------------------------------------------------------


def test_toolresult_success_with_none_output():
    """
        A ToolResult with success status and None output correctly
        stores and exposes all fields.

        **Validates: Requirements 6.1, 6.2, 6.5**
    """
    result = ToolResult(
        tool_name="my_tool",
        status=ToolResult.STATUS_SUCCESS,
        output=None,
        duration=0.5,
        error=None,
    )

    assert result.tool_name == "my_tool", (
        "tool_name mismatch: {!r}".format(result.tool_name)
    )
    assert result.status == ToolResult.STATUS_SUCCESS, (
        "status mismatch: {!r}".format(result.status)
    )
    assert result.output is None, (
        "output should be None, got: {!r}".format(result.output)
    )
    assert result.duration == 0.5, (
        "duration mismatch: {!r}".format(result.duration)
    )
    assert result.error is None, (
        "error should be None, got: {!r}".format(result.error)
    )
    assert result.is_success is True, (
        "is_success should be True for success status"
    )

    return


def test_toolresult_failure_with_error():
    """
        A ToolResult with failure status and an error correctly
        stores and exposes all fields including the error.

        **Validates: Requirements 6.1, 6.2, 6.5, 6.6**
    """
    error = RuntimeError("Something went wrong")
    result = ToolResult(
        tool_name="failing_tool",
        status=ToolResult.STATUS_FAILURE,
        output=None,
        duration=1.234,
        error=error,
    )

    assert result.tool_name == "failing_tool", (
        "tool_name mismatch: {!r}".format(result.tool_name)
    )
    assert result.status == ToolResult.STATUS_FAILURE, (
        "status mismatch: {!r}".format(result.status)
    )
    assert result.output is None, (
        "output should be None for failure, got: {!r}".format(result.output)
    )
    assert result.duration == 1.234, (
        "duration mismatch: {!r}".format(result.duration)
    )
    assert result.error is error, (
        "error should be the same exception instance"
    )
    assert result.is_success is False, (
        "is_success should be False for failure status"
    )

    return


def test_toolresult_repr_output():
    """
        ToolResult __repr__ returns a string in the format
        "ToolResult(tool_name='...', status='...')".

        **Validates: Requirements 18.7**
    """
    result = ToolResult(
        tool_name="test_tool",
        status=ToolResult.STATUS_SUCCESS,
        output={"key": "value"},
        duration=0.123,
    )

    repr_str = repr(result)
    assert repr_str == "ToolResult(tool_name='test_tool', status='success')", (
        "repr mismatch: {!r}".format(repr_str)
    )

    return


def test_toolresult_repr_failure():
    """
        ToolResult __repr__ correctly reflects failure status.

        **Validates: Requirements 18.7**
    """
    error = ValueError("bad input")
    result = ToolResult(
        tool_name="bad_tool",
        status=ToolResult.STATUS_FAILURE,
        output=None,
        duration=0.0,
        error=error,
    )

    repr_str = repr(result)
    assert repr_str == "ToolResult(tool_name='bad_tool', status='failure')", (
        "repr mismatch for failure: {!r}".format(repr_str)
    )

    return


def test_toolresult_str_output():
    """
        ToolResult __str__ returns a string in the format
        "ToolResult: tool_name - status (duration: X.XXXs)".

        **Validates: Requirements 18.8**
    """
    result = ToolResult(
        tool_name="my_tool",
        status=ToolResult.STATUS_SUCCESS,
        output={"result": 42},
        duration=2.567,
    )

    str_output = str(result)
    assert str_output == "ToolResult: my_tool - success (duration: 2.567s)", (
        "str mismatch: {!r}".format(str_output)
    )

    return


def test_toolresult_str_zero_duration():
    """
        ToolResult __str__ correctly formats zero duration.

        **Validates: Requirements 18.8**
    """
    result = ToolResult(
        tool_name="quick_tool",
        status=ToolResult.STATUS_SUCCESS,
        output=None,
        duration=0.0,
    )

    str_output = str(result)
    assert str_output == "ToolResult: quick_tool - success (duration: 0.000s)", (
        "str with zero duration mismatch: {!r}".format(str_output)
    )

    return


def test_toolresult_default_duration_and_optional_params():
    """
        ToolResult uses default values for optional parameters
        (output=None, duration=0.0, error=None).

        **Validates: Requirements 6.1, 6.2**
    """
    result = ToolResult(
        tool_name="minimal_tool",
        status=ToolResult.STATUS_SUCCESS,
    )

    assert result.output is None, (
        "Default output should be None, got: {!r}".format(result.output)
    )
    assert result.duration == 0.0, (
        "Default duration should be 0.0, got: {!r}".format(result.duration)
    )
    assert result.error is None, (
        "Default error should be None, got: {!r}".format(result.error)
    )

    return


def test_toolresult_status_constants():
    """
        ToolResult class constants STATUS_SUCCESS and STATUS_FAILURE
        have the expected string values.

        **Validates: Requirements 6.1**
    """
    assert ToolResult.STATUS_SUCCESS == "success", (
        "STATUS_SUCCESS mismatch: {!r}".format(ToolResult.STATUS_SUCCESS)
    )
    assert ToolResult.STATUS_FAILURE == "failure", (
        "STATUS_FAILURE mismatch: {!r}".format(ToolResult.STATUS_FAILURE)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
