"""
    .. module:: automojo.tests.singlehost.agentkit.test_contextwindowstrategy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ContextWindowStrategy enumeration.
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.contextwindowstrategy import ContextWindowStrategy


# ---- ContextWindowStrategy.from_string Tests ----


def test_context_window_strategy_from_string_fifo():
    """
        Verify that from_string returns FIFO for 'FIFO'.
    """
    strategy = ContextWindowStrategy.from_string("FIFO")
    assert strategy is ContextWindowStrategy.FIFO, "from_string('FIFO') should return ContextWindowStrategy.FIFO"
    return


def test_context_window_strategy_from_string_relevance():
    """
        Verify that from_string returns RELEVANCE for 'RELEVANCE'.
    """
    strategy = ContextWindowStrategy.from_string("RELEVANCE")
    assert strategy is ContextWindowStrategy.RELEVANCE, "from_string('RELEVANCE') should return ContextWindowStrategy.RELEVANCE"
    return


def test_context_window_strategy_from_string_summarize():
    """
        Verify that from_string returns SUMMARIZE for 'SUMMARIZE'.
    """
    strategy = ContextWindowStrategy.from_string("SUMMARIZE")
    assert strategy is ContextWindowStrategy.SUMMARIZE, "from_string('SUMMARIZE') should return ContextWindowStrategy.SUMMARIZE"
    return


def test_context_window_strategy_from_string_case_insensitive_lowercase():
    """
        Verify that from_string handles lowercase input.
    """
    strategy = ContextWindowStrategy.from_string("fifo")
    assert strategy is ContextWindowStrategy.FIFO, "from_string('fifo') should return ContextWindowStrategy.FIFO"
    return


def test_context_window_strategy_from_string_case_insensitive_mixed():
    """
        Verify that from_string handles mixed case input.
    """
    strategy = ContextWindowStrategy.from_string("Relevance")
    assert strategy is ContextWindowStrategy.RELEVANCE, "from_string('Relevance') should return ContextWindowStrategy.RELEVANCE"
    return


def test_context_window_strategy_from_string_with_whitespace():
    """
        Verify that from_string strips leading and trailing whitespace.
    """
    strategy = ContextWindowStrategy.from_string("  SUMMARIZE  ")
    assert strategy is ContextWindowStrategy.SUMMARIZE, "from_string with whitespace should return ContextWindowStrategy.SUMMARIZE"
    return


def test_context_window_strategy_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for invalid values.
    """
    raised = False
    try:
        ContextWindowStrategy.from_string("INVALID")
    except SemanticError:
        raised = True

    assert raised is True, "from_string('INVALID') should raise SemanticError"
    return


def test_context_window_strategy_from_string_invalid_error_lists_valid_values():
    """
        Verify that the SemanticError message lists valid strategy values.
    """
    error_message = ""
    try:
        ContextWindowStrategy.from_string("BOGUS")
    except SemanticError as exc:
        error_message = exc.message

    has_fifo = "FIFO" in error_message
    has_relevance = "RELEVANCE" in error_message
    has_summarize = "SUMMARIZE" in error_message
    assert has_fifo is True, "error message should list FIFO as a valid value"
    assert has_relevance is True, "error message should list RELEVANCE as a valid value"
    assert has_summarize is True, "error message should list SUMMARIZE as a valid value"
    return


def test_context_window_strategy_from_string_invalid_error_contains_invalid_value():
    """
        Verify that the SemanticError message contains the invalid value.
    """
    error_message = ""
    try:
        ContextWindowStrategy.from_string("BOGUS")
    except SemanticError as exc:
        error_message = exc.message

    has_invalid = "BOGUS" in error_message
    assert has_invalid is True, "error message should contain the invalid value"
    return


# ---- ContextWindowStrategy __repr__ and __str__ Tests ----


def test_context_window_strategy_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    repr_str = repr(ContextWindowStrategy.FIFO)
    has_class_name = "ContextWindowStrategy" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_context_window_strategy_repr_contains_value():
    """
        Verify that __repr__ contains the enum value.
    """
    repr_str = repr(ContextWindowStrategy.RELEVANCE)
    has_value = "RELEVANCE" in repr_str
    assert has_value is True, "repr should contain the enum value"
    return


def test_context_window_strategy_str_returns_value():
    """
        Verify that __str__ returns the enum value string.
    """
    str_val = str(ContextWindowStrategy.SUMMARIZE)
    assert str_val == "SUMMARIZE", "__str__ should return the enum value string"
    return


def test_context_window_strategy_str_fifo():
    """
        Verify that __str__ returns 'FIFO' for ContextWindowStrategy.FIFO.
    """
    str_val = str(ContextWindowStrategy.FIFO)
    assert str_val == "FIFO", "__str__ should return 'FIFO'"
    return


def test_context_window_strategy_str_relevance():
    """
        Verify that __str__ returns 'RELEVANCE' for ContextWindowStrategy.RELEVANCE.
    """
    str_val = str(ContextWindowStrategy.RELEVANCE)
    assert str_val == "RELEVANCE", "__str__ should return 'RELEVANCE'"
    return


# ---- ContextWindowStrategy Enum Values ----


def test_context_window_strategy_has_three_members():
    """
        Verify that ContextWindowStrategy has exactly three members.
    """
    member_count = len(ContextWindowStrategy)
    assert member_count == 3, "ContextWindowStrategy should have exactly 3 members"
    return


def test_context_window_strategy_fifo_value():
    """
        Verify that ContextWindowStrategy.FIFO has value 'FIFO'.
    """
    value = ContextWindowStrategy.FIFO.value
    assert value == "FIFO", "ContextWindowStrategy.FIFO should have value 'FIFO'"
    return


def test_context_window_strategy_relevance_value():
    """
        Verify that ContextWindowStrategy.RELEVANCE has value 'RELEVANCE'.
    """
    value = ContextWindowStrategy.RELEVANCE.value
    assert value == "RELEVANCE", "ContextWindowStrategy.RELEVANCE should have value 'RELEVANCE'"
    return


def test_context_window_strategy_summarize_value():
    """
        Verify that ContextWindowStrategy.SUMMARIZE has value 'SUMMARIZE'.
    """
    value = ContextWindowStrategy.SUMMARIZE.value
    assert value == "SUMMARIZE", "ContextWindowStrategy.SUMMARIZE should have value 'SUMMARIZE'"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
