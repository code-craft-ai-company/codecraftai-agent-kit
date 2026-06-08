"""
    Unit tests for the ccai.agentkit.featureflagevaluator module.

    Tests the FeatureFlagEvaluator class covering evaluate with runtime
    override, configuration value, default fallback, SemanticError for
    unregistered flags, evaluate_with_context, and string representations.

    Uses testbase mocking for ConfigurationManager.

    Requirements: 13.1, 13.2, 13.3, 13.5
"""

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.featureflag import FeatureFlag
from ccai.agentkit.featureflagevaluator import FeatureFlagEvaluator
from ccai.agentkit.featureflagregistry import FeatureFlagRegistry
from ccai.testbase.mocking import Mock


# ---- Helper Functions ----


def create_mock_configuration_manager(config_values=None):
    """
        Creates a mock ConfigurationManager that returns values from
        the provided config_values dictionary when get is called.

        :param config_values: A dictionary mapping field paths to values.

        :returns: A Mock object configured as a ConfigurationManager.
    """
    if config_values is None:
        config_values = {}

    mock_manager = Mock()
    mock_manager.configure(recursive=True)

    def get_side_effect(field_path, default=None):
        if field_path in config_values:
            return config_values[field_path]
        return default

    mock_manager.mock_context().mock_method("get", side_effect=get_side_effect)
    return mock_manager


# ---- evaluate with runtime override Tests ----


def test_evaluate_returns_override_when_set():
    """
        Verify that evaluate returns the runtime override value when one is set.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="test-flag", default_value=False)
    registry.register(flag)
    registry.set_override("test-flag", True)

    evaluator = FeatureFlagEvaluator(registry=registry)
    result = evaluator.evaluate("test-flag")

    assert result is True, "evaluate should return the override value"
    return


def test_evaluate_override_takes_precedence_over_config():
    """
        Verify that runtime override takes precedence over configuration value.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="precedence-flag", default_value=False)
    registry.register(flag)
    registry.set_override("precedence-flag", True)

    mock_manager = create_mock_configuration_manager(
        config_values={"feature_flags.precedence-flag": False}
    )
    evaluator = FeatureFlagEvaluator(registry=registry, configuration_manager=mock_manager)
    result = evaluator.evaluate("precedence-flag")

    assert result is True, "override should take precedence over config"
    return


# ---- evaluate with configuration value Tests ----


def test_evaluate_returns_config_value_when_no_override():
    """
        Verify that evaluate returns the configuration value when no
        runtime override is set.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="config-flag", default_value=False)
    registry.register(flag)

    mock_manager = create_mock_configuration_manager(
        config_values={"feature_flags.config-flag": True}
    )
    evaluator = FeatureFlagEvaluator(registry=registry, configuration_manager=mock_manager)
    result = evaluator.evaluate("config-flag")

    assert result is True, "evaluate should return the config value when no override"
    return


def test_evaluate_config_takes_precedence_over_default():
    """
        Verify that configuration value takes precedence over default value.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="config-over-default", default_value=True)
    registry.register(flag)

    mock_manager = create_mock_configuration_manager(
        config_values={"feature_flags.config-over-default": False}
    )
    evaluator = FeatureFlagEvaluator(registry=registry, configuration_manager=mock_manager)
    result = evaluator.evaluate("config-over-default")

    assert result is False, "config should take precedence over default"
    return


# ---- evaluate with default fallback Tests ----


def test_evaluate_returns_default_when_no_override_or_config():
    """
        Verify that evaluate returns the default value when no override
        or configuration value is present.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="default-flag", default_value=True)
    registry.register(flag)

    evaluator = FeatureFlagEvaluator(registry=registry)
    result = evaluator.evaluate("default-flag")

    assert result is True, "evaluate should return the default value"
    return


def test_evaluate_returns_false_default():
    """
        Verify that evaluate returns False when the default value is False
        and no override or config is present.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="false-default", default_value=False)
    registry.register(flag)

    evaluator = FeatureFlagEvaluator(registry=registry)
    result = evaluator.evaluate("false-default")

    assert result is False, "evaluate should return the False default value"
    return


def test_evaluate_returns_default_when_config_manager_has_no_value():
    """
        Verify that evaluate returns the default value when the
        ConfigurationManager has no value for the flag path.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="no-config", default_value=True)
    registry.register(flag)

    mock_manager = create_mock_configuration_manager(config_values={})
    evaluator = FeatureFlagEvaluator(registry=registry, configuration_manager=mock_manager)
    result = evaluator.evaluate("no-config")

    assert result is True, "evaluate should return default when config has no value"
    return


# ---- SemanticError for unregistered flag Tests ----


def test_evaluate_raises_semantic_error_for_unregistered_flag():
    """
        Verify that evaluate raises SemanticError for an unregistered flag.
    """
    registry = FeatureFlagRegistry()
    evaluator = FeatureFlagEvaluator(registry=registry)

    caught_error = False
    try:
        evaluator.evaluate("nonexistent")
    except SemanticError:
        caught_error = True

    assert caught_error is True, "evaluate should raise SemanticError for unregistered flags"
    return


def test_evaluate_with_context_raises_semantic_error_for_unregistered_flag():
    """
        Verify that evaluate_with_context raises SemanticError for an
        unregistered flag.
    """
    registry = FeatureFlagRegistry()
    evaluator = FeatureFlagEvaluator(registry=registry)

    caught_error = False
    try:
        evaluator.evaluate_with_context("nonexistent", context={})
    except SemanticError:
        caught_error = True

    assert caught_error is True, \
        "evaluate_with_context should raise SemanticError for unregistered flags"
    return


# ---- evaluate_with_context Tests ----


def test_evaluate_with_context_delegates_to_evaluate():
    """
        Verify that evaluate_with_context delegates to evaluate and
        returns the same result.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="context-flag", default_value=True)
    registry.register(flag)

    evaluator = FeatureFlagEvaluator(registry=registry)
    result = evaluator.evaluate_with_context("context-flag", context={"env": "prod"})

    assert result is True, "evaluate_with_context should delegate to evaluate"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'FeatureFlagEvaluator'.
    """
    registry = FeatureFlagRegistry()
    evaluator = FeatureFlagEvaluator(registry=registry)

    repr_str = repr(evaluator)
    has_class_name = "FeatureFlagEvaluator" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_flag_count():
    """
        Verify that __repr__ contains the flag count.
    """
    registry = FeatureFlagRegistry()
    registry.register(FeatureFlag(name="a"))
    registry.register(FeatureFlag(name="b"))

    evaluator = FeatureFlagEvaluator(registry=registry)
    repr_str = repr(evaluator)
    has_count = "2" in repr_str
    assert has_count is True, "repr should contain the flag count"
    return


# ---- __str__ Tests ----


def test_str_contains_flag_count():
    """
        Verify that __str__ contains the flag count.
    """
    registry = FeatureFlagRegistry()
    registry.register(FeatureFlag(name="x"))

    evaluator = FeatureFlagEvaluator(registry=registry)
    str_val = str(evaluator)
    has_count = "1" in str_val
    assert has_count is True, "str should contain the flag count"
    return


def test_str_contains_configuration_manager_status():
    """
        Verify that __str__ contains whether a ConfigurationManager is configured.
    """
    registry = FeatureFlagRegistry()
    evaluator = FeatureFlagEvaluator(registry=registry, configuration_manager=None)

    str_val = str(evaluator)
    has_config_status = "configuration_manager" in str_val
    assert has_config_status is True, "str should contain configuration_manager status"
    return
