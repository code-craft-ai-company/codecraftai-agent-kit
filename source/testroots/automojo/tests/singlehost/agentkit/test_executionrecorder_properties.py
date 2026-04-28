"""
    Property-based tests for the automojo.agentkit.executionrecorder module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 25: ExecutionRecorder assigns monotonically increasing
      sequence numbers

    **Validates: Requirements 19.3**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.executionrecorder import ExecutionRecorder


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_short_text = st.text(min_size=1, max_size=50)

_event_strategy = st.tuples(
    _short_text,
    _short_text,
)

_events_strategy = st.lists(
    _event_strategy,
    min_size=1,
    max_size=50,
)


# ---------------------------------------------------------------------------
# Property 25: ExecutionRecorder assigns monotonically increasing
#              sequence numbers
# ---------------------------------------------------------------------------

@given(
    agent_id=_short_text,
    events=_events_strategy,
    constraints={"max_examples": 50},
)
def test_executionrecorder_monotonically_increasing_sequence_numbers(agent_id, events):
    """
        **Validates: Requirements 19.3**

        FOR ANY N events recorded by an ExecutionRecorder, the sequence
        numbers assigned to the records SHALL be 1 through N in order.
    """
    recorder = ExecutionRecorder(agent_id=agent_id)
    recorder.start()

    for event_type, correlation_id in events:
        recorder.record(event_type, correlation_id)

    recording = recorder.get_recording()
    records = recording.records

    expected_count = len(events)
    actual_count = len(records)
    assert actual_count == expected_count, (
        "Record count mismatch: expected {}, got {}".format(
            expected_count, actual_count)
    )

    for i, record in enumerate(records):
        expected_seq = i + 1
        actual_seq = record.sequence_number
        assert actual_seq == expected_seq, (
            "Sequence number at index {} mismatch: expected {}, got {}".format(
                i, expected_seq, actual_seq)
        )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
