"""
    Property-based tests for the automojo.agentkit.workflowcontext module.

    Uses automojo.testbase.properties to verify:
    - Property 1: WorkflowContext JSON Round-Trip

    **Validates: Requirement 5 AC 13**
"""

import json

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.workflowcontext import WorkflowContext


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_json_value = st.one_of(
    st.integers(-100, 100),
    st.text(min_size=0, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz")
)

_string_key = st.text(
    min_size=1,
    max_size=10,
    alphabet="abcdefghijklmnopqrstuvwxyz"
)

_inputs = st.dictionaries(
    keys=_string_key,
    values=_json_value,
    min_size=0,
    max_size=5,
)

_metadata = st.dictionaries(
    keys=_string_key,
    values=_json_value,
    min_size=0,
    max_size=5,
)

_step_outputs = st.dictionaries(
    keys=st.text(
        min_size=1,
        max_size=10,
        alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
    ),
    values=st.fixed_dictionaries({
        "val": st.integers(-100, 100),
    }),
    min_size=0,
    max_size=3,
)


# ---------------------------------------------------------------------------
# Property 1: WorkflowContext JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    inputs=_inputs,
    metadata=_metadata,
    step_outputs=_step_outputs,
    constraints={"max_examples": 100},
)
def test_workflowcontext_json_roundtrip(
    inputs: dict,
    metadata: dict,
    step_outputs: dict,
) -> None:
    """
        **Validates: Requirement 5 AC 13**

        For all valid WorkflowContext instances with JSON-serializable
        content, calling to_json and then parsing the JSON and calling
        from_dict shall produce a WorkflowContext with equivalent
        inputs, step outputs, and metadata.
    """
    original = WorkflowContext(inputs=inputs, agent=None, metadata=metadata)

    for step_id, output in step_outputs.items():
        original.set_step_output(step_id, output)

    json_str = original.to_json()
    parsed = json.loads(json_str)
    restored = WorkflowContext.from_dict(parsed, agent=None)

    testbase.assert_equal(restored.inputs, original.inputs,
        "inputs mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.inputs, original.inputs))

    testbase.assert_equal(restored.step_outputs, original.step_outputs,
        "step_outputs mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.step_outputs, original.step_outputs))

    testbase.assert_equal(restored.metadata, original.metadata,
        "metadata mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.metadata, original.metadata))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
