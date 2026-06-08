"""
    Property-based tests for the ccai.agentkit.deadletterquery module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 27: DeadLetterQuery filtering correctness

    **Validates: Requirements 14.1**
"""

from datetime import datetime

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.deadletterentry import DeadLetterEntry
from ccai.agentkit.deadletterquery import DeadLetterQuery
from ccai.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore


# ---------------------------------------------------------------------------
# Composite Strategies
# ---------------------------------------------------------------------------

@composite
def _uuid_string(draw):
    hex_chars = "0123456789abcdef"
    parts = []
    for length in (8, 4, 4, 4, 12):
        parts.append(draw(st.text(alphabet=hex_chars, min_size=length, max_size=length)))
    return "-".join(parts)


@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_operation_type = st.sampled_from([
    "tool_execution",
    "llm_request",
    "message_delivery",
    "memory_write",
    "workflow_step",
])

_payload = st.fixed_dictionaries({"key": st.text(min_size=1, max_size=50)})

_exception_info = st.text(min_size=1, max_size=200)

_retry_attempts = st.integers(min_value=0, max_value=10)

_source_component = st.sampled_from([
    "tool_executor",
    "llm_provider",
    "transport",
    "memory_store",
    "workflow_engine",
])

_agent_identifier = st.sampled_from([
    "agent-alpha",
    "agent-beta",
    "agent-gamma",
])

_timestamp = _datetimes()

_metadata = st.just({})


def _dead_letter_entry_strategy():
    """
        Returns a strategy that builds a DeadLetterEntry with constrained
        field values drawn from the module-level strategies.
    """
    return st.builds(
        DeadLetterEntry,
        operation_type=_operation_type,
        payload=_payload,
        exception_info=_exception_info,
        retry_attempts=_retry_attempts,
        source_component=_source_component,
        agent_identifier=_agent_identifier,
        identifier=_uuid_string(),
        timestamp=_timestamp,
        metadata=_metadata,
    )


_entries_list = st.lists(
    _dead_letter_entry_strategy(),
    min_size=1,
    max_size=20,
)


# ---------------------------------------------------------------------------
# Property 27: DeadLetterQuery filtering correctness
# ---------------------------------------------------------------------------

@given(
    entries=_entries_list,
    filter_operation_type=_operation_type,
    constraints={"max_examples": 50},
)
def test_deadletterquery_filtering_by_operation_type(
    entries: list,
    filter_operation_type: str,
) -> None:
    """
        **Validates: Requirements 14.1**

        For all InMemoryDeadLetterStore instances containing a set of
        DeadLetterEntry objects, a DeadLetterQuery filtering by
        operation_type shall return only entries whose operation_type
        matches the filter value.
    """
    store = InMemoryDeadLetterStore()
    for entry in entries:
        store.store(entry)

    query = DeadLetterQuery(operation_type=filter_operation_type)
    result = store.search(query)

    # Every returned entry must match the filter
    for returned_entry in result.entries:
        assert returned_entry.operation_type == filter_operation_type, (
            "returned entry has operation_type {!r}, expected {!r}".format(
                returned_entry.operation_type, filter_operation_type
            )
        )

    # Count the expected matches from the original entries
    expected_matches = [
        e for e in entries if e.operation_type == filter_operation_type
    ]

    assert result.total_count == len(expected_matches), (
        "total_count mismatch: expected {}, got {}".format(
            len(expected_matches), result.total_count
        )
    )

    assert len(result.entries) == len(expected_matches), (
        "entries length mismatch: expected {}, got {}".format(
            len(expected_matches), len(result.entries)
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
