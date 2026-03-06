"""
    Property-based tests for the automojo.agentkit.llmprovider module.

    Uses automojo.testbase.properties to verify:
    - Property 7: LlmProvider construction preserves fields
    - Property 8: LlmProvider construction rejects missing name or model

    **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9**
"""

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmprovider import LlmProvider


# ---------------------------------------------------------------------------
# Concrete test subclass
# ---------------------------------------------------------------------------

class _TestProvider(LlmProvider):
    """
        Minimal concrete subclass of LlmProvider for testing construction.
        Implements abstract methods as no-ops.
    """

    def complete(self, conversation, **kwargs):
        return None

    def complete_stream(self, conversation, handler, **kwargs):
        return None


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

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

_config_value = st.one_of(
    st.text(min_size=0, max_size=100),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1e6, max_value=1e6),
    st.booleans(),
    st.none(),
)

_config = st.dictionaries(
    keys=st.text(min_size=1, max_size=30),
    values=_config_value,
    max_size=10,
)

_credential_names = st.lists(
    st.text(min_size=1, max_size=50),
    max_size=10,
)

_tags = st.dictionaries(
    keys=st.text(min_size=1, max_size=30),
    values=st.text(min_size=0, max_size=50),
    max_size=10,
)

_empty_or_whitespace = st.one_of(
    st.just(""),
    st.text(
        alphabet=st.sampled_from([" ", "\t", "\n", "\r"]),
        min_size=1,
        max_size=20,
    ),
)


# ---------------------------------------------------------------------------
# Property 7: LlmProvider construction preserves fields
# ---------------------------------------------------------------------------

@given(
    provider_name=_provider_name,
    model_name=_model_name,
    config=_config,
    credential_names=_credential_names,
    tags=_tags,
    settings=settings(max_examples=100),
)
def test_llmprovider_construction_preserves_fields(
    provider_name: str,
    model_name: str,
    config: dict,
    credential_names: list,
    tags: dict,
) -> None:
    """
        **Validates: Requirements 1.3, 1.4, 1.5, 1.6, 1.7**

        For any valid provider name string, model name string, config
        dictionary, credential names list, and tags dictionary,
        constructing an LlmProvider subclass shall produce an instance
        whose provider_name, model_name, config, credential_names, and
        tags properties return values equal to the provided arguments.
    """
    provider = _TestProvider(
        provider_name=provider_name,
        model_name=model_name,
        config=config,
        credential_names=credential_names,
        tags=tags,
    )

    assert provider.provider_name == provider_name, (
        "provider_name should be {!r}, got {!r}".format(
            provider_name, provider.provider_name
        )
    )

    assert provider.model_name == model_name, (
        "model_name should be {!r}, got {!r}".format(
            model_name, provider.model_name
        )
    )

    assert provider.config == config, (
        "config should be {!r}, got {!r}".format(
            config, provider.config
        )
    )

    assert provider.credential_names == credential_names, (
        "credential_names should be {!r}, got {!r}".format(
            credential_names, provider.credential_names
        )
    )

    assert provider.tags == tags, (
        "tags should be {!r}, got {!r}".format(
            tags, provider.tags
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 8: LlmProvider construction rejects missing name or model
# ---------------------------------------------------------------------------

@given(
    model_name=_model_name,
    settings=settings(max_examples=100),
)
def test_llmprovider_rejects_none_provider_name(
    model_name: str,
) -> None:
    """
        **Validates: Requirements 1.8**

        For a None provider name, constructing an LlmProvider shall
        raise SemanticError.
    """
    raised = False
    try:
        _TestProvider(provider_name=None, model_name=model_name)
    except SemanticError:
        raised = True

    assert raised is True, (
        "LlmProvider should raise SemanticError for None provider_name"
    )

    return


@given(
    provider_name=_empty_or_whitespace,
    model_name=_model_name,
    settings=settings(max_examples=100),
)
def test_llmprovider_rejects_empty_provider_name(
    provider_name: str,
    model_name: str,
) -> None:
    """
        **Validates: Requirements 1.8**

        For any empty or whitespace-only provider name string,
        constructing an LlmProvider shall raise SemanticError.
    """
    raised = False
    try:
        _TestProvider(provider_name=provider_name, model_name=model_name)
    except SemanticError:
        raised = True

    assert raised is True, (
        "LlmProvider should raise SemanticError for empty/whitespace "
        "provider_name {!r}".format(provider_name)
    )

    return


@given(
    provider_name=_provider_name,
    settings=settings(max_examples=100),
)
def test_llmprovider_rejects_none_model_name(
    provider_name: str,
) -> None:
    """
        **Validates: Requirements 1.9**

        For a None model name, constructing an LlmProvider shall
        raise SemanticError.
    """
    raised = False
    try:
        _TestProvider(provider_name=provider_name, model_name=None)
    except SemanticError:
        raised = True

    assert raised is True, (
        "LlmProvider should raise SemanticError for None model_name"
    )

    return


@given(
    provider_name=_provider_name,
    model_name=_empty_or_whitespace,
    settings=settings(max_examples=100),
)
def test_llmprovider_rejects_empty_model_name(
    provider_name: str,
    model_name: str,
) -> None:
    """
        **Validates: Requirements 1.9**

        For any empty or whitespace-only model name string,
        constructing an LlmProvider shall raise SemanticError.
    """
    raised = False
    try:
        _TestProvider(provider_name=provider_name, model_name=model_name)
    except SemanticError:
        raised = True

    assert raised is True, (
        "LlmProvider should raise SemanticError for empty/whitespace "
        "model_name {!r}".format(model_name)
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
