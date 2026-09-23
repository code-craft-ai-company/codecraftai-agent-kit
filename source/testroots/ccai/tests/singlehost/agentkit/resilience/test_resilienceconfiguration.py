"""
    Unit tests for ResilienceConfiguration.
"""

from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.resilienceconfiguration import ResilienceConfiguration
from ccai.agentkit.retrypolicy import RetryPolicy


def test_resilienceconfiguration_defaults():
    """
        Verify ResilienceConfiguration has correct defaults.
    """
    config = ResilienceConfiguration()

    assert config.default_retry_policy is None, "default_retry_policy should be None"
    assert config.circuit_breaker_enabled is True, "circuit_breaker_enabled should default True"
    assert config.degradation_enabled is True, "degradation_enabled should default True"
    assert config.dead_letter_enabled is True, "dead_letter_enabled should default True"
    assert config.health_monitoring_enabled is True, "health_monitoring_enabled should default True"
    assert config.health_check_interval == 30.0, "health_check_interval should default 30.0"
    assert config.self_healing_enabled is True, "self_healing_enabled should default True"
    return


def test_resilienceconfiguration_custom_values():
    """
        Verify ResilienceConfiguration stores custom values.
    """
    policy = RetryPolicy(max_retries=5, backoff_strategy="exponential",
                         base_delay=2.0, max_delay=60.0)
    config = ResilienceConfiguration(
        default_retry_policy=policy,
        circuit_breaker_enabled=False,
        degradation_enabled=False,
        dead_letter_enabled=False,
        health_monitoring_enabled=False,
        health_check_interval=10.0,
        self_healing_enabled=False
    )

    assert config.default_retry_policy is policy, "retry_policy should match"
    assert config.circuit_breaker_enabled is False, "cb should be False"
    assert config.degradation_enabled is False, "degradation should be False"
    assert config.dead_letter_enabled is False, "dead_letter should be False"
    assert config.health_monitoring_enabled is False, "health_monitoring should be False"
    assert config.health_check_interval == 10.0, "interval should be 10.0"
    assert config.self_healing_enabled is False, "self_healing should be False"
    return


def test_resilienceconfiguration_as_dict_no_policy():
    """
        Verify as_dict with no retry policy.
    """
    config = ResilienceConfiguration()
    data = config.as_dict()

    assert data["default_retry_policy"] is None, "retry_policy should be None"
    assert data["circuit_breaker_enabled"] is True, "cb should be True"
    return


def test_resilienceconfiguration_as_dict_with_policy():
    """
        Verify as_dict includes retry policy dict.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="fixed",
                         base_delay=1.0, max_delay=10.0)
    config = ResilienceConfiguration(default_retry_policy=policy)
    data = config.as_dict()

    assert data["default_retry_policy"]["max_retries"] == 3, "max_retries should match"
    assert data["default_retry_policy"]["backoff_strategy"] == "fixed", "strategy should match"
    return


def test_resilienceconfiguration_json_roundtrip():
    """
        Verify JSON serialization round-trip.
    """
    policy = RetryPolicy(max_retries=3, backoff_strategy="exponential",
                         base_delay=1.0, max_delay=30.0)
    original = ResilienceConfiguration(
        default_retry_policy=policy,
        circuit_breaker_enabled=False,
        health_check_interval=15.0
    )

    json_str = original.to_json()
    restored = ResilienceConfiguration.from_json(json_str)

    assert restored.circuit_breaker_enabled is False, "cb should be False"
    assert restored.health_check_interval == 15.0, "interval should match"
    assert restored.default_retry_policy.max_retries == 3, "max_retries should match"
    return


def test_resilienceconfiguration_yaml_roundtrip():
    """
        Verify YAML serialization round-trip.
    """
    config = ResilienceConfiguration(
        circuit_breaker_enabled=False,
        degradation_enabled=True,
        health_check_interval=20.0
    )

    yaml_str = config.to_yaml()
    restored = ResilienceConfiguration.from_yaml(yaml_str)

    assert restored.circuit_breaker_enabled is False, "cb should be False"
    assert restored.degradation_enabled is True, "degradation should be True"
    assert restored.health_check_interval == 20.0, "interval should match"
    return


def test_resilienceconfiguration_from_dict_defaults():
    """
        Verify from_dict uses defaults for missing fields.
    """
    config = ResilienceConfiguration.from_dict({})

    assert config.circuit_breaker_enabled is True, "should default True"
    assert config.health_check_interval == 30.0, "should default 30.0"
    return


def test_resilienceconfiguration_from_json_invalid():
    """
        Verify from_json raises ConfigurationError for invalid JSON.
    """
    raised = False
    try:
        ResilienceConfiguration.from_json("not valid json")
    except ConfigurationError:
        raised = True

    assert raised is True, "should raise ConfigurationError for invalid JSON"
    return


def test_resilienceconfiguration_from_yaml_invalid():
    """
        Verify from_yaml raises ConfigurationError for invalid YAML.
    """
    raised = False
    try:
        ResilienceConfiguration.from_yaml("- [invalid: yaml: {")
    except ConfigurationError:
        raised = True

    assert raised is True, "should raise ConfigurationError for invalid YAML"
    return


def test_resilienceconfiguration_from_yaml_non_mapping():
    """
        Verify from_yaml raises ConfigurationError for non-mapping YAML.
    """
    raised = False
    try:
        ResilienceConfiguration.from_yaml("- item1\n- item2")
    except ConfigurationError:
        raised = True

    assert raised is True, "should raise ConfigurationError for non-mapping YAML"
    return


def test_resilienceconfiguration_repr():
    """
        Verify __repr__ contains key fields.
    """
    config = ResilienceConfiguration()
    repr_str = repr(config)

    assert "ResilienceConfiguration" in repr_str, "repr should contain class name"
    return


def test_resilienceconfiguration_str():
    """
        Verify __str__ contains key fields.
    """
    config = ResilienceConfiguration(health_check_interval=15.0)
    str_val = str(config)

    assert "ResilienceConfiguration" in str_val, "str should contain class name"
    assert "15.0" in str_val, "str should contain interval"
    return
