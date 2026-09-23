"""
    Unit tests for SelfHealingPolicy.
"""

from ccai.testbase.mocking import Mock

from ccai.agentkit.selfhealingpolicy import SelfHealingPolicy


def _create_mock_action(action_name="test_action"):
    """
        Creates a mock SelfHealingAction with the given action_name.
    """
    mock_action = Mock()
    mock_action.configure(recursive=True)
    ctx = mock_action.mock_context()
    ctx.set_attribute("action_name", action_name)
    return mock_action


def test_selfhealingpolicy_construction():
    """
        Verify SelfHealingPolicy stores all fields correctly.
    """
    action = _create_mock_action("reconnect_transport")
    policy = SelfHealingPolicy(
        check_name="transport-check",
        action=action,
        max_attempts=3,
        cooldown_interval=60.0
    )

    assert policy.check_name == "transport-check", "check_name should match"
    assert policy.action is action, "action should match"
    assert policy.max_attempts == 3, "max_attempts should match"
    assert policy.cooldown_interval == 60.0, "cooldown_interval should match"
    return


def test_selfhealingpolicy_as_dict():
    """
        Verify SelfHealingPolicy as_dict returns correct dictionary.
    """
    action = _create_mock_action("clear_cache")
    policy = SelfHealingPolicy(
        check_name="cache-check",
        action=action,
        max_attempts=5,
        cooldown_interval=120.0
    )

    data = policy.as_dict()

    assert data["check_name"] == "cache-check", "check_name should match"
    assert data["action_name"] == "clear_cache", "action_name should match"
    assert data["max_attempts"] == 5, "max_attempts should match"
    assert data["cooldown_interval"] == 120.0, "cooldown_interval should match"
    return


def test_selfhealingpolicy_repr():
    """
        Verify SelfHealingPolicy __repr__ contains key fields.
    """
    action = _create_mock_action("reconnect_transport")
    policy = SelfHealingPolicy("transport-check", action, 3, 60.0)

    repr_str = repr(policy)

    assert "SelfHealingPolicy" in repr_str, "repr should contain class name"
    assert "transport-check" in repr_str, "repr should contain check_name"
    return


def test_selfhealingpolicy_str():
    """
        Verify SelfHealingPolicy __str__ contains key fields.
    """
    action = _create_mock_action("clear_cache")
    policy = SelfHealingPolicy("cache-check", action, 5, 120.0)

    str_val = str(policy)

    assert "cache-check" in str_val, "str should contain check_name"
    assert "clear_cache" in str_val, "str should contain action_name"
    assert "5" in str_val, "str should contain max_attempts"
    return
