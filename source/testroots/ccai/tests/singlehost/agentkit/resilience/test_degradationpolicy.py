"""
    Unit tests for the ccai.agentkit.degradationpolicy module.
"""

from ccai.agentkit.defaultvaluestrategy import DefaultValueStrategy
from ccai.agentkit.degradationlevel import DegradationLevel
from ccai.agentkit.degradationpolicy import DegradationPolicy


def test_policy_construction():
    """
        Verify that DegradationPolicy stores all fields correctly.
    """
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy(
        dependency_name="db",
        strategy=strategy,
        activation_level=DegradationLevel.DEGRADED,
        fallback_value="default"
    )
    assert policy.dependency_name == "db", "dependency_name should match"
    assert policy.strategy is strategy, "strategy should match"
    assert policy.activation_level is DegradationLevel.DEGRADED, "activation_level should match"
    assert policy.fallback_value == "default", "fallback_value should match"
    return


def test_policy_as_dict():
    """
        Verify that as_dict returns the expected dictionary.
    """
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    data = policy.as_dict()
    assert data["dependency_name"] == "db", "dependency_name should match"
    assert data["strategy_name"] == "default_value", "strategy_name should match"
    assert data["activation_level"] == "DEGRADED", "activation_level should match"
    return


def test_policy_repr():
    """
        Verify that __repr__ includes key fields.
    """
    strategy = DefaultValueStrategy("fallback")
    policy = DegradationPolicy("db", strategy, DegradationLevel.DEGRADED)
    repr_str = repr(policy)
    assert "DegradationPolicy" in repr_str, "repr should contain class name"
    assert "db" in repr_str, "repr should contain dependency name"
    return
