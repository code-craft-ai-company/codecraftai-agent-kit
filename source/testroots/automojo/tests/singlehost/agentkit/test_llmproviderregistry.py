"""
    Unit tests for the automojo.agentkit.llmproviderregistry module.

    Tests LLMProviderRegistry construction, registration, lookup,
    deregistration, has_provider, lookup_by_provider, lookup_by_tags,
    clear, count, and string representations.

    Feature: llm-integration, Task 8.3
    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 19.17, 19.18**
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.llmprovider import LLMProvider
from automojo.agentkit.llmproviderregistry import LLMProviderRegistry


# ---------------------------------------------------------------------------
# Concrete test subclass for testing with the abstract LLMProvider
# ---------------------------------------------------------------------------


class _TestProvider(LLMProvider):
    """
        Minimal concrete subclass of LLMProvider for testing purposes.
    """

    def complete(self, conversation, **kwargs):
        return None

    def complete_stream(self, conversation, handler, **kwargs):
        return None


# ---------------------------------------------------------------------------
# Empty registry
# ---------------------------------------------------------------------------


def test_empty_registry_count_is_zero():
    """
        A new LLMProviderRegistry has count 0.

        **Validates: Requirements 9.8**
    """
    registry = LLMProviderRegistry()

    assert registry.count == 0, (
        "Empty registry count should be 0, got: {}".format(registry.count)
    )

    return


def test_empty_registry_list_all_is_empty():
    """
        A new LLMProviderRegistry returns an empty list from list_all.

        **Validates: Requirements 9.7**
    """
    registry = LLMProviderRegistry()

    result = registry.list_all()

    assert result == [], (
        "Empty registry list_all should return [], got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Register and lookup
# ---------------------------------------------------------------------------


def test_register_and_lookup():
    """
        Registering a provider and looking it up by name+model returns
        the same instance.

        **Validates: Requirements 9.1, 9.4**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")

    registry.register(provider)
    result = registry.lookup("openai", "gpt-4")

    assert result is provider, (
        "lookup should return the registered provider instance"
    )

    return


def test_register_increments_count():
    """
        Registering a provider increments the count.

        **Validates: Requirements 9.1, 9.8**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")

    registry.register(provider)

    assert registry.count == 1, (
        "Count should be 1 after registering one provider, got: {}".format(registry.count)
    )

    return


def test_register_multiple_providers():
    """
        Registering multiple providers with different keys works correctly.

        **Validates: Requirements 9.1, 9.7, 9.8**
    """
    registry = LLMProviderRegistry()
    provider_a = _TestProvider(provider_name="openai", model_name="gpt-4")
    provider_b = _TestProvider(provider_name="anthropic", model_name="claude-3")

    registry.register(provider_a)
    registry.register(provider_b)

    assert registry.count == 2, (
        "Count should be 2 after registering two providers, got: {}".format(registry.count)
    )

    all_providers = registry.list_all()
    assert len(all_providers) == 2, (
        "list_all should return 2 providers, got: {}".format(len(all_providers))
    )

    return


def test_lookup_not_found_returns_none():
    """
        Looking up a provider that is not registered returns None.

        **Validates: Requirements 9.4**
    """
    registry = LLMProviderRegistry()

    result = registry.lookup("openai", "gpt-4")

    assert result is None, (
        "lookup for unregistered provider should return None, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# has_provider
# ---------------------------------------------------------------------------


def test_has_provider_returns_true_when_registered():
    """
        has_provider returns True for a registered provider.

        **Validates: Requirements 9.9**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")
    registry.register(provider)

    result = registry.has_provider("openai", "gpt-4")

    assert result is True, (
        "has_provider should return True for registered provider"
    )

    return


def test_has_provider_returns_false_when_not_registered():
    """
        has_provider returns False for an unregistered provider.

        **Validates: Requirements 9.9**
    """
    registry = LLMProviderRegistry()

    result = registry.has_provider("openai", "gpt-4")

    assert result is False, (
        "has_provider should return False for unregistered provider"
    )

    return


# ---------------------------------------------------------------------------
# Deregister
# ---------------------------------------------------------------------------


def test_deregister_removes_provider():
    """
        Deregistering a provider removes it from the registry.

        **Validates: Requirements 9.3**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")
    registry.register(provider)

    registry.deregister("openai", "gpt-4")

    assert registry.count == 0, (
        "Count should be 0 after deregistering, got: {}".format(registry.count)
    )
    assert registry.lookup("openai", "gpt-4") is None, (
        "lookup should return None after deregistering"
    )

    return


def test_deregister_nonexistent_is_noop():
    """
        Deregistering a provider that is not registered does nothing.

        **Validates: Requirements 9.3**
    """
    registry = LLMProviderRegistry()

    registry.deregister("openai", "gpt-4")

    assert registry.count == 0, (
        "Count should remain 0 after deregistering nonexistent provider"
    )

    return


# ---------------------------------------------------------------------------
# Duplicate registration
# ---------------------------------------------------------------------------


def test_duplicate_registration_raises_semantic_error():
    """
        Registering a provider with the same name+model raises SemanticError.

        **Validates: Requirements 9.2**
    """
    registry = LLMProviderRegistry()
    provider_a = _TestProvider(provider_name="openai", model_name="gpt-4")
    provider_b = _TestProvider(provider_name="openai", model_name="gpt-4")

    registry.register(provider_a)

    caught = False
    error_message = ""

    try:
        registry.register(provider_b)
    except SemanticError as err:
        caught = True
        error_message = str(err)

    assert caught is True, (
        "Duplicate registration should raise SemanticError"
    )
    assert "openai" in error_message, (
        "Error message should contain provider name 'openai', got: {!r}".format(error_message)
    )
    assert "gpt-4" in error_message, (
        "Error message should contain model name 'gpt-4', got: {!r}".format(error_message)
    )

    return


# ---------------------------------------------------------------------------
# lookup_by_provider
# ---------------------------------------------------------------------------


def test_lookup_by_provider_single_model():
    """
        lookup_by_provider returns a list with one provider when only one
        model is registered for that provider name.

        **Validates: Requirements 9.5**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")
    registry.register(provider)

    result = registry.lookup_by_provider("openai")

    assert len(result) == 1, (
        "lookup_by_provider should return 1 provider, got: {}".format(len(result))
    )
    assert result[0] is provider, (
        "lookup_by_provider should return the registered provider instance"
    )

    return


def test_lookup_by_provider_multiple_models():
    """
        lookup_by_provider returns all providers for a given provider name
        when multiple models are registered.

        **Validates: Requirements 9.5**
    """
    registry = LLMProviderRegistry()
    provider_gpt4 = _TestProvider(provider_name="openai", model_name="gpt-4")
    provider_gpt35 = _TestProvider(provider_name="openai", model_name="gpt-3.5-turbo")
    provider_claude = _TestProvider(provider_name="anthropic", model_name="claude-3")

    registry.register(provider_gpt4)
    registry.register(provider_gpt35)
    registry.register(provider_claude)

    result = registry.lookup_by_provider("openai")

    assert len(result) == 2, (
        "lookup_by_provider('openai') should return 2 providers, got: {}".format(len(result))
    )
    assert provider_gpt4 in result, (
        "Result should contain the gpt-4 provider"
    )
    assert provider_gpt35 in result, (
        "Result should contain the gpt-3.5-turbo provider"
    )

    return


def test_lookup_by_provider_no_match():
    """
        lookup_by_provider returns an empty list when no providers match.

        **Validates: Requirements 9.5**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(provider_name="openai", model_name="gpt-4")
    registry.register(provider)

    result = registry.lookup_by_provider("anthropic")

    assert result == [], (
        "lookup_by_provider for unregistered provider should return [], got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# lookup_by_tags
# ---------------------------------------------------------------------------


def test_lookup_by_tags_no_matches():
    """
        lookup_by_tags returns an empty list when no providers match the
        given tag criteria.

        **Validates: Requirements 9.6**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4",
        tags={"tier": "premium"}
    )
    registry.register(provider)

    result = registry.lookup_by_tags(tier="free")

    assert result == [], (
        "lookup_by_tags with non-matching value should return [], got: {!r}".format(result)
    )

    return


def test_lookup_by_tags_no_matches_missing_key():
    """
        lookup_by_tags returns an empty list when providers do not have
        the requested tag key.

        **Validates: Requirements 9.6**
    """
    registry = LLMProviderRegistry()
    provider = _TestProvider(
        provider_name="openai", model_name="gpt-4",
        tags={"tier": "premium"}
    )
    registry.register(provider)

    result = registry.lookup_by_tags(region="us-east")

    assert result == [], (
        "lookup_by_tags with missing key should return [], got: {!r}".format(result)
    )

    return


def test_lookup_by_tags_partial_match():
    """
        lookup_by_tags returns only providers that match ALL tag criteria.
        A provider matching only some tags is excluded.

        **Validates: Requirements 9.6**
    """
    registry = LLMProviderRegistry()
    provider_a = _TestProvider(
        provider_name="openai", model_name="gpt-4",
        tags={"tier": "premium", "region": "us-east"}
    )
    provider_b = _TestProvider(
        provider_name="anthropic", model_name="claude-3",
        tags={"tier": "premium"}
    )
    registry.register(provider_a)
    registry.register(provider_b)

    result = registry.lookup_by_tags(tier="premium", region="us-east")

    assert len(result) == 1, (
        "lookup_by_tags with partial match should return 1 provider, got: {}".format(len(result))
    )
    assert result[0] is provider_a, (
        "Result should contain only the provider matching all tags"
    )

    return


def test_lookup_by_tags_full_match():
    """
        lookup_by_tags returns all providers that match all tag criteria.

        **Validates: Requirements 9.6**
    """
    registry = LLMProviderRegistry()
    provider_a = _TestProvider(
        provider_name="openai", model_name="gpt-4",
        tags={"tier": "premium", "region": "us-east"}
    )
    provider_b = _TestProvider(
        provider_name="anthropic", model_name="claude-3",
        tags={"tier": "premium", "region": "us-east"}
    )
    provider_c = _TestProvider(
        provider_name="bedrock", model_name="titan",
        tags={"tier": "standard"}
    )
    registry.register(provider_a)
    registry.register(provider_b)
    registry.register(provider_c)

    result = registry.lookup_by_tags(tier="premium")

    assert len(result) == 2, (
        "lookup_by_tags should return 2 matching providers, got: {}".format(len(result))
    )
    assert provider_a in result, (
        "Result should contain the openai provider"
    )
    assert provider_b in result, (
        "Result should contain the anthropic provider"
    )

    return


def test_lookup_by_tags_empty_tags_returns_all():
    """
        lookup_by_tags with no tag criteria returns all providers.

        **Validates: Requirements 9.6**
    """
    registry = LLMProviderRegistry()
    provider_a = _TestProvider(provider_name="openai", model_name="gpt-4")
    provider_b = _TestProvider(provider_name="anthropic", model_name="claude-3")
    registry.register(provider_a)
    registry.register(provider_b)

    result = registry.lookup_by_tags()

    assert len(result) == 2, (
        "lookup_by_tags with no criteria should return all providers, got: {}".format(len(result))
    )

    return


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------


def test_clear_removes_all_providers():
    """
        clear removes all registered providers from the registry.

        **Validates: Requirements 9.7, 9.8**
    """
    registry = LLMProviderRegistry()
    provider_a = _TestProvider(provider_name="openai", model_name="gpt-4")
    provider_b = _TestProvider(provider_name="anthropic", model_name="claude-3")
    registry.register(provider_a)
    registry.register(provider_b)

    registry.clear()

    assert registry.count == 0, (
        "Count should be 0 after clear, got: {}".format(registry.count)
    )
    assert registry.list_all() == [], (
        "list_all should return [] after clear"
    )

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_repr_empty_registry():
    """
        __repr__ of an empty registry includes the class name and count 0.

        **Validates: Requirements 19.17**
    """
    registry = LLMProviderRegistry()

    result = repr(registry)

    assert "LLMProviderRegistry" in result, (
        "repr should contain class name, got: {!r}".format(result)
    )
    assert "0" in result, (
        "repr should contain count 0, got: {!r}".format(result)
    )

    return


def test_repr_with_providers():
    """
        __repr__ of a registry with providers includes the correct count.

        **Validates: Requirements 19.17**
    """
    registry = LLMProviderRegistry()
    registry.register(_TestProvider(provider_name="openai", model_name="gpt-4"))
    registry.register(_TestProvider(provider_name="anthropic", model_name="claude-3"))

    result = repr(registry)

    assert "LLMProviderRegistry" in result, (
        "repr should contain class name, got: {!r}".format(result)
    )
    assert "2" in result, (
        "repr should contain count 2, got: {!r}".format(result)
    )

    return


def test_str_empty_registry():
    """
        __str__ of an empty registry lists no provider pairs.

        **Validates: Requirements 19.18**
    """
    registry = LLMProviderRegistry()

    result = str(registry)

    assert "LLMProviderRegistry" in result, (
        "str should contain class name, got: {!r}".format(result)
    )

    return


def test_str_with_providers():
    """
        __str__ of a registry with providers lists the provider/model pairs.

        **Validates: Requirements 19.18**
    """
    registry = LLMProviderRegistry()
    registry.register(_TestProvider(provider_name="openai", model_name="gpt-4"))

    result = str(registry)

    assert "openai/gpt-4" in result, (
        "str should contain 'openai/gpt-4', got: {!r}".format(result)
    )

    return
