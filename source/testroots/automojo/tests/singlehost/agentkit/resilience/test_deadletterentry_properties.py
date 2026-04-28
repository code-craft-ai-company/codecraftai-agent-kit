"""
    Property-based tests for the automojo.agentkit.deadletterentry module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 23: DeadLetterEntry JSON round-trip
    - Property 24: DeadLetterEntry auto-generates identifier and timestamp

    **Validates: Requirements 12.2, 12.3, 12.9**
"""

from datetime import datetime

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.deadletterentry import DeadLetterEntry


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

_timestamp = _datetimes()

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=st.text(min_size=0, max_size=200),
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 23: DeadLetterEntry JSON round-trip
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
    constraints={"max_examples": 50},
)
def test_deadletterentry_json_roundtrip(
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
        **Validates: Requirements 12.9**

        For all valid DeadLetterEntry instances constructed with arbitrary
        identifier (UUID string), operation_type (non-empty string),
        payload (dict of string keys and string values), exception_info
        (string), retry_attempts (int), source_component (string),
        agent_identifier (string), timestamp (datetime), and metadata
        (dict of string keys and string values), calling to_json() and
        then from_json() shall produce an equivalent DeadLetterEntry object.
    """
    original = DeadLetterEntry(
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

    json_str = original.to_json()
    restored = DeadLetterEntry.from_json(json_str)

    assert restored.identifier == original.identifier, (
        "identifier mismatch: expected {!r}, got {!r}".format(
            original.identifier, restored.identifier
        )
    )

    assert restored.operation_type == original.operation_type, (
        "operation_type mismatch: expected {!r}, got {!r}".format(
            original.operation_type, restored.operation_type
        )
    )

    assert restored.payload == original.payload, (
        "payload mismatch: expected {!r}, got {!r}".format(
            original.payload, restored.payload
        )
    )

    assert restored.exception_info == original.exception_info, (
        "exception_info mismatch: expected {!r}, got {!r}".format(
            original.exception_info, restored.exception_info
        )
    )

    assert restored.retry_attempts == original.retry_attempts, (
        "retry_attempts mismatch: expected {!r}, got {!r}".format(
            original.retry_attempts, restored.retry_attempts
        )
    )

    assert restored.source_component == original.source_component, (
        "source_component mismatch: expected {!r}, got {!r}".format(
            original.source_component, restored.source_component
        )
    )

    assert restored.agent_identifier == original.agent_identifier, (
        "agent_identifier mismatch: expected {!r}, got {!r}".format(
            original.agent_identifier, restored.agent_identifier
        )
    )

    assert restored.timestamp == original.timestamp, (
        "timestamp mismatch: expected {}, got {}".format(
            original.timestamp, restored.timestamp
        )
    )

    assert restored.metadata == original.metadata, (
        "metadata mismatch: expected {!r}, got {!r}".format(
            original.metadata, restored.metadata
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 24: DeadLetterEntry auto-generates identifier and timestamp
# ---------------------------------------------------------------------------

@given(
    operation_type=_operation_type,
    payload=_payload,
    exception_info=_exception_info,
    retry_attempts=_retry_attempts,
    source_component=_source_component,
    agent_identifier=_agent_identifier,
    metadata=_metadata,
    constraints={"max_examples": 50},
)
def test_deadletterentry_auto_generates_identifier_and_timestamp(
    operation_type: str,
    payload: dict,
    exception_info: str,
    retry_attempts: int,
    source_component: str,
    agent_identifier: str,
    metadata: dict,
) -> None:
    """
        **Validates: Requirements 12.2, 12.3**

        For all valid DeadLetterEntry instances constructed without explicit
        identifier and timestamp, the identifier property shall be a non-empty
        string and the timestamp property shall be a datetime instance.
        Additionally, two separately constructed entries shall receive
        different identifiers (uniqueness).
    """
    entry_a = DeadLetterEntry(
        operation_type=operation_type,
        payload=payload,
        exception_info=exception_info,
        retry_attempts=retry_attempts,
        source_component=source_component,
        agent_identifier=agent_identifier,
        metadata=metadata,
    )

    entry_b = DeadLetterEntry(
        operation_type=operation_type,
        payload=payload,
        exception_info=exception_info,
        retry_attempts=retry_attempts,
        source_component=source_component,
        agent_identifier=agent_identifier,
        metadata=metadata,
    )

    # Identifier is a non-empty string
    assert isinstance(entry_a.identifier, str), (
        "identifier should be a string, got {!r}".format(type(entry_a.identifier))
    )
    assert len(entry_a.identifier) > 0, "identifier should be non-empty"

    # Timestamp is a datetime instance
    assert isinstance(entry_a.timestamp, datetime), (
        "timestamp should be a datetime, got {!r}".format(type(entry_a.timestamp))
    )

    # Two separately constructed entries get different identifiers
    assert entry_a.identifier != entry_b.identifier, (
        "Two entries should have different identifiers, both got {!r}".format(
            entry_a.identifier
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
