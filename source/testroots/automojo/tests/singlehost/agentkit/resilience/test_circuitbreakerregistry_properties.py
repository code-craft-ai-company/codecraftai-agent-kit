"""
    Property-based tests for the automojo.agentkit.circuitbreakerregistry module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 15: CircuitBreakerRegistry register-lookup consistency
    - Property 16: CircuitBreakerRegistry count consistency
    - Property 17: CircuitBreakerRegistry has_circuit_breaker consistency

    **Validates: Requirements 6.1, 6.3, 6.4, 6.5, 6.6, 6.7**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.circuitbreaker import CircuitBreaker
from automojo.agentkit.circuitbreakerconfiguration import CircuitBreakerConfiguration
from automojo.agentkit.circuitbreakerregistry import CircuitBreakerRegistry


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_unique_names = st.lists(
    st.text(min_size=1, max_size=100, alphabet=st.characters(
        categories=("L", "N", "P", "S"),
    )),
    min_size=1,
    max_size=20,
).map(lambda names: list(dict.fromkeys(names))).filter(lambda names: len(names) >= 1)

_failure_threshold = st.integers(min_value=1, max_value=100)

_success_threshold = st.integers(min_value=1, max_value=100)

_open_state_timeout = st.floats(
    min_value=0.1, max_value=3600.0,
)

_half_open_max_attempts = st.integers(min_value=1, max_value=100)

_circuit_breaker_configuration = st.builds(
    CircuitBreakerConfiguration,
    failure_threshold=_failure_threshold,
    success_threshold=_success_threshold,
    open_state_timeout=_open_state_timeout,
    half_open_max_attempts=_half_open_max_attempts,
)


# ---------------------------------------------------------------------------
# Property 15: CircuitBreakerRegistry register-lookup consistency
# ---------------------------------------------------------------------------

@given(
    names=_unique_names,
    configuration=_circuit_breaker_configuration,
    constraints={"max_examples": 50},
)
def test_circuitbreakerregistry_register_lookup_consistency(
    names: list,
    configuration: CircuitBreakerConfiguration,
) -> None:
    """
        **Validates: Requirements 6.1, 6.4**

        For all sequences of unique-named CircuitBreaker registrations,
        looking up each registered name shall return the same CircuitBreaker
        instance that was registered.

        # Feature: error-handling-resilience, Property 15: CircuitBreakerRegistry register-lookup consistency
    """
    registry = CircuitBreakerRegistry()

    # Create and register a CircuitBreaker for each unique name
    breakers = {}
    for name in names:
        cb = CircuitBreaker(name=name, configuration=configuration)
        registry.register(cb)
        breakers[name] = cb

    # Verify that lookup returns the exact same instance for each name
    for name, expected_cb in breakers.items():
        looked_up = registry.lookup(name)

        assert looked_up is not None, (
            "Expected lookup('{}') to return a CircuitBreaker, got None".format(name)
        )

        assert looked_up is expected_cb, (
            "Expected lookup('{}') to return the same instance (id={}), "
            "got a different instance (id={})".format(
                name, id(expected_cb), id(looked_up)
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 16: CircuitBreakerRegistry count consistency
# ---------------------------------------------------------------------------

@given(
    names=_unique_names,
    configuration=_circuit_breaker_configuration,
    constraints={"max_examples": 50},
)
def test_circuitbreakerregistry_count_consistency(
    names: list,
    configuration: CircuitBreakerConfiguration,
) -> None:
    """
        **Validates: Requirements 6.5, 6.6**

        For all sequences of unique-named CircuitBreaker registrations,
        the count property shall equal the number of registered circuit
        breakers and list_all() shall return the same number of items.

        # Feature: error-handling-resilience, Property 16: CircuitBreakerRegistry count consistency
    """
    registry = CircuitBreakerRegistry()

    # Register a CircuitBreaker for each unique name
    for name in names:
        cb = CircuitBreaker(name=name, configuration=configuration)
        registry.register(cb)

    expected_count = len(names)

    # Verify count property matches the number of registered breakers
    assert registry.count == expected_count, (
        "Expected count to be {}, got {}".format(expected_count, registry.count)
    )

    # Verify list_all() returns the same number of items
    all_breakers = registry.list_all()
    assert len(all_breakers) == expected_count, (
        "Expected list_all() to return {} items, got {}".format(
            expected_count, len(all_breakers)
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 17: CircuitBreakerRegistry has_circuit_breaker consistency
# ---------------------------------------------------------------------------

@given(
    registered_names=_unique_names,
    unregistered_names=_unique_names,
    configuration=_circuit_breaker_configuration,
    constraints={"max_examples": 50},
)
def test_circuitbreakerregistry_has_circuit_breaker_consistency(
    registered_names: list,
    unregistered_names: list,
    configuration: CircuitBreakerConfiguration,
) -> None:
    """
        **Validates: Requirements 6.3, 6.7**

        For all CircuitBreakerRegistry instances, after registering a
        CircuitBreaker with name X, has_circuit_breaker(X) shall return True,
        and after deregistering name X, has_circuit_breaker(X) shall return
        False. Names that were never registered shall also return False.

        # Feature: error-handling-resilience, Property 17: CircuitBreakerRegistry has_circuit_breaker consistency
    """
    registry = CircuitBreakerRegistry()

    # Ensure unregistered_names does not overlap with registered_names
    registered_set = set(registered_names)
    truly_unregistered = [n for n in unregistered_names if n not in registered_set]

    # Register circuit breakers for all registered_names
    for name in registered_names:
        cb = CircuitBreaker(name=name, configuration=configuration)
        registry.register(cb)

    # Verify has_circuit_breaker returns True for all registered names
    for name in registered_names:
        assert registry.has_circuit_breaker(name) is True, (
            "Expected has_circuit_breaker('{}') to return True after "
            "registration, got False".format(name)
        )

    # Verify has_circuit_breaker returns False for unregistered names
    for name in truly_unregistered:
        assert registry.has_circuit_breaker(name) is False, (
            "Expected has_circuit_breaker('{}') to return False for "
            "unregistered name, got True".format(name)
        )

    # Deregister all registered names and verify has_circuit_breaker returns False
    for name in registered_names:
        registry.deregister(name)

        assert registry.has_circuit_breaker(name) is False, (
            "Expected has_circuit_breaker('{}') to return False after "
            "deregistration, got True".format(name)
        )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
