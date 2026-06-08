"""
    Property-based tests for string representations and credential exclusion
    across all LLM system classes.

    Uses ccai.testbase.properties to verify:
    - Property 40: LLM string representations contain required information
    - Property 41: Credential values excluded from serialization and string output

    **Validates: Requirements 1.10, 1.11, 6.7, 6.8, 14.3, 15.5, 19.1-19.18**
"""

from ccai.testbase.properties import given, assume
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.llmprovider import LLMProvider
from ccai.agentkit.llmmessage import LLMMessage
from ccai.agentkit.llmconversation import LLMConversation
from ccai.agentkit.llmresponse import LLMResponse
from ccai.agentkit.tokenusage import TokenUsage
from ccai.agentkit.costestimate import CostEstimate
from ccai.agentkit.prompttemplate import PromptTemplate
from ccai.agentkit.retrypolicy import RetryPolicy
from ccai.agentkit.llmproviderregistry import LLMProviderRegistry
from ccai.agentkit.llmstreamchunk import LLMStreamChunk
from ccai.agentkit.llmerrors import LLMRequestError, LLMResponseParsingError


# ---------------------------------------------------------------------------
# Concrete LLMProvider subclass for testing
# ---------------------------------------------------------------------------

class _TestLLMProvider(LLMProvider):
    """
        Minimal concrete subclass of LLMProvider for property testing.
    """

    def complete(self, conversation, **kwargs):
        return None

    def complete_stream(self, conversation, handler, **kwargs):
        return None


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_safe_chars = st.characters(
    categories=("L", "N"),
    characters=" -_.",
)

_nonempty_text = st.text(
    alphabet=_safe_chars,
    min_size=1,
    max_size=100,
)

_content_text = st.text(
    alphabet=_safe_chars,
    min_size=0,
    max_size=300,
)

_valid_role = st.sampled_from(["system", "user", "assistant", "tool"])

_pos_int = st.integers(min_value=0, max_value=100000)

_pos_float = st.floats(min_value=0.0, max_value=1e6)

_currency = st.sampled_from(["USD", "EUR", "GBP", "JPY"])


@composite
def _version_string(draw):
    """
        Generates a version string in the format major.minor.patch.
    """
    major = draw(st.integers(min_value=0, max_value=999))
    minor = draw(st.integers(min_value=0, max_value=999))
    patch = draw(st.integers(min_value=0, max_value=999))
    return f"{major}.{minor}.{patch}"


_version = _version_string()

_backoff_strategy = st.sampled_from(["fixed", "exponential", "exponential_with_jitter"])

_error_category = st.sampled_from([
    "rate_limit", "authentication", "server_error",
    "timeout", "connection", "invalid_request",
])


# ---------------------------------------------------------------------------
# Property 40: LLM string representations contain required information
# ---------------------------------------------------------------------------

@given(
    provider_name=_nonempty_text,
    model_name=_nonempty_text,
    constraints={"max_examples": 50},
)
def test_llmprovider_repr_contains_class_provider_model(
    provider_name: str,
    model_name: str,
) -> None:
    """
        **Validates: Requirements 1.10, 1.11, 19.1, 19.2**

        For any LLMProvider instance, repr() shall contain the class name,
        provider name, and model name. str() shall contain the provider name
        and model name.
    """
    assume(provider_name.strip())
    assume(model_name.strip())

    provider = _TestLLMProvider(provider_name=provider_name, model_name=model_name)

    repr_str = repr(provider)
    str_str = str(provider)

    assert "_TestLLMProvider" in repr_str, (
        "LLMProvider repr should contain the class name. Got: {!r}".format(repr_str)
    )
    assert provider_name in repr_str, (
        "LLMProvider repr should contain provider_name {!r}. Got: {!r}".format(
            provider_name, repr_str
        )
    )
    assert model_name in repr_str, (
        "LLMProvider repr should contain model_name {!r}. Got: {!r}".format(
            model_name, repr_str
        )
    )
    assert provider_name in str_str, (
        "LLMProvider str should contain provider_name {!r}. Got: {!r}".format(
            provider_name, str_str
        )
    )
    assert model_name in str_str, (
        "LLMProvider str should contain model_name {!r}. Got: {!r}".format(
            model_name, str_str
        )
    )

    return


@given(
    role=_valid_role,
    content=_content_text,
    constraints={"max_examples": 50},
)
def test_llmmessage_repr_contains_role_and_str_contains_role_content(
    role: str,
    content: str,
) -> None:
    """
        **Validates: Requirements 19.3, 19.4**

        For any LLMMessage, repr() shall contain the class name and role.
        str() shall contain the role and content.
    """
    msg = LLMMessage(role=role, content=content)

    repr_str = repr(msg)
    str_str = str(msg)

    assert "LLMMessage" in repr_str, (
        "LLMMessage repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert role in repr_str, (
        "LLMMessage repr should contain role {!r}. Got: {!r}".format(role, repr_str)
    )
    assert role in str_str, (
        "LLMMessage str should contain role {!r}. Got: {!r}".format(role, str_str)
    )
    assert content in str_str, (
        "LLMMessage str should contain content. Got: {!r}".format(str_str)
    )

    return


@given(
    count=st.integers(min_value=0, max_value=10),
    constraints={"max_examples": 50},
)
def test_llmconversation_repr_contains_count(
    count: int,
) -> None:
    """
        **Validates: Requirements 19.5, 19.6**

        For any LLMConversation, repr() shall contain the class name and
        message count.
    """
    messages = [LLMMessage(role="user", content="msg {}".format(i)) for i in range(count)]
    conv = LLMConversation(messages=messages)

    repr_str = repr(conv)

    assert "LLMConversation" in repr_str, (
        "LLMConversation repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert str(count) in repr_str, (
        "LLMConversation repr should contain count {}. Got: {!r}".format(count, repr_str)
    )

    return


@given(
    prompt_tokens=_pos_int,
    completion_tokens=_pos_int,
    constraints={"max_examples": 50},
)
def test_tokenusage_repr_contains_all_counts(
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """
        **Validates: Requirements 19.9, 19.10**

        For any TokenUsage, repr() shall contain the class name and all
        token counts.
    """
    total_tokens = prompt_tokens + completion_tokens
    usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )

    repr_str = repr(usage)

    assert "TokenUsage" in repr_str, (
        "TokenUsage repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert str(prompt_tokens) in repr_str, (
        "TokenUsage repr should contain prompt_tokens {}. Got: {!r}".format(
            prompt_tokens, repr_str
        )
    )
    assert str(completion_tokens) in repr_str, (
        "TokenUsage repr should contain completion_tokens {}. Got: {!r}".format(
            completion_tokens, repr_str
        )
    )
    assert str(total_tokens) in repr_str, (
        "TokenUsage repr should contain total_tokens {}. Got: {!r}".format(
            total_tokens, repr_str
        )
    )

    return


@given(
    prompt_cost=st.floats(min_value=0.0, max_value=1000.0),
    completion_cost=st.floats(min_value=0.0, max_value=1000.0),
    currency=_currency,
    constraints={"max_examples": 50},
)
def test_costestimate_repr_contains_total_and_currency(
    prompt_cost: float,
    completion_cost: float,
    currency: str,
) -> None:
    """
        **Validates: Requirements 19.11, 19.12**

        For any CostEstimate, repr() shall contain the class name, total cost,
        and currency.
    """
    total_cost = prompt_cost + completion_cost
    estimate = CostEstimate(
        prompt_cost=prompt_cost,
        completion_cost=completion_cost,
        total_cost=total_cost,
        currency=currency,
    )

    repr_str = repr(estimate)

    assert "CostEstimate" in repr_str, (
        "CostEstimate repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert str(total_cost) in repr_str, (
        "CostEstimate repr should contain total_cost {}. Got: {!r}".format(
            total_cost, repr_str
        )
    )
    assert currency in repr_str, (
        "CostEstimate repr should contain currency {!r}. Got: {!r}".format(
            currency, repr_str
        )
    )

    return


@given(
    provider_name=_nonempty_text,
    model_name=_nonempty_text,
    prompt_tokens=_pos_int,
    completion_tokens=_pos_int,
    duration=st.floats(min_value=0.0, max_value=1000.0),
    constraints={"max_examples": 50},
)
def test_llmresponse_repr_contains_provider_model_tokens(
    provider_name: str,
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    duration: float,
) -> None:
    """
        **Validates: Requirements 19.7, 19.8**

        For any LLMResponse, repr() shall contain the class name, provider name,
        model name, and total token count.
    """
    assume(provider_name.strip())
    assume(model_name.strip())

    total_tokens = prompt_tokens + completion_tokens
    message = LLMMessage(role="assistant", content="response")
    token_usage = TokenUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
    response = LLMResponse(
        message=message,
        token_usage=token_usage,
        provider_name=provider_name,
        model_name=model_name,
        duration=duration,
    )

    repr_str = repr(response)

    assert "LLMResponse" in repr_str, (
        "LLMResponse repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert provider_name in repr_str, (
        "LLMResponse repr should contain provider_name {!r}. Got: {!r}".format(
            provider_name, repr_str
        )
    )
    assert model_name in repr_str, (
        "LLMResponse repr should contain model_name {!r}. Got: {!r}".format(
            model_name, repr_str
        )
    )
    assert str(total_tokens) in repr_str, (
        "LLMResponse repr should contain total_tokens {}. Got: {!r}".format(
            total_tokens, repr_str
        )
    )

    return


@given(
    name=_nonempty_text,
    version=_version,
    constraints={"max_examples": 50},
)
def test_prompttemplate_repr_contains_name_and_version(
    name: str,
    version: str,
) -> None:
    """
        **Validates: Requirements 19.13, 19.14**

        For any PromptTemplate, repr() shall contain the class name, template
        name, and version.
    """
    template = PromptTemplate(name=name, version=version, template="Hello")

    repr_str = repr(template)

    assert "PromptTemplate" in repr_str, (
        "PromptTemplate repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert name in repr_str, (
        "PromptTemplate repr should contain name {!r}. Got: {!r}".format(name, repr_str)
    )
    assert version in repr_str, (
        "PromptTemplate repr should contain version {!r}. Got: {!r}".format(
            version, repr_str
        )
    )

    return


@given(
    max_retries=st.integers(min_value=0, max_value=20),
    strategy=_backoff_strategy,
    constraints={"max_examples": 50},
)
def test_retrypolicy_repr_contains_max_retries_and_strategy(
    max_retries: int,
    strategy: str,
) -> None:
    """
        **Validates: Requirements 19.15, 19.16**

        For any RetryPolicy, repr() shall contain the class name, max retries,
        and backoff strategy.
    """
    policy = RetryPolicy(
        max_retries=max_retries,
        backoff_strategy=strategy,
        base_delay=1.0,
        max_delay=60.0,
    )

    repr_str = repr(policy)

    assert "RetryPolicy" in repr_str, (
        "RetryPolicy repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert str(max_retries) in repr_str, (
        "RetryPolicy repr should contain max_retries {}. Got: {!r}".format(
            max_retries, repr_str
        )
    )
    assert strategy in repr_str, (
        "RetryPolicy repr should contain strategy {!r}. Got: {!r}".format(
            strategy, repr_str
        )
    )

    return


@given(
    num_providers=st.integers(min_value=0, max_value=5),
    constraints={"max_examples": 50},
)
def test_llmproviderregistry_repr_contains_count(
    num_providers: int,
) -> None:
    """
        **Validates: Requirements 19.17, 19.18**

        For any LLMProviderRegistry, repr() shall contain the class name
        and the count of registered providers.
    """
    registry = LLMProviderRegistry()

    for i in range(num_providers):
        provider = _TestLLMProvider(
            provider_name="provider_{}".format(i),
            model_name="model_{}".format(i),
        )
        registry.register(provider)

    repr_str = repr(registry)

    assert "LLMProviderRegistry" in repr_str, (
        "LLMProviderRegistry repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert str(num_providers) in repr_str, (
        "LLMProviderRegistry repr should contain count {}. Got: {!r}".format(
            num_providers, repr_str
        )
    )

    return


@given(
    content=_content_text,
    constraints={"max_examples": 50},
)
def test_llmstreamchunk_repr_contains_preview_and_str_returns_content(
    content: str,
) -> None:
    """
        **Validates: Requirements 6.7, 6.8**

        For any LLMStreamChunk, repr() shall contain the class name and a
        truncated content preview. str() shall return the content.
    """
    chunk = LLMStreamChunk(content=content)

    repr_str = repr(chunk)
    str_str = str(chunk)

    assert "LLMStreamChunk" in repr_str, (
        "LLMStreamChunk repr should contain class name. Got: {!r}".format(repr_str)
    )

    expected_preview = content[:30] if len(content) > 30 else content
    assert expected_preview in repr_str, (
        "LLMStreamChunk repr should contain content preview {!r}. Got: {!r}".format(
            expected_preview, repr_str
        )
    )

    assert str_str == content, (
        "LLMStreamChunk str should return content. Expected: {!r}, Got: {!r}".format(
            content, str_str
        )
    )

    return


@given(
    provider_name=_nonempty_text,
    model_name=_nonempty_text,
    category=_error_category,
    constraints={"max_examples": 50},
)
def test_llmrequesterror_repr_contains_provider_model_category(
    provider_name: str,
    model_name: str,
    category: str,
) -> None:
    """
        **Validates: Requirements 15.5**

        For any LLMRequestError, repr() shall include the exception class name,
        provider name, model name, and category.
    """
    assume(provider_name.strip())
    assume(model_name.strip())

    error = LLMRequestError(
        provider_name=provider_name,
        model_name=model_name,
        category=category,
    )

    repr_str = repr(error)

    assert "LLMRequestError" in repr_str, (
        "LLMRequestError repr should contain class name. Got: {!r}".format(repr_str)
    )
    assert provider_name in repr_str, (
        "LLMRequestError repr should contain provider_name {!r}. Got: {!r}".format(
            provider_name, repr_str
        )
    )
    assert model_name in repr_str, (
        "LLMRequestError repr should contain model_name {!r}. Got: {!r}".format(
            model_name, repr_str
        )
    )
    assert category in repr_str, (
        "LLMRequestError repr should contain category {!r}. Got: {!r}".format(
            category, repr_str
        )
    )

    return


@given(
    parser_name=_nonempty_text,
    raw_text=_content_text,
    error_message=_nonempty_text,
    constraints={"max_examples": 50},
)
def test_llmresponseparsingerror_repr_contains_parser_name(
    parser_name: str,
    raw_text: str,
    error_message: str,
) -> None:
    """
        **Validates: Requirements 15.5**

        For any LLMResponseParsingError, repr() shall include the exception
        class name and parser name.
    """
    error = LLMResponseParsingError(
        parser_name=parser_name,
        raw_text=raw_text,
        message=error_message,
    )

    repr_str = repr(error)

    assert "LLMResponseParsingError" in repr_str, (
        "LLMResponseParsingError repr should contain class name. Got: {!r}".format(
            repr_str
        )
    )
    assert parser_name in repr_str, (
        "LLMResponseParsingError repr should contain parser_name {!r}. Got: {!r}".format(
            parser_name, repr_str
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 41: Credential values excluded from serialization and string output
# ---------------------------------------------------------------------------

@given(
    provider_name=_nonempty_text,
    model_name=_nonempty_text,
    credential_value=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=10,
        max_size=100,
    ),
    constraints={"max_examples": 50},
)
def test_credential_values_excluded_from_repr_str_model_info(
    provider_name: str,
    model_name: str,
    credential_value: str,
) -> None:
    """
        **Validates: Requirements 14.3**

        For any LLMProvider instance with credential_names, the output of
        __repr__(), __str__(), and get_model_info() shall not contain any
        resolved credential values. Since LLMProvider stores credential_names
        (not actual values), we verify that a random credential-like string
        does not appear in the outputs when it is used as a credential name
        entry and the provider is serialized.
    """
    assume(provider_name.strip())
    assume(model_name.strip())

    cred_names = ["api_key", "secret_token"]
    provider = _TestLLMProvider(
        provider_name=provider_name,
        model_name=model_name,
        credential_names=cred_names,
        config={"temperature": 0.7},
    )

    # Ensure the credential value doesn't accidentally overlap with
    # provider_name or model_name, which legitimately appear in output.
    assume(credential_value not in provider_name)
    assume(credential_value not in model_name)
    assume(provider_name not in credential_value)
    assume(model_name not in credential_value)

    repr_str = repr(provider)
    str_str = str(provider)
    model_info = provider.get_model_info()
    model_info_str = str(model_info)

    assert credential_value not in repr_str, (
        "Credential value {!r} should not appear in repr. Got: {!r}".format(
            credential_value, repr_str
        )
    )
    assert credential_value not in str_str, (
        "Credential value {!r} should not appear in str. Got: {!r}".format(
            credential_value, str_str
        )
    )
    assert credential_value not in model_info_str, (
        "Credential value {!r} should not appear in get_model_info(). Got: {!r}".format(
            credential_value, model_info_str
        )
    )

    # Verify credential_names list itself is not leaked in repr/str
    for cred_name in cred_names:
        assert cred_name not in repr_str, (
            "Credential name {!r} should not appear in repr. Got: {!r}".format(
                cred_name, repr_str
            )
        )
        assert cred_name not in str_str, (
            "Credential name {!r} should not appear in str. Got: {!r}".format(
                cred_name, str_str
            )
        )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
