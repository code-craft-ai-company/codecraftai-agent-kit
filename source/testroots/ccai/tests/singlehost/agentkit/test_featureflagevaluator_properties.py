"""
    Property-based tests for the ccai.agentkit.featureflagevaluator module.

    Uses the ccai.testbase.properties engine to verify that the FeatureFlagEvaluator
    respects three-tier precedence: runtime override > configuration value
    > default value.

    **Validates: Requirement 12 AC 8, Requirement 13 AC 3**
"""

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.agentkit.configurationmanager import ConfigurationManager
from ccai.agentkit.featureflag import FeatureFlag
from ccai.agentkit.featureflagevaluator import FeatureFlagEvaluator
from ccai.agentkit.featureflagregistry import FeatureFlagRegistry


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_optional_bool = st.one_of(st.none(), st.booleans())


# ---------------------------------------------------------------------------
# Property 11: FeatureFlag Evaluation Precedence
# ---------------------------------------------------------------------------

@given(
    flag_name=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz"),
    default_value=st.booleans(),
    override_value=_optional_bool,
    config_value=_optional_bool,
    constraints={"max_examples": 50},
)
def test_featureflag_evaluation_precedence(flag_name, default_value, override_value, config_value):
    """
        **Validates: Requirement 12 AC 8, Requirement 13 AC 3**

        For any FeatureFlag with any combination of runtime override,
        configuration value, and default value, the evaluator returns:
        override when present, else config when present, else default.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name=flag_name, default_value=default_value)
    registry.register(flag)

    config_manager = ConfigurationManager(agent_identifier="test-agent")

    if config_value is not None:
        config_path = "feature_flags.{}".format(flag_name)
        config_manager.set(config_path, config_value)

    if override_value is not None:
        registry.set_override(flag_name, override_value)

    evaluator = FeatureFlagEvaluator(
        registry=registry,
        configuration_manager=config_manager
    )

    result = evaluator.evaluate(flag_name)

    if override_value is not None:
        expected = override_value
        tier = "override"
    elif config_value is not None:
        expected = config_value
        tier = "config"
    else:
        expected = default_value
        tier = "default"

    assert result == expected, (
        "Evaluation precedence failed at tier '{}': "
        "expected {!r}, got {!r} "
        "(override={!r}, config={!r}, default={!r})".format(
            tier, expected, result, override_value, config_value, default_value)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
