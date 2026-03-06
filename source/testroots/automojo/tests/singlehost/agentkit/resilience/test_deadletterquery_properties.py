"""
    Property-based tests for the automojo.agentkit.deadletterquery module.

    Uses the hypothesis library to verify:
    - Property 27: DeadLetterQuery filtering correctness

    **Validates: Requirements 14.1**
"""

from datetime import datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.deadletterentry import DeadLetterEntry
from automojo.agentkit.deadletterquery import DeadLetterQuery
from automojo.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_uuid_string = st.uuids().map(str)

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

_timestamp = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
)

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
        identifier=_uuid_string,
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
)
@settings(max_examples=100)
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
