"""
    Unit tests for the ccai.agentkit.metrictype module.

    Tests the MetricType enum: COUNTER, GAUGE, HISTOGRAM values
    and the from_string class method for valid and invalid inputs.
"""

from ccai.agentkit.metrictype import MetricType
from ccai.agentkit.errors import SemanticError


def test_counter_value() -> None:
    """
        Verify that MetricType.COUNTER has the value "COUNTER".
    """
    assert MetricType.COUNTER.value == "COUNTER", \
        "MetricType.COUNTER should have value 'COUNTER'"
    return


def test_gauge_value() -> None:
    """
        Verify that MetricType.GAUGE has the value "GAUGE".
    """
    assert MetricType.GAUGE.value == "GAUGE", \
        "MetricType.GAUGE should have value 'GAUGE'"
    return


def test_histogram_value() -> None:
    """
        Verify that MetricType.HISTOGRAM has the value "HISTOGRAM".
    """
    assert MetricType.HISTOGRAM.value == "HISTOGRAM", \
        "MetricType.HISTOGRAM should have value 'HISTOGRAM'"
    return


def test_from_string_counter() -> None:
    """
        Verify that from_string returns MetricType.COUNTER for "COUNTER".
    """
    result = MetricType.from_string("COUNTER")

    assert result == MetricType.COUNTER, \
        "from_string('COUNTER') should return MetricType.COUNTER"
    return


def test_from_string_gauge() -> None:
    """
        Verify that from_string returns MetricType.GAUGE for "GAUGE".
    """
    result = MetricType.from_string("GAUGE")

    assert result == MetricType.GAUGE, \
        "from_string('GAUGE') should return MetricType.GAUGE"
    return


def test_from_string_histogram() -> None:
    """
        Verify that from_string returns MetricType.HISTOGRAM for "HISTOGRAM".
    """
    result = MetricType.from_string("HISTOGRAM")

    assert result == MetricType.HISTOGRAM, \
        "from_string('HISTOGRAM') should return MetricType.HISTOGRAM"
    return


def test_from_string_invalid_raises_semantic_error() -> None:
    """
        Verify that from_string raises SemanticError for an invalid value.
    """
    caught = False

    try:
        MetricType.from_string("INVALID")
    except SemanticError:
        caught = True

    assert caught is True, \
        "from_string('INVALID') should raise SemanticError"
    return


def test_from_string_lowercase_raises_semantic_error() -> None:
    """
        Verify that from_string raises SemanticError for a lowercase
        version of a valid value, since comparison is case-sensitive.
    """
    caught = False

    try:
        MetricType.from_string("counter")
    except SemanticError:
        caught = True

    assert caught is True, \
        "from_string('counter') should raise SemanticError (case-sensitive)"
    return


def test_from_string_empty_raises_semantic_error() -> None:
    """
        Verify that from_string raises SemanticError for an empty string.
    """
    caught = False

    try:
        MetricType.from_string("")
    except SemanticError:
        caught = True

    assert caught is True, \
        "from_string('') should raise SemanticError"
    return


def test_enum_has_three_members() -> None:
    """
        Verify that MetricType has exactly three members.
    """
    members = list(MetricType)

    assert len(members) == 3, \
        "MetricType should have exactly 3 members"
    return
