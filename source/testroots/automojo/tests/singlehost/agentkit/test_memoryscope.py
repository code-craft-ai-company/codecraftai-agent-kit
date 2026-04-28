"""
    .. module:: automojo.tests.singlehost.agentkit.test_memoryscope
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryScope enumeration.
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.memoryscope import MemoryScope


# ---- MemoryScope.from_string Tests ----


def test_memory_scope_from_string_agent():
    """
        Verify that from_string returns AGENT for 'AGENT'.
    """
    scope = MemoryScope.from_string("AGENT")
    assert scope is MemoryScope.AGENT, "from_string('AGENT') should return MemoryScope.AGENT"
    return


def test_memory_scope_from_string_shared():
    """
        Verify that from_string returns SHARED for 'SHARED'.
    """
    scope = MemoryScope.from_string("SHARED")
    assert scope is MemoryScope.SHARED, "from_string('SHARED') should return MemoryScope.SHARED"
    return


def test_memory_scope_from_string_global():
    """
        Verify that from_string returns GLOBAL for 'GLOBAL'.
    """
    scope = MemoryScope.from_string("GLOBAL")
    assert scope is MemoryScope.GLOBAL, "from_string('GLOBAL') should return MemoryScope.GLOBAL"
    return


def test_memory_scope_from_string_case_insensitive_lowercase():
    """
        Verify that from_string handles lowercase input.
    """
    scope = MemoryScope.from_string("agent")
    assert scope is MemoryScope.AGENT, "from_string('agent') should return MemoryScope.AGENT"
    return


def test_memory_scope_from_string_case_insensitive_mixed():
    """
        Verify that from_string handles mixed case input.
    """
    scope = MemoryScope.from_string("Shared")
    assert scope is MemoryScope.SHARED, "from_string('Shared') should return MemoryScope.SHARED"
    return


def test_memory_scope_from_string_with_whitespace():
    """
        Verify that from_string strips leading and trailing whitespace.
    """
    scope = MemoryScope.from_string("  GLOBAL  ")
    assert scope is MemoryScope.GLOBAL, "from_string with whitespace should return MemoryScope.GLOBAL"
    return


def test_memory_scope_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for invalid values.
    """
    raised = False
    try:
        MemoryScope.from_string("INVALID")
    except SemanticError:
        raised = True

    assert raised is True, "from_string('INVALID') should raise SemanticError"
    return


def test_memory_scope_from_string_invalid_error_lists_valid_values():
    """
        Verify that the SemanticError message lists valid scope values.
    """
    error_message = ""
    try:
        MemoryScope.from_string("BOGUS")
    except SemanticError as exc:
        error_message = exc.message

    has_agent = "AGENT" in error_message
    has_shared = "SHARED" in error_message
    has_global = "GLOBAL" in error_message
    assert has_agent is True, "error message should list AGENT as a valid value"
    assert has_shared is True, "error message should list SHARED as a valid value"
    assert has_global is True, "error message should list GLOBAL as a valid value"
    return


def test_memory_scope_from_string_invalid_error_contains_invalid_value():
    """
        Verify that the SemanticError message contains the invalid value.
    """
    error_message = ""
    try:
        MemoryScope.from_string("BOGUS")
    except SemanticError as exc:
        error_message = exc.message

    has_invalid = "BOGUS" in error_message
    assert has_invalid is True, "error message should contain the invalid value"
    return


# ---- MemoryScope __repr__ and __str__ Tests ----


def test_memory_scope_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    repr_str = repr(MemoryScope.AGENT)
    has_class_name = "MemoryScope" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_memory_scope_repr_contains_value():
    """
        Verify that __repr__ contains the enum value.
    """
    repr_str = repr(MemoryScope.SHARED)
    has_value = "SHARED" in repr_str
    assert has_value is True, "repr should contain the enum value"
    return


def test_memory_scope_str_returns_value():
    """
        Verify that __str__ returns the enum value string.
    """
    str_val = str(MemoryScope.GLOBAL)
    assert str_val == "GLOBAL", "__str__ should return the enum value string"
    return


def test_memory_scope_str_agent():
    """
        Verify that __str__ returns 'AGENT' for MemoryScope.AGENT.
    """
    str_val = str(MemoryScope.AGENT)
    assert str_val == "AGENT", "__str__ should return 'AGENT'"
    return


def test_memory_scope_str_shared():
    """
        Verify that __str__ returns 'SHARED' for MemoryScope.SHARED.
    """
    str_val = str(MemoryScope.SHARED)
    assert str_val == "SHARED", "__str__ should return 'SHARED'"
    return


# ---- MemoryScope Enum Values ----


def test_memory_scope_has_three_members():
    """
        Verify that MemoryScope has exactly three members.
    """
    member_count = len(MemoryScope)
    assert member_count == 3, "MemoryScope should have exactly 3 members"
    return


def test_memory_scope_agent_value():
    """
        Verify that MemoryScope.AGENT has value 'AGENT'.
    """
    value = MemoryScope.AGENT.value
    assert value == "AGENT", "MemoryScope.AGENT should have value 'AGENT'"
    return


def test_memory_scope_shared_value():
    """
        Verify that MemoryScope.SHARED has value 'SHARED'.
    """
    value = MemoryScope.SHARED.value
    assert value == "SHARED", "MemoryScope.SHARED should have value 'SHARED'"
    return


def test_memory_scope_global_value():
    """
        Verify that MemoryScope.GLOBAL has value 'GLOBAL'.
    """
    value = MemoryScope.GLOBAL.value
    assert value == "GLOBAL", "MemoryScope.GLOBAL should have value 'GLOBAL'"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
