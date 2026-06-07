"""
    Property-based tests for the ccai.agentkit.transitionrecord module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 11 (partial): Defensive copy for TransitionRecord metadata

    **Validates: Requirements 5.3**
"""

from datetime import datetime
from datetime import timezone

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.transitionrecord import TransitionRecord


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_lifecycle_state_strategy = st.sampled_from(list(LifecycleState))

_metadata_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    values=st.text(min_size=0, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"),
    min_size=0,
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 11 (partial): Defensive copy for TransitionRecord metadata
# ---------------------------------------------------------------------------

@given(
    previous_state=_lifecycle_state_strategy,
    new_state=_lifecycle_state_strategy,
    metadata=_metadata_strategy,
    constraints={"max_examples": 30},
)
def test_transitionrecord_metadata_defensive_copy(
    previous_state: LifecycleState,
    new_state: LifecycleState,
    metadata: dict,
) -> None:
    """
        **Validates: Requirements 5.3**

        Modifying the dictionary returned by the metadata property does not
        affect the internal state of the TransitionRecord.
    """
    timestamp = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=previous_state,
        new_state=new_state,
        timestamp=timestamp,
        metadata=metadata,
    )

    original_metadata = record.metadata

    returned_metadata = record.metadata
    returned_metadata["__injected_key__"] = "injected_value"

    after_mutation_metadata = record.metadata

    testbase.assert_equal(after_mutation_metadata, original_metadata,
        "Metadata should not be affected by mutation of returned copy: "
        "expected {!r}, got {!r} (previous_state={!r}, new_state={!r})".format(
            original_metadata, after_mutation_metadata, previous_state, new_state))

    testbase.assert_false("__injected_key__" in after_mutation_metadata,
        "Injected key should not appear in metadata after mutating returned copy "
        "(previous_state={!r}, new_state={!r})".format(previous_state, new_state))

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
