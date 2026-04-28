"""
    Property-based tests for the automojo.agentkit.workflowresult module.

    Uses automojo.testbase.properties to verify:
    - Property 2: WorkflowResult JSON Round-Trip

    **Validates: Requirement 6 AC 8, Requirement 21 AC 11**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.workflowresult import WorkflowResult
from automojo.agentkit.workflowexecutionstatus import WorkflowExecutionStatus
from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_workflow_name = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
)

_workflow_status = st.sampled_from([
    WorkflowExecutionStatus.RUNNING,
    WorkflowExecutionStatus.COMPLETED,
    WorkflowExecutionStatus.FAILED,
    WorkflowExecutionStatus.PAUSED,
    WorkflowExecutionStatus.CANCELLED,
])

_step_status = st.sampled_from([
    StepExecutionStatus.PENDING,
    StepExecutionStatus.RUNNING,
    StepExecutionStatus.COMPLETED,
    StepExecutionStatus.FAILED,
    StepExecutionStatus.SKIPPED,
    StepExecutionStatus.PENDING_APPROVAL,
    StepExecutionStatus.CANCELLED,
])

_final_output = st.fixed_dictionaries({
    "result": st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz")
})

_duration = st.floats(0.0, 1000.0)

_error = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz ")
)


@composite
def step_results_strategy(draw, min_size=0, max_size=3):
    """
        Composite strategy that generates a list of StepResult objects
        with unique step identifiers.
    """
    count = draw(st.integers(min_size, max_size))
    results = []

    for idx in range(count):
        step_id = "step-{}".format(idx)
        step_name = draw(st.text(
            min_size=1,
            max_size=20,
            alphabet="abcdefghijklmnopqrstuvwxyz "
        ))
        status = draw(_step_status)
        output = draw(st.fixed_dictionaries({
            "key": st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz")
        }))
        dur = draw(st.floats(0.0, 1000.0))
        err = draw(_error)

        step_result = StepResult(
            step_id=step_id,
            step_name=step_name,
            status=status,
            output=output,
            duration=dur,
            error=err,
        )
        results.append(step_result)

    return results


# ---------------------------------------------------------------------------
# Property 2: WorkflowResult JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    workflow_name=_workflow_name,
    status=_workflow_status,
    step_results=step_results_strategy(min_size=0, max_size=3),
    final_output=_final_output,
    duration=_duration,
    error=_error,
    constraints={"max_examples": 100},
)
def test_workflowresult_json_roundtrip(
    workflow_name: str,
    status: WorkflowExecutionStatus,
    step_results: list,
    final_output: dict,
    duration: float,
    error: str,
) -> None:
    """
        **Validates: Requirement 6 AC 8, Requirement 21 AC 11**

        For all valid WorkflowResult instances, calling to_json and then
        from_json shall produce an equivalent WorkflowResult object.
    """
    original = WorkflowResult(
        workflow_name=workflow_name,
        status=status,
        step_results=step_results,
        final_output=final_output,
        duration=duration,
        error=error,
    )

    json_str = original.to_json()
    restored = WorkflowResult.from_json(json_str)

    testbase.assert_equal(restored.workflow_name, original.workflow_name,
        "workflow_name mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.workflow_name, original.workflow_name))

    testbase.assert_equal(restored.status, original.status,
        "status mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.status, original.status))

    testbase.assert_equal(restored.final_output, original.final_output,
        "final_output mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.final_output, original.final_output))

    testbase.assert_equal(restored.duration, original.duration,
        "duration mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.duration, original.duration))

    testbase.assert_equal(restored.error, original.error,
        "error mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.error, original.error))

    testbase.assert_equal(restored.is_success, original.is_success,
        "is_success mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.is_success, original.is_success))

    testbase.assert_equal(len(restored.step_results), len(original.step_results),
        "step_results count mismatch after JSON round-trip: {} != {}".format(
            len(restored.step_results), len(original.step_results)))

    for idx in range(len(original.step_results)):
        orig_sr = original.step_results[idx]
        rest_sr = restored.step_results[idx]

        testbase.assert_equal(rest_sr.step_id, orig_sr.step_id,
            "step_results[{}].step_id mismatch: {!r} != {!r}".format(
                idx, rest_sr.step_id, orig_sr.step_id))

        testbase.assert_equal(rest_sr.step_name, orig_sr.step_name,
            "step_results[{}].step_name mismatch: {!r} != {!r}".format(
                idx, rest_sr.step_name, orig_sr.step_name))

        testbase.assert_equal(rest_sr.status, orig_sr.status,
            "step_results[{}].status mismatch: {!r} != {!r}".format(
                idx, rest_sr.status, orig_sr.status))

        testbase.assert_equal(rest_sr.output, orig_sr.output,
            "step_results[{}].output mismatch: {!r} != {!r}".format(
                idx, rest_sr.output, orig_sr.output))

        testbase.assert_equal(rest_sr.duration, orig_sr.duration,
            "step_results[{}].duration mismatch: {!r} != {!r}".format(
                idx, rest_sr.duration, orig_sr.duration))

        testbase.assert_equal(rest_sr.error, orig_sr.error,
            "step_results[{}].error mismatch: {!r} != {!r}".format(
                idx, rest_sr.error, orig_sr.error))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
