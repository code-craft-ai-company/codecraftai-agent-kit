"""
    Unit tests for the ccai.agentkit.circuitbreakerconfiguration module.

    Tests CircuitBreakerConfiguration construction, properties, and serialization.
"""

from ccai.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration


def test_configuration_construction():
    """
        Verify that CircuitBreakerConfiguration stores all fields correctly.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=3,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    assert config.failure_threshold == 5, "failure_threshold should be 5"
    assert config.success_threshold == 3, "success_threshold should be 3"
    assert config.open_state_timeout == 30.0, "open_state_timeout should be 30.0"
    assert config.half_open_max_attempts == 2, "half_open_max_attempts should be 2"
    assert config.monitored_exception_types == [], "monitored_exception_types should default to empty"
    return


def test_configuration_with_monitored_exceptions():
    """
        Verify that monitored_exception_types are stored correctly.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=3, success_threshold=1,
        open_state_timeout=10.0, half_open_max_attempts=1,
        monitored_exception_types=[ValueError, IOError]
    )
    types = config.monitored_exception_types
    assert len(types) == 2, "should have 2 monitored exception types"
    return


def test_configuration_as_dict():
    """
        Verify that as_dict returns the expected dictionary.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=3,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    data = config.as_dict()
    assert data["failure_threshold"] == 5, "failure_threshold should be 5"
    assert data["open_state_timeout"] == 30.0, "open_state_timeout should be 30.0"
    return


def test_configuration_json_round_trip():
    """
        Verify that to_json followed by from_json produces equivalent values.
    """
    original = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=3,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    json_str = original.to_json()
    restored = CircuitBreakerConfiguration.from_json(json_str)

    assert restored.failure_threshold == original.failure_threshold, "failure_threshold should match"
    assert restored.success_threshold == original.success_threshold, "success_threshold should match"
    assert restored.open_state_timeout == original.open_state_timeout, "open_state_timeout should match"
    assert restored.half_open_max_attempts == original.half_open_max_attempts, "half_open_max_attempts should match"
    return


def test_configuration_repr():
    """
        Verify that __repr__ includes class name and key fields.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=3,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    repr_str = repr(config)
    assert "CircuitBreakerConfiguration" in repr_str, "repr should contain class name"
    assert "5" in repr_str, "repr should contain failure threshold"
    return


def test_configuration_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    config = CircuitBreakerConfiguration(
        failure_threshold=5, success_threshold=3,
        open_state_timeout=30.0, half_open_max_attempts=2
    )
    str_val = str(config)
    assert "5" in str_val, "str should contain failure threshold"
    assert "30" in str_val, "str should contain timeout"
    return
