"""
    Unit tests for degradation strategies: CachedResultStrategy,
    DefaultValueStrategy, and AlternateProviderStrategy.
"""

from automojo.agentkit.alternateproviderstrategy import AlternateProviderStrategy
from automojo.agentkit.cachedresultstrategy import CachedResultStrategy
from automojo.agentkit.defaultvaluestrategy import DefaultValueStrategy


def test_cached_result_strategy_returns_cached():
    """
        Verify that CachedResultStrategy returns the cached result.
    """
    strategy = CachedResultStrategy()
    strategy.cache_result("db", {"data": "cached"})

    result = strategy.degrade("db", RuntimeError("unavailable"))
    assert result == {"data": "cached"}, "should return cached result"
    return


def test_cached_result_strategy_returns_none_when_no_cache():
    """
        Verify that CachedResultStrategy returns None when no cache exists.
    """
    strategy = CachedResultStrategy()
    result = strategy.degrade("db", RuntimeError("unavailable"))
    assert result is None, "should return None when no cache"
    return


def test_cached_result_strategy_name():
    """
        Verify that CachedResultStrategy has the correct strategy name.
    """
    strategy = CachedResultStrategy()
    assert strategy.strategy_name == "cached_result", "strategy name should be 'cached_result'"
    return


def test_default_value_strategy_returns_default():
    """
        Verify that DefaultValueStrategy returns the configured default.
    """
    strategy = DefaultValueStrategy("fallback")
    result = strategy.degrade("service", RuntimeError("down"))
    assert result == "fallback", "should return default value"
    return


def test_default_value_strategy_name():
    """
        Verify that DefaultValueStrategy has the correct strategy name.
    """
    strategy = DefaultValueStrategy(42)
    assert strategy.strategy_name == "default_value", "strategy name should be 'default_value'"
    return


def test_default_value_strategy_property():
    """
        Verify that DefaultValueStrategy exposes the default_value property.
    """
    strategy = DefaultValueStrategy({"key": "value"})
    assert strategy.default_value == {"key": "value"}, "default_value property should match"
    return


def test_alternate_provider_strategy_invokes_callable():
    """
        Verify that AlternateProviderStrategy invokes the alternate callable.
    """
    strategy = AlternateProviderStrategy(lambda: "alternate result")
    result = strategy.degrade("primary", RuntimeError("down"))
    assert result == "alternate result", "should return alternate callable result"
    return


def test_alternate_provider_strategy_name():
    """
        Verify that AlternateProviderStrategy has the correct strategy name.
    """
    strategy = AlternateProviderStrategy(lambda: None)
    assert strategy.strategy_name == "alternate_provider", "strategy name should be 'alternate_provider'"
    return


def test_strategy_repr():
    """
        Verify that strategy __repr__ includes class name and strategy name.
    """
    strategy = DefaultValueStrategy("test")
    repr_str = repr(strategy)
    assert "DefaultValueStrategy" in repr_str, "repr should contain class name"
    assert "default_value" in repr_str, "repr should contain strategy name"
    return


def test_strategy_str():
    """
        Verify that strategy __str__ returns a human-readable summary.
    """
    strategy = CachedResultStrategy()
    str_val = str(strategy)
    assert "cached_result" in str_val, "str should contain strategy name"
    return
