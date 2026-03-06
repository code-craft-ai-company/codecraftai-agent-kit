"""
    Property-based tests for the automojo.agentkit.degradationlevel module.

    Uses the hypothesis library to verify:
    - Property 19: DegradationLevel from_string round-trip

    **Validates: Requirements 8.2**
"""

from hypothesis import given, settings
from hypothesis.strategies import sampled_from

from automojo.agentkit.degradationlevel import DegradationLevel


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_degradation_level_strategy = sampled_from(list(DegradationLevel))


# ---------------------------------------------------------------------------
# Property 19: DegradationLevel from_string round-trip
# ---------------------------------------------------------------------------

@given(level=_degradation_level_strategy)
@settings(max_examples=100)
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
