"""
    Property-based tests for the automojo.agentkit.llmmessage module.

    Uses automojo.testbase.properties to verify:
    - Property 1: LLMMessage JSON round-trip
    - Property 9: LLMMessage construction rejects invalid roles

    **Validates: Requirements 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 17.1, 17.2, 17.9**
"""

from automojo.testbase.properties import given, assume
from automojo.testbase.properties import strategies as st

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmmessage import LLMMessage


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

VALID_ROLES = ["system", "user", "assistant", "tool"]

_valid_role = st.sampled_from(VALID_ROLES)

_content = st.text(min_size=0, max_size=500)

_metadata_value = st.one_of(
    st.text(min_size=0, max_size=100),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1e6, max_value=1e6),
    st.booleans(),
    st.none(),
)

_metadata = st.dictionaries(
    keys=st.text(min_size=1, max_size=50),
    values=_metadata_value,
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 1: LLMMessage JSON round-trip
# ---------------------------------------------------------------------------

@given(
    role=_valid_role,
    content=_content,
    metadata=_metadata,
    constraints={"max_examples": 50},
)
def test_llmmessage_json_roundtrip(
    role: str,
    content: str,
    metadata: dict,
) -> None:
    """
        **Validates: Requirements 2.4, 2.5, 2.6, 2.7, 2.8, 17.1, 17.2, 17.9**

        For any valid LLMMessage instance (with a valid role, arbitrary content
        string, and arbitrary metadata dictionary), calling to_json() and then
        from_json() on the resulting string shall produce an LLMMessage whose
        role, content, and metadata are equal to the original.
    """
    original = LLMMessage(role=role, content=content, metadata=metadata)

    json_str = original.to_json()
    restored = LLMMessage.from_json(json_str)

    assert original == restored, (
        "LLMMessage JSON round-trip failed. "
        "Original: role={!r}, content={!r}, metadata={!r}. "
        "Restored: role={!r}, content={!r}, metadata={!r}.".format(
            original.role, original.content, original.metadata,
            restored.role, restored.content, restored.metadata,
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 9: LLMMessage construction rejects invalid roles
# ---------------------------------------------------------------------------

@given(
    role=st.text(min_size=1, max_size=50),
    constraints={"max_examples": 50},
)
def test_llmmessage_invalid_role_raises_semantic_error(
    role: str,
) -> None:
    """
        **Validates: Requirements 2.3**

        For any string not in the set {"system", "user", "assistant", "tool"},
        constructing an LLMMessage with that role shall raise SemanticError
        that identifies the invalid role and lists the valid roles.
    """
    assume(role not in {"system", "user", "assistant", "tool"})

    raised = False
    error_message = ""
    try:
        LLMMessage(role=role, content="test content")
    except SemanticError as exc:
        raised = True
        error_message = str(exc)

    assert raised is True, (
        "LLMMessage should raise SemanticError for invalid role {!r}".format(role)
    )

    assert repr(role) in error_message or role in error_message, (
        "SemanticError message should identify the invalid role {!r}. "
        "Got message: {!r}".format(role, error_message)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
