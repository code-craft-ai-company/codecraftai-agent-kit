"""
    Property-based tests for the ccai.agentkit.healthcheckregistry module.

    Uses the ccai.testbase.properties engine to verify:
    - Property 30: HealthCheckRegistry register-lookup consistency

    **Validates: Requirements 17.1, 17.4**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.testbase.mocking import Mock

from ccai.agentkit.healthcheckregistry import HealthCheckRegistry
from ccai.agentkit.transporthealthcheck import TransportHealthCheck


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_health_check(name: str) -> TransportHealthCheck:
    """
        Creates a concrete HealthCheck instance using TransportHealthCheck
        with a mock transport.
    """
    mock_transport = Mock()
    mock_transport.configure(recursive=True)
    return TransportHealthCheck(name, mock_transport)


# ---------------------------------------------------------------------------
# Property 30: HealthCheckRegistry register-lookup consistency
# ---------------------------------------------------------------------------

@given(
    names=_unique_names,
    constraints={"max_examples": 50},
)
def test_healthcheckregistry_register_lookup_consistency(names: list) -> None:
    """
        **Validates: Requirements 17.1, 17.4**

        For all sequences of unique-named HealthCheck registrations,
        looking up each registered name shall return the same HealthCheck
        instance that was registered.

        # Feature: error-handling-resilience, Property 30: HealthCheckRegistry register-lookup consistency
    """
    registry = HealthCheckRegistry()

    # Create and register a HealthCheck for each unique name
    checks = {}
    for name in names:
        hc = _make_health_check(name)
        registry.register(hc)
        checks[name] = hc

    # Verify that lookup returns the exact same instance for each name
    for name, expected_hc in checks.items():
        looked_up = registry.lookup(name)

        assert looked_up is not None, (
            "Expected lookup('{}') to return a HealthCheck, got None".format(name)
        )

        assert looked_up is expected_hc, (
            "Expected lookup('{}') to return the same instance (id={}), "
            "got a different instance (id={})".format(
                name, id(expected_hc), id(looked_up)
            )
        )

    return


# ---------------------------------------------------------------------------
# Property 31: HealthCheckRegistry count consistency
# ---------------------------------------------------------------------------

@given(
    names=_unique_names,
    constraints={"max_examples": 50},
)
def test_healthcheckregistry_count_consistency(names: list) -> None:
    """
        **Validates: Requirements 17.5, 17.6**

        For all sequences of N unique-named HealthCheck registrations
        (with no deregistrations), the count property shall equal N
        and list_all() shall return a list of length N.

        # Feature: error-handling-resilience, Property 31: HealthCheckRegistry count consistency
    """
    registry = HealthCheckRegistry()

    for name in names:
        hc = _make_health_check(name)
        registry.register(hc)

    expected_count = len(names)

    assert registry.count == expected_count, (
        "Expected count to be {}, got {}".format(expected_count, registry.count)
    )

    all_checks = registry.list_all()

    assert len(all_checks) == expected_count, (
        "Expected list_all() to return {} items, got {}".format(
            expected_count, len(all_checks)
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
