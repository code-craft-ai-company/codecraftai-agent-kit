"""
    Defines the FeatureFlagEvaluator class that evaluates FeatureFlag values
    for an Agent with three-tier precedence in the automojo-agent-kit framework.

    The evaluator checks: 1) runtime override, 2) configuration value at
    feature_flags.<flag_name>, 3) default value.
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.featureflagregistry import FeatureFlagRegistry


class FeatureFlagEvaluator:
    """
        Evaluates FeatureFlag values for an Agent with three-tier precedence:
        runtime override, configuration value, default value.

        Supports conditional evaluation based on context dictionaries.

        :param registry: The FeatureFlagRegistry to evaluate flags from.
        :param configuration_manager: An optional ConfigurationManager for
            configuration-driven flag values.
    """

    def __init__(self, registry: FeatureFlagRegistry,
                 configuration_manager=None) -> None:
        self._registry = registry
        self._configuration_manager = configuration_manager
        return

    def evaluate(self, flag_name: str) -> bool:
        """
            Evaluates a flag: runtime override > config at
            feature_flags.<flag_name> > default value.

            :param flag_name: The flag name to evaluate.

            :returns: True if the flag is enabled.

            :raises SemanticError: If the flag name is not registered.
        """
        flag = self._registry.lookup(flag_name)

        if flag is None:
            errmsg = "FeatureFlag '{}' is not registered".format(flag_name)
            raise SemanticError(errmsg)

        # 1. Check runtime override in registry
        if flag_name in self._registry._overrides:
            return self._registry._overrides[flag_name]

        # 2. Check config at feature_flags.<flag_name> via configuration_manager
        if self._configuration_manager is not None:
            config_path = "feature_flags.{}".format(flag_name)
            config_value = self._configuration_manager.get(config_path)

            if config_value is not None:
                if isinstance(config_value, bool) is True:
                    return config_value

                if isinstance(config_value, str) is True:
                    lower_value = config_value.lower()
                    if lower_value == "true":
                        return True
                    elif lower_value == "false":
                        return False

        # 3. Fall back to default value
        return flag.default_value

    def evaluate_with_context(self, flag_name: str, context: dict) -> bool:
        """
            Evaluates a flag with conditional rules based on context.
            For now, delegates to evaluate (context support is extensible).

            :param flag_name: The flag name to evaluate.
            :param context: Context dictionary for conditional evaluation.

            :returns: True if the flag is enabled.

            :raises SemanticError: If the flag name is not registered.
        """
        result = self.evaluate(flag_name)
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation including class name
            and the count of registered flags.

            :returns: A repr string for debugging.
        """
        flag_count = self._registry.count
        repr_str = "FeatureFlagEvaluator(flag_count={})".format(flag_count)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary including the count of registered
            flags and whether a ConfigurationManager is configured.

            :returns: A human-readable string.
        """
        flag_count = self._registry.count
        has_config = self._configuration_manager is not None
        str_val = "FeatureFlagEvaluator({} flags, configuration_manager={})".format(
            flag_count, has_config
        )
        return str_val
