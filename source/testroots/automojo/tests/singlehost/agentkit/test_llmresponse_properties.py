"""
    Property-based tests for the automojo.agentkit.llmresponse module.

    Uses automojo.testbase.properties to verify:
    - Property 3: LLMResponse JSON round-trip

    **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 17.5, 17.6, 17.11**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.llmmessage import LLMMessage
from automojo.agentkit.llmresponse import LLMResponse
from automojo.agentkit.tokenusage import TokenUsage


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

_non_negative_int = st.integers(min_value=0, max_value=1_000_000)

_provider_name = st.text(
    alphabet=st.characters(categories=("L", "N", "Pd")),
    min_size=1,
    max_size=50,
)

_model_name = st.text(
    alphabet=st.characters(categories=("L", "N", "Pd")),
    min_size=1,
    max_size=50,
)

_duration = st.floats(
    min_value=0.0,
    max_value=1_000_000.0,
)


# ---------------------------------------------------------------------------
# Property 3: LLMResponse JSON round-trip
# ---------------------------------------------------------------------------

@given(
    role=_valid_role,
    content=_content,
    metadata=_metadata,
    prompt_tokens=_non_negative_int,
    completion_tokens=_non_negative_int,
    provider_name=_provider_name,
    model_name=_model_name,
    duration=_duration,
    constraints={"max_examples": 50},
)
def test_llmresponse_json_roundtrip(
    role: str,
    content: str,
    metadata: dict,
    prompt_tokens: int,
    completion_tokens: int,
    provider_name: str,
    model_name: str,
    duration: float,
) -> None:
    """
        **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 17.5, 17.6, 17.11**

        For any valid LLMResponse instance (with a valid LLMMessage,
        TokenUsage, provider name, model name, and duration), calling
        to_json() and then from_json() on the resulting string shall
        produce an LLMResponse whose message, token_usage, provider_name,
        model_name, and duration are equal to the original.
    """
    message = LLMMessage(role=role, content=content, metadata=metadata)
    total_tokens = prompt_tokens + completion_tokens
    token_usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    original = LLMResponse(
        message=message,
        token_usage=token_usage,
        provider_name=provider_name,
        model_name=model_name,
        duration=duration,
    )

    json_str = original.to_json()
    restored = LLMResponse.from_json(json_str)

    assert original == restored, (
        "LLMResponse JSON round-trip failed. "
        "Original: provider={!r}, model={!r}, tokens={}, duration={}. "
        "Restored: provider={!r}, model={!r}, tokens={}, duration={}.".format(
            original.provider_name, original.model_name,
            original.token_usage.total_tokens, original.duration,
            restored.provider_name, restored.model_name,
            restored.token_usage.total_tokens, restored.duration,
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
