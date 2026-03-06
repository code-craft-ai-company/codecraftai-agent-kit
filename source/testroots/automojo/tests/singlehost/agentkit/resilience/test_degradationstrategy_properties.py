"""
    Property-based tests for degradation strategy classes.

    Uses the hypothesis library to verify:
    - Property 21: DefaultValueStrategy returns configured default
    - Property 22: CachedResultStrategy returns cached result

    **Validates: Requirements 7.4, 7.5**
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.cachedresultstrategy import CachedResultStrategy
from automojo.agentkit.defaultvaluestrategy import DefaultValueStrategy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_default_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10000, max_value=10000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100),
    st.lists(st.integers(min_value=-100, max_value=100), max_size=10),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.integers(min_value=-100, max_value=100),
        max_size=5,
    ),
)

_dependency_names = st.text(
    min_size=1,
    max_size=50,
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S"),
        blacklist_characters=("\x00",),
    ),
)

_exception_messages = st.text(min_size=0, max_size=100)

_optional_contexts = st.one_of(
    st.none(),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.text(min_size=0, max_size=50),
        max_size=5,
    ),
)


# ---------------------------------------------------------------------------
# Property 21: DefaultValueStrategy returns configured default
# ---------------------------------------------------------------------------

@given(
    default_value=_default_values,
    dependency_name=_dependency_names,
    exception_message=_exception_messages,
    context=_optional_contexts,
)
@settings(max_examples=200)
def test_default_value_strategy_returns_configured_default(
    default_value,
    dependency_name: str,
    exception_message: str,
    context,
) -> None:
    """
        **Validates: Requirements 7.5**

        For all DefaultValueStrategy instances constructed with an arbitrary
        default_value, calling degrade() with any dependency_name and exception
        shall return the configured default_value.

        # Feature: error-handling-resilience, Property 21: DefaultValueStrategy returns configured default
    """
    strategy = DefaultValueStrategy(default_value)

    exception = RuntimeError(exception_message)

    result = strategy.degrade(dependency_name, exception, context)

    assert result is default_value, (
        "Expected degrade() to return the configured default_value {!r} "
        "but got {!r}".format(default_value, result)
    )

    return


# ---------------------------------------------------------------------------
# Strategies for Property 22
# ---------------------------------------------------------------------------

_cached_values = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-10000, max_value=10000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100),
    st.lists(st.integers(min_value=-100, max_value=100), max_size=10),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=20),
        values=st.integers(min_value=-100, max_value=100),
        max_size=5,
    ),
)


# ---------------------------------------------------------------------------
# Property 22: CachedResultStrategy returns cached result
# ---------------------------------------------------------------------------

@given(
    cached_value=_cached_values,
    dependency_name=_dependency_names,
    exception_message=_exception_messages,
    context=_optional_contexts,
)
@settings(max_examples=200)
def test_cached_result_strategy_returns_cached_result(
    cached_value,
    dependency_name: str,
    exception_message: str,
    context,
) -> None:
    """
        **Validates: Requirements 7.4**

        For all CachedResultStrategy instances, after calling
        cache_result(dependency_name, value), calling degrade() with the same
        dependency_name and any exception shall return the cached value.

        # Feature: error-handling-resilience, Property 22: CachedResultStrategy returns cached result
    """
    strategy = CachedResultStrategy()

    strategy.cache_result(dependency_name, cached_value)

    exception = RuntimeError(exception_message)

    result = strategy.degrade(dependency_name, exception, context)

    assert result is cached_value, (
        "Expected degrade() to return the cached value {!r} "
        "but got {!r}".format(cached_value, result)
    )

    return
