"""
    Unit tests for the automojo.agentkit.fallbackchain module.

    Tests FallbackChain construction, providers property, next_provider
    traversal, and string representations.

    Feature: llm-integration, Task 13.4
    **Validates: Requirements 10.8, 10.9, 10.10**
"""

from automojo.agentkit.fallbackchain import FallbackChain


# ---------------------------------------------------------------------------
# Construction and providers property
# ---------------------------------------------------------------------------


def test_construction_stores_providers():
    """
        FallbackChain stores the ordered list of provider tuples.

        **Validates: Requirements 10.8, 10.9**
    """
    providers = [("openai", "gpt-4"), ("anthropic", "claude-3")]
    chain = FallbackChain(providers)

    result = chain.providers

    assert result == [("openai", "gpt-4"), ("anthropic", "claude-3")], (
        "providers should match input, got: {!r}".format(result)
    )

    return


def test_providers_returns_copy():
    """
        The providers property returns a copy of the internal list.

        **Validates: Requirements 10.9**
    """
    providers = [("openai", "gpt-4"), ("anthropic", "claude-3")]
    chain = FallbackChain(providers)

    result = chain.providers
    result.append(("bedrock", "titan"))

    assert len(chain.providers) == 2, (
        "Modifying the returned list should not affect the chain"
    )

    return


def test_construction_with_single_provider():
    """
        FallbackChain works with a single provider.

        **Validates: Requirements 10.8**
    """
    chain = FallbackChain([("openai", "gpt-4")])

    assert chain.providers == [("openai", "gpt-4")], (
        "Single provider chain should have one entry"
    )

    return


def test_construction_with_empty_list():
    """
        FallbackChain can be constructed with an empty list.

        **Validates: Requirements 10.8**
    """
    chain = FallbackChain([])

    assert chain.providers == [], (
        "Empty chain should have no providers"
    )

    return


# ---------------------------------------------------------------------------
# next_provider
# ---------------------------------------------------------------------------


def test_next_provider_returns_second_after_first():
    """
        next_provider returns the second provider when given the first.

        **Validates: Requirements 10.10**
    """
    chain = FallbackChain([
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
        ("bedrock", "titan")
    ])

    result = chain.next_provider("openai", "gpt-4")

    assert result == ("anthropic", "claude-3"), (
        "next_provider after first should be second, got: {!r}".format(result)
    )

    return


def test_next_provider_returns_third_after_second():
    """
        next_provider returns the third provider when given the second.

        **Validates: Requirements 10.10**
    """
    chain = FallbackChain([
        ("openai", "gpt-4"),
        ("anthropic", "claude-3"),
        ("bedrock", "titan")
    ])

    result = chain.next_provider("anthropic", "claude-3")

    assert result == ("bedrock", "titan"), (
        "next_provider after second should be third, got: {!r}".format(result)
    )

    return


def test_next_provider_at_end_of_chain_returns_none():
    """
        next_provider returns None when the current provider is the last
        in the chain.

        **Validates: Requirements 10.10**
    """
    chain = FallbackChain([
        ("openai", "gpt-4"),
        ("anthropic", "claude-3")
    ])

    result = chain.next_provider("anthropic", "claude-3")

    assert result is None, (
        "next_provider at end of chain should return None, got: {!r}".format(result)
    )

    return


def test_next_provider_unknown_provider_returns_none():
    """
        next_provider returns None when the current provider is not in
        the chain.

        **Validates: Requirements 10.10**
    """
    chain = FallbackChain([
        ("openai", "gpt-4"),
        ("anthropic", "claude-3")
    ])

    result = chain.next_provider("unknown", "model-x")

    assert result is None, (
        "next_provider for unknown provider should return None, got: {!r}".format(result)
    )

    return


def test_next_provider_single_provider_chain_returns_none():
    """
        next_provider returns None for a single-provider chain when
        given that provider.

        **Validates: Requirements 10.10**
    """
    chain = FallbackChain([("openai", "gpt-4")])

    result = chain.next_provider("openai", "gpt-4")

    assert result is None, (
        "next_provider in single-provider chain should return None, got: {!r}".format(
            result
        )
    )

    return


def test_next_provider_empty_chain_returns_none():
    """
        next_provider returns None for an empty chain.

        **Validates: Requirements 10.10**
    """
    chain = FallbackChain([])

    result = chain.next_provider("openai", "gpt-4")

    assert result is None, (
        "next_provider in empty chain should return None, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# __repr__ and __str__
# ---------------------------------------------------------------------------


def test_repr_contains_class_name_and_count():
    """
        __repr__ includes the class name and provider count.

        **Validates: Requirements 10.8**
    """
    chain = FallbackChain([
        ("openai", "gpt-4"),
        ("anthropic", "claude-3")
    ])

    result = repr(chain)

    assert "FallbackChain" in result, (
        "__repr__ should contain 'FallbackChain', got: {!r}".format(result)
    )
    assert "2" in result, (
        "__repr__ should contain count '2', got: {!r}".format(result)
    )

    return


def test_str_lists_provider_pairs():
    """
        __str__ lists the provider name/model pairs.

        **Validates: Requirements 10.8**
    """
    chain = FallbackChain([
        ("openai", "gpt-4"),
        ("anthropic", "claude-3")
    ])

    result = str(chain)

    assert "FallbackChain" in result, (
        "__str__ should contain 'FallbackChain', got: {!r}".format(result)
    )
    assert "openai/gpt-4" in result, (
        "__str__ should contain 'openai/gpt-4', got: {!r}".format(result)
    )
    assert "anthropic/claude-3" in result, (
        "__str__ should contain 'anthropic/claude-3', got: {!r}".format(result)
    )

    return


def test_repr_empty_chain():
    """
        __repr__ for an empty chain shows count 0.

        **Validates: Requirements 10.8**
    """
    chain = FallbackChain([])

    result = repr(chain)

    assert "0" in result, (
        "__repr__ for empty chain should contain '0', got: {!r}".format(result)
    )

    return


def test_str_empty_chain():
    """
        __str__ for an empty chain shows an empty list.

        **Validates: Requirements 10.8**
    """
    chain = FallbackChain([])

    result = str(chain)

    assert "FallbackChain: []" in result, (
        "__str__ for empty chain should contain 'FallbackChain: []', got: {!r}".format(
            result
        )
    )

    return
