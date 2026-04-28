"""
    Property-based tests for the automojo.agentkit.workflowcheckpoint module.

    Uses automojo.testbase.properties to verify:
    - Property 4: WorkflowCheckpoint JSON Round-Trip

    **Validates: Requirement 9 AC 15, Requirement 21 AC 14**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.workflowcheckpoint import WorkflowCheckpoint


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_string_key = st.text(
    min_size=1,
    max_size=10,
    alphabet="abcdefghijklmnopqrstuvwxyz"
)

_json_value = st.one_of(
    st.integers(-100, 100),
    st.text(min_size=0, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz")
)

_workflow_name = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz-"
)

_execution_id = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
)

_step_id = st.text(
    min_size=1,
    max_size=15,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
)

_completed_step_ids = st.sets(
    _step_id,
    min_size=0,
    max_size=3
)

_context_state = st.fixed_dictionaries({
    "inputs": st.dictionaries(
        keys=_string_key,
        values=_json_value,
        min_size=0,
        max_size=2
    ),
    "step_outputs": st.dictionaries(
        keys=_step_id,
        values=st.fixed_dictionaries({
            "val": st.integers(-50, 50)
        }),
        min_size=0,
        max_size=2
    ),
    "metadata": st.dictionaries(
        keys=_string_key,
        values=_json_value,
        min_size=0,
        max_size=2
    )
})


# ---------------------------------------------------------------------------
# Property 4: WorkflowCheckpoint JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    workflow_name=_workflow_name,
    execution_id=_execution_id,
    completed_step_ids=_completed_step_ids,
    context_state=_context_state,
    current_step_id=_step_id,
    constraints={"max_examples": 50},
)
def test_workflowcheckpoint_json_roundtrip(
    workflow_name: str,
    execution_id: str,
    completed_step_ids: set,
    context_state: dict,
    current_step_id: str,
) -> None:
    """
        **Validates: Requirement 9 AC 15, Requirement 21 AC 14**

        For all valid WorkflowCheckpoint instances, calling to_json
        and then from_json shall produce an equivalent
        WorkflowCheckpoint object with the same workflow name,
        execution identifier, completed step identifiers, context
        state, current step identifier, and timestamp.
    """
    original = WorkflowCheckpoint(
        workflow_name=workflow_name,
        execution_id=execution_id,
        completed_step_ids=completed_step_ids,
        context_state=context_state,
        current_step_id=current_step_id
    )

    json_str = original.to_json()
    restored = WorkflowCheckpoint.from_json(json_str)

    testbase.assert_equal(restored.workflow_name, original.workflow_name,
        "workflow_name mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.workflow_name, original.workflow_name))

    testbase.assert_equal(restored.execution_id, original.execution_id,
        "execution_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.execution_id, original.execution_id))

    testbase.assert_equal(restored.completed_step_ids, original.completed_step_ids,
        "completed_step_ids mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.completed_step_ids, original.completed_step_ids))

    testbase.assert_equal(restored.context_state, original.context_state,
        "context_state mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.context_state, original.context_state))

    testbase.assert_equal(restored.current_step_id, original.current_step_id,
        "current_step_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.current_step_id, original.current_step_id))

    testbase.assert_equal(
        restored.timestamp.isoformat(), original.timestamp.isoformat(),
        "timestamp mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.timestamp.isoformat(), original.timestamp.isoformat()))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
