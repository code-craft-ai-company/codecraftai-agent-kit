"""
    Property-based tests for the ccai.agentkit.pluginconfiguration module.

    Uses the ccai.testbase.properties engine to verify that PluginConfiguration instances
    survive a JSON round-trip (to_json followed by from_json) with all
    fields preserved.

    **Validates: Requirement 19 AC 11**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.pluginconfiguration import PluginConfiguration


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_plugin_names_strategy = st.lists(
    st.text(min_size=1, max_size=30),
    min_size=0,
    max_size=5,
)

_search_paths_strategy = st.lists(
    st.text(min_size=1, max_size=50),
    min_size=0,
    max_size=5,
)


# ---------------------------------------------------------------------------
# Property 9: PluginConfiguration JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    enabled_plugins=_plugin_names_strategy,
    disabled_plugins=_plugin_names_strategy,
    search_paths=_search_paths_strategy,
    automatic_discovery_enabled=st.booleans(),
    constraints={"max_examples": 50},
)
def test_pluginconfiguration_json_round_trip(enabled_plugins, disabled_plugins,
                                              search_paths, automatic_discovery_enabled):
    """
        **Validates: Requirement 19 AC 11**

        FOR ALL valid PluginConfiguration instances, calling to_json and then
        from_json SHALL produce an equivalent PluginConfiguration object with
        the same enabled_plugins, disabled_plugins, search_paths, and
        automatic_discovery_enabled.
    """
    original = PluginConfiguration(
        enabled_plugins=enabled_plugins,
        disabled_plugins=disabled_plugins,
        search_paths=search_paths,
        automatic_discovery_enabled=automatic_discovery_enabled,
    )

    json_str = original.to_json()
    reconstructed = PluginConfiguration.from_json(json_str)

    reconstructed_enabled = reconstructed.enabled_plugins
    assert reconstructed_enabled == enabled_plugins, (
        "Round-trip enabled_plugins mismatch: expected {!r}, got {!r}".format(
            enabled_plugins, reconstructed_enabled)
    )

    reconstructed_disabled = reconstructed.disabled_plugins
    assert reconstructed_disabled == disabled_plugins, (
        "Round-trip disabled_plugins mismatch: expected {!r}, got {!r}".format(
            disabled_plugins, reconstructed_disabled)
    )

    reconstructed_paths = reconstructed.search_paths
    assert reconstructed_paths == search_paths, (
        "Round-trip search_paths mismatch: expected {!r}, got {!r}".format(
            search_paths, reconstructed_paths)
    )

    reconstructed_auto = reconstructed.automatic_discovery_enabled
    assert reconstructed_auto == automatic_discovery_enabled, (
        "Round-trip automatic_discovery_enabled mismatch: expected {!r}, got {!r}".format(
            automatic_discovery_enabled, reconstructed_auto)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
