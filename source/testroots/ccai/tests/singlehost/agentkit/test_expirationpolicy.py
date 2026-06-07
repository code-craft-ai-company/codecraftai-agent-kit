"""
    .. module:: ccai.tests.singlehost.agentkit.test_expirationpolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the ExpirationPolicy configuration object.
"""

import json

from ccai.agentkit.expirationpolicy import ExpirationPolicy


# ---- Construction Tests ----


def test_expirationpolicy_construction_with_default_ttl():
    """
        Verify that ExpirationPolicy stores the provided default_ttl.
    """
    policy = ExpirationPolicy(default_ttl=3600.0)
    ttl = policy.default_ttl
    assert ttl == 3600.0, "default_ttl should be 3600.0"
    return


def test_expirationpolicy_construction_without_default_ttl():
    """
        Verify that default_ttl is None when not provided.
    """
    policy = ExpirationPolicy()
    ttl = policy.default_ttl
    assert ttl is None, "default_ttl should be None when not provided"
    return


def test_expirationpolicy_default_cleanup_interval():
    """
        Verify that cleanup_interval defaults to 300.0.
    """
    policy = ExpirationPolicy()
    interval = policy.cleanup_interval
    assert interval == 300.0, "cleanup_interval should default to 300.0"
    return


def test_expirationpolicy_custom_cleanup_interval():
    """
        Verify that a custom cleanup_interval is stored.
    """
    policy = ExpirationPolicy(cleanup_interval=60.0)
    interval = policy.cleanup_interval
    assert interval == 60.0, "cleanup_interval should be 60.0"
    return


# ---- Serialization Tests ----


def test_expirationpolicy_as_dict_contains_fields():
    """
        Verify that as_dict returns a dictionary with both fields.
    """
    policy = ExpirationPolicy(default_ttl=1800.0, cleanup_interval=120.0)
    d = policy.as_dict()
    assert d["default_ttl"] == 1800.0, "as_dict should contain default_ttl"
    assert d["cleanup_interval"] == 120.0, "as_dict should contain cleanup_interval"
    return


def test_expirationpolicy_as_dict_with_none_ttl():
    """
        Verify that as_dict includes None for default_ttl when not set.
    """
    policy = ExpirationPolicy()
    d = policy.as_dict()
    assert d["default_ttl"] is None, "as_dict should have None for default_ttl"
    return


def test_expirationpolicy_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    policy = ExpirationPolicy(default_ttl=600.0, cleanup_interval=60.0)
    json_str = policy.to_json()
    data = json.loads(json_str)
    assert data["default_ttl"] == 600.0, "to_json should produce valid JSON with correct default_ttl"
    assert data["cleanup_interval"] == 60.0, "to_json should produce valid JSON with correct cleanup_interval"
    return


def test_expirationpolicy_from_dict_reconstructs_policy():
    """
        Verify that from_dict constructs an equivalent ExpirationPolicy.
    """
    original = ExpirationPolicy(default_ttl=7200.0, cleanup_interval=150.0)
    d = original.as_dict()
    restored = ExpirationPolicy.from_dict(d)
    assert original == restored, "from_dict should reconstruct an equivalent ExpirationPolicy"
    return


def test_expirationpolicy_from_dict_uses_default_cleanup_interval():
    """
        Verify that from_dict uses 300.0 as default cleanup_interval when not in data.
    """
    d = {"default_ttl": 100.0}
    policy = ExpirationPolicy.from_dict(d)
    interval = policy.cleanup_interval
    assert interval == 300.0, "from_dict should default cleanup_interval to 300.0"
    return


def test_expirationpolicy_from_json_reconstructs_policy():
    """
        Verify that from_json constructs an equivalent ExpirationPolicy.
    """
    original = ExpirationPolicy(default_ttl=500.0, cleanup_interval=50.0)
    json_str = original.to_json()
    restored = ExpirationPolicy.from_json(json_str)
    assert original == restored, "from_json should reconstruct an equivalent ExpirationPolicy"
    return


def test_expirationpolicy_from_json_with_none_ttl():
    """
        Verify that from_json handles None default_ttl.
    """
    original = ExpirationPolicy(cleanup_interval=200.0)
    json_str = original.to_json()
    restored = ExpirationPolicy.from_json(json_str)
    ttl = restored.default_ttl
    assert ttl is None, "from_json should handle None default_ttl"
    return


# ---- __repr__, __str__, __eq__ Tests ----


def test_expirationpolicy_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    policy = ExpirationPolicy(default_ttl=100.0)
    repr_str = repr(policy)
    has_class_name = "ExpirationPolicy" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_expirationpolicy_repr_contains_ttl():
    """
        Verify that __repr__ contains the default_ttl value.
    """
    policy = ExpirationPolicy(default_ttl=3600.0)
    repr_str = repr(policy)
    has_ttl = "3600.0" in repr_str
    assert has_ttl is True, "repr should contain the default_ttl value"
    return


def test_expirationpolicy_repr_contains_cleanup_interval():
    """
        Verify that __repr__ contains the cleanup_interval value.
    """
    policy = ExpirationPolicy(cleanup_interval=120.0)
    repr_str = repr(policy)
    has_interval = "120.0" in repr_str
    assert has_interval is True, "repr should contain the cleanup_interval value"
    return


def test_expirationpolicy_str_contains_ttl_info():
    """
        Verify that __str__ contains TTL information.
    """
    policy = ExpirationPolicy(default_ttl=600.0)
    str_val = str(policy)
    has_ttl = "600.0" in str_val
    assert has_ttl is True, "__str__ should contain the TTL value"
    return


def test_expirationpolicy_str_shows_none_when_no_ttl():
    """
        Verify that __str__ shows 'none' when default_ttl is None.
    """
    policy = ExpirationPolicy()
    str_val = str(policy)
    has_none = "none" in str_val
    assert has_none is True, "__str__ should show 'none' when default_ttl is None"
    return


def test_expirationpolicy_str_contains_cleanup_interval():
    """
        Verify that __str__ contains the cleanup interval.
    """
    policy = ExpirationPolicy(cleanup_interval=45.0)
    str_val = str(policy)
    has_interval = "45.0" in str_val
    assert has_interval is True, "__str__ should contain the cleanup interval"
    return


def test_expirationpolicy_eq_returns_true_for_equivalent():
    """
        Verify that __eq__ returns True for equivalent policies.
    """
    policy_a = ExpirationPolicy(default_ttl=100.0, cleanup_interval=50.0)
    policy_b = ExpirationPolicy(default_ttl=100.0, cleanup_interval=50.0)
    assert policy_a == policy_b, "Equivalent policies should be equal"
    return


def test_expirationpolicy_eq_returns_false_for_different_ttl():
    """
        Verify that __eq__ returns False when default_ttl differs.
    """
    policy_a = ExpirationPolicy(default_ttl=100.0)
    policy_b = ExpirationPolicy(default_ttl=200.0)
    result = policy_a == policy_b
    assert result is False, "Policies with different TTL should not be equal"
    return


def test_expirationpolicy_eq_returns_false_for_different_interval():
    """
        Verify that __eq__ returns False when cleanup_interval differs.
    """
    policy_a = ExpirationPolicy(cleanup_interval=100.0)
    policy_b = ExpirationPolicy(cleanup_interval=200.0)
    result = policy_a == policy_b
    assert result is False, "Policies with different cleanup_interval should not be equal"
    return


def test_expirationpolicy_eq_returns_false_for_non_policy():
    """
        Verify that __eq__ returns False when compared to a non-ExpirationPolicy.
    """
    policy = ExpirationPolicy()
    result = policy == "not a policy"
    assert result is False, "__eq__ should return False for non-ExpirationPolicy objects"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
