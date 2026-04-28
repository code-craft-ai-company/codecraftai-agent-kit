"""
    Property-based tests for the automojo.agentkit.breakpoint module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 29: Breakpoint matches logic

    **Validates: Requirements 23.4, 23.5, 23.6**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.breakpoint import Breakpoint


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_valid_type_strategy = st.sampled_from(list(Breakpoint.VALID_TYPES))

_target_name_strategy = st.text(
    min_size=1,
    max_size=50,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
)

_optional_target_name_strategy = st.one_of(st.none(), _target_name_strategy)


# ---------------------------------------------------------------------------
# Property 29: Breakpoint matches logic
# ---------------------------------------------------------------------------

@given(
    bp_type=_valid_type_strategy,
    bp_target=_optional_target_name_strategy,
    event_type=_valid_type_strategy,
    event_target=_optional_target_name_strategy,
    constraints={"max_examples": 50},
)
def test_breakpoint_matches_logic(
    bp_type: str,
    bp_target: str,
    event_type: str,
    event_target: str,
) -> None:
    """
        **Validates: Requirements 23.4, 23.5, 23.6**

        For any valid Breakpoint with a given breakpoint_type and
        optional target_name:
        (a) matches returns True when event_type equals breakpoint_type
            and target_name matches (or breakpoint has no target_name)
        (b) matches returns False when event_type differs from
            breakpoint_type
        (c) matches returns False when breakpoint has a target_name
            that differs from the provided target_name
    """
    bp = Breakpoint(
        breakpoint_type=bp_type,
        target_name=bp_target,
    )

    result = bp.matches(event_type, target_name=event_target)

    # (b) When event_type differs from breakpoint_type, matches is False
    if bp_type != event_type:
        assert result is False, (
            "matches should return False when event_type {!r} differs "
            "from breakpoint_type {!r}".format(event_type, bp_type)
        )
        return

    # At this point bp_type == event_type
    if bp_target is None:
        # (a) When breakpoint has no target_name, matches is True
        assert result is True, (
            "matches should return True when type matches and "
            "breakpoint has no target_name"
        )
    elif bp_target == event_target:
        # (a) When target_name matches, matches is True
        assert result is True, (
            "matches should return True when type and target_name "
            "both match"
        )
    else:
        # (c) When breakpoint has a target_name that differs, matches is False
        assert result is False, (
            "matches should return False when breakpoint target_name "
            "{!r} differs from event target_name {!r}".format(
                bp_target, event_target
            )
        )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
