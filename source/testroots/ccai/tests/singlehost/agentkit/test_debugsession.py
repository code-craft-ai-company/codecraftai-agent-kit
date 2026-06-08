"""
    Unit tests for the ccai.agentkit.debugsession module.

    Tests the DebugSession class: add/remove/list/clear breakpoints,
    start/stop, pause callback invocation, continue_execution, step,
    is_paused/is_active, __repr__, and __str__.
"""

from ccai.agentkit.breakpoint import Breakpoint
from ccai.agentkit.debuginspector import DebugInspector
from ccai.agentkit.debugsession import DebugSession
from ccai.testbase.mocking import Mock


def _create_mock_agent():
    """
        Creates a mock Agent with recursive attribute access configured.

        :returns: A Mock object configured to simulate an Agent.
    """
    mock_agent = Mock()
    mock_agent.configure(recursive=True)
    mock_identity = Mock()
    mock_identity.configure(recursive=True)
    mock_identity.mock_context().set_attribute("identifier", "agent-test")
    mock_agent.mock_context().set_attribute("identity", mock_identity)
    return mock_agent


def test_initial_state():
    """
        Verify that a new DebugSession starts inactive and not paused.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    assert session.is_active is False, "Session should start inactive"
    assert session.is_paused is False, "Session should start not paused"
    assert session.inspector is None, "Inspector should be None initially"
    return


def test_add_breakpoint():
    """
        Verify that add_breakpoint registers a breakpoint.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool", target_name="search")
    session.add_breakpoint(bp)

    breakpoints = session.list_breakpoints()
    assert len(breakpoints) == 1, "Should have 1 breakpoint"
    assert breakpoints[0] is bp, "Should be the same breakpoint"
    return


def test_add_multiple_breakpoints():
    """
        Verify that multiple breakpoints can be added.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp1 = Breakpoint(breakpoint_type="tool")
    bp2 = Breakpoint(breakpoint_type="lifecycle")
    bp3 = Breakpoint(breakpoint_type="llm")

    session.add_breakpoint(bp1)
    session.add_breakpoint(bp2)
    session.add_breakpoint(bp3)

    breakpoints = session.list_breakpoints()
    assert len(breakpoints) == 3, "Should have 3 breakpoints"
    return


def test_remove_breakpoint():
    """
        Verify that remove_breakpoint deregisters a breakpoint.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.remove_breakpoint(bp)

    breakpoints = session.list_breakpoints()
    assert len(breakpoints) == 0, "Should have 0 breakpoints after removal"
    return


def test_remove_nonexistent_breakpoint_does_nothing():
    """
        Verify that removing a breakpoint not in the list does nothing.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp1 = Breakpoint(breakpoint_type="tool")
    bp2 = Breakpoint(breakpoint_type="lifecycle")
    session.add_breakpoint(bp1)
    session.remove_breakpoint(bp2)

    breakpoints = session.list_breakpoints()
    assert len(breakpoints) == 1, "Should still have 1 breakpoint"
    return


def test_list_breakpoints_returns_copy():
    """
        Verify that list_breakpoints returns a copy of the list.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)

    result = session.list_breakpoints()
    result.clear()

    assert len(session.list_breakpoints()) == 1, (
        "Modifying returned list should not affect session"
    )
    return


def test_clear_breakpoints():
    """
        Verify that clear_breakpoints removes all breakpoints.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    session.add_breakpoint(Breakpoint(breakpoint_type="tool"))
    session.add_breakpoint(Breakpoint(breakpoint_type="lifecycle"))
    session.clear_breakpoints()

    breakpoints = session.list_breakpoints()
    assert len(breakpoints) == 0, "Should have 0 breakpoints after clear"
    return


def test_start_activates_session():
    """
        Verify that start enables the debug session.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    session.start()
    assert session.is_active is True, "Session should be active after start"
    return


def test_stop_deactivates_session():
    """
        Verify that stop disables the debug session.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    session.start()
    session.stop()

    assert session.is_active is False, "Session should be inactive after stop"
    assert session.is_paused is False, "Session should not be paused after stop"
    return


def test_stop_resumes_paused_execution():
    """
        Verify that stop clears paused state and inspector.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()
    session.check_breakpoint("tool")

    assert session.is_paused is True, "Should be paused after matching breakpoint"

    session.stop()

    assert session.is_paused is False, "Should not be paused after stop"
    assert session.inspector is None, "Inspector should be None after stop"
    return


def test_check_breakpoint_pauses_on_match():
    """
        Verify that check_breakpoint pauses when a breakpoint matches.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()

    session.check_breakpoint("tool")

    assert session.is_paused is True, "Should be paused on matching breakpoint"
    assert session.inspector is not None, "Inspector should be set when paused"
    return


def test_check_breakpoint_does_not_pause_on_no_match():
    """
        Verify that check_breakpoint does not pause when no breakpoint matches.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()

    session.check_breakpoint("lifecycle")

    assert session.is_paused is False, "Should not be paused when no match"
    assert session.inspector is None, "Inspector should be None when not paused"
    return


def test_check_breakpoint_inactive_session_does_not_pause():
    """
        Verify that check_breakpoint does nothing when session is inactive.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)

    session.check_breakpoint("tool")

    assert session.is_paused is False, "Should not pause when session is inactive"
    return


def test_pause_callback_invoked_on_match():
    """
        Verify that the pause callback is invoked with a DebugInspector
        when a breakpoint matches.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    callback_args = []

    def on_pause(inspector):
        callback_args.append(inspector)
        return

    session.set_pause_callback(on_pause)
    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()

    session.check_breakpoint("tool")

    assert len(callback_args) == 1, "Callback should be invoked once"
    assert isinstance(callback_args[0], DebugInspector), (
        "Callback should receive a DebugInspector"
    )
    return


def test_pause_callback_not_invoked_on_no_match():
    """
        Verify that the pause callback is not invoked when no breakpoint
        matches.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    callback_count = [0]

    def on_pause(inspector):
        callback_count[0] += 1
        return

    session.set_pause_callback(on_pause)
    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()

    session.check_breakpoint("lifecycle")

    assert callback_count[0] == 0, "Callback should not be invoked on no match"
    return


def test_continue_execution_clears_pause():
    """
        Verify that continue_execution clears the paused state.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()
    session.check_breakpoint("tool")

    assert session.is_paused is True, "Should be paused"

    session.continue_execution()

    assert session.is_paused is False, "Should not be paused after continue"
    assert session.inspector is None, "Inspector should be None after continue"
    return


def test_step_clears_pause():
    """
        Verify that step clears the paused state.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool")
    session.add_breakpoint(bp)
    session.start()
    session.check_breakpoint("tool")

    assert session.is_paused is True, "Should be paused"

    session.step()

    assert session.is_paused is False, "Should not be paused after step"
    assert session.inspector is None, "Inspector should be None after step"
    return


def test_check_breakpoint_with_target_name():
    """
        Verify that check_breakpoint matches breakpoints with target_name.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool", target_name="search")
    session.add_breakpoint(bp)
    session.start()

    session.check_breakpoint("tool", target_name="search")

    assert session.is_paused is True, "Should pause on matching type and target"
    return


def test_check_breakpoint_with_wrong_target_name():
    """
        Verify that check_breakpoint does not pause when target_name
        does not match.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    bp = Breakpoint(breakpoint_type="tool", target_name="search")
    session.add_breakpoint(bp)
    session.start()

    session.check_breakpoint("tool", target_name="execute")

    assert session.is_paused is False, "Should not pause on wrong target_name"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    repr_str = repr(session)
    assert "DebugSession" in repr_str, "__repr__ should contain class name"
    return


def test_repr_contains_agent_id():
    """
        Verify that __repr__ contains the agent identifier.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    repr_str = repr(session)
    assert "agent-test" in repr_str, "__repr__ should contain agent_id"
    return


def test_str_contains_breakpoint_count():
    """
        Verify that __str__ contains the breakpoint count.
    """
    mock_agent = _create_mock_agent()
    session = DebugSession(mock_agent)

    session.add_breakpoint(Breakpoint(breakpoint_type="tool"))
    session.add_breakpoint(Breakpoint(breakpoint_type="lifecycle"))

    str_val = str(session)
    assert "2" in str_val, "__str__ should contain breakpoint count"
    return
