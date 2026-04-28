"""
    Property-based tests for the automojo.agentkit.hotreloadpolicy module.

    Uses the automojo.testbase.properties engine to verify that HotReloadPolicy instances
    survive a JSON round-trip (to_json followed by from_json) with all fields
    preserved.

    **Validates: Requirement 10 AC 7**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.hotreloadpolicy import HotReloadPolicy


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_polling_interval_strategy = st.floats(
    min_value=0.1,
    max_value=3600.0,
)

_monitored_files_strategy = st.lists(
    st.text(min_size=0, max_size=50),
    max_size=10,
)


# ---------------------------------------------------------------------------
# Property 5: HotReloadPolicy JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    polling_interval=_polling_interval_strategy,
    monitored_files=_monitored_files_strategy,
    environment_monitoring_enabled=st.booleans(),
    automatic_reload_enabled=st.booleans(),
    constraints={"max_examples": 50},
)
def test_hotreloadpolicy_json_round_trip(polling_interval, monitored_files,
                                         environment_monitoring_enabled,
                                         automatic_reload_enabled):
    """
        **Validates: Requirement 10 AC 7**

        FOR ALL valid HotReloadPolicy instances, calling to_json and then
        from_json SHALL produce an equivalent HotReloadPolicy object with
        the same polling_interval, monitored_files,
        environment_monitoring_enabled, and automatic_reload_enabled.
    """
    original = HotReloadPolicy(
        polling_interval=polling_interval,
        monitored_files=monitored_files,
        environment_monitoring_enabled=environment_monitoring_enabled,
        automatic_reload_enabled=automatic_reload_enabled,
    )

    json_str = original.to_json()
    reconstructed = HotReloadPolicy.from_json(json_str)

    reconstructed_polling_interval = reconstructed.polling_interval
    assert reconstructed_polling_interval == polling_interval, (
        "Round-trip polling_interval mismatch: expected {!r}, got {!r}".format(
            polling_interval, reconstructed_polling_interval
        )
    )

    reconstructed_monitored_files = reconstructed.monitored_files
    assert reconstructed_monitored_files == monitored_files, (
        "Round-trip monitored_files mismatch: expected {!r}, got {!r}".format(
            monitored_files, reconstructed_monitored_files
        )
    )

    reconstructed_env_monitoring = reconstructed.environment_monitoring_enabled
    assert reconstructed_env_monitoring == environment_monitoring_enabled, (
        "Round-trip environment_monitoring_enabled mismatch: expected {!r}, got {!r}".format(
            environment_monitoring_enabled, reconstructed_env_monitoring
        )
    )

    reconstructed_auto_reload = reconstructed.automatic_reload_enabled
    assert reconstructed_auto_reload == automatic_reload_enabled, (
        "Round-trip automatic_reload_enabled mismatch: expected {!r}, got {!r}".format(
            automatic_reload_enabled, reconstructed_auto_reload
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
