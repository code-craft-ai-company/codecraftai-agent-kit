"""
    Property-based tests for the automojo.agentkit.resilienceconfiguration module.

    Uses the hypothesis library to verify:
    - Property 34: ResilienceConfiguration JSON round-trip
    - Property 35: ResilienceConfiguration YAML round-trip

    **Validates: Requirements 21.13, 21.14**
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.resilienceconfiguration import ResilienceConfiguration
from automojo.agentkit.retrypolicy import RetryPolicy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_backoff_strategy = st.sampled_from(["fixed", "exponential", "exponential_with_jitter"])

_retry_policy = st.builds(
    RetryPolicy,
    max_retries=st.integers(min_value=0, max_value=100),
    backoff_strategy=_backoff_strategy,
    base_delay=st.floats(min_value=0.0, max_value=300.0, allow_nan=False, allow_infinity=False),
    max_delay=st.floats(min_value=0.0, max_value=600.0, allow_nan=False, allow_infinity=False),
)

_optional_retry_policy = st.one_of(st.none(), _retry_policy)

_circuit_breaker_enabled = st.booleans()

_degradation_enabled = st.booleans()

_dead_letter_enabled = st.booleans()

_health_monitoring_enabled = st.booleans()

_health_check_interval = st.floats(
    min_value=0.1, max_value=3600.0, allow_nan=False, allow_infinity=False,
)

_self_healing_enabled = st.booleans()


# ---------------------------------------------------------------------------
# Property 34: ResilienceConfiguration JSON round-trip
# ---------------------------------------------------------------------------

@given(
    default_retry_policy=_optional_retry_policy,
    circuit_breaker_enabled=_circuit_breaker_enabled,
    degradation_enabled=_degradation_enabled,
    dead_letter_enabled=_dead_letter_enabled,
    health_monitoring_enabled=_health_monitoring_enabled,
    health_check_interval=_health_check_interval,
    self_healing_enabled=_self_healing_enabled,
)
@settings(max_examples=100)
def test_resilienceconfiguration_json_roundtrip(
    default_retry_policy,
    circuit_breaker_enabled: bool,
    degradation_enabled: bool,
    dead_letter_enabled: bool,
    health_monitoring_enabled: bool,
    health_check_interval: float,
    self_healing_enabled: bool,
) -> None:
    """
        **Validates: Requirements 21.13**

        For all valid ResilienceConfiguration instances constructed with
        arbitrary circuit_breaker_enabled (bool), degradation_enabled (bool),
        dead_letter_enabled (bool), health_monitoring_enabled (bool),
        health_check_interval (positive float), self_healing_enabled (bool),
        and an optional default_retry_policy (RetryPolicy or None), calling
        to_json() and then from_json() shall produce an equivalent
        ResilienceConfiguration object.
    """
    original = ResilienceConfiguration(
        default_retry_policy=default_retry_policy,
        circuit_breaker_enabled=circuit_breaker_enabled,
        degradation_enabled=degradation_enabled,
        dead_letter_enabled=dead_letter_enabled,
        health_monitoring_enabled=health_monitoring_enabled,
        health_check_interval=health_check_interval,
        self_healing_enabled=self_healing_enabled,
    )

    json_str = original.to_json()
    restored = ResilienceConfiguration.from_json(json_str)

    assert restored.circuit_breaker_enabled == original.circuit_breaker_enabled, (
        "circuit_breaker_enabled mismatch: expected {!r}, got {!r}".format(
            original.circuit_breaker_enabled, restored.circuit_breaker_enabled
        )
    )

    assert restored.degradation_enabled == original.degradation_enabled, (
        "degradation_enabled mismatch: expected {!r}, got {!r}".format(
            original.degradation_enabled, restored.degradation_enabled
        )
    )

    assert restored.dead_letter_enabled == original.dead_letter_enabled, (
        "dead_letter_enabled mismatch: expected {!r}, got {!r}".format(
            original.dead_letter_enabled, restored.dead_letter_enabled
        )
    )

    assert restored.health_monitoring_enabled == original.health_monitoring_enabled, (
        "health_monitoring_enabled mismatch: expected {!r}, got {!r}".format(
            original.health_monitoring_enabled, restored.health_monitoring_enabled
        )
    )

    assert restored.health_check_interval == original.health_check_interval, (
        "health_check_interval mismatch: expected {!r}, got {!r}".format(
            original.health_check_interval, restored.health_check_interval
        )
    )

    assert restored.self_healing_enabled == original.self_healing_enabled, (
        "self_healing_enabled mismatch: expected {!r}, got {!r}".format(
            original.self_healing_enabled, restored.self_healing_enabled
        )
    )

    if original.default_retry_policy is None:
        assert restored.default_retry_policy is None, (
            "default_retry_policy should be None but got {!r}".format(
                restored.default_retry_policy
            )
        )
    else:
        assert restored.default_retry_policy is not None, (
            "default_retry_policy should not be None"
        )
        assert restored.default_retry_policy.max_retries == original.default_retry_policy.max_retries, (
            "max_retries mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.max_retries,
                restored.default_retry_policy.max_retries,
            )
        )
        assert restored.default_retry_policy.backoff_strategy == original.default_retry_policy.backoff_strategy, (
            "backoff_strategy mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.backoff_strategy,
                restored.default_retry_policy.backoff_strategy,
            )
        )
        assert restored.default_retry_policy.base_delay == original.default_retry_policy.base_delay, (
            "base_delay mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.base_delay,
                restored.default_retry_policy.base_delay,
            )
        )
        assert restored.default_retry_policy.max_delay == original.default_retry_policy.max_delay, (
            "max_delay mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.max_delay,
                restored.default_retry_policy.max_delay,
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 35: ResilienceConfiguration YAML round-trip
# ---------------------------------------------------------------------------

@given(
    default_retry_policy=_optional_retry_policy,
    circuit_breaker_enabled=_circuit_breaker_enabled,
    degradation_enabled=_degradation_enabled,
    dead_letter_enabled=_dead_letter_enabled,
    health_monitoring_enabled=_health_monitoring_enabled,
    health_check_interval=_health_check_interval,
    self_healing_enabled=_self_healing_enabled,
)
@settings(max_examples=100)
def test_resilienceconfiguration_yaml_roundtrip(
    default_retry_policy,
    circuit_breaker_enabled: bool,
    degradation_enabled: bool,
    dead_letter_enabled: bool,
    health_monitoring_enabled: bool,
    health_check_interval: float,
    self_healing_enabled: bool,
) -> None:
    """
        **Validates: Requirements 21.14**

        For all valid ResilienceConfiguration instances constructed with
        arbitrary enablement flags and health_check_interval, calling
        to_yaml() and then from_yaml() shall produce an equivalent
        ResilienceConfiguration object.
    """
    original = ResilienceConfiguration(
        default_retry_policy=default_retry_policy,
        circuit_breaker_enabled=circuit_breaker_enabled,
        degradation_enabled=degradation_enabled,
        dead_letter_enabled=dead_letter_enabled,
        health_monitoring_enabled=health_monitoring_enabled,
        health_check_interval=health_check_interval,
        self_healing_enabled=self_healing_enabled,
    )

    yaml_str = original.to_yaml()
    restored = ResilienceConfiguration.from_yaml(yaml_str)

    assert restored.circuit_breaker_enabled == original.circuit_breaker_enabled, (
        "circuit_breaker_enabled mismatch: expected {!r}, got {!r}".format(
            original.circuit_breaker_enabled, restored.circuit_breaker_enabled
        )
    )

    assert restored.degradation_enabled == original.degradation_enabled, (
        "degradation_enabled mismatch: expected {!r}, got {!r}".format(
            original.degradation_enabled, restored.degradation_enabled
        )
    )

    assert restored.dead_letter_enabled == original.dead_letter_enabled, (
        "dead_letter_enabled mismatch: expected {!r}, got {!r}".format(
            original.dead_letter_enabled, restored.dead_letter_enabled
        )
    )

    assert restored.health_monitoring_enabled == original.health_monitoring_enabled, (
        "health_monitoring_enabled mismatch: expected {!r}, got {!r}".format(
            original.health_monitoring_enabled, restored.health_monitoring_enabled
        )
    )

    assert restored.health_check_interval == original.health_check_interval, (
        "health_check_interval mismatch: expected {!r}, got {!r}".format(
            original.health_check_interval, restored.health_check_interval
        )
    )

    assert restored.self_healing_enabled == original.self_healing_enabled, (
        "self_healing_enabled mismatch: expected {!r}, got {!r}".format(
            original.self_healing_enabled, restored.self_healing_enabled
        )
    )

    if original.default_retry_policy is None:
        assert restored.default_retry_policy is None, (
            "default_retry_policy should be None but got {!r}".format(
                restored.default_retry_policy
            )
        )
    else:
        assert restored.default_retry_policy is not None, (
            "default_retry_policy should not be None"
        )
        assert restored.default_retry_policy.max_retries == original.default_retry_policy.max_retries, (
            "max_retries mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.max_retries,
                restored.default_retry_policy.max_retries,
            )
        )
        assert restored.default_retry_policy.backoff_strategy == original.default_retry_policy.backoff_strategy, (
            "backoff_strategy mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.backoff_strategy,
                restored.default_retry_policy.backoff_strategy,
            )
        )
        assert restored.default_retry_policy.base_delay == original.default_retry_policy.base_delay, (
            "base_delay mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.base_delay,
                restored.default_retry_policy.base_delay,
            )
        )
        assert restored.default_retry_policy.max_delay == original.default_retry_policy.max_delay, (
            "max_delay mismatch: expected {!r}, got {!r}".format(
                original.default_retry_policy.max_delay,
                restored.default_retry_policy.max_delay,
            )
        )

    return
