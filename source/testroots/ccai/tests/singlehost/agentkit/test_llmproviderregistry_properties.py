"""
    Property-based tests for the ccai.agentkit.llmproviderregistry module.

    Uses ccai.testbase.properties to verify:
    - Property 26: LLMProviderRegistry registration, lookup, and enumeration
    - Property 27: LLMProviderRegistry deregistration removes provider
    - Property 28: LLMProviderRegistry lookup by tags returns matching providers

    **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9**
"""

from ccai.testbase.properties import given, assume
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.llmprovider import LLMProvider
from ccai.agentkit.llmproviderregistry import LLMProviderRegistry


# ---------------------------------------------------------------------------
# Concrete test subclass for testing the abstract base class
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
# Strategies
# ---------------------------------------------------------------------------

_identifier = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=12,
)

_tag_key = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=8,
)

_tag_value = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=8,
)

_tags_dict = st.dictionaries(
    keys=_tag_key,
    values=_tag_value,
    min_size=0,
    max_size=4,
)


@composite
def _provider_spec(draw):
    """
        Draws a (provider_name, model_name, tags) tuple for constructing
        a _TestProvider instance.
    """
    provider_name = draw(_identifier)
    model_name = draw(_identifier)
    tags = draw(_tags_dict)
    return (provider_name, model_name, tags)


@composite
def _unique_provider_specs(draw, min_size=0, max_size=10):
    """
        Draws a list of (provider_name, model_name, tags) tuples with
        unique (provider_name, model_name) composite keys.
    """
    specs = draw(st.lists(_provider_spec(), min_size=min_size, max_size=max_size))

    seen_keys = set()
    unique_specs = []

    for provider_name, model_name, tags in specs:
        key = (provider_name, model_name)

        if key not in seen_keys:
            seen_keys.add(key)
            unique_specs.append((provider_name, model_name, tags))

    return unique_specs


def _make_provider(provider_name, model_name, tags=None):
    """
        Helper to construct a _TestProvider instance.
    """
    rtnval = _TestProvider(
        provider_name=provider_name,
        model_name=model_name,
        tags=tags,
    )
    return rtnval


# ---------------------------------------------------------------------------
# Property 26: LLMProviderRegistry registration, lookup, and enumeration
# ---------------------------------------------------------------------------


@given(specs=_unique_provider_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_count_equals_number_of_registered_providers(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.1, 9.8**

        For any set of N providers with unique keys, after registration
        count shall equal N.
    """
    registry = LLMProviderRegistry()

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

    assert registry.count == len(specs), (
        "count should be {}, got {}".format(len(specs), registry.count)
    )

    return


@given(specs=_unique_provider_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_lookup_returns_correct_provider(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.1, 9.4**

        For any registered provider, lookup(provider_name, model_name)
        shall return the correct provider instance.
    """
    registry = LLMProviderRegistry()
    providers = []

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)
        providers.append(provider)

    for provider in providers:
        result = registry.lookup(provider.provider_name, provider.model_name)

        assert result is provider, (
            "lookup({!r}, {!r}) should return the registered provider".format(
                provider.provider_name, provider.model_name
            )
        )

    return


@given(specs=_unique_provider_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_lookup_returns_none_for_unregistered(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.4**

        lookup() shall return None for provider name / model name pairs
        that are not registered.
    """
    registry = LLMProviderRegistry()

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

    result = registry.lookup("nonexistent_provider", "nonexistent_model")

    assert result is None, (
        "lookup for unregistered provider should return None, got {!r}".format(result)
    )

    return


@given(specs=_unique_provider_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_has_provider_returns_true_for_registered(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.1, 9.9**

        has_provider() shall return True for registered pairs.
    """
    registry = LLMProviderRegistry()

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

    for provider_name, model_name, _ in specs:
        result = registry.has_provider(provider_name, model_name)

        assert result is True, (
            "has_provider({!r}, {!r}) should be True".format(
                provider_name, model_name
            )
        )

    return


@given(specs=_unique_provider_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_has_provider_returns_false_for_unregistered(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.9**

        has_provider() shall return False for unregistered pairs.
    """
    registry = LLMProviderRegistry()

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

    result = registry.has_provider("nonexistent_provider", "nonexistent_model")

    assert result is False, (
        "has_provider for unregistered provider should be False"
    )

    return


@given(specs=_unique_provider_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_list_all_returns_all_providers(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.1, 9.7**

        list_all() shall return all N registered providers.
    """
    registry = LLMProviderRegistry()
    providers = []

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)
        providers.append(provider)

    all_providers = registry.list_all()

    assert len(all_providers) == len(providers), (
        "list_all() should return {} providers, got {}".format(
            len(providers), len(all_providers)
        )
    )

    for provider in providers:
        assert provider in all_providers, (
            "list_all() should contain provider ({!r}, {!r})".format(
                provider.provider_name, provider.model_name
            )
        )

    return


@given(specs=_unique_provider_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_duplicate_registration_raises_semantic_error(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.2**

        Registering a duplicate (provider_name, model_name) shall raise
        SemanticError.
    """
    registry = LLMProviderRegistry()

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

    # Pick the first spec and try to register a duplicate
    first_pname, first_mname, first_tags = specs[0]
    duplicate_provider = _make_provider(first_pname, first_mname, first_tags)

    raised = False
    try:
        registry.register(duplicate_provider)
    except SemanticError:
        raised = True

    assert raised is True, (
        "Registering duplicate ({!r}, {!r}) should raise SemanticError".format(
            first_pname, first_mname
        )
    )

    return


@given(specs=_unique_provider_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_lookup_by_provider_returns_matching_providers(
    specs: list,
) -> None:
    """
        **Validates: Requirements 9.1, 9.5**

        lookup_by_provider(provider_name) shall return all providers
        for that provider name.
    """
    registry = LLMProviderRegistry()
    providers_by_name = {}

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

        if provider_name not in providers_by_name:
            providers_by_name[provider_name] = []
        providers_by_name[provider_name].append(provider)

    for pname, expected_providers in providers_by_name.items():
        result = registry.lookup_by_provider(pname)

        assert len(result) == len(expected_providers), (
            "lookup_by_provider({!r}) should return {} providers, got {}".format(
                pname, len(expected_providers), len(result)
            )
        )

        for ep in expected_providers:
            assert ep in result, (
                "lookup_by_provider({!r}) should contain provider with model {!r}".format(
                    pname, ep.model_name
                )
            )

    return


# ---------------------------------------------------------------------------
# Property 27: LLMProviderRegistry deregistration removes provider
# ---------------------------------------------------------------------------


@given(
    specs=_unique_provider_specs(min_size=1, max_size=15),
    index_data=st.integers(min_value=0, max_value=1000),
    constraints={"max_examples": 50},
)
def test_registry_deregister_removes_provider(
    specs: list,
    index_data: int,
) -> None:
    """
        **Validates: Requirements 9.3**

        For any registered LLMProvider, calling deregister(provider_name,
        model_name) shall remove it so that lookup() returns None,
        has_provider() returns False, and count decreases by one.
    """
    registry = LLMProviderRegistry()

    for provider_name, model_name, tags in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

    original_count = registry.count

    # Pick a provider to deregister using modular index
    target_index = index_data % len(specs)
    target_pname, target_mname, _ = specs[target_index]

    registry.deregister(target_pname, target_mname)

    lookup_result = registry.lookup(target_pname, target_mname)
    assert lookup_result is None, (
        "lookup({!r}, {!r}) should return None after deregister".format(
            target_pname, target_mname
        )
    )

    has_result = registry.has_provider(target_pname, target_mname)
    assert has_result is False, (
        "has_provider({!r}, {!r}) should be False after deregister".format(
            target_pname, target_mname
        )
    )

    assert registry.count == original_count - 1, (
        "count should be {}, got {}".format(
            original_count - 1, registry.count
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 28: LLMProviderRegistry lookup by tags returns matching providers
# ---------------------------------------------------------------------------


@composite
def _tagged_provider_specs(draw):
    """
        Draws a list of unique provider specs where some providers share
        a common tag and others do not, enabling tag-based lookup testing.
    """
    common_tag_key = draw(_tag_key)
    common_tag_value = draw(_tag_value)

    num_matching = draw(st.integers(min_value=1, max_value=5))
    num_non_matching = draw(st.integers(min_value=0, max_value=5))

    specs = []
    seen_keys = set()

    for i in range(num_matching):
        provider_name = draw(_identifier)
        model_name = draw(_identifier)
        key = (provider_name, model_name)

        if key in seen_keys:
            continue
        seen_keys.add(key)

        extra_tags = draw(_tags_dict)
        tags = dict(extra_tags)
        tags[common_tag_key] = common_tag_value

        specs.append((provider_name, model_name, tags, True))

    for i in range(num_non_matching):
        provider_name = draw(_identifier)
        model_name = draw(_identifier)
        key = (provider_name, model_name)

        if key in seen_keys:
            continue
        seen_keys.add(key)

        extra_tags = draw(_tags_dict)
        tags = dict(extra_tags)

        # Ensure this provider does NOT match the common tag criteria
        if common_tag_key in tags and tags[common_tag_key] == common_tag_value:
            del tags[common_tag_key]

        specs.append((provider_name, model_name, tags, False))

    return (common_tag_key, common_tag_value, specs)


@given(data=_tagged_provider_specs(), constraints={"max_examples": 50})
def test_registry_lookup_by_tags_returns_matching_providers(
    data: tuple,
) -> None:
    """
        **Validates: Requirements 9.6**

        lookup_by_tags(**criteria) shall return exactly those providers
        whose tags contain all the specified key-value pairs.
    """
    common_tag_key, common_tag_value, specs = data

    # Need at least one spec to test
    assume(len(specs) > 0)

    registry = LLMProviderRegistry()
    expected_matching = []

    for provider_name, model_name, tags, should_match in specs:
        provider = _make_provider(provider_name, model_name, tags)
        registry.register(provider)

        if should_match is True:
            expected_matching.append(provider)

    criteria = {common_tag_key: common_tag_value}
    result = registry.lookup_by_tags(**criteria)

    assert len(result) == len(expected_matching), (
        "lookup_by_tags should return {} providers, got {}".format(
            len(expected_matching), len(result)
        )
    )

    for provider in expected_matching:
        assert provider in result, (
            "lookup_by_tags should contain provider ({!r}, {!r})".format(
                provider.provider_name, provider.model_name
            )
        )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
