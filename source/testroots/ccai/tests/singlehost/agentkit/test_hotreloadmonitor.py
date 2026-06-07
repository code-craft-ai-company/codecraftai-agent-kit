"""
    Unit tests for the ccai.agentkit.hotreloadmonitor module.

    Tests the HotReloadMonitor class covering constructor initialization,
    start/stop state transitions, change_count behavior, reload failure
    handling, and string representations.

    Requirements: 9.1, 9.2, 9.3, 9.6, 9.7, 9.8
"""

from ccai.agentkit.configurationerrors import ConfigurationValidationError
from ccai.agentkit.hotreloadmonitor import HotReloadMonitor
from ccai.agentkit.hotreloadpolicy import HotReloadPolicy
from ccai.testbase.mocking import Mock


# ---- Helper Functions ----


def create_mock_configuration_manager():
    """
        Creates a mock ConfigurationManager with a recursive configuration
        and a reload method that returns None by default.

        :returns: A Mock object configured as a ConfigurationManager.
    """
    mock_manager = Mock()
    mock_manager.configure(recursive=True)
    mock_manager.mock_context().mock_method("reload", return_value=None)
    return mock_manager


# ---- Constructor Tests ----


def test_constructor_initializes_is_active_to_false():
    """
        Verify that the constructor initializes is_active to False.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    stored_active = monitor.is_active
    assert stored_active is False, "constructor should initialize is_active to False"
    return


def test_constructor_initializes_change_count_to_zero():
    """
        Verify that the constructor initializes change_count to 0.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    stored_count = monitor.change_count
    assert stored_count == 0, "constructor should initialize change_count to 0"
    return


# ---- Start / Stop State Transition Tests ----


def test_start_sets_is_active_to_true():
    """
        Verify that calling start sets is_active to True.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor.start()
    stored_active = monitor.is_active
    monitor.stop()

    assert stored_active is True, "start should set is_active to True"
    return


def test_stop_sets_is_active_to_false():
    """
        Verify that calling stop sets is_active to False.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor.start()
    monitor.stop()
    stored_active = monitor.is_active

    assert stored_active is False, "stop should set is_active to False"
    return


def test_stop_after_start_transitions_correctly():
    """
        Verify that start followed by stop transitions is_active from
        True back to False.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor.start()
    active_after_start = monitor.is_active

    monitor.stop()
    active_after_stop = monitor.is_active

    assert active_after_start is True, "is_active should be True after start"
    assert active_after_stop is False, "is_active should be False after stop"
    return


def test_start_with_no_monitored_files():
    """
        Verify that start works correctly with an empty policy (no monitored files).
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy(monitored_files=[])
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor.start()
    stored_active = monitor.is_active
    monitor.stop()

    assert stored_active is True, "start should set is_active to True even with no monitored files"
    return


def test_double_start_is_idempotent():
    """
        Verify that calling start twice does not raise an error and
        is_active remains True.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor.start()
    monitor.start()
    stored_active = monitor.is_active
    monitor.stop()

    assert stored_active is True, "double start should be idempotent, is_active should remain True"
    return


def test_double_stop_is_idempotent():
    """
        Verify that calling stop twice does not raise an error and
        is_active remains False.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor.start()
    monitor.stop()
    monitor.stop()
    stored_active = monitor.is_active

    assert stored_active is False, "double stop should be idempotent, is_active should remain False"
    return


# ---- Change Count Tests ----


def test_change_count_starts_at_zero():
    """
        Verify that change_count is 0 when the monitor is first created.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    stored_count = monitor.change_count
    assert stored_count == 0, "change_count should start at 0"
    return


def test_trigger_reload_increments_change_count():
    """
        Verify that calling _trigger_reload increments change_count when
        the reload succeeds.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor._trigger_reload()
    stored_count = monitor.change_count

    assert stored_count == 1, "change_count should be 1 after one successful reload"
    return


def test_trigger_reload_increments_change_count_multiple_times():
    """
        Verify that calling _trigger_reload multiple times increments
        change_count each time.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor._trigger_reload()
    monitor._trigger_reload()
    monitor._trigger_reload()
    stored_count = monitor.change_count

    assert stored_count == 3, "change_count should be 3 after three successful reloads"
    return


# ---- Reload Failure Tests ----


def _raise_validation_error():
    """
        Helper that raises a ConfigurationValidationError for testing
        reload failure scenarios.
    """
    raise ConfigurationValidationError(
        schema_name="test-schema",
        errors=["validation failed"]
    )


def _raise_runtime_error():
    """
        Helper that raises a RuntimeError for testing unexpected
        reload failure scenarios.
    """
    raise RuntimeError("unexpected error during reload")


def test_reload_failure_does_not_increment_change_count():
    """
        Verify that when reload raises a ConfigurationValidationError,
        the change_count is not incremented.
    """
    mock_manager = Mock()
    mock_manager.configure(recursive=True)
    mock_manager.mock_context().mock_method(
        "reload",
        side_effect=_raise_validation_error
    )

    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor._trigger_reload()
    stored_count = monitor.change_count

    assert stored_count == 0, \
        "change_count should not increment when reload raises ConfigurationValidationError"
    return


def test_reload_failure_retains_previous_config():
    """
        Verify that when reload raises a ConfigurationValidationError,
        the monitor does not crash and continues operating. The previous
        configuration is retained (reload failure is handled gracefully).
    """
    mock_manager = Mock()
    mock_manager.configure(recursive=True)
    mock_manager.mock_context().mock_method(
        "reload",
        side_effect=_raise_validation_error
    )

    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    exception_raised = False
    try:
        monitor._trigger_reload()
    except ConfigurationValidationError:
        exception_raised = True

    assert exception_raised is False, \
        "reload failure should be caught and not propagate"
    return


def test_reload_unexpected_error_does_not_increment_change_count():
    """
        Verify that when reload raises an unexpected exception,
        the change_count is not incremented.
    """
    mock_manager = Mock()
    mock_manager.configure(recursive=True)
    mock_manager.mock_context().mock_method(
        "reload",
        side_effect=_raise_runtime_error
    )

    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    monitor._trigger_reload()
    stored_count = monitor.change_count

    assert stored_count == 0, \
        "change_count should not increment when reload raises an unexpected error"
    return


# ---- __repr__ and __str__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'HotReloadMonitor'.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    repr_str = repr(monitor)
    assert "HotReloadMonitor" in repr_str, "__repr__ should contain the class name"
    return


def test_repr_contains_is_active():
    """
        Verify that __repr__ contains the is_active status.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    repr_str = repr(monitor)
    assert "is_active=False" in repr_str, "__repr__ should contain is_active status"
    return


def test_repr_contains_polling_interval():
    """
        Verify that __repr__ contains the polling interval from the policy.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy(polling_interval=10.0)
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    repr_str = repr(monitor)
    assert "10.0" in repr_str, "__repr__ should contain the polling interval"
    return


def test_str_contains_polling_interval():
    """
        Verify that __str__ contains the polling interval.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy(polling_interval=3.0)
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    str_val = str(monitor)
    assert "3.0" in str_val, "__str__ should contain the polling interval"
    return


def test_str_contains_monitored_files_count():
    """
        Verify that __str__ contains the count of monitored files.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy(monitored_files=["/tmp/a.json", "/tmp/b.yaml"])
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    str_val = str(monitor)
    assert "monitored_files=2" in str_val, "__str__ should contain the monitored file count"
    return


def test_str_contains_is_active():
    """
        Verify that __str__ contains the is_active status.
    """
    mock_manager = create_mock_configuration_manager()
    policy = HotReloadPolicy()
    monitor = HotReloadMonitor(configuration_manager=mock_manager, policy=policy)

    str_val = str(monitor)
    assert "is_active=False" in str_val, "__str__ should contain the is_active status"
    return
