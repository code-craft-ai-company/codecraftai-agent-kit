"""
    Tests for the automojo.agentkit.agentstatemachine module.

    Contains property-based tests (using automojo.testbase.properties) and unit tests
    for the AgentStateMachine class.

    Feature: core-agent-framework
"""

import threading

from datetime import datetime
from datetime import timezone


from automojo.testbase.properties import given, assume
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.agentstatemachine import AgentStateMachine
from automojo.agentkit.errors import SemanticError
from automojo.agentkit.lifecyclestate import LifecycleState
from automojo.agentkit.transitionrecord import TransitionRecord


# ---------------------------------------------------------------------------
# testbase property strategies for generating valid transition sequences
# ---------------------------------------------------------------------------

VALID_TRANSITIONS = AgentStateMachine.VALID_TRANSITIONS

ALL_STATES = list(LifecycleState)


def build_valid_transition_sequence(draw, min_length: int = 1, max_length: int = 20):
    """
        Builds a random valid transition sequence starting from CREATED.

        Uses a draw callable to draw random valid targets at each step.

        :param draw: The draw callable for drawing values from strategies.
        :param min_length: Minimum number of transitions.
        :param max_length: Maximum number of transitions.

        :returns: A list of LifecycleState values representing the sequence of targets.
    """
    sequence = []
    current = LifecycleState.CREATED
    length = draw(st.integers(min_value=min_length, max_value=max_length))

    for _ in range(length):
        valid_targets = VALID_TRANSITIONS[current]
        if len(valid_targets) == 0:
            break
        target = draw(st.sampled_from(valid_targets))
        sequence.append(target)
        current = target

    return sequence


# ---------------------------------------------------------------------------
# Property 8: State machine accepts valid transitions and updates state
# **Validates: Requirements 4.2, 4.3**
# ---------------------------------------------------------------------------

@composite
def _valid_transition_sequence_strategy(draw, min_length=1, max_length=20):
    """
        Composite strategy that generates a valid transition sequence.

        :returns: A list of LifecycleState values.
    """
    return build_valid_transition_sequence(draw, min_length=min_length, max_length=max_length)


@composite
def _invalid_transition_data(draw):
    """
        Composite strategy that generates a state machine navigated to a random state
        and an invalid target for that state.

        :returns: A tuple of (sequence_to_current, invalid_target).
    """
    sequence = build_valid_transition_sequence(draw, min_length=0, max_length=10)
    current = LifecycleState.CREATED
    for target in sequence:
        current = target
    valid_targets = VALID_TRANSITIONS[current]
    invalid_candidates = [s for s in ALL_STATES if s not in valid_targets]
    if len(invalid_candidates) == 0:
        return None
    invalid_target = draw(st.sampled_from(invalid_candidates))
    return (sequence, invalid_target)


@given(sequence=_valid_transition_sequence_strategy(min_length=1, max_length=20),
    constraints={"max_examples": 100})
def test_property_8_valid_transitions_update_state(sequence):
    """
        Property 8: State machine accepts valid transitions and updates state.

        For any valid transition sequence from the transition table,
        calling transition_to for each target updates current_state
        to the last target.

        **Validates: Requirements 4.2, 4.3**
    """
    sm = AgentStateMachine()

    assume(len(sequence) > 0)

    for target in sequence:
        sm.transition_to(target)

    last_target = sequence[-1]
    current = sm.current_state
    assert current is last_target, (
        "current_state should be {} but was {}".format(last_target, current)
    )
    return


# ---------------------------------------------------------------------------
# Property 9: State machine rejects invalid transitions
# **Validates: Requirements 4.4**
# ---------------------------------------------------------------------------

@given(test_data=_invalid_transition_data(),
    constraints={"max_examples": 100})
def test_property_9_rejects_invalid_transitions(test_data):
    """
        Property 9: State machine rejects invalid transitions.

        For any state and target not in the valid transitions table,
        calling transition_to raises SemanticError whose message
        includes the current state, target, and valid transitions.

        **Validates: Requirements 4.4**
    """
    assume(test_data is not None)
    sequence, invalid_target = test_data

    sm = AgentStateMachine()

    # First, navigate to a random valid state
    for target in sequence:
        sm.transition_to(target)

    current = sm.current_state
    valid_targets = VALID_TRANSITIONS[current]

    raised = False
    caught_error = None
    try:
        sm.transition_to(invalid_target)
    except SemanticError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "SemanticError should be raised for invalid transition from {} to {}".format(
            current.value, invalid_target.value
        )
    )

    error_message = str(caught_error)
    has_current = current.value in error_message
    has_target = invalid_target.value in error_message

    assert has_current is True, (
        "Error message should contain current state '{}', got: {}".format(
            current.value, error_message
        )
    )
    assert has_target is True, (
        "Error message should contain target state '{}', got: {}".format(
            invalid_target.value, error_message
        )
    )

    # Verify valid transitions are mentioned in the error message
    for valid_state in valid_targets:
        has_valid = valid_state.value in error_message
        assert has_valid is True, (
            "Error message should contain valid transition '{}', got: {}".format(
                valid_state.value, error_message
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 10: State machine records transition history
# **Validates: Requirements 4.5**
# ---------------------------------------------------------------------------

@given(sequence=_valid_transition_sequence_strategy(min_length=1, max_length=15),
    constraints={"max_examples": 100})
def test_property_10_records_transition_history(sequence):
    """
        Property 10: State machine records transition history.

        For any sequence of valid transitions, transition_history
        contains a TransitionRecord for each transition in order,
        with correct previous_state, new_state, and a valid timestamp.

        **Validates: Requirements 4.5**
    """
    sm = AgentStateMachine()

    assume(len(sequence) > 0)

    before_time = datetime.now(tz=timezone.utc)

    for target in sequence:
        sm.transition_to(target)

    after_time = datetime.now(tz=timezone.utc)

    history = sm.transition_history
    history_length = len(history)
    expected_length = len(sequence)

    assert history_length == expected_length, (
        "History length should be {} but was {}".format(expected_length, history_length)
    )

    expected_previous = LifecycleState.CREATED
    for idx in range(len(sequence)):
        record = history[idx]
        target = sequence[idx]

        is_transition_record = isinstance(record, TransitionRecord)
        assert is_transition_record is True, (
            "History entry {} should be a TransitionRecord".format(idx)
        )

        assert record.previous_state is expected_previous, (
            "Record {} previous_state should be {} but was {}".format(
                idx, expected_previous, record.previous_state
            )
        )

        assert record.new_state is target, (
            "Record {} new_state should be {} but was {}".format(
                idx, target, record.new_state
            )
        )

        ts = record.timestamp
        is_after_before = ts >= before_time
        is_before_after = ts <= after_time
        assert is_after_before is True, (
            "Record {} timestamp should be >= test start time".format(idx)
        )
        assert is_before_after is True, (
            "Record {} timestamp should be <= test end time".format(idx)
        )

        expected_previous = target

    return


# ---------------------------------------------------------------------------
# Property 11: State machine get_valid_transitions matches transition table
# **Validates: Requirements 4.7**
# ---------------------------------------------------------------------------

@given(state=st.sampled_from(ALL_STATES),
    constraints={"max_examples": 100})
def test_property_11_get_valid_transitions_matches_table(state):
    """
        Property 11: State machine get_valid_transitions matches transition table.

        For each LifecycleState, get_valid_transitions returns exactly
        the target states defined in VALID_TRANSITIONS[state].

        **Validates: Requirements 4.7**
    """
    sm = AgentStateMachine()

    # Navigate to the desired state via a known path
    paths_to_state = {
        LifecycleState.CREATED: [],
        LifecycleState.INITIALIZED: [LifecycleState.INITIALIZED],
        LifecycleState.RUNNING: [LifecycleState.INITIALIZED, LifecycleState.RUNNING],
        LifecycleState.PAUSED: [LifecycleState.INITIALIZED, LifecycleState.RUNNING, LifecycleState.PAUSED],
        LifecycleState.STOPPED: [LifecycleState.INITIALIZED, LifecycleState.STOPPED],
        LifecycleState.ERROR: [LifecycleState.INITIALIZED, LifecycleState.RUNNING, LifecycleState.ERROR],
    }

    path = paths_to_state[state]
    for target in path:
        sm.transition_to(target)

    actual = sm.get_valid_transitions()
    expected = VALID_TRANSITIONS[state]

    assert actual == expected, (
        "get_valid_transitions for {} should be {} but was {}".format(
            state.value, expected, actual
        )
    )
    return


# ---------------------------------------------------------------------------
# Unit tests for AgentStateMachine edge cases (Task 2.6)
# **Validates: Requirements 4.6, 4.8, 13.6, 16.5, 16.6**
# ---------------------------------------------------------------------------

def test_initial_state_is_created():
    """
        Verify that a new AgentStateMachine starts in the CREATED state.
    """
    sm = AgentStateMachine()
    current = sm.current_state
    assert current is LifecycleState.CREATED, (
        "Initial state should be CREATED but was {}".format(current)
    )
    return


def test_initial_transition_history_is_empty():
    """
        Verify that a new AgentStateMachine has an empty transition history.
    """
    sm = AgentStateMachine()
    history = sm.transition_history
    length = len(history)
    assert length == 0, "Initial transition history should be empty"
    return


def test_transition_history_is_defensive_copy():
    """
        Verify that transition_history returns a copy, not the internal list.
    """
    sm = AgentStateMachine()
    sm.transition_to(LifecycleState.INITIALIZED)

    history_one = sm.transition_history
    history_one.append("injected")

    history_two = sm.transition_history
    length = len(history_two)
    assert length == 1, "Modifying returned history should not affect internal state"
    return


def test_thread_safety_concurrent_transitions():
    """
        Verify that concurrent transitions do not corrupt the state machine.

        Multiple threads attempt valid transitions concurrently. The state
        machine should remain consistent with no exceptions other than
        SemanticError for invalid transitions.
    """
    sm = AgentStateMachine()
    sm.transition_to(LifecycleState.INITIALIZED)
    sm.transition_to(LifecycleState.RUNNING)

    errors = []
    semantic_errors = []

    def attempt_transition(target: LifecycleState) -> None:
        """
            Attempts a transition, recording any unexpected errors.

            :param target: The target state to transition to.
        """
        try:
            sm.transition_to(target)
        except SemanticError:
            semantic_errors.append(target)
        except Exception as exc:
            errors.append(exc)
        return

    threads = []
    # Multiple threads try to transition from RUNNING to different states
    targets = [
        LifecycleState.PAUSED,
        LifecycleState.STOPPED,
        LifecycleState.ERROR,
        LifecycleState.PAUSED,
        LifecycleState.STOPPED,
    ]

    for target in targets:
        t = threading.Thread(target=attempt_transition, args=(target,))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    unexpected_error_count = len(errors)
    assert unexpected_error_count == 0, (
        "No unexpected errors should occur, got: {}".format(errors)
    )

    # Exactly one transition should succeed, the rest should get SemanticError
    # because after the first transition, the state changes and the others become invalid
    history = sm.transition_history
    # We had 2 transitions before (INITIALIZED, RUNNING) plus at least 1 from threads
    total_transitions = len(history)
    assert total_transitions >= 3, (
        "At least 3 transitions should be recorded (2 setup + 1 concurrent)"
    )
    return


def test_repr_contains_class_name_and_state():
    """
        Verify that __repr__ includes the class name and current state.
    """
    sm = AgentStateMachine()
    repr_str = repr(sm)
    has_class_name = "AgentStateMachine" in repr_str
    has_state = "CREATED" in repr_str
    assert has_class_name is True, "repr should contain AgentStateMachine"
    assert has_state is True, "repr should contain the current state"
    return


def test_repr_updates_after_transition():
    """
        Verify that __repr__ reflects the updated state after a transition.
    """
    sm = AgentStateMachine()
    sm.transition_to(LifecycleState.INITIALIZED)
    repr_str = repr(sm)
    has_initialized = "INITIALIZED" in repr_str
    assert has_initialized is True, "repr should contain INITIALIZED after transition"
    return


def test_str_contains_current_state():
    """
        Verify that __str__ returns a human-readable string with the current state.
    """
    sm = AgentStateMachine()
    str_val = str(sm)
    has_class_name = "AgentStateMachine" in str_val
    has_state = "CREATED" in str_val
    assert has_class_name is True, "str should contain AgentStateMachine"
    assert has_state is True, "str should contain the current state"
    return


def test_str_updates_after_transition():
    """
        Verify that __str__ reflects the updated state after a transition.
    """
    sm = AgentStateMachine()
    sm.transition_to(LifecycleState.INITIALIZED)
    sm.transition_to(LifecycleState.RUNNING)
    str_val = str(sm)
    has_running = "RUNNING" in str_val
    assert has_running is True, "str should contain RUNNING after transition"
    return


def test_transition_to_returns_transition_record():
    """
        Verify that transition_to returns a TransitionRecord with correct fields.
    """
    sm = AgentStateMachine()
    before = datetime.now(tz=timezone.utc)
    record = sm.transition_to(LifecycleState.INITIALIZED)
    after = datetime.now(tz=timezone.utc)

    is_record = isinstance(record, TransitionRecord)
    assert is_record is True, "transition_to should return a TransitionRecord"

    assert record.previous_state is LifecycleState.CREATED, (
        "previous_state should be CREATED"
    )
    assert record.new_state is LifecycleState.INITIALIZED, (
        "new_state should be INITIALIZED"
    )

    is_after_before = record.timestamp >= before
    is_before_after = record.timestamp <= after
    assert is_after_before is True, "timestamp should be >= before time"
    assert is_before_after is True, "timestamp should be <= after time"
    return


def test_full_lifecycle_sequence():
    """
        Verify a complete lifecycle: CREATED -> INITIALIZED -> RUNNING ->
        PAUSED -> RUNNING -> STOPPED -> INITIALIZED.
    """
    sm = AgentStateMachine()

    sequence = [
        LifecycleState.INITIALIZED,
        LifecycleState.RUNNING,
        LifecycleState.PAUSED,
        LifecycleState.RUNNING,
        LifecycleState.STOPPED,
        LifecycleState.INITIALIZED,
    ]

    for target in sequence:
        sm.transition_to(target)

    current = sm.current_state
    assert current is LifecycleState.INITIALIZED, (
        "After full lifecycle, state should be INITIALIZED"
    )

    history = sm.transition_history
    history_length = len(history)
    assert history_length == 6, "Should have 6 transitions in history"
    return


def test_error_to_stopped_transition():
    """
        Verify that ERROR state can only transition to STOPPED.
    """
    sm = AgentStateMachine()
    sm.transition_to(LifecycleState.INITIALIZED)
    sm.transition_to(LifecycleState.RUNNING)
    sm.transition_to(LifecycleState.ERROR)

    valid = sm.get_valid_transitions()
    assert valid == [LifecycleState.STOPPED], (
        "ERROR should only allow transition to STOPPED"
    )

    sm.transition_to(LifecycleState.STOPPED)
    current = sm.current_state
    assert current is LifecycleState.STOPPED, "State should be STOPPED after ERROR -> STOPPED"
    return


def test_state_unchanged_after_invalid_transition():
    """
        Verify that the state does not change when an invalid transition is attempted.
    """
    sm = AgentStateMachine()

    raised = False
    try:
        sm.transition_to(LifecycleState.RUNNING)
    except SemanticError:
        raised = True

    assert raised is True, "SemanticError should be raised for CREATED -> RUNNING"

    current = sm.current_state
    assert current is LifecycleState.CREATED, (
        "State should remain CREATED after invalid transition attempt"
    )

    history = sm.transition_history
    history_length = len(history)
    assert history_length == 0, "No transition should be recorded for invalid attempt"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
