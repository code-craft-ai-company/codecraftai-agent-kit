"""
    Property-based tests for the automojo.agentkit.degradationmanager module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 20: DegradationManager overall level is maximum

    **Validates: Requirements 9.6**
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.defaultvaluestrategy import DefaultValueStrategy
from automojo.agentkit.degradationlevel import DegradationLevel
from automojo.agentkit.degradationmanager import DegradationManager
from automojo.agentkit.degradationpolicy import DegradationPolicy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_agent_identifiers = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        categories=("L", "N", "P", "S"),
    ),
)

_dependency_names = st.lists(
    st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(
            categories=("L", "N", "P", "S"),
        ),
    ),
    min_size=2,
    max_size=10,
).map(lambda names: list(dict.fromkeys(names))).filter(lambda names: len(names) >= 2)

# Number of failures to report per dependency: 0 = NORMAL, 1 = DEGRADED, 2+ = CRITICAL
_failure_counts = st.integers(min_value=0, max_value=3)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LEVEL_ORDER = {
    DegradationLevel.NORMAL: 0,
    DegradationLevel.DEGRADED: 1,
    DegradationLevel.CRITICAL: 2,
}

_FAILURES_TO_LEVEL = {
    0: DegradationLevel.NORMAL,
    1: DegradationLevel.DEGRADED,
    2: DegradationLevel.CRITICAL,
    3: DegradationLevel.CRITICAL,
}


# ---------------------------------------------------------------------------
# Property 20: DegradationManager overall level is maximum
# ---------------------------------------------------------------------------

@given(
    agent_id=_agent_identifiers,
    dep_names=_dependency_names,
    failure_counts=st.lists(_failure_counts, min_size=2, max_size=10),
    settings=settings(max_examples=50),
)
def test_degradationmanager_overall_level_is_maximum(
    agent_id: str,
    dep_names: list,
    failure_counts: list,
) -> None:
    """
        **Validates: Requirements 9.6**

        For all DegradationManager instances with tracked dependencies at
        various DegradationLevel values, the overall_level property shall
        equal the highest DegradationLevel across all tracked dependencies
        (CRITICAL > DEGRADED > NORMAL).

        # Feature: error-handling-resilience, Property 20: DegradationManager overall level is maximum
    """
    manager = DegradationManager(agent_id)
    strategy = DefaultValueStrategy("fallback")

    # Align failure_counts to dep_names length
    aligned_counts = failure_counts[:len(dep_names)]
    while len(aligned_counts) < len(dep_names):
        aligned_counts.append(0)

    # Register a policy for each dependency and report the specified number
    # of failures to drive each dependency to the expected level.
    expected_levels = []

    for dep_name, num_failures in zip(dep_names, aligned_counts):
        policy = DegradationPolicy(dep_name, strategy, DegradationLevel.DEGRADED)
        manager.register_policy(policy)

        for _ in range(num_failures):
            manager.report_failure(dep_name, RuntimeError("test failure"))

        expected_level = _FAILURES_TO_LEVEL[num_failures]
        expected_levels.append(expected_level)

    # Compute the expected maximum level
    expected_max = max(expected_levels, key=lambda lvl: _LEVEL_ORDER[lvl])

    # Verify overall_level equals the maximum
    actual_overall = manager.overall_level

    assert actual_overall is expected_max, (
        "Expected overall_level to be {} but got {}. "
        "Dependency levels: {}".format(
            expected_max.value,
            actual_overall.value,
            {name: _FAILURES_TO_LEVEL[cnt].value
             for name, cnt in zip(dep_names, aligned_counts)},
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
