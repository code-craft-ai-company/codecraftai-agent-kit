"""
    Unit tests for the automojo.agentkit.executionrecorder module.

    Tests the ExecutionRecorder class: start/stop, record while active
    and inactive, sequence numbers, get_recording, clear, count,
    is_recording, __repr__, and __str__.
"""

from automojo.agentkit.executionrecorder import ExecutionRecorder


def test_initial_state():
    """
        Verify that a new ExecutionRecorder starts with count 0 and not recording.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")

    assert recorder.count == 0, "initial count should be 0"
    assert recorder.is_recording is False, "initial is_recording should be False"
    return


def test_start_enables_recording():
    """
        Verify that start sets is_recording to True.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()

    assert recorder.is_recording is True, "is_recording should be True after start"
    return


def test_stop_disables_recording():
    """
        Verify that stop sets is_recording to False.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.stop()

    assert recorder.is_recording is False, "is_recording should be False after stop"
    return


def test_record_while_active_captures_event():
    """
        Verify that record captures an event when recording is active.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc", payload={"state": "running"})

    assert recorder.count == 1, "count should be 1 after recording one event"
    return


def test_record_while_inactive_discards_event():
    """
        Verify that record silently discards events when not recording.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.record("lifecycle", "corr-abc")

    assert recorder.count == 0, "count should be 0 when recording while inactive"
    return


def test_sequence_numbers_start_from_one():
    """
        Verify that sequence numbers start from 1.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc")

    recording = recorder.get_recording()
    records = recording.records

    assert records[0].sequence_number == 1, "first sequence number should be 1"
    return


def test_sequence_numbers_are_monotonically_increasing():
    """
        Verify that sequence numbers increase monotonically.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc")
    recorder.record("tool", "corr-abc")
    recorder.record("llm", "corr-abc")

    recording = recorder.get_recording()
    records = recording.records

    assert records[0].sequence_number == 1, "first seq should be 1"
    assert records[1].sequence_number == 2, "second seq should be 2"
    assert records[2].sequence_number == 3, "third seq should be 3"
    return


def test_get_recording_returns_all_records():
    """
        Verify that get_recording returns an ExecutionRecording with all captured records.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc")
    recorder.record("tool", "corr-def")
    recorder.stop()

    recording = recorder.get_recording()

    assert recording.agent_id == "agent-001", "recording agent_id should match"
    assert len(recording.records) == 2, "recording should have 2 records"
    return


def test_get_recording_preserves_event_types():
    """
        Verify that get_recording preserves event types in order.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc")
    recorder.record("tool", "corr-abc")
    recorder.stop()

    recording = recorder.get_recording()
    records = recording.records

    assert records[0].event_type == "lifecycle", "first event_type should be lifecycle"
    assert records[1].event_type == "tool", "second event_type should be tool"
    return


def test_clear_resets_records_and_counter():
    """
        Verify that clear removes all records and resets the sequence counter.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc")
    recorder.record("tool", "corr-abc")
    recorder.clear()

    assert recorder.count == 0, "count should be 0 after clear"

    recorder.start()
    recorder.record("llm", "corr-xyz")

    recording = recorder.get_recording()
    records = recording.records

    assert records[0].sequence_number == 1, "sequence should restart from 1 after clear"
    return


def test_record_after_stop_discards():
    """
        Verify that recording after stop discards events.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    recorder.start()
    recorder.record("lifecycle", "corr-abc")
    recorder.stop()
    recorder.record("tool", "corr-abc")

    assert recorder.count == 1, "count should still be 1 after recording while stopped"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    repr_str = repr(recorder)

    assert "ExecutionRecorder" in repr_str, "__repr__ should contain class name"
    return


def test_str_contains_agent_id():
    """
        Verify that __str__ contains the agent identifier.
    """
    recorder = ExecutionRecorder(agent_id="agent-001")
    str_val = str(recorder)

    assert "agent-001" in str_val, "__str__ should contain agent_id"
    return
