"""
    Unit tests for the ccai.agentkit.transitionrecord module.

    Tests that TransitionRecord properties are read-only, metadata
    returns a defensive copy, and all fields are correctly stored.
"""

from datetime import datetime
from datetime import timezone

from ccai.agentkit.lifecyclestate import LifecycleState
from ccai.agentkit.transitionrecord import TransitionRecord


def test_transitionrecord_stores_previous_state():
    """
        Verify that previous_state property returns the provided state.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now
    )
    previous = record.previous_state
    assert previous is LifecycleState.CREATED, "previous_state should be CREATED"
    return


def test_transitionrecord_stores_new_state():
    """
        Verify that new_state property returns the provided state.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now
    )
    new = record.new_state
    assert new is LifecycleState.INITIALIZED, "new_state should be INITIALIZED"
    return


def test_transitionrecord_stores_timestamp():
    """
        Verify that timestamp property returns the provided datetime.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.RUNNING,
        new_state=LifecycleState.PAUSED,
        timestamp=now
    )
    ts = record.timestamp
    assert ts is now, "timestamp should be the exact datetime provided"
    return


def test_transitionrecord_metadata_default_is_empty_dict():
    """
        Verify that metadata defaults to an empty dict when not provided.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now
    )
    meta = record.metadata
    assert meta == {}, "metadata should default to an empty dict"
    return


def test_transitionrecord_metadata_stores_provided_values():
    """
        Verify that metadata stores the provided dictionary values.
    """
    now = datetime.now(tz=timezone.utc)
    input_meta = {"reason": "user request", "agent_id": "abc-123"}
    record = TransitionRecord(
        previous_state=LifecycleState.RUNNING,
        new_state=LifecycleState.STOPPED,
        timestamp=now,
        metadata=input_meta
    )
    meta = record.metadata
    assert meta == input_meta, "metadata should contain the provided values"
    return


def test_transitionrecord_metadata_returns_defensive_copy():
    """
        Verify that metadata property returns a copy, not the internal dict.
    """
    now = datetime.now(tz=timezone.utc)
    input_meta = {"key": "value"}
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now,
        metadata=input_meta
    )

    copy_one = record.metadata
    copy_one["injected"] = "should not appear"

    copy_two = record.metadata
    has_injected = "injected" in copy_two
    assert has_injected is False, "Modifying returned metadata should not affect the internal state"
    return


def test_transitionrecord_input_metadata_mutation_does_not_affect_record():
    """
        Verify that mutating the input metadata dict does not affect the record.
    """
    now = datetime.now(tz=timezone.utc)
    input_meta = {"original": "data"}
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now,
        metadata=input_meta
    )

    input_meta["mutated"] = "should not appear"

    meta = record.metadata
    has_mutated = "mutated" in meta
    assert has_mutated is False, "Mutating input metadata should not affect the record"
    return


def test_transitionrecord_previous_state_is_readonly():
    """
        Verify that previous_state cannot be set directly.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now
    )

    raised = False
    try:
        record.previous_state = LifecycleState.RUNNING
    except AttributeError:
        raised = True

    assert raised is True, "previous_state should be read-only"
    return


def test_transitionrecord_new_state_is_readonly():
    """
        Verify that new_state cannot be set directly.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now
    )

    raised = False
    try:
        record.new_state = LifecycleState.RUNNING
    except AttributeError:
        raised = True

    assert raised is True, "new_state should be read-only"
    return


def test_transitionrecord_timestamp_is_readonly():
    """
        Verify that timestamp cannot be set directly.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.CREATED,
        new_state=LifecycleState.INITIALIZED,
        timestamp=now
    )

    raised = False
    try:
        record.timestamp = datetime.now(tz=timezone.utc)
    except AttributeError:
        raised = True

    assert raised is True, "timestamp should be read-only"
    return


def test_transitionrecord_repr_contains_states():
    """
        Verify that __repr__ includes the previous and new states.
    """
    now = datetime.now(tz=timezone.utc)
    record = TransitionRecord(
        previous_state=LifecycleState.RUNNING,
        new_state=LifecycleState.PAUSED,
        timestamp=now
    )
    repr_str = repr(record)
    has_class_name = "TransitionRecord" in repr_str
    has_running = "RUNNING" in repr_str
    has_paused = "PAUSED" in repr_str
    assert has_class_name is True, "repr should contain TransitionRecord"
    assert has_running is True, "repr should contain the previous state"
    assert has_paused is True, "repr should contain the new state"
    return
