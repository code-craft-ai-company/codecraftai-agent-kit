"""
    Property-based tests for the automojo.agentkit.healthstatus module.

    Uses the automojo.testbase.properties engine to verify:
    - Property 28: HealthStatus JSON round-trip
    - Property 29: HealthStatus is_healthy consistency

    **Validates: Requirements 16.10, 16.5**
"""

from datetime import datetime

from automojo.testbase.properties import given, settings
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.healthstatus import HealthStatus


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_check_name = st.text(min_size=1, max_size=200)

_status = st.sampled_from(["healthy", "degraded", "unhealthy"])

_detail = st.one_of(st.none(), st.text(min_size=0, max_size=200))

_response_time = st.floats(min_value=0.0, max_value=1e6)


@composite
def _datetimes(draw, min_value=datetime(2000, 1, 1), max_value=datetime(2099, 12, 31)):
    min_ts = int(min_value.timestamp())
    max_ts = int(max_value.timestamp())
    ts = draw(st.integers(min_value=min_ts, max_value=max_ts))
    return datetime.fromtimestamp(ts)


_timestamp = _datetimes()


# ---------------------------------------------------------------------------
# Property 28: HealthStatus JSON round-trip
# ---------------------------------------------------------------------------

@given(
    check_name=_check_name,
    status=_status,
    detail=_detail,
    response_time=_response_time,
    timestamp=_timestamp,
    settings=settings(max_examples=50),
)
def test_healthstatus_json_roundtrip(
    check_name: str,
    status: str,
    detail: str,
    response_time: float,
    timestamp: datetime,
) -> None:
    """
        **Validates: Requirements 16.10**

        For all valid HealthStatus instances constructed with arbitrary
        check_name (non-empty string), status (one of "healthy", "degraded",
        "unhealthy"), detail (optional string), response_time (non-negative
        float), and timestamp (datetime), calling to_json() and then
        from_json() shall produce an equivalent HealthStatus object.
    """
    original = HealthStatus(
        check_name=check_name,
        status=status,
        detail=detail,
        response_time=response_time,
        timestamp=timestamp,
    )

    json_str = original.to_json()
    restored = HealthStatus.from_json(json_str)

    assert restored.check_name == original.check_name, (
        "check_name mismatch: expected {!r}, got {!r}".format(
            original.check_name, restored.check_name
        )
    )

    assert restored.status == original.status, (
        "status mismatch: expected {!r}, got {!r}".format(
            original.status, restored.status
        )
    )

    assert restored.detail == original.detail, (
        "detail mismatch: expected {!r}, got {!r}".format(
            original.detail, restored.detail
        )
    )

    assert restored.response_time == original.response_time, (
        "response_time mismatch: expected {!r}, got {!r}".format(
            original.response_time, restored.response_time
        )
    )

    assert restored.timestamp == original.timestamp, (
        "timestamp mismatch: expected {}, got {}".format(
            original.timestamp, restored.timestamp
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 29: HealthStatus is_healthy consistency
# ---------------------------------------------------------------------------

@given(
    check_name=_check_name,
    status=_status,
    detail=_detail,
    response_time=_response_time,
    timestamp=_timestamp,
    settings=settings(max_examples=50),
)
def test_healthstatus_is_healthy_consistency(
    check_name: str,
    status: str,
    detail: str,
    response_time: float,
    timestamp: datetime,
) -> None:
    """
        **Validates: Requirements 16.5**

        For all valid HealthStatus instances, the is_healthy property shall
        return True if and only if the status property equals "healthy".
    """
    hs = HealthStatus(
        check_name=check_name,
        status=status,
        detail=detail,
        response_time=response_time,
        timestamp=timestamp,
    )

    if status == "healthy":
        assert hs.is_healthy is True, (
            "is_healthy should be True when status is 'healthy', "
            "got is_healthy={!r} for status={!r}".format(hs.is_healthy, hs.status)
        )
    else:
        assert hs.is_healthy is False, (
            "is_healthy should be False when status is {!r}, "
            "got is_healthy={!r}".format(hs.status, hs.is_healthy)
        )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
