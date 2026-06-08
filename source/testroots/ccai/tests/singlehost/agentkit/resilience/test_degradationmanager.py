"""
    Unit tests for the ccai.agentkit.degradationmanager module.
"""

from ccai.agentkit.defaultvaluestrategy import DefaultValueStrategy
from ccai.agentkit.degradationlevel import DegradationLevel
from ccai.agentkit.degradationmanager import DegradationManager
from ccai.agentkit.degradationpolicy import DegradationPolicy


def test_initial_overall_level_is_normal():
    """
        Verify that initial overall level is NORMAL.
    """
    manager = DegradationManager("agent-1")
    assert manager.overall_level is DegradationLevel.NORMAL, "initial level should be NORMAL"
    return


def test_register_and_deregister_policy():
    """
        Verify that policies can be registered and deregistered.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)

    manager.register_policy(policy)
    assert manager.get_policy("db") is policy, "policy should be registered"

    manager.deregister_policy("db")
    assert manager.get_policy("db") is None, "policy should be deregistered"
    return


def test_report_failure_changes_level():
    """
        Verify that report_failure changes the dependency level.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    manager.register_policy(policy)

    manager.report_failure("db", RuntimeError("connection lost"))
    assert manager.get_dependency_level("db") is DegradationLevel.DEGRADED, "should be DEGRADED"

    manager.report_failure("db", RuntimeError("still down"))
    assert manager.get_dependency_level("db") is DegradationLevel.CRITICAL, "should be CRITICAL"
    return


def test_report_recovery_returns_to_normal():
    """
        Verify that report_recovery returns the dependency to NORMAL.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    manager.register_policy(policy)

    manager.report_failure("db", RuntimeError("down"))
    assert manager.get_dependency_level("db") is DegradationLevel.DEGRADED, "should be DEGRADED"

    manager.report_recovery("db")
    assert manager.get_dependency_level("db") is DegradationLevel.NORMAL, "should be NORMAL after recovery"
    return


def test_overall_level_is_maximum():
    """
        Verify that overall_level is the maximum across all dependencies.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")

    policy1 = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    policy2 = DegradationPolicy("cache", strategy, DegradationLevel.DEGRADED)
    manager.register_policy(policy1)
    manager.register_policy(policy2)

    manager.report_failure("db", RuntimeError("down"))
    assert manager.overall_level is DegradationLevel.DEGRADED, "overall should be DEGRADED"

    manager.report_failure("cache", RuntimeError("down"))
    manager.report_failure("cache", RuntimeError("still down"))
    assert manager.overall_level is DegradationLevel.CRITICAL, "overall should be CRITICAL"
    return


def test_listener_notification():
    """
        Verify that listeners are notified on degradation changes.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    manager.register_policy(policy)

    events = []
    manager.add_listener(lambda e: events.append(e))

    manager.report_failure("db", RuntimeError("down"))
    assert len(events) == 1, "listener should be notified"
    assert events[0].dependency_name == "db", "event should contain dependency name"
    return


def test_listener_exception_handling():
    """
        Verify that listener exceptions are caught and logged.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    manager.register_policy(policy)

    def bad_listener(event):
        raise RuntimeError("listener error")

    good_events = []
    manager.add_listener(bad_listener)
    manager.add_listener(lambda e: good_events.append(e))

    # Should not raise despite bad listener
    manager.report_failure("db", RuntimeError("down"))
    assert len(good_events) == 1, "good listener should still be notified"
    return


def test_remove_listener():
    """
        Verify that removed listeners are no longer notified.
    """
    manager = DegradationManager("agent-1")
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    manager.register_policy(policy)

    events = []
    listener = lambda e: events.append(e)
    manager.add_listener(listener)
    manager.remove_listener(listener)

    manager.report_failure("db", RuntimeError("down"))
    assert len(events) == 0, "removed listener should not be notified"
    return


def test_repr():
    """
        Verify that __repr__ includes key fields.
    """
    manager = DegradationManager("agent-1")
    repr_str = repr(manager)
    assert "DegradationManager" in repr_str, "repr should contain class name"
    assert "agent-1" in repr_str, "repr should contain agent identifier"
    return
