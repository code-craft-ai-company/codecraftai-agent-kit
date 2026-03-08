"""
    Property-based tests for the automojo.agentkit.inmemorydeadletterstore module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 25: InMemoryDeadLetterStore store-retrieve consistency

    **Validates: Requirements 13.4**
"""

from datetime import datetime

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.deadletterentry import DeadLetterEntry
from automojo.agentkit.inmemorydeadletterstore import InMemoryDeadLetterStore


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def _uuid_string(draw):
    hex_chars = "0123456789abcdef"
    parts = []
    for length in (8, 4, 4, 4, 12):
        parts.append(draw(st.text(alphabet=hex_chars, min_size=length, max_size=length)))
    return "-".join(parts)


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


@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_timestamp = _datetimes()

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.text(min_size=0, max_size=200),
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 25: InMemoryDeadLetterStore store-retrieve consistency
# ---------------------------------------------------------------------------

@given(
    identifier=_uuid_string(),
    operation_type=_operation_type,
    payload=_payload,
    exception_info=_exception_info,
    retry_attempts=_retry_attempts,
    source_component=_source_component,
    agent_identifier=_agent_identifier,
    timestamp=_timestamp,
    metadata=_metadata,
    settings=settings(max_examples=50),
)
def test_inmemorydeadletterstore_store_retrieve_consistency(
    identifier: str,
    operation_type: str,
    payload: dict,
    exception_info: str,
    retry_attempts: int,
    source_component: str,
    agent_identifier: str,
    timestamp: datetime,
    metadata: dict,
) -> None:
    """
        **Validates: Requirements 13.4**

        For all valid DeadLetterEntry instances stored in an
        InMemoryDeadLetterStore, calling retrieve(entry.identifier)
        shall return the same DeadLetterEntry instance with matching
        fields.
    """
    entry = DeadLetterEntry(
        operation_type=operation_type,
        payload=payload,
        exception_info=exception_info,
        retry_attempts=retry_attempts,
        source_component=source_component,
        agent_identifier=agent_identifier,
        identifier=identifier,
        timestamp=timestamp,
        metadata=metadata,
    )

    store = InMemoryDeadLetterStore()
    store.store(entry)

    retrieved = store.retrieve(entry.identifier)

    assert retrieved is not None, (
        "retrieve returned None for identifier {!r}".format(entry.identifier)
    )

    assert retrieved.identifier == entry.identifier, (
        "identifier mismatch: expected {!r}, got {!r}".format(
            entry.identifier, retrieved.identifier
        )
    )

    assert retrieved.operation_type == entry.operation_type, (
        "operation_type mismatch: expected {!r}, got {!r}".format(
            entry.operation_type, retrieved.operation_type
        )
    )

    assert retrieved.payload == entry.payload, (
        "payload mismatch: expected {!r}, got {!r}".format(
            entry.payload, retrieved.payload
        )
    )

    assert retrieved.exception_info == entry.exception_info, (
        "exception_info mismatch: expected {!r}, got {!r}".format(
            entry.exception_info, retrieved.exception_info
        )
    )

    assert retrieved.retry_attempts == entry.retry_attempts, (
        "retry_attempts mismatch: expected {!r}, got {!r}".format(
            entry.retry_attempts, retrieved.retry_attempts
        )
    )

    assert retrieved.source_component == entry.source_component, (
        "source_component mismatch: expected {!r}, got {!r}".format(
            entry.source_component, retrieved.source_component
        )
    )

    assert retrieved.agent_identifier == entry.agent_identifier, (
        "agent_identifier mismatch: expected {!r}, got {!r}".format(
            entry.agent_identifier, retrieved.agent_identifier
        )
    )

    assert retrieved.timestamp == entry.timestamp, (
        "timestamp mismatch: expected {}, got {}".format(
            entry.timestamp, retrieved.timestamp
        )
    )

    assert retrieved.metadata == entry.metadata, (
        "metadata mismatch: expected {!r}, got {!r}".format(
            entry.metadata, retrieved.metadata
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
