"""
    Property-based tests for the automojo.agentkit.healthmonitor module.

    Uses the hypothesis library to verify:
    - Property 32: HealthMonitor overall status computation

    **Validates: Requirements 18.6**
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from automojo.agentkit.healthcheck import HealthCheck
from automojo.agentkit.healthcheckregistry import HealthCheckRegistry
from automojo.agentkit.healthmonitor import HealthMonitor
from automojo.agentkit.healthstatus import HealthStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class StubHealthCheck(HealthCheck):
    """
        A concrete HealthCheck that returns a fixed status string.
    """

    def __init__(self, name: str, status_str: str) -> None:
        super().__init__(name)
        self._status_str = status_str
        return

    def check(self) -> HealthStatus:
        return HealthStatus(
            check_name=self._name,
            status=self._status_str,
        )


def _compute_expected_overall(statuses: list) -> str:
    """
        Computes the expected overall status from a list of status strings.

        :param statuses: List of status strings.

        :returns: The expected overall status string.
    """
    if any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    if any(s == "degraded" for s in statuses):
        return "degraded"
    return "healthy"


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_status_values = st.sampled_from(["healthy", "degraded", "unhealthy"])

_status_lists = st.lists(
    _status_values,
    min_size=1,
    max_size=15,
)


# ---------------------------------------------------------------------------
# Property 32: HealthMonitor overall status computation
# ---------------------------------------------------------------------------

@given(statuses=_status_lists)
@settings(max_examples=200)
def test_healthmonitor_overall_status_computation(statuses: list) -> None:
    """
        **Validates: Requirements 18.6**

        For all HealthMonitor instances, the overall_status property shall be
        "healthy" when all checks are healthy, "degraded" when any check is
        degraded but none are unhealthy, and "unhealthy" when any check is
        unhealthy.

        # Feature: error-handling-resilience, Property 32: HealthMonitor overall status computation
    """
    registry = HealthCheckRegistry()

    for index, status_str in enumerate(statuses):
        check_name = "check-{}".format(index)
        stub = StubHealthCheck(check_name, status_str)
        registry.register(stub)

    monitor = HealthMonitor(registry)
    monitor.check_now()

    expected = _compute_expected_overall(statuses)
    actual = monitor.overall_status

    assert actual == expected, (
        "Expected overall_status '{}' but got '{}'. "
        "Individual statuses: {}".format(expected, actual, statuses)
    )

    return
