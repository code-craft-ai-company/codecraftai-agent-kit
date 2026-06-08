"""
    Unit tests for the ccai.agentkit.circuitbreakerstate module.

    Tests CircuitBreakerState enum values and from_string method.
"""

from ccai.agentkit.circuitbreakerstate import CircuitBreakerState
from ccai.agentkit.errors import SemanticError


def test_circuit_breaker_state_closed_value():
    """
        Verify that CLOSED has the expected string value.
    """
    assert CircuitBreakerState.CLOSED.value == "CLOSED", "CLOSED value should be 'CLOSED'"
    return


def test_circuit_breaker_state_open_value():
    """
        Verify that OPEN has the expected string value.
    """
    assert CircuitBreakerState.OPEN.value == "OPEN", "OPEN value should be 'OPEN'"
    return


def test_circuit_breaker_state_half_open_value():
    """
        Verify that HALF_OPEN has the expected string value.
    """
    assert CircuitBreakerState.HALF_OPEN.value == "HALF_OPEN", "HALF_OPEN value should be 'HALF_OPEN'"
    return


def test_from_string_closed():
    """
        Verify that from_string returns CLOSED for 'CLOSED'.
    """
    state = CircuitBreakerState.from_string("CLOSED")
    assert state is CircuitBreakerState.CLOSED, "from_string('CLOSED') should return CLOSED"
    return


def test_from_string_open():
    """
        Verify that from_string returns OPEN for 'OPEN'.
    """
    state = CircuitBreakerState.from_string("OPEN")
    assert state is CircuitBreakerState.OPEN, "from_string('OPEN') should return OPEN"
    return


def test_from_string_half_open():
    """
        Verify that from_string returns HALF_OPEN for 'HALF_OPEN'.
    """
    state = CircuitBreakerState.from_string("HALF_OPEN")
    assert state is CircuitBreakerState.HALF_OPEN, "from_string('HALF_OPEN') should return HALF_OPEN"
    return


def test_from_string_case_insensitive():
    """
        Verify that from_string handles lowercase input.
    """
    state = CircuitBreakerState.from_string("closed")
    assert state is CircuitBreakerState.CLOSED, "from_string should be case-insensitive"
    return


def test_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for invalid values.
    """
    caught = False
    try:
        CircuitBreakerState.from_string("INVALID")
    except SemanticError as err:
        caught = True
        has_invalid = "INVALID" in err.message
        assert has_invalid is True, "Error message should contain the invalid value"

    assert caught is True, "from_string should raise SemanticError for invalid values"
    return


def test_enum_member_count():
    """
        Verify that CircuitBreakerState has exactly three members.
    """
    members = list(CircuitBreakerState)
    assert len(members) == 3, "CircuitBreakerState should have exactly 3 members"
    return
