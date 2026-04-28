"""
    Property-based tests for the
    automojo.agentkit.workflowconfiguration module.

    Uses automojo.testbase.properties to verify:
    - Property 8: WorkflowConfiguration JSON Round-Trip
    - Property 9: WorkflowConfiguration YAML Round-Trip

    **Validates: Requirement 17 AC 15, Requirement 17 AC 16**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.workflowconfiguration import WorkflowConfiguration


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_max_parallel_workers = st.integers(1, 32)

_checkpoint_interval = st.integers(1, 100)

_default_approval_timeout = st.floats(0.1, 86400.0)


# ---------------------------------------------------------------------------
# Property 8: WorkflowConfiguration JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    max_parallel_workers=_max_parallel_workers,
    checkpoint_interval=_checkpoint_interval,
    default_approval_timeout=_default_approval_timeout,
    constraints={"max_examples": 50},
)
def test_workflowconfiguration_json_roundtrip(
    max_parallel_workers: int,
    checkpoint_interval: int,
    default_approval_timeout: float,
) -> None:
    """
        **Validates: Requirement 17 AC 15**

        For all valid WorkflowConfiguration instances, calling
        to_json and then from_json shall produce an equivalent
        WorkflowConfiguration object with the same
        max_parallel_workers, checkpoint_interval, and
        default_approval_timeout.
    """
    original = WorkflowConfiguration(
        max_parallel_workers=max_parallel_workers,
        checkpoint_interval=checkpoint_interval,
        default_approval_timeout=default_approval_timeout,
    )

    json_str = original.to_json()
    restored = WorkflowConfiguration.from_json(json_str)

    testbase.assert_equal(
        restored.max_parallel_workers, original.max_parallel_workers,
        "max_parallel_workers mismatch after JSON round-trip: {} != {}".format(
            restored.max_parallel_workers, original.max_parallel_workers))

    testbase.assert_equal(
        restored.checkpoint_interval, original.checkpoint_interval,
        "checkpoint_interval mismatch after JSON round-trip: {} != {}".format(
            restored.checkpoint_interval, original.checkpoint_interval))

    testbase.assert_equal(
        restored.default_approval_timeout, original.default_approval_timeout,
        "default_approval_timeout mismatch after JSON round-trip: {} != {}".format(
            restored.default_approval_timeout, original.default_approval_timeout))

    testbase.assert_equal(
        restored.default_retry_policy, original.default_retry_policy,
        "default_retry_policy mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.default_retry_policy, original.default_retry_policy))

    return


# ---------------------------------------------------------------------------
# Property 9: WorkflowConfiguration YAML Round-Trip
# ---------------------------------------------------------------------------

@given(
    max_parallel_workers=_max_parallel_workers,
    checkpoint_interval=_checkpoint_interval,
    default_approval_timeout=_default_approval_timeout,
    constraints={"max_examples": 50},
)
def test_workflowconfiguration_yaml_roundtrip(
    max_parallel_workers: int,
    checkpoint_interval: int,
    default_approval_timeout: float,
) -> None:
    """
        **Validates: Requirement 17 AC 16**

        For all valid WorkflowConfiguration instances, calling
        to_yaml and then from_yaml shall produce an equivalent
        WorkflowConfiguration object with the same
        max_parallel_workers, checkpoint_interval, and
        default_approval_timeout.
    """
    original = WorkflowConfiguration(
        max_parallel_workers=max_parallel_workers,
        checkpoint_interval=checkpoint_interval,
        default_approval_timeout=default_approval_timeout,
    )

    yaml_str = original.to_yaml()
    restored = WorkflowConfiguration.from_yaml(yaml_str)

    testbase.assert_equal(
        restored.max_parallel_workers, original.max_parallel_workers,
        "max_parallel_workers mismatch after YAML round-trip: {} != {}".format(
            restored.max_parallel_workers, original.max_parallel_workers))

    testbase.assert_equal(
        restored.checkpoint_interval, original.checkpoint_interval,
        "checkpoint_interval mismatch after YAML round-trip: {} != {}".format(
            restored.checkpoint_interval, original.checkpoint_interval))

    testbase.assert_equal(
        restored.default_approval_timeout, original.default_approval_timeout,
        "default_approval_timeout mismatch after YAML round-trip: {} != {}".format(
            restored.default_approval_timeout, original.default_approval_timeout))

    testbase.assert_equal(
        restored.default_retry_policy, original.default_retry_policy,
        "default_retry_policy mismatch after YAML round-trip: {!r} != {!r}".format(
            restored.default_retry_policy, original.default_retry_policy))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
