"""
    Unit tests for the ccai.agentkit.lifecyclestate module.

    Tests that all six LifecycleState enum values exist and have
    the expected string values.
"""

import enum

from ccai.agentkit.lifecyclestate import LifecycleState


def test_lifecyclestate_is_enum():
    """
        Verify that LifecycleState is an Enum class.
    """
    is_enum = issubclass(LifecycleState, enum.Enum)
    assert is_enum is True, "LifecycleState should be an Enum"
    return


def test_lifecyclestate_has_created():
    """
        Verify that the CREATED state exists with value 'CREATED'.
    """
    state = LifecycleState.CREATED
    assert state.value == "CREATED", "CREATED state should have value 'CREATED'"
    return


def test_lifecyclestate_has_initialized():
    """
        Verify that the INITIALIZED state exists with value 'INITIALIZED'.
    """
    state = LifecycleState.INITIALIZED
    assert state.value == "INITIALIZED", "INITIALIZED state should have value 'INITIALIZED'"
    return


def test_lifecyclestate_has_running():
    """
        Verify that the RUNNING state exists with value 'RUNNING'.
    """
    state = LifecycleState.RUNNING
    assert state.value == "RUNNING", "RUNNING state should have value 'RUNNING'"
    return


def test_lifecyclestate_has_paused():
    """
        Verify that the PAUSED state exists with value 'PAUSED'.
    """
    state = LifecycleState.PAUSED
    assert state.value == "PAUSED", "PAUSED state should have value 'PAUSED'"
    return


def test_lifecyclestate_has_stopped():
    """
        Verify that the STOPPED state exists with value 'STOPPED'.
    """
    state = LifecycleState.STOPPED
    assert state.value == "STOPPED", "STOPPED state should have value 'STOPPED'"
    return


def test_lifecyclestate_has_error():
    """
        Verify that the ERROR state exists with value 'ERROR'.
    """
    state = LifecycleState.ERROR
    assert state.value == "ERROR", "ERROR state should have value 'ERROR'"
    return


def test_lifecyclestate_has_exactly_six_members():
    """
        Verify that LifecycleState has exactly six members.
    """
    member_count = len(LifecycleState)
    assert member_count == 6, "LifecycleState should have exactly 6 members, got {}".format(member_count)
    return


def test_lifecyclestate_members_are_correct_set():
    """
        Verify that the set of member names matches the expected set.
    """
    expected_names = {"CREATED", "INITIALIZED", "RUNNING", "PAUSED", "STOPPED", "ERROR"}
    actual_names = {member.name for member in LifecycleState}
    assert actual_names == expected_names, "LifecycleState members should be {}".format(expected_names)
    return
