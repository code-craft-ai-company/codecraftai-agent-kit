"""
    Property-based tests for the automojo.agentkit.configurationmanager module.

    Uses the automojo.testbase.properties engine to verify that the ConfigurationManager merges
    configuration layers in ascending priority order, where higher-priority
    layers override lower-priority values at any key.

    **Validates: Requirement 1 AC 3**
"""

from automojo.testbase.properties import given, settings, assume
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.configurationlayer import ConfigurationLayer
from automojo.agentkit.configurationlayersource import ConfigurationLayerSource
from automojo.agentkit.configurationmanager import ConfigurationManager


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_json_primitive_values = st.one_of(
    st.text(min_size=1, max_size=20),
    st.integers(),
    st.booleans(),
    st.floats(),
)

_source_strategy = st.sampled_from([
    ConfigurationLayerSource.DEFAULTS,
    ConfigurationLayerSource.FILE,
    ConfigurationLayerSource.ENVIRONMENT,
    ConfigurationLayerSource.RUNTIME,
    ConfigurationLayerSource.OVERRIDE,
])

_flat_config_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    values=_json_primitive_values,
    min_size=1,
    max_size=5,
)


@composite
def _layer_list_strategy(draw):
    """
        Generates a list of ConfigurationLayer instances with distinct priorities
        and at least one shared key across layers so that merge behavior can be
        verified.

        Each layer has a unique priority drawn from a shuffled range. At least
        two layers are generated, and all layers contain a common key so that
        the highest-priority layer's value for that key can be checked.
    """
    num_layers = draw(st.integers(min_value=2, max_value=5))

    priority_set = draw(
        st.sets(
            st.integers(min_value=0, max_value=10000),
            min_size=num_layers,
            max_size=num_layers,
        )
    )
    priorities = list(priority_set)

    common_key = draw(st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"))

    layers = []
    for idx in range(num_layers):
        extra_config = draw(_flat_config_strategy)
        common_value = draw(_json_primitive_values)
        config = dict(extra_config)
        config[common_key] = common_value

        source = draw(_source_strategy)
        layer_name = "layer-{}".format(idx)

        layer = ConfigurationLayer(
            name=layer_name,
            priority=priorities[idx],
            source=source,
            configuration=config,
        )
        layers.append(layer)

    return (layers, common_key)


# ---------------------------------------------------------------------------
# Property 10: Configuration Hierarchy Merge Priority
# ---------------------------------------------------------------------------

@given(
    data=_layer_list_strategy(),
    settings=settings(max_examples=50),
)
def test_configuration_hierarchy_merge_priority(data):
    """
        **Validates: Requirement 1 AC 3**

        FOR ANY set of ConfigurationLayer instances with distinct priorities,
        the merged configuration value at any key SHALL equal the value from
        the highest-priority layer that defines that key. Lower-priority
        layers SHALL NOT override higher-priority values.
    """
    layers, common_key = data

    manager = ConfigurationManager(agent_identifier="test-agent")

    for layer in layers:
        manager._layers.append(layer)

    manager._merge_layers()

    merged = manager.merged_configuration

    # Collect all keys defined across all layers.
    all_keys = set()
    for layer in layers:
        layer_config = layer.configuration
        for key in layer_config:
            all_keys.add(key)

    # For each key, find the highest-priority layer that defines it and
    # verify the merged value matches.
    for key in all_keys:
        highest_priority = -1
        expected_value = None

        for layer in layers:
            layer_config = layer.configuration
            if key in layer_config:
                layer_priority = layer.priority
                if layer_priority > highest_priority:
                    highest_priority = layer_priority
                    expected_value = layer_config[key]

        merged_value = merged.get(key)
        assert merged_value == expected_value, (
            "Merge priority violation for key {!r}: expected value {!r} from "
            "layer with priority {}, got {!r}".format(
                key, expected_value, highest_priority, merged_value
            )
        )

    # Specifically verify the common key that all layers define.
    highest_priority_for_common = -1
    expected_common_value = None

    for layer in layers:
        layer_config = layer.configuration
        layer_priority = layer.priority
        if layer_priority > highest_priority_for_common:
            highest_priority_for_common = layer_priority
            expected_common_value = layer_config[common_key]

    merged_common_value = merged.get(common_key)
    assert merged_common_value == expected_common_value, (
        "Merge priority violation for common key {!r}: expected value {!r} "
        "from layer with priority {}, got {!r}".format(
            common_key, expected_common_value, highest_priority_for_common,
            merged_common_value
        )
    )

    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
