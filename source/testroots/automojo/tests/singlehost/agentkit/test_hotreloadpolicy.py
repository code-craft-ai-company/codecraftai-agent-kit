"""
    Unit tests for the automojo.agentkit.hotreloadpolicy module.

    Tests the HotReloadPolicy immutable data type including constructor defaults,
    constructor with custom values, read-only properties, serialization,
    deserialization, and string representations.
"""

import json

from automojo.agentkit.hotreloadpolicy import HotReloadPolicy


# ---- Constructor Default Tests ----


def test_constructor_default_polling_interval():
    """
        Verify that the constructor defaults polling_interval to 5.0.
    """
    policy = HotReloadPolicy()
    stored_interval = policy.polling_interval
    assert stored_interval == 5.0, "constructor should default polling_interval to 5.0"
    return


def test_constructor_default_monitored_files():
    """
        Verify that the constructor defaults monitored_files to an empty list.
    """
    policy = HotReloadPolicy()
    stored_files = policy.monitored_files
    assert stored_files == [], "constructor should default monitored_files to an empty list"
    return


def test_constructor_default_environment_monitoring_enabled():
    """
        Verify that the constructor defaults environment_monitoring_enabled to False.
    """
    policy = HotReloadPolicy()
    stored_flag = policy.environment_monitoring_enabled
    assert stored_flag is False, "constructor should default environment_monitoring_enabled to False"
    return


def test_constructor_default_automatic_reload_enabled():
    """
        Verify that the constructor defaults automatic_reload_enabled to True.
    """
    policy = HotReloadPolicy()
    stored_flag = policy.automatic_reload_enabled
    assert stored_flag is True, "constructor should default automatic_reload_enabled to True"
    return


# ---- Constructor Custom Values Tests ----


def test_constructor_stores_custom_polling_interval():
    """
        Verify that the constructor stores a custom polling_interval value.
    """
    policy = HotReloadPolicy(polling_interval=10.0)
    stored_interval = policy.polling_interval
    assert stored_interval == 10.0, "constructor should store the custom polling_interval"
    return


def test_constructor_stores_custom_monitored_files():
    """
        Verify that the constructor stores a custom monitored_files list.
    """
    files = ["/etc/config.json", "/opt/settings.yaml"]
    policy = HotReloadPolicy(monitored_files=files)
    stored_files = policy.monitored_files
    assert stored_files == ["/etc/config.json", "/opt/settings.yaml"], \
        "constructor should store the custom monitored_files list"
    return


def test_constructor_stores_custom_environment_monitoring_enabled():
    """
        Verify that the constructor stores a custom environment_monitoring_enabled value.
    """
    policy = HotReloadPolicy(environment_monitoring_enabled=True)
    stored_flag = policy.environment_monitoring_enabled
    assert stored_flag is True, "constructor should store the custom environment_monitoring_enabled"
    return


def test_constructor_stores_custom_automatic_reload_enabled():
    """
        Verify that the constructor stores a custom automatic_reload_enabled value.
    """
    policy = HotReloadPolicy(automatic_reload_enabled=False)
    stored_flag = policy.automatic_reload_enabled
    assert stored_flag is False, "constructor should store the custom automatic_reload_enabled"
    return


# ---- Read-Only Property Tests ----


def test_polling_interval_property_returns_expected_value():
    """
        Verify that the polling_interval property returns the expected value.
    """
    policy = HotReloadPolicy(polling_interval=2.5)
    interval_value = policy.polling_interval
    assert interval_value == 2.5, "polling_interval property should return the expected value"
    return


def test_monitored_files_property_returns_copy():
    """
        Verify that the monitored_files property returns a defensive copy,
        so modifications to the returned list do not affect the policy.
    """
    original_files = ["/path/to/config.json"]
    policy = HotReloadPolicy(monitored_files=original_files)

    first_copy = policy.monitored_files
    first_copy.append("/injected/file.yaml")

    second_copy = policy.monitored_files
    file_count = len(second_copy)
    assert file_count == 1, "monitored_files should return a defensive copy, injected file not present"
    return


def test_environment_monitoring_enabled_property_returns_expected_value():
    """
        Verify that the environment_monitoring_enabled property returns the expected value.
    """
    policy = HotReloadPolicy(environment_monitoring_enabled=True)
    flag_value = policy.environment_monitoring_enabled
    assert flag_value is True, "environment_monitoring_enabled property should return the expected value"
    return


def test_automatic_reload_enabled_property_returns_expected_value():
    """
        Verify that the automatic_reload_enabled property returns the expected value.
    """
    policy = HotReloadPolicy(automatic_reload_enabled=False)
    flag_value = policy.automatic_reload_enabled
    assert flag_value is False, "automatic_reload_enabled property should return the expected value"
    return


# ---- as_dict Tests ----


def test_as_dict_returns_correct_dictionary():
    """
        Verify that as_dict returns a dictionary with all fields.
    """
    policy = HotReloadPolicy(
        polling_interval=3.0,
        monitored_files=["/etc/app.json"],
        environment_monitoring_enabled=True,
        automatic_reload_enabled=False
    )
    result = policy.as_dict()

    result_interval = result["polling_interval"]
    result_files = result["monitored_files"]
    result_env_flag = result["environment_monitoring_enabled"]
    result_auto_flag = result["automatic_reload_enabled"]

    assert result_interval == 3.0, "as_dict polling_interval should match"
    assert result_files == ["/etc/app.json"], "as_dict monitored_files should match"
    assert result_env_flag is True, "as_dict environment_monitoring_enabled should match"
    assert result_auto_flag is False, "as_dict automatic_reload_enabled should match"
    return


def test_as_dict_contains_all_expected_keys():
    """
        Verify that as_dict contains all four expected keys.
    """
    policy = HotReloadPolicy()
    result = policy.as_dict()

    has_polling = "polling_interval" in result
    has_files = "monitored_files" in result
    has_env = "environment_monitoring_enabled" in result
    has_auto = "automatic_reload_enabled" in result

    assert has_polling is True, "as_dict should contain polling_interval key"
    assert has_files is True, "as_dict should contain monitored_files key"
    assert has_env is True, "as_dict should contain environment_monitoring_enabled key"
    assert has_auto is True, "as_dict should contain automatic_reload_enabled key"
    return


# ---- to_json Tests ----


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string that can be parsed.
    """
    policy = HotReloadPolicy(
        polling_interval=7.5,
        monitored_files=["/tmp/config.json"],
        environment_monitoring_enabled=False,
        automatic_reload_enabled=True
    )
    json_str = policy.to_json()
    parsed = json.loads(json_str)

    parsed_interval = parsed["polling_interval"]
    parsed_files = parsed["monitored_files"]
    parsed_env_flag = parsed["environment_monitoring_enabled"]
    parsed_auto_flag = parsed["automatic_reload_enabled"]

    assert parsed_interval == 7.5, "to_json polling_interval should match after parsing"
    assert parsed_files == ["/tmp/config.json"], "to_json monitored_files should match after parsing"
    assert parsed_env_flag is False, "to_json environment_monitoring_enabled should match after parsing"
    assert parsed_auto_flag is True, "to_json automatic_reload_enabled should match after parsing"
    return


# ---- from_dict Tests ----


def test_from_dict_reconstructs_equivalent_object():
    """
        Verify that from_dict reconstructs a HotReloadPolicy with equivalent fields.
    """
    data = {
        "polling_interval": 15.0,
        "monitored_files": ["/opt/settings.yaml", "/etc/app.json"],
        "environment_monitoring_enabled": True,
        "automatic_reload_enabled": False
    }
    policy = HotReloadPolicy.from_dict(data)

    policy_interval = policy.polling_interval
    policy_files = policy.monitored_files
    policy_env_flag = policy.environment_monitoring_enabled
    policy_auto_flag = policy.automatic_reload_enabled

    assert policy_interval == 15.0, "from_dict should reconstruct the polling_interval"
    assert policy_files == ["/opt/settings.yaml", "/etc/app.json"], \
        "from_dict should reconstruct the monitored_files"
    assert policy_env_flag is True, "from_dict should reconstruct the environment_monitoring_enabled"
    assert policy_auto_flag is False, "from_dict should reconstruct the automatic_reload_enabled"
    return


def test_from_dict_uses_defaults_for_missing_keys():
    """
        Verify that from_dict uses default values when keys are missing.
    """
    data = {}
    policy = HotReloadPolicy.from_dict(data)

    policy_interval = policy.polling_interval
    policy_files = policy.monitored_files
    policy_env_flag = policy.environment_monitoring_enabled
    policy_auto_flag = policy.automatic_reload_enabled

    assert policy_interval == 5.0, "from_dict should default polling_interval to 5.0"
    assert policy_files == [], "from_dict should default monitored_files to empty list"
    assert policy_env_flag is False, "from_dict should default environment_monitoring_enabled to False"
    assert policy_auto_flag is True, "from_dict should default automatic_reload_enabled to True"
    return


# ---- from_json Tests ----


def test_from_json_reconstructs_equivalent_object():
    """
        Verify that from_json reconstructs a HotReloadPolicy with equivalent fields.
    """
    json_str = json.dumps({
        "polling_interval": 20.0,
        "monitored_files": ["/var/config.json"],
        "environment_monitoring_enabled": True,
        "automatic_reload_enabled": True
    })
    policy = HotReloadPolicy.from_json(json_str)

    policy_interval = policy.polling_interval
    policy_files = policy.monitored_files
    policy_env_flag = policy.environment_monitoring_enabled
    policy_auto_flag = policy.automatic_reload_enabled

    assert policy_interval == 20.0, "from_json should reconstruct the polling_interval"
    assert policy_files == ["/var/config.json"], "from_json should reconstruct the monitored_files"
    assert policy_env_flag is True, "from_json should reconstruct the environment_monitoring_enabled"
    assert policy_auto_flag is True, "from_json should reconstruct the automatic_reload_enabled"
    return


# ---- Round-Trip Tests ----


def test_as_dict_from_dict_round_trip():
    """
        Verify that as_dict followed by from_dict produces an equivalent object.
    """
    original = HotReloadPolicy(
        polling_interval=8.0,
        monitored_files=["/etc/config.json", "/opt/app.yaml"],
        environment_monitoring_enabled=True,
        automatic_reload_enabled=False
    )
    data = original.as_dict()
    reconstructed = HotReloadPolicy.from_dict(data)

    assert reconstructed.polling_interval == original.polling_interval, \
        "round-trip polling_interval should match"
    assert reconstructed.monitored_files == original.monitored_files, \
        "round-trip monitored_files should match"
    assert reconstructed.environment_monitoring_enabled == original.environment_monitoring_enabled, \
        "round-trip environment_monitoring_enabled should match"
    assert reconstructed.automatic_reload_enabled == original.automatic_reload_enabled, \
        "round-trip automatic_reload_enabled should match"
    return


def test_to_json_from_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent object.
    """
    original = HotReloadPolicy(
        polling_interval=12.0,
        monitored_files=["/tmp/test.json"],
        environment_monitoring_enabled=False,
        automatic_reload_enabled=True
    )
    json_str = original.to_json()
    reconstructed = HotReloadPolicy.from_json(json_str)

    assert reconstructed.polling_interval == original.polling_interval, \
        "json round-trip polling_interval should match"
    assert reconstructed.monitored_files == original.monitored_files, \
        "json round-trip monitored_files should match"
    assert reconstructed.environment_monitoring_enabled == original.environment_monitoring_enabled, \
        "json round-trip environment_monitoring_enabled should match"
    assert reconstructed.automatic_reload_enabled == original.automatic_reload_enabled, \
        "json round-trip automatic_reload_enabled should match"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name 'HotReloadPolicy'.
    """
    policy = HotReloadPolicy()
    repr_str = repr(policy)
    has_class_name = "HotReloadPolicy" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_polling_interval():
    """
        Verify that __repr__ contains the polling interval value.
    """
    policy = HotReloadPolicy(polling_interval=9.5)
    repr_str = repr(policy)
    has_interval = "9.5" in repr_str
    assert has_interval is True, "repr should contain the polling interval value"
    return


def test_repr_contains_automatic_reload_enabled():
    """
        Verify that __repr__ contains the automatic reload enabled status.
    """
    policy = HotReloadPolicy(automatic_reload_enabled=False)
    repr_str = repr(policy)
    has_auto_flag = "False" in repr_str
    assert has_auto_flag is True, "repr should contain the automatic reload enabled status"
    return


# ---- __str__ Tests ----


def test_str_contains_polling_interval():
    """
        Verify that __str__ contains the polling interval value.
    """
    policy = HotReloadPolicy(polling_interval=4.0)
    str_val = str(policy)
    has_interval = "4.0" in str_val
    assert has_interval is True, "str should contain the polling interval value"
    return


def test_str_contains_monitored_file_count():
    """
        Verify that __str__ contains the monitored file count.
    """
    policy = HotReloadPolicy(monitored_files=["/a.json", "/b.yaml", "/c.json"])
    str_val = str(policy)
    has_count = "3" in str_val
    assert has_count is True, "str should contain the monitored file count"
    return


def test_str_contains_automatic_reload_enabled():
    """
        Verify that __str__ contains the automatic reload enabled status.
    """
    policy = HotReloadPolicy(automatic_reload_enabled=True)
    str_val = str(policy)
    has_auto_flag = "True" in str_val
    assert has_auto_flag is True, "str should contain the automatic reload enabled status"
    return
