"""
    Unit tests for the automojo.agentkit.featureflagregistry module.

    Tests the FeatureFlagRegistry including register/deregister, duplicate
    detection, lookup, is_enabled with override precedence, set_override,
    clear_override, clear_all_overrides, count, and string representations.
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.featureflag import FeatureFlag
from automojo.agentkit.featureflagregistry import FeatureFlagRegistry


# ---- Register Tests ----


def test_register_stores_flag():
    """
        Verify that register stores a FeatureFlag in the registry.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="test-flag", default_value=True)
    registry.register(flag)

    result = registry.lookup("test-flag")
    assert result is not None, "register should store the flag"
    assert result.name == "test-flag", "registered flag name should match"
    return


def test_register_raises_semantic_error_for_duplicate():
    """
        Verify that registering a duplicate flag name raises SemanticError.
    """
    registry = FeatureFlagRegistry()
    flag1 = FeatureFlag(name="dup-flag", default_value=True)
    flag2 = FeatureFlag(name="dup-flag", default_value=False)
    registry.register(flag1)

    caught_error = False
    try:
        registry.register(flag2)
    except SemanticError:
        caught_error = True

    assert caught_error is True, "registering a duplicate should raise SemanticError"
    return


# ---- Deregister Tests ----


def test_deregister_removes_flag():
    """
        Verify that deregister removes a flag from the registry.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="remove-me", default_value=False)
    registry.register(flag)
    registry.deregister("remove-me")

    result = registry.lookup("remove-me")
    assert result is None, "deregister should remove the flag"
    return


def test_deregister_also_removes_override():
    """
        Verify that deregister also removes any override for the flag.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="override-flag", default_value=False)
    registry.register(flag)
    registry.set_override("override-flag", True)
    registry.deregister("override-flag")

    has_flag = registry.has_flag("override-flag")
    assert has_flag is False, "deregister should remove the flag and its override"
    return


# ---- Lookup Tests ----


def test_lookup_returns_flag_when_found():
    """
        Verify that lookup returns the FeatureFlag when it exists.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="found-flag", default_value=True)
    registry.register(flag)

    result = registry.lookup("found-flag")
    assert result is not None, "lookup should return the flag"
    assert result.name == "found-flag", "lookup should return the correct flag"
    return


def test_lookup_returns_none_when_not_found():
    """
        Verify that lookup returns None when the flag is not registered.
    """
    registry = FeatureFlagRegistry()
    result = registry.lookup("nonexistent")
    assert result is None, "lookup should return None for unregistered flags"
    return


# ---- list_all Tests ----


def test_list_all_returns_all_flags():
    """
        Verify that list_all returns all registered flags.
    """
    registry = FeatureFlagRegistry()
    flag1 = FeatureFlag(name="flag-a", default_value=True)
    flag2 = FeatureFlag(name="flag-b", default_value=False)
    registry.register(flag1)
    registry.register(flag2)

    all_flags = registry.list_all()
    flag_names = [f.name for f in all_flags]
    assert len(all_flags) == 2, "list_all should return all registered flags"
    assert "flag-a" in flag_names, "list_all should include flag-a"
    assert "flag-b" in flag_names, "list_all should include flag-b"
    return


# ---- has_flag Tests ----


def test_has_flag_returns_true_when_registered():
    """
        Verify that has_flag returns True for a registered flag.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="exists", default_value=False)
    registry.register(flag)

    result = registry.has_flag("exists")
    assert result is True, "has_flag should return True for registered flags"
    return


def test_has_flag_returns_false_when_not_registered():
    """
        Verify that has_flag returns False for an unregistered flag.
    """
    registry = FeatureFlagRegistry()
    result = registry.has_flag("missing")
    assert result is False, "has_flag should return False for unregistered flags"
    return


# ---- count Tests ----


def test_count_returns_zero_for_empty_registry():
    """
        Verify that count returns 0 for an empty registry.
    """
    registry = FeatureFlagRegistry()
    result = registry.count
    assert result == 0, "count should be 0 for an empty registry"
    return


def test_count_returns_correct_number():
    """
        Verify that count returns the correct number of registered flags.
    """
    registry = FeatureFlagRegistry()
    registry.register(FeatureFlag(name="a"))
    registry.register(FeatureFlag(name="b"))
    registry.register(FeatureFlag(name="c"))

    result = registry.count
    assert result == 3, "count should return the number of registered flags"
    return


# ---- is_enabled Tests ----


def test_is_enabled_returns_default_value_when_no_override():
    """
        Verify that is_enabled returns the default value when no override is set.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="default-flag", default_value=True)
    registry.register(flag)

    result = registry.is_enabled("default-flag")
    assert result is True, "is_enabled should return the default value"
    return


def test_is_enabled_returns_override_when_set():
    """
        Verify that is_enabled returns the override value when one is set.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="overridden", default_value=False)
    registry.register(flag)
    registry.set_override("overridden", True)

    result = registry.is_enabled("overridden")
    assert result is True, "is_enabled should return the override value"
    return


def test_is_enabled_override_takes_precedence_over_default():
    """
        Verify that override takes precedence over default value.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="precedence", default_value=True)
    registry.register(flag)
    registry.set_override("precedence", False)

    result = registry.is_enabled("precedence")
    assert result is False, "override should take precedence over default"
    return


def test_is_enabled_returns_false_for_unregistered_flag():
    """
        Verify that is_enabled returns False for an unregistered flag.
    """
    registry = FeatureFlagRegistry()
    result = registry.is_enabled("unknown")
    assert result is False, "is_enabled should return False for unregistered flags"
    return


# ---- set_override / clear_override / clear_all_overrides Tests ----


def test_set_override_stores_value():
    """
        Verify that set_override stores the override value.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="set-test", default_value=False)
    registry.register(flag)
    registry.set_override("set-test", True)

    result = registry.is_enabled("set-test")
    assert result is True, "set_override should store the override value"
    return


def test_clear_override_removes_override():
    """
        Verify that clear_override removes the override and reverts to default.
    """
    registry = FeatureFlagRegistry()
    flag = FeatureFlag(name="clear-test", default_value=False)
    registry.register(flag)
    registry.set_override("clear-test", True)
    registry.clear_override("clear-test")

    result = registry.is_enabled("clear-test")
    assert result is False, "clear_override should revert to default value"
    return


def test_clear_all_overrides_removes_all():
    """
        Verify that clear_all_overrides removes all overrides.
    """
    registry = FeatureFlagRegistry()
    flag1 = FeatureFlag(name="flag-x", default_value=False)
    flag2 = FeatureFlag(name="flag-y", default_value=False)
    registry.register(flag1)
    registry.register(flag2)
    registry.set_override("flag-x", True)
    registry.set_override("flag-y", True)
    registry.clear_all_overrides()

    result_x = registry.is_enabled("flag-x")
    result_y = registry.is_enabled("flag-y")
    assert result_x is False, "clear_all_overrides should revert flag-x to default"
    assert result_y is False, "clear_all_overrides should revert flag-y to default"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'FeatureFlagRegistry'.
    """
    registry = FeatureFlagRegistry()
    repr_str = repr(registry)
    has_class_name = "FeatureFlagRegistry" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_count():
    """
        Verify that __repr__ contains the flag count.
    """
    registry = FeatureFlagRegistry()
    registry.register(FeatureFlag(name="a"))
    registry.register(FeatureFlag(name="b"))

    repr_str = repr(registry)
    has_count = "2" in repr_str
    assert has_count is True, "repr should contain the flag count"
    return


# ---- __str__ Tests ----


def test_str_contains_flag_names():
    """
        Verify that __str__ contains the registered flag names.
    """
    registry = FeatureFlagRegistry()
    registry.register(FeatureFlag(name="alpha", default_value=True))
    registry.register(FeatureFlag(name="beta", default_value=False))

    str_val = str(registry)
    has_alpha = "alpha" in str_val
    has_beta = "beta" in str_val
    assert has_alpha is True, "str should contain flag name 'alpha'"
    assert has_beta is True, "str should contain flag name 'beta'"
    return


def test_str_contains_enabled_status():
    """
        Verify that __str__ contains the enabled status of flags.
    """
    registry = FeatureFlagRegistry()
    registry.register(FeatureFlag(name="on-flag", default_value=True))

    str_val = str(registry)
    has_true = "True" in str_val
    assert has_true is True, "str should contain the enabled status"
    return
