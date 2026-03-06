"""
    Unit tests for the automojo.agentkit.breakpoint module.

    Tests the Breakpoint class: construction, invalid type error,
    matches with and without target_name, as_dict, __repr__, and
    __str__.
"""

from automojo.agentkit.breakpoint import Breakpoint
from automojo.agentkit.errors import SemanticError


def test_construction_stores_all_fields():
    """
        Verify that all fields provided at construction are stored correctly.
    """
    bp = Breakpoint(
        breakpoint_type="tool",
        target_name="search",
        condition="count > 5"
    )

    assert bp.breakpoint_type == "tool", "breakpoint_type should be tool"
    assert bp.target_name == "search", "target_name should be search"
    assert bp.condition == "count > 5", "condition should be count > 5"
    return


def test_construction_defaults_optional_fields():
    """
        Verify that target_name and condition default to None.
    """
    bp = Breakpoint(breakpoint_type="lifecycle")

    assert bp.breakpoint_type == "lifecycle", "breakpoint_type should be lifecycle"
    assert bp.target_name is None, "target_name should default to None"
    assert bp.condition is None, "condition should default to None"
    return


def test_all_valid_types_accepted():
    """
        Verify that all valid breakpoint types are accepted without error.
    """
    for valid_type in Breakpoint.VALID_TYPES:
        bp = Breakpoint(breakpoint_type=valid_type)
        assert bp.breakpoint_type == valid_type, (
            "breakpoint_type should be {}".format(valid_type)
        )

    return


def test_invalid_type_raises_semantic_error():
    """
        Verify that an invalid breakpoint type raises SemanticError.
    """
    raised = False
    try:
        Breakpoint(breakpoint_type="invalid_type")
    except SemanticError:
        raised = True

    assert raised is True, "Invalid breakpoint type should raise SemanticError"
    return


def test_invalid_type_error_message_contains_type():
    """
        Verify that the SemanticError message contains the invalid type.
    """
    try:
        Breakpoint(breakpoint_type="bogus")
    except SemanticError as err:
        assert "bogus" in str(err), "Error message should contain the invalid type"
    return


def test_matches_same_type_no_target():
    """
        Verify that matches returns True when type matches and breakpoint
        has no target_name.
    """
    bp = Breakpoint(breakpoint_type="tool")

    result = bp.matches("tool")
    assert result is True, "Should match when type matches and no target_name"
    return


def test_matches_same_type_with_matching_target():
    """
        Verify that matches returns True when both type and target_name match.
    """
    bp = Breakpoint(breakpoint_type="tool", target_name="search")

    result = bp.matches("tool", target_name="search")
    assert result is True, "Should match when type and target_name both match"
    return


def test_matches_different_type_returns_false():
    """
        Verify that matches returns False when event_type differs.
    """
    bp = Breakpoint(breakpoint_type="tool")

    result = bp.matches("lifecycle")
    assert result is False, "Should not match when type differs"
    return


def test_matches_same_type_different_target_returns_false():
    """
        Verify that matches returns False when breakpoint has a target_name
        that differs from the provided target_name.
    """
    bp = Breakpoint(breakpoint_type="tool", target_name="search")

    result = bp.matches("tool", target_name="execute")
    assert result is False, "Should not match when target_name differs"
    return


def test_matches_with_target_but_no_event_target():
    """
        Verify that matches returns False when breakpoint has a target_name
        but the event provides no target_name.
    """
    bp = Breakpoint(breakpoint_type="tool", target_name="search")

    result = bp.matches("tool")
    assert result is False, "Should not match when breakpoint has target but event does not"
    return


def test_matches_no_target_ignores_event_target():
    """
        Verify that matches returns True when breakpoint has no target_name,
        regardless of the event's target_name.
    """
    bp = Breakpoint(breakpoint_type="tool")

    result = bp.matches("tool", target_name="anything")
    assert result is True, "Should match when breakpoint has no target_name"
    return


def test_as_dict_returns_all_fields():
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    bp = Breakpoint(
        breakpoint_type="llm",
        target_name="gpt-4",
        condition="tokens > 100"
    )

    result = bp.as_dict()

    assert result["breakpoint_type"] == "llm", "as_dict breakpoint_type should be llm"
    assert result["target_name"] == "gpt-4", "as_dict target_name should be gpt-4"
    assert result["condition"] == "tokens > 100", "as_dict condition should match"
    return


def test_as_dict_with_none_fields():
    """
        Verify that as_dict includes None for optional fields when not set.
    """
    bp = Breakpoint(breakpoint_type="lifecycle")

    result = bp.as_dict()

    assert result["breakpoint_type"] == "lifecycle"
    assert result["target_name"] is None
    assert result["condition"] is None
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    bp = Breakpoint(breakpoint_type="tool", target_name="search")

    repr_str = repr(bp)
    assert "Breakpoint" in repr_str, "__repr__ should contain class name"
    return


def test_repr_contains_type_and_target():
    """
        Verify that __repr__ contains the breakpoint type and target name.
    """
    bp = Breakpoint(breakpoint_type="tool", target_name="search")

    repr_str = repr(bp)
    assert "tool" in repr_str, "__repr__ should contain breakpoint_type"
    assert "search" in repr_str, "__repr__ should contain target_name"
    return


def test_str_contains_type():
    """
        Verify that __str__ contains the breakpoint type.
    """
    bp = Breakpoint(breakpoint_type="memory", condition="size > 1000")

    str_val = str(bp)
    assert "memory" in str_val, "__str__ should contain breakpoint_type"
    return


def test_str_contains_condition():
    """
        Verify that __str__ contains the condition expression.
    """
    bp = Breakpoint(breakpoint_type="custom", condition="x == 1")

    str_val = str(bp)
    assert "x == 1" in str_val, "__str__ should contain condition"
    return
