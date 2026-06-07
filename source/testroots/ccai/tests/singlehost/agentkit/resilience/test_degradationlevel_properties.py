"""
    Property-based tests for the ccai.agentkit.degradationlevel module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 19: DegradationLevel from_string round-trip

    **Validates: Requirements 8.2**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.degradationlevel import DegradationLevel


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_degradation_level_strategy = st.sampled_from(list(DegradationLevel))


# ---------------------------------------------------------------------------
# Property 19: DegradationLevel from_string round-trip
# ---------------------------------------------------------------------------

@given(
    level=_degradation_level_strategy,
    constraints={"max_examples": 50},
)
def test_degradation_level_from_string_round_trip(
    level: DegradationLevel,
) -> None:
    """
        **Validates: Requirements 8.2**

        For all DegradationLevel members, calling
        DegradationLevel.from_string(level.value) shall return the
        same DegradationLevel member.
    """
    result = DegradationLevel.from_string(level.value)

    assert result is level, (
        "from_string({!r}) should return {!r}, got {!r}".format(
            level.value, level, result
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
