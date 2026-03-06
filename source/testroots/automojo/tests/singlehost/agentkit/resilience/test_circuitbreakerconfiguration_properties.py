"""
    Property-based tests for the automojo.agentkit.circuitbreakerconfiguration module.

    Uses the hypothesis library to verify:
    - Property 7: CircuitBreakerConfiguration JSON round-trip

    **Validates: Requirements 4.10**
"""

import json

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_positive_int = st.integers(min_value=1, max_value=1_000_000)

_positive_float = st.floats(
    min_value=0.01,
    max_value=1_000_000.0,
    allow_nan=False,
    allow_infinity=False,
)


# ---------------------------------------------------------------------------
# Property 7: CircuitBreakerConfiguration JSON round-trip
# ---------------------------------------------------------------------------

@given(
    failure_threshold=_positive_int,
    success_threshold=_positive_int,
    open_state_timeout=_positive_float,
    half_open_max_attempts=_positive_int,
)
@settings(max_examples=100)
def test_circuitbreakerconfiguration_json_roundtrip(
    failure_threshold: int,
    success_threshold: int,
    open_state_timeout: float,
    half_open_max_attempts: int,
) -> None:
    """
        **Validates: Requirements 4.10**

        For all valid CircuitBreakerConfiguration instances constructed with
        arbitrary failure_threshold (positive int), success_threshold
        (positive int), open_state_timeout (positive float), and
        half_open_max_attempts (positive int), calling to_json() and then
        parsing the JSON and calling CircuitBreakerConfiguration.from_dict()
        shall produce a CircuitBreakerConfiguration with equivalent
        failure_threshold, success_threshold, open_state_timeout, and
        half_open_max_attempts values.
    """
    original = CircuitBreakerConfiguration(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        open_state_timeout=open_state_timeout,
        half_open_max_attempts=half_open_max_attempts,
    )

    json_str = original.to_json()
    parsed = json.loads(json_str)
    restored = CircuitBreakerConfiguration.from_dict(parsed)

    assert restored.failure_threshold == original.failure_threshold, (
        "failure_threshold mismatch: expected {}, got {}".format(
            original.failure_threshold, restored.failure_threshold
        )
    )

    assert restored.success_threshold == original.success_threshold, (
        "success_threshold mismatch: expected {}, got {}".format(
            original.success_threshold, restored.success_threshold
        )
    )

    assert restored.open_state_timeout == original.open_state_timeout, (
        "open_state_timeout mismatch: expected {}, got {}".format(
            original.open_state_timeout, restored.open_state_timeout
        )
    )

    assert restored.half_open_max_attempts == original.half_open_max_attempts, (
        "half_open_max_attempts mismatch: expected {}, got {}".format(
            original.half_open_max_attempts, restored.half_open_max_attempts
        )
    )

    return
