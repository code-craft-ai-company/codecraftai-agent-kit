"""
    Property-based tests for the automojo.agentkit.configurationlayer module.

    Uses the automojo.testbase.properties engine to verify that ConfigurationLayer instances
    survive a JSON round-trip (to_json followed by from_json) with all fields
    preserved.

    **Validates: Requirement 2 AC 8**
"""

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.configurationlayer import ConfigurationLayer
from automojo.agentkit.configurationlayersource import ConfigurationLayerSource


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_json_primitive_values = st.one_of(
    st.text(),
    st.integers(),
    st.booleans(),
    st.floats(),
    st.none(),
)

_configuration_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20),
    values=_json_primitive_values,
)

_source_strategy = st.sampled_from([
    ConfigurationLayerSource.DEFAULTS,
    ConfigurationLayerSource.FILE,
    ConfigurationLayerSource.ENVIRONMENT,
    ConfigurationLayerSource.RUNTIME,
    ConfigurationLayerSource.OVERRIDE,
])


# ---------------------------------------------------------------------------
# Property 1: ConfigurationLayer JSON Round-Trip
# ---------------------------------------------------------------------------

@given(
    name=st.text(min_size=0, max_size=50),
    priority=st.integers(),
    source=_source_strategy,
    configuration=_configuration_strategy,
    constraints={"max_examples": 50},
)
def test_configurationlayer_json_round_trip(name, priority, source, configuration):
    """
        **Validates: Requirement 2 AC 8**

        FOR ALL valid ConfigurationLayer instances, calling to_json and then
        from_json SHALL produce an equivalent ConfigurationLayer object with
        the same name, priority, source, and configuration dictionary.
    """
    original = ConfigurationLayer(
        name=name,
        priority=priority,
        source=source,
        configuration=configuration,
    )

    json_str = original.to_json()
    reconstructed = ConfigurationLayer.from_json(json_str)

    reconstructed_name = reconstructed.name
    assert reconstructed_name == name, (
        "Round-trip name mismatch: expected {!r}, got {!r}".format(name, reconstructed_name)
    )

    reconstructed_priority = reconstructed.priority
    assert reconstructed_priority == priority, (
        "Round-trip priority mismatch: expected {!r}, got {!r}".format(priority, reconstructed_priority)
    )

    reconstructed_source = reconstructed.source
    assert reconstructed_source == source, (
        "Round-trip source mismatch: expected {!r}, got {!r}".format(source, reconstructed_source)
    )

    reconstructed_configuration = reconstructed.configuration
    assert reconstructed_configuration == configuration, (
        "Round-trip configuration mismatch: expected {!r}, got {!r}".format(
            configuration, reconstructed_configuration
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
