"""
    Property-based tests for the ccai.agentkit.approvalrequest
    module.

    Uses ccai.testbase.properties to verify:
    - Property 5: ApprovalRequest JSON Round-Trip

    **Validates: Requirement 11 AC 18, Requirement 21 AC 17**
"""

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.approvalrequest import ApprovalRequest


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

_identifier = st.text(
    min_size=1,
    max_size=30,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
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

_description = st.text(
    min_size=1,
    max_size=40,
    alphabet="abcdefghijklmnopqrstuvwxyz "
)

_agent_id = st.text(
    min_size=1,
    max_size=20,
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-"
)

_status = st.sampled_from(["pending", "approved", "rejected", "expired"])

_metadata = st.dictionaries(
    keys=_string_key,
    values=_json_value,
    min_size=0,
    max_size=3
)

_rejection_reason = st.one_of(
    st.none(),
    st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz ")
)


# ---------------------------------------------------------------------------
# Property 5: ApprovalRequest JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    identifier=_identifier,
    execution_id=_execution_id,
    step_id=_step_id,
    description=_description,
    requesting_agent_id=_agent_id,
    status=_status,
    metadata=_metadata,
    rejection_reason=_rejection_reason,
    constraints={"max_examples": 50},
)
def test_approvalrequest_json_roundtrip(
    identifier: str,
    execution_id: str,
    step_id: str,
    description: str,
    requesting_agent_id: str,
    status: str,
    metadata: dict,
    rejection_reason: str,
) -> None:
    """
        **Validates: Requirement 11 AC 18, Requirement 21 AC 17**

        For all valid ApprovalRequest instances, calling to_json
        and then from_json shall produce an equivalent
        ApprovalRequest object with the same identifier,
        execution_id, step_id, description, requesting_agent_id,
        status, metadata, rejection_reason, and timestamp.
    """
    original = ApprovalRequest(
        identifier=identifier,
        execution_id=execution_id,
        step_id=step_id,
        description=description,
        requesting_agent_id=requesting_agent_id,
        status=status,
        metadata=metadata,
        rejection_reason=rejection_reason
    )

    json_str = original.to_json()
    restored = ApprovalRequest.from_json(json_str)

    testbase.assert_equal(restored.identifier, original.identifier,
        "identifier mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.identifier, original.identifier))

    testbase.assert_equal(restored.execution_id, original.execution_id,
        "execution_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.execution_id, original.execution_id))

    testbase.assert_equal(restored.step_id, original.step_id,
        "step_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.step_id, original.step_id))

    testbase.assert_equal(restored.description, original.description,
        "description mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.description, original.description))

    testbase.assert_equal(restored.requesting_agent_id, original.requesting_agent_id,
        "requesting_agent_id mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.requesting_agent_id, original.requesting_agent_id))

    testbase.assert_equal(restored.status, original.status,
        "status mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.status, original.status))

    testbase.assert_equal(restored.metadata, original.metadata,
        "metadata mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.metadata, original.metadata))

    testbase.assert_equal(restored.rejection_reason, original.rejection_reason,
        "rejection_reason mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.rejection_reason, original.rejection_reason))

    testbase.assert_equal(
        restored.timestamp.isoformat(), original.timestamp.isoformat(),
        "timestamp mismatch after JSON round-trip: {!r} != {!r}".format(
            restored.timestamp.isoformat(), original.timestamp.isoformat()))

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
