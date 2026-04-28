"""
    Property-based tests for the automojo.agentkit.stepresult module.

    Uses automojo.testbase.properties to verify:
    - Property 3: StepResult JSON Round-Trip

    **Validates: Requirement 6 AC 15**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.stepresult import StepResult
from automojo.agentkit.stepexecutionstatus import StepExecutionStatus


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_step_id = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
)

_step_name = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz "
)

_status = st.sampled_from([
    StepExecutionStatus.PENDING,
    StepExecutionStatus.RUNNING,
    StepExecutionStatus.COMPLETED,
    StepExecutionStatus.FAILED,
    StepExecutionStatus.SKIPPED,
    StepExecutionStatus.PENDING_APPROVAL,
    StepExecutionStatus.CANCELLED,
])

_output = st.fixed_dictionaries({
    "key": st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz")
})

_duration = st.floats(0.0, 1000.0)

_error = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz ")
)


# ---------------------------------------------------------------------------
# Property 3: StepResult JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    step_id=_step_id,
    step_name=_step_name,
    status=_status,
    output=_output,
    duration=_duration,
    error=_error,
    constraints={"max_examples": 100},
)
def test_stepresult_json_roundtrip(
    step_id: str,
    step_name: str,
    status: StepExecutionStatus,
    output: dict,
    duration: float,
    error: str,
) -> None:
    """
        **Validates: Requirement 6 AC 15**

        For all valid StepResult instances, calling to_json and then
        from_json shall produce an equivalent StepResult object.
    """
    original = StepResult(
        step_id=step_id,
        step_name=step_name,
        status=status,
        output=output,
        duration=duration,
        error=error,
    )

    json_str = original.to_json()
    restored = StepResult.from_json(json_str)

    testbase.assert_equal(restored.step_id, original.step_id,
        "step_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.step_id, original.step_id))

    testbase.assert_equal(restored.step_name, original.step_name,
        "step_name mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.step_name, original.step_name))

    testbase.assert_equal(restored.status, original.status,
        "status mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.status, original.status))

    testbase.assert_equal(restored.output, original.output,
        "output mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.output, original.output))

    testbase.assert_equal(restored.duration, original.duration,
        "duration mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.duration, original.duration))

    testbase.assert_equal(restored.error, original.error,
        "error mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.error, original.error))

    testbase.assert_equal(restored.is_success, original.is_success,
        "is_success mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.is_success, original.is_success))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
