"""
    Property-based tests for the automojo.agentkit.observabilityconfiguration module.

    Uses the hypothesis library to verify:
    - Property 30: ObservabilityConfiguration JSON round-trip
    - Property 31: ObservabilityConfiguration YAML round-trip
    - Property 32: ObservabilityConfiguration serialization excludes credentials
    - Property 33: ObservabilityConfiguration validation rejects invalid configs

    **Validates: Requirements 25.7, 25.8, 25.9, 25.12, 25.13, 25.14, 25.16, 25.17, 25.18, 25.19**
"""

import json

from hypothesis import given, settings, assume
from hypothesis.strategies import (
    booleans,
    dictionaries,
    floats,
    sampled_from,
    text,
)

from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.observabilityconfiguration import ObservabilityConfiguration


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_log_level_strategy = sampled_from(list(ObservabilityConfiguration.VALID_LOG_LEVELS))

_log_format_strategy = sampled_from(list(ObservabilityConfiguration.VALID_LOG_FORMATS))

_sampling_rate_strategy = floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

_bool_strategy = booleans()

_short_text = text(min_size=1, max_size=50)

_exporter_settings_strategy = dictionaries(
    keys=text(min_size=1, max_size=20),
    values=text(min_size=0, max_size=50),
    max_size=3,
)


# ---------------------------------------------------------------------------
# Property 30: ObservabilityConfiguration JSON round-trip
# ---------------------------------------------------------------------------

@given(
    log_level=_log_level_strategy,
    log_format=_log_format_strategy,
    tracing_enabled=_bool_strategy,
    metrics_enabled=_bool_strategy,
    recording_enabled=_bool_strategy,
    debug_mode_enabled=_bool_strategy,
    sampling_rate=_sampling_rate_strategy,
    exporter_settings=_exporter_settings_strategy,
)
@settings(max_examples=100)
def test_observabilityconfiguration_json_round_trip(
    log_level, log_format, tracing_enabled, metrics_enabled,
    recording_enabled, debug_mode_enabled, sampling_rate, exporter_settings
):
    """
        **Validates: Requirements 25.13, 25.16, 25.18**

        FOR ALL valid ObservabilityConfiguration instances (without credential
        references), calling to_json() and then from_json() SHALL produce an
        ObservabilityConfiguration whose as_dict() output is equal to the original.
    """
    original = ObservabilityConfiguration(
        log_level=log_level,
        log_format=log_format,
        tracing_enabled=tracing_enabled,
        metrics_enabled=metrics_enabled,
        recording_enabled=recording_enabled,
        debug_mode_enabled=debug_mode_enabled,
        sampling_rate=sampling_rate,
        exporter_settings=exporter_settings,
    )

    json_str = original.to_json()
    restored = ObservabilityConfiguration.from_json(json_str)

    original_dict = original.as_dict()
    restored_dict = restored.as_dict()

    assert restored_dict == original_dict, (
        "JSON round-trip as_dict mismatch: expected {!r}, got {!r}".format(
            original_dict, restored_dict)
    )

    return



# ---------------------------------------------------------------------------
# Property 31: ObservabilityConfiguration YAML round-trip
# ---------------------------------------------------------------------------

@given(
    log_level=_log_level_strategy,
    log_format=_log_format_strategy,
    tracing_enabled=_bool_strategy,
    metrics_enabled=_bool_strategy,
    recording_enabled=_bool_strategy,
    debug_mode_enabled=_bool_strategy,
    sampling_rate=_sampling_rate_strategy,
    exporter_settings=_exporter_settings_strategy,
)
@settings(max_examples=100)
def test_observabilityconfiguration_yaml_round_trip(
    log_level, log_format, tracing_enabled, metrics_enabled,
    recording_enabled, debug_mode_enabled, sampling_rate, exporter_settings
):
    """
        **Validates: Requirements 25.14, 25.17, 25.19**

        FOR ALL valid ObservabilityConfiguration instances (without credential
        references), calling to_yaml() and then from_yaml() SHALL produce an
        ObservabilityConfiguration whose as_dict() output is equal to the original.
    """
    original = ObservabilityConfiguration(
        log_level=log_level,
        log_format=log_format,
        tracing_enabled=tracing_enabled,
        metrics_enabled=metrics_enabled,
        recording_enabled=recording_enabled,
        debug_mode_enabled=debug_mode_enabled,
        sampling_rate=sampling_rate,
        exporter_settings=exporter_settings,
    )

    yaml_str = original.to_yaml()
    restored = ObservabilityConfiguration.from_yaml(yaml_str)

    original_dict = original.as_dict()
    restored_dict = restored.as_dict()

    assert restored_dict == original_dict, (
        "YAML round-trip as_dict mismatch: expected {!r}, got {!r}".format(
            original_dict, restored_dict)
    )

    return



# ---------------------------------------------------------------------------
# Property 32: ObservabilityConfiguration serialization excludes credentials
# ---------------------------------------------------------------------------

@given(
    log_level=_log_level_strategy,
    log_format=_log_format_strategy,
    sampling_rate=_sampling_rate_strategy,
    secret_value=text(min_size=10, max_size=60),
    cred_name=text(min_size=1, max_size=20),
)
@settings(max_examples=100)
def test_observabilityconfiguration_serialization_excludes_credentials(
    log_level, log_format, sampling_rate, secret_value, cred_name
):
    """
        **Validates: Requirements 25.12, 25.13, 25.14**

        FOR ALL valid ObservabilityConfiguration instances with CredentialReference
        entries, as_dict(), to_json(), and to_yaml() SHALL NOT contain resolved
        credential secret values.
    """
    # Ensure the secret value is distinct from any credential reference data
    # or configuration field names/values that would naturally appear in the
    # serialized output.
    assume(secret_value != cred_name)
    assume(secret_value != "vault")
    assume(secret_value != "secret-key")

    # Exclude secret values that match config field names present in the
    # serialized dictionary keys.
    _config_field_names = {
        "log_level", "log_format", "tracing_enabled", "metrics_enabled",
        "recording_enabled", "debug_mode_enabled", "sampling_rate",
        "exporter_settings", "credentials", "provider", "key",
    }
    assume(secret_value not in _config_field_names)

    # Exclude secret values that match the actual config field values.
    assume(secret_value != log_level)
    assume(secret_value != log_format)
    assume(secret_value != str(sampling_rate))

    credentials = {
        cred_name: {"provider": "vault", "key": "secret-key"}
    }
    resolved_credentials = {
        cred_name: secret_value
    }

    config = ObservabilityConfiguration(
        log_level=log_level,
        log_format=log_format,
        sampling_rate=sampling_rate,
        credentials=credentials,
        resolved_credentials=resolved_credentials,
    )

    # Check as_dict
    dict_output = config.as_dict()
    dict_str = json.dumps(dict_output)
    assert secret_value not in dict_str, (
        "as_dict should not contain resolved credential secret value {!r}".format(secret_value)
    )

    # Check to_json
    json_output = config.to_json()
    assert secret_value not in json_output, (
        "to_json should not contain resolved credential secret value {!r}".format(secret_value)
    )

    # Check to_yaml
    yaml_output = config.to_yaml()
    assert secret_value not in yaml_output, (
        "to_yaml should not contain resolved credential secret value {!r}".format(secret_value)
    )

    return



# ---------------------------------------------------------------------------
# Property 33: ObservabilityConfiguration validation rejects invalid configs
# ---------------------------------------------------------------------------

_invalid_log_level_strategy = text(min_size=1, max_size=30).filter(
    lambda x: x not in ObservabilityConfiguration.VALID_LOG_LEVELS
)

_invalid_log_format_strategy = text(min_size=1, max_size=30).filter(
    lambda x: x not in ObservabilityConfiguration.VALID_LOG_FORMATS
)

_invalid_sampling_rate_below = floats(max_value=-0.001, allow_nan=False, allow_infinity=False)

_invalid_sampling_rate_above = floats(min_value=1.001, allow_nan=False, allow_infinity=False)


@given(
    invalid_log_level=_invalid_log_level_strategy,
)
@settings(max_examples=100)
def test_observabilityconfiguration_rejects_invalid_log_level(invalid_log_level):
    """
        **Validates: Requirements 25.7**

        FOR ALL configuration dictionaries with an invalid log_level,
        from_dict() SHALL raise ConfigurationError.
    """
    data = {"log_level": invalid_log_level}

    raised = False
    try:
        ObservabilityConfiguration.from_dict(data)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "from_dict should raise ConfigurationError for invalid log_level {!r}".format(
            invalid_log_level)
    )

    return


@given(
    invalid_log_format=_invalid_log_format_strategy,
)
@settings(max_examples=100)
def test_observabilityconfiguration_rejects_invalid_log_format(invalid_log_format):
    """
        **Validates: Requirements 25.8**

        FOR ALL configuration dictionaries with an invalid log_format,
        from_dict() SHALL raise ConfigurationError.
    """
    data = {"log_format": invalid_log_format}

    raised = False
    try:
        ObservabilityConfiguration.from_dict(data)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "from_dict should raise ConfigurationError for invalid log_format {!r}".format(
            invalid_log_format)
    )

    return


@given(
    invalid_rate=_invalid_sampling_rate_below,
)
@settings(max_examples=100)
def test_observabilityconfiguration_rejects_sampling_rate_below_zero(invalid_rate):
    """
        **Validates: Requirements 25.9**

        FOR ALL configuration dictionaries with a sampling_rate below 0.0,
        from_dict() SHALL raise ConfigurationError.
    """
    data = {"sampling_rate": invalid_rate}

    raised = False
    try:
        ObservabilityConfiguration.from_dict(data)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "from_dict should raise ConfigurationError for sampling_rate {!r}".format(
            invalid_rate)
    )

    return


@given(
    invalid_rate=_invalid_sampling_rate_above,
)
@settings(max_examples=100)
def test_observabilityconfiguration_rejects_sampling_rate_above_one(invalid_rate):
    """
        **Validates: Requirements 25.9**

        FOR ALL configuration dictionaries with a sampling_rate above 1.0,
        from_dict() SHALL raise ConfigurationError.
    """
    data = {"sampling_rate": invalid_rate}

    raised = False
    try:
        ObservabilityConfiguration.from_dict(data)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "from_dict should raise ConfigurationError for sampling_rate {!r}".format(
            invalid_rate)
    )

    return