"""
    Property-based tests for the automojo.agentkit.correlationcontext module.

    Uses the automojo.testbase.properties engine to verify universal properties of
    CorrelationContext: JSON round-trip fidelity, auto-generated UUID
    validity, and create_child parent chain preservation.
"""

import uuid

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.correlationcontext import CorrelationContext


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_correlation_id_strategy = st.text(min_size=1, max_size=100)

_parent_correlation_id_strategy = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=100),
)


# ---------------------------------------------------------------------------
# Property 1: CorrelationContext JSON round-trip
# ---------------------------------------------------------------------------

@given(
    correlation_id=_correlation_id_strategy,
    parent_correlation_id=_parent_correlation_id_strategy,
    constraints={"max_examples": 50},
)
def test_correlationcontext_json_round_trip(correlation_id, parent_correlation_id):
    """
        **Validates: Requirements 1.6, 1.8, 1.9**

        FOR ALL valid CorrelationContext instances with any combination of
        correlation_id and parent_correlation_id, calling to_json and then
        from_json SHALL produce a CorrelationContext whose correlation_id
        and parent_correlation_id are equal to the original.
    """
    original = CorrelationContext(
        correlation_id=correlation_id,
        parent_correlation_id=parent_correlation_id,
    )

    json_str = original.to_json()
    reconstructed = CorrelationContext.from_json(json_str)

    reconstructed_correlation_id = reconstructed.correlation_id
    assert reconstructed_correlation_id == correlation_id, (
        "Round-trip correlation_id mismatch: expected {!r}, got {!r}".format(
            correlation_id, reconstructed_correlation_id)
    )

    reconstructed_parent_id = reconstructed.parent_correlation_id
    assert reconstructed_parent_id == parent_correlation_id, (
        "Round-trip parent_correlation_id mismatch: expected {!r}, got {!r}".format(
            parent_correlation_id, reconstructed_parent_id)
    )

    return


# ---------------------------------------------------------------------------
# Property 2: CorrelationContext auto-generates valid UUID
# ---------------------------------------------------------------------------

@given(
    parent_correlation_id=_parent_correlation_id_strategy,
    constraints={"max_examples": 50},
)
def test_correlationcontext_auto_generates_valid_uuid(parent_correlation_id):
    """
        **Validates: Requirements 1.2**

        FOR ALL CorrelationContext instances created without an explicit
        correlation_id, the resulting correlation_id property SHALL be a
        valid UUID string parseable by uuid.UUID.
    """
    ctx = CorrelationContext(
        parent_correlation_id=parent_correlation_id,
    )

    correlation_id = ctx.correlation_id

    parsed = uuid.UUID(correlation_id)
    round_tripped = str(parsed)
    assert round_tripped == correlation_id, (
        "Auto-generated correlation_id is not a valid UUID: {!r}".format(
            correlation_id)
    )

    return


# ---------------------------------------------------------------------------
# Property 3: CorrelationContext create_child preserves parent chain
# ---------------------------------------------------------------------------

@given(
    correlation_id=_correlation_id_strategy,
    parent_correlation_id=_parent_correlation_id_strategy,
    constraints={"max_examples": 50},
)
def test_correlationcontext_create_child_preserves_parent_chain(correlation_id, parent_correlation_id):
    """
        **Validates: Requirements 1.4**

        FOR ALL valid CorrelationContext instances, calling create_child
        SHALL produce a new CorrelationContext whose parent_correlation_id
        equals the original's correlation_id, and whose correlation_id is
        a new distinct value.
    """
    parent = CorrelationContext(
        correlation_id=correlation_id,
        parent_correlation_id=parent_correlation_id,
    )

    child = parent.create_child()

    child_parent_id = child.parent_correlation_id
    assert child_parent_id == correlation_id, (
        "Child parent_correlation_id should equal parent correlation_id: "
        "expected {!r}, got {!r}".format(correlation_id, child_parent_id)
    )

    child_correlation_id = child.correlation_id
    assert child_correlation_id != correlation_id, (
        "Child correlation_id should differ from parent correlation_id: "
        "both are {!r}".format(correlation_id)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
