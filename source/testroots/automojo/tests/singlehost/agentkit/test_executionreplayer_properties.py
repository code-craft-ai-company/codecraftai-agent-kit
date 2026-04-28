"""
    Property-based tests for the automojo.agentkit.executionreplayer module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 28: ExecutionReplayer traversal visits all records in order

    **Validates: Requirements 21.2, 21.3**
"""

from datetime import datetime

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.executionrecord import ExecutionRecord
from automojo.agentkit.executionrecording import ExecutionRecording
from automojo.agentkit.executionreplayer import ExecutionReplayer


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

_short_text = st.text(min_size=1, max_size=50)

_event_type_strategy = st.sampled_from(["lifecycle", "tool", "llm", "memory", "workflow"])


# ---------------------------------------------------------------------------
# Property 28: ExecutionReplayer traversal visits all records in order
# ---------------------------------------------------------------------------

@given(
    agent_id=_short_text,
    start_time=_timestamp_strategy,
    end_time=_timestamp_strategy,
    event_types=st.lists(_event_type_strategy, min_size=1, max_size=20),
    correlation_id=_short_text,
    constraints={"max_examples": 50},
)
def test_executionreplayer_traversal_visits_all_records_in_order(agent_id, start_time, end_time, event_types, correlation_id):
    """
        **Validates: Requirements 21.2, 21.3**

        FOR ANY ExecutionRecording with N records, calling next() N times
        on an ExecutionReplayer SHALL return each record in sequence order
        (sequence numbers 1 through N), and calling next() once more SHALL
        return None.
    """
    records = []
    for i, event_type in enumerate(event_types):
        record = ExecutionRecord(
            sequence_number=i + 1,
            timestamp=start_time,
            event_type=event_type,
            agent_id=agent_id,
            correlation_id=correlation_id,
        )
        records.append(record)

    recording = ExecutionRecording(
        agent_id=agent_id,
        start_time=start_time,
        end_time=end_time,
        records=records,
    )

    replayer = ExecutionReplayer(recording)

    expected_count = len(records)

    for i in range(expected_count):
        record = replayer.next()

        assert record is not None, (
            "next() returned None at step {} of {}, expected a record".format(
                i + 1, expected_count)
        )

        expected_seq = i + 1
        actual_seq = record.sequence_number
        assert actual_seq == expected_seq, (
            "Traversal sequence mismatch at step {}: expected seq {}, got {}".format(
                i + 1, expected_seq, actual_seq)
        )

    past_end = replayer.next()
    assert past_end is None, (
        "next() after traversing all {} records should return None, got {!r}".format(
            expected_count, past_end)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
