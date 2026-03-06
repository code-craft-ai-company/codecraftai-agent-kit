"""
    Property-based tests for tool exception field accessibility.

    Contains property-based tests (using automojo.testbase.properties) verifying that
    ToolValidationError and ToolExecutionError fields are accessible
    and match their constructor arguments.

    Feature: tool-capability-system
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.toolerrors import ToolValidationError
from automojo.agentkit.toolerrors import ToolExecutionError


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

tool_name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N")),
    min_size=1,
    max_size=30
).filter(lambda s: len(s.strip()) > 0)

direction_strategy = st.sampled_from(["input", "output"])

error_list_strategy = st.lists(
    st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z")),
        min_size=1,
        max_size=60,
    ),
    min_size=0,
    max_size=10,
)

cause_strategy = st.one_of(
    st.text(min_size=1, max_size=50).map(lambda msg: RuntimeError(msg)),
    st.text(min_size=1, max_size=50).map(lambda msg: ValueError(msg)),
    st.text(min_size=1, max_size=50).map(lambda msg: TypeError(msg)),
)


# ---------------------------------------------------------------------------
# Property 30: Tool exception fields are accessible
# Feature: tool-capability-system, Property 30
# **Validates: Requirements 15.2, 15.4**
# ---------------------------------------------------------------------------


@given(
    tool_name=tool_name_strategy,
    direction=direction_strategy,
    errors=error_list_strategy,
    settings=settings(max_examples=100),
)
def test_property_30_tool_validation_error_fields_accessible(tool_name, direction, errors):
    """
        Property 30 (ToolValidationError): tool_name, direction, and errors
        properties are accessible and match the constructor arguments.

        **Validates: Requirements 15.2**
    """
    error = ToolValidationError(
        tool_name=tool_name,
        direction=direction,
        errors=errors,
    )

    name_matches = error.tool_name == tool_name
    assert name_matches is True, (
        "tool_name mismatch: expected {!r}, got {!r}".format(tool_name, error.tool_name)
    )

    direction_matches = error.direction == direction
    assert direction_matches is True, (
        "direction mismatch: expected {!r}, got {!r}".format(direction, error.direction)
    )

    errors_match = error.errors == errors
    assert errors_match is True, (
        "errors mismatch: expected {!r}, got {!r}".format(errors, error.errors)
    )

    return


@given(
    tool_name=tool_name_strategy,
    cause=cause_strategy,
    settings=settings(max_examples=100),
)
def test_property_30_tool_execution_error_fields_accessible(tool_name, cause):
    """
        Property 30 (ToolExecutionError): tool_name and cause properties
        are accessible and match the constructor arguments.

        **Validates: Requirements 15.4**
    """
    error = ToolExecutionError(
        tool_name=tool_name,
        cause=cause,
    )

    name_matches = error.tool_name == tool_name
    assert name_matches is True, (
        "tool_name mismatch: expected {!r}, got {!r}".format(tool_name, error.tool_name)
    )

    cause_matches = error.cause is cause
    assert cause_matches is True, (
        "cause should be the same exception instance"
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
