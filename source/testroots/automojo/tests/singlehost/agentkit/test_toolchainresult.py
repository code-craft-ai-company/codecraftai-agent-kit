"""
    Property-based tests for the automojo.agentkit.toolchainresult module.

    Contains property-based tests (using automojo.testbase.properties) for the ToolChainResult
    class, validating is_success status reflection and field/as_dict correctness.

    Feature: tool-capability-system
"""


from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.agentkit.toolchainresult import ToolChainResult
from automojo.agentkit.toolresult import ToolResult


# ---------------------------------------------------------------------------
# testbase property strategies for generating ToolChainResult inputs
# ---------------------------------------------------------------------------

# Strategy for generating valid chain name strings
chain_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating status values
status_strategy = st.sampled_from([
    ToolChainResult.STATUS_SUCCESS,
    ToolChainResult.STATUS_FAILURE,
])

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
    st.text(min_size=1, max_size=50).map(lambda msg: RuntimeError(msg)),
    st.text(min_size=1, max_size=50).map(lambda msg: ValueError(msg)),
)

# Strategy for generating a valid tool name for ToolResult
tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating a single ToolResult
tool_result_strategy = st.builds(
    ToolResult,
    tool_name=tool_name_strategy,
    status=st.sampled_from([ToolResult.STATUS_SUCCESS, ToolResult.STATUS_FAILURE]),
    output=st.one_of(
        st.none(),
        st.dictionaries(
            keys=st.text(
                alphabet=st.characters(categories=("L", "N")),
                min_size=1,
                max_size=10
            ),
            values=st.one_of(
                st.text(min_size=0, max_size=10),
                st.integers(min_value=-100, max_value=100),
            ),
            max_size=3
        )
    ),
    duration=st.floats(
        min_value=0.0,
        max_value=100.0
    ),
    error=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=20).map(lambda msg: RuntimeError(msg)),
    ),
)

# Strategy for generating a list of ToolResult objects
step_results_strategy = st.lists(
    tool_result_strategy,
    min_size=0,
    max_size=5
)


# ---------------------------------------------------------------------------
# Property 22: ToolChainResult is_success reflects status
# Feature: tool-capability-system, Property 22: ToolChainResult is_success reflects status
# **Validates: Requirements 8.3**
# ---------------------------------------------------------------------------

@given(
    chain_name=chain_name_strategy,
    status=status_strategy,
    output=output_strategy,
    step_results=step_results_strategy,
    duration=duration_strategy,
    constraints={"max_examples": 100})
def test_property_22_toolchainresult_is_success_reflects_status(
    chain_name, status, output, step_results, duration
):
    """
        Property 22: ToolChainResult is_success reflects status.

        For any ToolChainResult instance, is_success shall return True when
        status is "success" and False when status is "failure".

        **Validates: Requirements 8.3**
    """
    if status == ToolChainResult.STATUS_SUCCESS:
        result = ToolChainResult(
            chain_name=chain_name,
            status=status,
            output=output,
            step_results=step_results,
            duration=duration,
            error=None,
        )
    else:
        error = RuntimeError("chain failure")
        result = ToolChainResult(
            chain_name=chain_name,
            status=status,
            output=None,
            step_results=step_results,
            duration=duration,
            error=error,
        )

    if status == ToolChainResult.STATUS_SUCCESS:
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
# Property 23: ToolChainResult fields and as_dict correctness
# Feature: tool-capability-system, Property 23: ToolChainResult fields and as_dict correctness
# **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
# ---------------------------------------------------------------------------

@given(
    chain_name=chain_name_strategy,
    status=status_strategy,
    output=output_strategy,
    step_results=step_results_strategy,
    duration=duration_strategy,
    error=error_strategy,
    constraints={"max_examples": 100})
def test_property_23_toolchainresult_fields_and_as_dict_correctness(
    chain_name, status, output, step_results, duration, error
):
    """
        Property 23: ToolChainResult fields and as_dict correctness.

        For any ToolChainResult instance, all fields (chain_name, status,
        output, step_results, duration, error) shall be accessible as
        read-only properties, and as_dict() shall return a dictionary
        containing these fields with matching values.

        **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
    """
    result = ToolChainResult(
        chain_name=chain_name,
        status=status,
        output=output,
        step_results=step_results,
        duration=duration,
        error=error,
    )

    # Verify all fields are accessible as properties
    assert result.chain_name == chain_name, (
        "chain_name mismatch: {!r} != {!r}".format(result.chain_name, chain_name)
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

    # Verify step_results returns a list with the same length
    actual_step_results = result.step_results
    assert len(actual_step_results) == len(step_results), (
        "step_results length mismatch: {} != {}".format(
            len(actual_step_results), len(step_results)
        )
    )

    # Verify each step_result matches
    for idx in range(len(step_results)):
        expected_sr = step_results[idx]
        actual_sr = actual_step_results[idx]
        assert actual_sr.tool_name == expected_sr.tool_name, (
            "step_results[{}].tool_name mismatch: {!r} != {!r}".format(
                idx, actual_sr.tool_name, expected_sr.tool_name
            )
        )
        assert actual_sr.status == expected_sr.status, (
            "step_results[{}].status mismatch: {!r} != {!r}".format(
                idx, actual_sr.status, expected_sr.status
            )
        )

    # Verify as_dict returns correct values
    result_dict = result.as_dict()

    assert result_dict["chain_name"] == chain_name, (
        "as_dict chain_name mismatch: {!r} != {!r}".format(
            result_dict["chain_name"], chain_name
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

    # Verify step_results in as_dict
    assert len(result_dict["step_results"]) == len(step_results), (
        "as_dict step_results length mismatch: {} != {}".format(
            len(result_dict["step_results"]), len(step_results)
        )
    )

    for idx in range(len(step_results)):
        expected_sr = step_results[idx]
        actual_sr_dict = result_dict["step_results"][idx]
        assert actual_sr_dict["tool_name"] == expected_sr.tool_name, (
            "as_dict step_results[{}].tool_name mismatch".format(idx)
        )
        assert actual_sr_dict["status"] == expected_sr.status, (
            "as_dict step_results[{}].status mismatch".format(idx)
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
# Unit tests for ToolChainResult
# ---------------------------------------------------------------------------

def test_repr_format():
    """
        Verifies that __repr__ contains 'ToolChainResult', the chain name,
        and the status.

        **Validates: Requirements 8.6, 18.9**
    """
    result = ToolChainResult(
        chain_name="my_chain",
        status=ToolChainResult.STATUS_SUCCESS,
        output={"key": "val"},
        step_results=[],
        duration=1.5,
    )

    repr_str = repr(result)

    assert "ToolChainResult" in repr_str, (
        "__repr__ should contain 'ToolChainResult', got: {!r}".format(repr_str)
    )
    assert "my_chain" in repr_str, (
        "__repr__ should contain the chain name 'my_chain', got: {!r}".format(repr_str)
    )
    assert "success" in repr_str, (
        "__repr__ should contain the status 'success', got: {!r}".format(repr_str)
    )

    return


def test_str_format():
    """
        Verifies that __str__ contains the chain name, status, step count,
        and duration.

        **Validates: Requirements 8.7, 18.10**
    """
    step_result_a = ToolResult(
        tool_name="tool_a",
        status=ToolResult.STATUS_SUCCESS,
        output={"a": 1},
        duration=0.5,
    )
    step_result_b = ToolResult(
        tool_name="tool_b",
        status=ToolResult.STATUS_SUCCESS,
        output={"b": 2},
        duration=0.3,
    )

    result = ToolChainResult(
        chain_name="pipeline",
        status=ToolChainResult.STATUS_SUCCESS,
        output={"b": 2},
        step_results=[step_result_a, step_result_b],
        duration=0.8,
    )

    str_str = str(result)

    assert "pipeline" in str_str, (
        "__str__ should contain the chain name 'pipeline', got: {!r}".format(str_str)
    )
    assert "success" in str_str, (
        "__str__ should contain the status 'success', got: {!r}".format(str_str)
    )
    assert "2" in str_str, (
        "__str__ should contain the step count '2', got: {!r}".format(str_str)
    )
    assert "0.800" in str_str, (
        "__str__ should contain the duration '0.800', got: {!r}".format(str_str)
    )

    return


def test_empty_step_results():
    """
        Verifies that a ToolChainResult with an empty step_results list
        exposes an empty list and reports correct values in as_dict.

        **Validates: Requirements 8.1, 8.2, 8.4, 8.5**
    """
    result = ToolChainResult(
        chain_name="empty_chain",
        status=ToolChainResult.STATUS_FAILURE,
        output=None,
        step_results=[],
        duration=0.0,
        error=RuntimeError("no steps ran"),
    )

    actual_step_results = result.step_results
    assert actual_step_results == [], (
        "step_results should be an empty list, got: {!r}".format(actual_step_results)
    )

    assert result.is_success is False, (
        "is_success should be False for failure status"
    )

    result_dict = result.as_dict()
    assert result_dict["step_results"] == [], (
        "as_dict step_results should be an empty list, got: {!r}".format(
            result_dict["step_results"]
        )
    )
    assert result_dict["chain_name"] == "empty_chain", (
        "as_dict chain_name should be 'empty_chain', got: {!r}".format(
            result_dict["chain_name"]
        )
    )
    assert result_dict["error"] == "no steps ran", (
        "as_dict error should be 'no steps ran', got: {!r}".format(
            result_dict["error"]
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
