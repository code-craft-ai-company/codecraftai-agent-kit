"""
    Property-based tests for the ccai.agentkit.deadletterqueue module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 26: DeadLetterQueue enqueue increases count

    **Validates: Requirements 11.9**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.deadletterqueue import DeadLetterQueue
from ccai.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_operation_type = st.text(min_size=1, max_size=200)

_payload = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.text(min_size=0, max_size=200),
    max_size=10,
)

_exception_info = st.text(min_size=0, max_size=500)

_retry_attempts = st.integers(min_value=0, max_value=100)

_source_component = st.text(min_size=1, max_size=200)

_agent_identifier = st.text(min_size=1, max_size=200)

_enqueue_count = st.integers(min_value=1, max_value=50)


# ---------------------------------------------------------------------------
# Property 26: DeadLetterQueue enqueue increases count
# ---------------------------------------------------------------------------

@given(
    n=_enqueue_count,
    operation_type=_operation_type,
    payload=_payload,
    exception_info=_exception_info,
    retry_attempts=_retry_attempts,
    source_component=_source_component,
    agent_identifier=_agent_identifier,
    constraints={"max_examples": 50},
)
def test_deadletterqueue_enqueue_increases_count(
    n: int,
    operation_type: str,
    payload: dict,
    exception_info: str,
    retry_attempts: int,
    source_component: str,
    agent_identifier: str,
) -> None:
    """
        **Validates: Requirements 11.9**

        For all DeadLetterQueue instances backed by an InMemoryDeadLetterStore,
        after N enqueue operations the entry_count property shall equal N
        (assuming no purge or replay operations).
    """
    store = InMemoryDeadLetterStore()
    dlq = DeadLetterQueue(store=store)

    assert dlq.entry_count == 0, (
        "Expected initial entry_count 0, got {}".format(dlq.entry_count)
    )

    for i in range(n):
        dlq.enqueue(
            operation_type=operation_type,
            payload=payload,
            exception_info=exception_info,
            retry_attempts=retry_attempts,
            source_component=source_component,
            agent_identifier=agent_identifier,
        )

        expected_count = i + 1
        actual_count = dlq.entry_count

        assert actual_count == expected_count, (
            "After {} enqueue(s), expected entry_count {}, got {}".format(
                expected_count, expected_count, actual_count
            )
        )

    assert dlq.entry_count == n, (
        "After all {} enqueue(s), expected entry_count {}, got {}".format(
            n, n, dlq.entry_count
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
