"""
    Unit tests for the automojo.agentkit.llmprovider module.

    Tests LlmProvider abstract method enforcement, construction validation,
    read-only properties, string representations, and get_model_info.

    Feature: llm-integration, Task 4.4
    **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10, 1.11, 19.1, 19.2**
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmprovider import LlmProvider


# ---------------------------------------------------------------------------
# Concrete test subclass for testing the abstract base class
# ---------------------------------------------------------------------------


class _TestProvider(LlmProvider):
    """
        Minimal concrete subclass of LlmProvider for testing purposes.
    """

    def complete(self, conversation, **kwargs):
        return None

    def complete_stream(self, conversation, handler, **kwargs):
        return None


# ---------------------------------------------------------------------------
# Abstract method enforcement
# ---------------------------------------------------------------------------


def test_llm_provider_cannot_instantiate_directly():
    """
        LlmProvider cannot be instantiated directly because it has
        abstract methods.

        **Validates: Requirements 1.1, 1.2**
    """
    caught = False

    try:
        LlmProvider(provider_name="openai", model_name="gpt-4")
    except TypeError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise TypeError when instantiated directly"
    )

    return


def test_llm_provider_partial_subclass_cannot_instantiate():
    """
        A subclass that only implements one abstract method cannot be
        instantiated.

        **Validates: Requirements 1.1, 1.2**
    """

    class _PartialProvider(LlmProvider):
        def complete(self, conversation, **kwargs):
            return None

    caught = False

    try:
        _PartialProvider(provider_name="openai", model_name="gpt-4")
    except TypeError:
        caught = True

    assert caught is True, (
        "Partial LlmProvider subclass should raise TypeError"
    )

    return


# ---------------------------------------------------------------------------
# Construction with valid arguments
# ---------------------------------------------------------------------------


def test_llm_provider_valid_construction():
    """
        LlmProvider accepts valid provider_name and model_name.

        **Validates: Requirements 1.3, 1.4**
    """
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")

    assert provider.provider_name == "openai", (
        "provider_name mismatch: {!r}".format(provider.provider_name)
    )
    assert provider.model_name == "gpt-4", (
        "model_name mismatch: {!r}".format(provider.model_name)
    )

    return


def test_llm_provider_with_config():
    """
        LlmProvider stores a copy of the config dictionary.

        **Validates: Requirements 1.5**
    """
    config = {"temperature": 0.7, "max_tokens": 1000}
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", config=config
    )

    assert provider.config == config, (
        "config mismatch: {!r}".format(provider.config)
    )

    return


def test_llm_provider_with_credential_names():
    """
        LlmProvider stores a copy of the credential_names list.

        **Validates: Requirements 1.6**
    """
    creds = ["openai-api-key", "org-id"]
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", credential_names=creds
    )

    assert provider.credential_names == creds, (
        "credential_names mismatch: {!r}".format(provider.credential_names)
    )

    return


def test_llm_provider_with_tags():
    """
        LlmProvider stores a copy of the tags dictionary.

        **Validates: Requirements 1.7**
    """
    tags = {"tier": "premium", "region": "us-east-1"}
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", tags=tags
    )

    assert provider.tags == tags, (
        "tags mismatch: {!r}".format(provider.tags)
    )

    return


def test_llm_provider_defaults_empty_config():
    """
        LlmProvider defaults config to an empty dict when not provided.

        **Validates: Requirements 1.5**
    """
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")

    assert provider.config == {}, (
        "config should default to empty dict, got: {!r}".format(provider.config)
    )

    return


def test_llm_provider_defaults_empty_credential_names():
    """
        LlmProvider defaults credential_names to an empty list when not provided.

        **Validates: Requirements 1.6**
    """
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")

    assert provider.credential_names == [], (
        "credential_names should default to empty list, got: {!r}".format(
            provider.credential_names
        )
    )

    return


def test_llm_provider_defaults_empty_tags():
    """
        LlmProvider defaults tags to an empty dict when not provided.

        **Validates: Requirements 1.7**
    """
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")

    assert provider.tags == {}, (
        "tags should default to empty dict, got: {!r}".format(provider.tags)
    )

    return


# ---------------------------------------------------------------------------
# Missing name / model raises SemanticError
# ---------------------------------------------------------------------------


def test_llm_provider_none_provider_name_raises_semantic_error():
    """
        LlmProvider raises SemanticError when provider_name is None.

        **Validates: Requirements 1.8**
    """
    caught = False

    try:
        _TestProvider(provider_name=None, model_name="gpt-4")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise SemanticError for None provider_name"
    )

    return


def test_llm_provider_empty_provider_name_raises_semantic_error():
    """
        LlmProvider raises SemanticError when provider_name is empty.

        **Validates: Requirements 1.8**
    """
    caught = False

    try:
        _TestProvider(provider_name="", model_name="gpt-4")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise SemanticError for empty provider_name"
    )

    return


def test_llm_provider_whitespace_provider_name_raises_semantic_error():
    """
        LlmProvider raises SemanticError when provider_name is whitespace only.

        **Validates: Requirements 1.8**
    """
    caught = False

    try:
        _TestProvider(provider_name="   ", model_name="gpt-4")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise SemanticError for whitespace-only provider_name"
    )

    return


def test_llm_provider_none_model_name_raises_semantic_error():
    """
        LlmProvider raises SemanticError when model_name is None.

        **Validates: Requirements 1.9**
    """
    caught = False

    try:
        _TestProvider(provider_name="openai", model_name=None)
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise SemanticError for None model_name"
    )

    return


def test_llm_provider_empty_model_name_raises_semantic_error():
    """
        LlmProvider raises SemanticError when model_name is empty.

        **Validates: Requirements 1.9**
    """
    caught = False

    try:
        _TestProvider(provider_name="openai", model_name="")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise SemanticError for empty model_name"
    )

    return


def test_llm_provider_whitespace_model_name_raises_semantic_error():
    """
        LlmProvider raises SemanticError when model_name is whitespace only.

        **Validates: Requirements 1.9**
    """
    caught = False

    try:
        _TestProvider(provider_name="openai", model_name="   ")
    except SemanticError:
        caught = True

    assert caught is True, (
        "LlmProvider should raise SemanticError for whitespace-only model_name"
    )

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_llm_provider_repr_contains_class_name_and_fields():
    """
        LlmProvider __repr__ includes the concrete class name, provider name,
        and model name.

        **Validates: Requirements 1.10, 19.1**
    """
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")
    repr_str = repr(provider)

    assert "_TestProvider" in repr_str, (
        "repr should contain the concrete class name, got: {!r}".format(repr_str)
    )
    assert "openai" in repr_str, (
        "repr should contain provider_name, got: {!r}".format(repr_str)
    )
    assert "gpt-4" in repr_str, (
        "repr should contain model_name, got: {!r}".format(repr_str)
    )

    return


def test_llm_provider_str_contains_provider_and_model():
    """
        LlmProvider __str__ returns a human-readable summary with provider
        name and model name.

        **Validates: Requirements 1.11, 19.2**
    """
    provider = _TestProvider(provider_name="anthropic", model_name="claude-3")
    str_val = str(provider)

    assert "anthropic" in str_val, (
        "str should contain provider_name, got: {!r}".format(str_val)
    )
    assert "claude-3" in str_val, (
        "str should contain model_name, got: {!r}".format(str_val)
    )

    return


# ---------------------------------------------------------------------------
# get_model_info
# ---------------------------------------------------------------------------


def test_llm_provider_get_model_info():
    """
        get_model_info returns a dict with provider_name, model_name, and config.

        **Validates: Requirements 1.1**
    """
    config = {"temperature": 0.5}
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", config=config
    )
    info = provider.get_model_info()

    assert info["provider_name"] == "openai", (
        "get_model_info provider_name mismatch: {!r}".format(info["provider_name"])
    )
    assert info["model_name"] == "gpt-4", (
        "get_model_info model_name mismatch: {!r}".format(info["model_name"])
    )
    assert info["config"] == config, (
        "get_model_info config mismatch: {!r}".format(info["config"])
    )

    return


def test_llm_provider_get_model_info_config_is_copy():
    """
        get_model_info returns a copy of the config, not the internal dict.

        **Validates: Requirements 1.5**
    """
    config = {"temperature": 0.5}
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", config=config
    )
    info = provider.get_model_info()
    info["config"]["temperature"] = 999

    assert provider.config["temperature"] == 0.5, (
        "Modifying get_model_info result should not affect internal config"
    )

    return


# ---------------------------------------------------------------------------
# Properties return copies
# ---------------------------------------------------------------------------


def test_llm_provider_config_returns_copy():
    """
        The config property returns a copy of the internal dictionary.
        Modifying the returned dict does not affect the provider.

        **Validates: Requirements 1.5**
    """
    config = {"temperature": 0.7}
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", config=config
    )

    returned_config = provider.config
    returned_config["temperature"] = 999

    assert provider.config["temperature"] == 0.7, (
        "Modifying returned config should not affect internal state"
    )

    return


def test_llm_provider_credential_names_returns_copy():
    """
        The credential_names property returns a copy of the internal list.
        Modifying the returned list does not affect the provider.

        **Validates: Requirements 1.6**
    """
    creds = ["api-key"]
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", credential_names=creds
    )

    returned_creds = provider.credential_names
    returned_creds.append("extra-key")

    assert len(provider.credential_names) == 1, (
        "Modifying returned credential_names should not affect internal state"
    )

    return


def test_llm_provider_tags_returns_copy():
    """
        The tags property returns a copy of the internal dictionary.
        Modifying the returned dict does not affect the provider.

        **Validates: Requirements 1.7**
    """
    tags = {"tier": "premium"}
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4", tags=tags
    )

    returned_tags = provider.tags
    returned_tags["tier"] = "free"

    assert provider.tags["tier"] == "premium", (
        "Modifying returned tags should not affect internal state"
    )

    return
