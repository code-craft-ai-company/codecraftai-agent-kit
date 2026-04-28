"""
    Property-based tests for the automojo.agentkit.executionrecording module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 26: ExecutionRecording JSON round-trip preserves all fields
    - Property 27: ExecutionRecording filter_by_event_type correctness

    **Validates: Requirements 20.4, 20.6, 20.8, 20.9**
"""

from datetime import datetime

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.executionrecord import ExecutionRecord
from automojo.agentkit.executionrecording import ExecutionRecording


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
    max_size=3,
)

_event_type_strategy = st.sampled_from(["lifecycle", "tool", "llm", "memory", "workflow"])

_sequence_number_strategy = st.integers(min_value=1, max_value=1000000)


def _build_record(seq, event_type, agent_id, correlation_id, timestamp, payload):
    """
        Helper to build an ExecutionRecord from strategy-generated values.
    """
    return ExecutionRecord(
        sequence_number=seq,
        timestamp=timestamp,
        event_type=event_type,
        agent_id=agent_id,
        correlation_id=correlation_id,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# Property 26: ExecutionRecording JSON round-trip
# ---------------------------------------------------------------------------

@given(
    agent_id=_short_text,
    start_time=_timestamp_strategy,
    end_time=_timestamp_strategy,
    event_types=st.lists(_event_type_strategy, min_size=0, max_size=10),
    correlation_id=_short_text,
    payload=_payload_strategy,
    constraints={"max_examples": 50},
)
def test_executionrecording_json_round_trip(agent_id, start_time, end_time, event_types, correlation_id, payload):
    """
        **Validates: Requirements 20.6, 20.8, 20.9**

        FOR ALL valid ExecutionRecording instances with any combination of
        agent_id, start_time, end_time, and records, calling to_json and
        then from_json SHALL produce an ExecutionRecording whose fields
        are equal to the original.
    """
    records = []
    for i, event_type in enumerate(event_types):
        record = _build_record(i + 1, event_type, agent_id, correlation_id, start_time, payload)
        records.append(record)

    original = ExecutionRecording(
        agent_id=agent_id, start_time=start_time, end_time=end_time, records=records,
    )

    json_str = original.to_json()
    reconstructed = ExecutionRecording.from_json(json_str)

    assert reconstructed.agent_id == agent_id, (
        "Round-trip agent_id mismatch: expected {rm -rf .output}, got {rm -rf .output}".format(agent_id, reconstructed.agent_id))
    assert reconstructed.start_time == start_time, (
        "Round-trip start_time mismatch: expected {rm -rf .output}, got {rm -rf .output}".format(start_time, reconstructed.start_time))
    assert reconstructed.end_time == end_time, (
        "Round-trip end_time mismatch: expected {rm -rf .output}, got {rm -rf .output}".format(end_time, reconstructed.end_time))

    assert len(reconstructed.records) == len(original.records), (
        "Round-trip record count mismatch: expected {}, got {}".format(len(original.records), len(reconstructed.records)))

    for i in range(len(original.records)):
        orig_rec = original.records[i]
        recon_rec = reconstructed.records[i]
        assert recon_rec.sequence_number == orig_rec.sequence_number, (
            "Round-trip record[{}] sequence_number mismatch".format(i))
        assert recon_rec.event_type == orig_rec.event_type, (
            "Round-trip record[{}] event_type mismatch".format(i))
        assert recon_rec.agent_id == orig_rec.agent_id, (
            "Round-trip record[{}] agent_id mismatch".format(i))
        assert recon_rec.correlation_id == orig_rec.correlation_id, (
            "Round-trip record[{}] correlation_id mismatch".format(i))
        assert recon_rec.payload == orig_rec.payload, (
            "Round-trip record[{}] payload mismatch".format(i))

    return


# ---------------------------------------------------------------------------
# Property 27: ExecutionRecording filter_by_event_type correctness
# ---------------------------------------------------------------------------

@given(
    agent_id=_short_text,
    start_time=_timestamp_strategy,
    end_time=_timestamp_strategy,
    event_types=st.lists(_event_type_strategy, min_size=1, max_size=20),
    filter_type=_event_type_strategy,
    correlation_id=_short_text,
    constraints={"max_examples": 50},
)
def test_executionrecording_filter_by_event_type_correctness(agent_id, start_time, end_time, event_types, filter_type, correlation_id):
    """
        **Validates: Requirements 20.4**

        FOR ALL valid ExecutionRecording instances and any event type
        string, filter_by_event_type SHALL return exactly the records
        whose event_type matches the filter, in the original order.
    """
    records = []
    for i, event_type in enumerate(event_types):
        record = ExecutionRecord(
            sequence_number=i + 1, timestamp=start_time, event_type=event_type,
            agent_id=agent_id, correlation_id=correlation_id,
        )
        records.append(record)

    recording = ExecutionRecording(
        agent_id=agent_id, start_time=start_time, end_time=end_time, records=records,
    )

    filtered = recording.filter_by_event_type(filter_type)
    filtered_records = filtered.records
    expected_records = [r for r in records if r.event_type == filter_type]

    assert len(filtered_records) == len(expected_records), (
        "Filter count mismatch: expected {}, got {}".format(len(expected_records), len(filtered_records)))

    for i in range(len(expected_records)):
        assert filtered_records[i].sequence_number == expected_records[i].sequence_number, (
            "Filter record[{}] sequence_number mismatch: expected {}, got {}".format(
                i, expected_records[i].sequence_number, filtered_records[i].sequence_number))

    for record in filtered_records:
        assert record.event_type == filter_type, (
            "Filtered record has wrong event_type: expected {rm -rf .output}, got {rm -rf .output}".format(filter_type, record.event_type))

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
