"""
    Unit tests for the automojo.agentkit.degradationlevel module.

    Tests DegradationLevel enum values and from_string method.
"""

from automojo.agentkit.degradationlevel import DegradationLevel
from automojo.agentkit.errors import SemanticError


def test_degradation_level_normal_value():
    """
        Verify that NORMAL has the expected string value.
    """
    assert DegradationLevel.NORMAL.value == "NORMAL", "NORMAL value should be 'NORMAL'"
    return


def test_degradation_level_degraded_value():
    """
        Verify that DEGRADED has the expected string value.
    """
    assert DegradationLevel.DEGRADED.value == "DEGRADED", "DEGRADED value should be 'DEGRADED'"
    return


def test_degradation_level_critical_value():
    """
        Verify that CRITICAL has the expected string value.
    """
    assert DegradationLevel.CRITICAL.value == "CRITICAL", "CRITICAL value should be 'CRITICAL'"
    return


def test_from_string_normal():
    """
        Verify that from_string returns NORMAL for 'NORMAL'.
    """
    level = DegradationLevel.from_string("NORMAL")
    assert level is DegradationLevel.NORMAL, "from_string('NORMAL') should return NORMAL"
    return


def test_from_string_degraded():
    """
        Verify that from_string returns DEGRADED for 'DEGRADED'.
    """
    level = DegradationLevel.from_string("DEGRADED")
    assert level is DegradationLevel.DEGRADED, "from_string('DEGRADED') should return DEGRADED"
    return


def test_from_string_critical():
    """
        Verify that from_string returns CRITICAL for 'CRITICAL'.
    """
    level = DegradationLevel.from_string("CRITICAL")
    assert level is DegradationLevel.CRITICAL, "from_string('CRITICAL') should return CRITICAL"
    return


def test_from_string_case_insensitive():
    """
        Verify that from_string handles lowercase input.
    """
    level = DegradationLevel.from_string("degraded")
    assert level is DegradationLevel.DEGRADED, "from_string should be case-insensitive"
    return


def test_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for invalid values.
    """
    caught = False
    try:
        DegradationLevel.from_string("INVALID")
    except SemanticError as err:
        caught = True
        has_invalid = "INVALID" in err.message
        assert has_invalid is True, "Error message should contain the invalid value"

    assert caught is True, "from_string should raise SemanticError for invalid values"
    return


def test_enum_member_count():
    """
        Verify that DegradationLevel has exactly three members.
    """
    members = list(DegradationLevel)
    assert len(members) == 3, "DegradationLevel should have exactly 3 members"
    return
