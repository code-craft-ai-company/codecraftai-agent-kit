"""
    Property-based tests for the ccai.agentkit.executionrecord module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 24: ExecutionRecord JSON round-trip preserves all fields

    **Validates: Requirements 18.4, 18.6, 18.7**
"""

from datetime import datetime

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.executionrecord import ExecutionRecord


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_timestamp_strategy = _datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2030, 1, 1),
)

_short_text = st.text(min_size=1, max_size=100)

_payload_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=st.text(min_size=0, max_size=50),
    max_size=5,
)

_sequence_number_strategy = st.integers(min_value=1, max_value=1000000)


# ---------------------------------------------------------------------------
# Property 24: ExecutionRecord JSON round-trip
# ---------------------------------------------------------------------------

@given(
    sequence_number=_sequence_number_strategy,
    timestamp=_timestamp_strategy,
    event_type=_short_text,
    agent_id=_short_text,
    correlation_id=_short_text,
    payload=_payload_strategy,
    constraints={"max_examples": 50},
)
def test_executionrecord_json_round_trip(sequence_number, timestamp, event_type, agent_id, correlation_id, payload):
    """
        **Validates: Requirements 18.4, 18.6, 18.7**

        FOR ALL valid ExecutionRecord instances with any combination of
        sequence_number, timestamp, event_type, agent_id, correlation_id,
        and payload, calling to_json and then from_json SHALL produce an
        ExecutionRecord whose fields are equal to the original.
    """
    original = ExecutionRecord(
        sequence_number=sequence_number,
        timestamp=timestamp,
        event_type=event_type,
        agent_id=agent_id,
        correlation_id=correlation_id,
        payload=payload,
    )

    json_str = original.to_json()
    reconstructed = ExecutionRecord.from_json(json_str)

    reconstructed_seq = reconstructed.sequence_number
    assert reconstructed_seq == sequence_number, (
        "Round-trip sequence_number mismatch: expected {!r}, got {!r}".format(
            sequence_number, reconstructed_seq)
    )

    reconstructed_timestamp = reconstructed.timestamp
    assert reconstructed_timestamp == timestamp, (
        "Round-trip timestamp mismatch: expected {!r}, got {!r}".format(
            timestamp, reconstructed_timestamp)
    )

    reconstructed_event_type = reconstructed.event_type
    assert reconstructed_event_type == event_type, (
        "Round-trip event_type mismatch: expected {!r}, got {!r}".format(
            event_type, reconstructed_event_type)
    )

    reconstructed_agent_id = reconstructed.agent_id
    assert reconstructed_agent_id == agent_id, (
        "Round-trip agent_id mismatch: expected {!r}, got {!r}".format(
            agent_id, reconstructed_agent_id)
    )

    reconstructed_correlation_id = reconstructed.correlation_id
    assert reconstructed_correlation_id == correlation_id, (
        "Round-trip correlation_id mismatch: expected {!r}, got {!r}".format(
            correlation_id, reconstructed_correlation_id)
    )

    reconstructed_payload = reconstructed.payload
    assert reconstructed_payload == payload, (
        "Round-trip payload mismatch: expected {!r}, got {!r}".format(
            payload, reconstructed_payload)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
