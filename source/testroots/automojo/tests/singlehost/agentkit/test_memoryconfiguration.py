"""
    .. module:: automojo.tests.singlehost.agentkit.test_memoryconfiguration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the MemoryConfiguration class.

    **Validates: Requirements 12.1 through 12.16**
"""

import json
import os
import tempfile

from automojo.agentkit.errors import ConfigurationError
from automojo.agentkit.expirationpolicy import ExpirationPolicy
from automojo.agentkit.memoryconfiguration import MemoryConfiguration
from automojo.agentkit.memoryscope import MemoryScope


# ---- Construction Tests ----


def test_memoryconfiguration_construction_with_all_params():
    """
        Verify that MemoryConfiguration stores all provided parameters.
    """
    policy = ExpirationPolicy(default_ttl=3600.0, cleanup_interval=120.0)
    config = MemoryConfiguration(
        backend_type="file",
        connection_params={"directory": "/tmp/memory"},
        default_scope=MemoryScope.SHARED,
        expiration_policy=policy,
        embedding_settings={"provider": "openai", "dimension": 1536},
        credential_names=["api-key"],
    )
    assert config.backend_type == "file", "backend_type should be 'file'"
    assert config.connection_params == {"directory": "/tmp/memory"}, "connection_params mismatch"
    assert config.default_scope == MemoryScope.SHARED, "default_scope should be SHARED"
    assert config.expiration_policy == policy, "expiration_policy mismatch"
    assert config.embedding_settings == {"provider": "openai", "dimension": 1536}, "embedding_settings mismatch"
    assert config.credential_names == ["api-key"], "credential_names mismatch"
    return


def test_memoryconfiguration_construction_defaults():
    """
        Verify that MemoryConfiguration uses defaults for optional parameters.
    """
    config = MemoryConfiguration(backend_type="inmemory")
    assert config.backend_type == "inmemory", "backend_type should be 'inmemory'"
    assert config.connection_params == {}, "connection_params should default to empty dict"
    assert config.default_scope == MemoryScope.AGENT, "default_scope should default to AGENT"
    assert config.expiration_policy is None, "expiration_policy should default to None"
    assert config.embedding_settings == {}, "embedding_settings should default to empty dict"
    assert config.credential_names == [], "credential_names should default to empty list"
    return


def test_memoryconfiguration_defensive_copy_connection_params():
    """
        Verify that connection_params returns a defensive copy.
    """
    original_params = {"host": "localhost"}
    config = MemoryConfiguration(backend_type="redis", connection_params=original_params)
    returned = config.connection_params
    returned["port"] = 6379
    assert "port" not in config.connection_params, "Modifying returned dict should not affect internal state"
    return


def test_memoryconfiguration_defensive_copy_embedding_settings():
    """
        Verify that embedding_settings returns a defensive copy.
    """
    original_settings = {"provider": "openai"}
    config = MemoryConfiguration(backend_type="inmemory", embedding_settings=original_settings)
    returned = config.embedding_settings
    returned["dimension"] = 768
    assert "dimension" not in config.embedding_settings, "Modifying returned dict should not affect internal state"
    return


def test_memoryconfiguration_defensive_copy_credential_names():
    """
        Verify that credential_names returns a defensive copy.
    """
    original_names = ["db-password"]
    config = MemoryConfiguration(backend_type="postgres", credential_names=original_names)
    returned = config.credential_names
    returned.append("api-key")
    assert len(config.credential_names) == 1, "Modifying returned list should not affect internal state"
    return


# ---- from_dict Tests ----


def test_memoryconfiguration_from_dict_raises_when_backend_type_missing():
    """
        Verify that from_dict raises ConfigurationError when backend_type is missing.
    """
    raised = False
    try:
        MemoryConfiguration.from_dict({"connection_params": {}})
    except ConfigurationError:
        raised = True
    assert raised is True, "from_dict should raise ConfigurationError when backend_type is missing"
    return


def test_memoryconfiguration_from_dict_raises_when_backend_type_none():
    """
        Verify that from_dict raises ConfigurationError when backend_type is None.
    """
    raised = False
    try:
        MemoryConfiguration.from_dict({"backend_type": None})
    except ConfigurationError:
        raised = True
    assert raised is True, "from_dict should raise ConfigurationError when backend_type is None"
    return


def test_memoryconfiguration_from_dict_parses_default_scope():
    """
        Verify that from_dict parses the default_scope string into a MemoryScope.
    """
    data = {"backend_type": "inmemory", "default_scope": "GLOBAL"}
    config = MemoryConfiguration.from_dict(data)
    assert config.default_scope == MemoryScope.GLOBAL, "from_dict should parse default_scope"
    return


def test_memoryconfiguration_from_dict_parses_expiration_policy():
    """
        Verify that from_dict parses the expiration_policy dictionary.
    """
    data = {
        "backend_type": "file",
        "expiration_policy": {"default_ttl": 7200.0, "cleanup_interval": 60.0},
    }
    config = MemoryConfiguration.from_dict(data)
    expected_policy = ExpirationPolicy(default_ttl=7200.0, cleanup_interval=60.0)
    assert config.expiration_policy == expected_policy, "from_dict should parse expiration_policy"
    return


def test_memoryconfiguration_from_dict_defaults_scope_to_agent():
    """
        Verify that from_dict defaults scope to AGENT when not provided.
    """
    data = {"backend_type": "inmemory"}
    config = MemoryConfiguration.from_dict(data)
    assert config.default_scope == MemoryScope.AGENT, "from_dict should default scope to AGENT"
    return


# ---- Serialization Tests ----


def test_memoryconfiguration_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all configuration fields.
    """
    policy = ExpirationPolicy(default_ttl=600.0)
    config = MemoryConfiguration(
        backend_type="file",
        connection_params={"dir": "/data"},
        default_scope=MemoryScope.SHARED,
        expiration_policy=policy,
        embedding_settings={"dim": 128},
        credential_names=["secret"],
    )
    d = config.as_dict()
    assert d["backend_type"] == "file", "as_dict should contain backend_type"
    assert d["connection_params"] == {"dir": "/data"}, "as_dict should contain connection_params"
    assert d["default_scope"] == "SHARED", "as_dict should contain default_scope as string"
    assert d["expiration_policy"] == policy.as_dict(), "as_dict should contain expiration_policy"
    assert d["embedding_settings"] == {"dim": 128}, "as_dict should contain embedding_settings"
    assert d["credential_names"] == ["secret"], "as_dict should contain credential_names"
    return


def test_memoryconfiguration_as_dict_excludes_resolved_credentials():
    """
        Verify that as_dict includes credential_names but not resolved values.
    """
    config = MemoryConfiguration(
        backend_type="postgres",
        credential_names=["db-password", "api-key"],
    )
    d = config.as_dict()
    assert "credential_names" in d, "as_dict should include credential_names"
    assert d["credential_names"] == ["db-password", "api-key"], "credential_names should list names only"
    # No resolved credential values should appear
    for key in d:
        assert key in ("backend_type", "connection_params", "default_scope",
                        "expiration_policy", "embedding_settings", "credential_names"), \
            "as_dict should not contain unexpected keys"
    return


def test_memoryconfiguration_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    config = MemoryConfiguration(backend_type="inmemory")
    json_str = config.to_json()
    data = json.loads(json_str)
    assert data["backend_type"] == "inmemory", "to_json should produce valid JSON"
    return


def test_memoryconfiguration_from_json_roundtrip():
    """
        Verify that from_json reconstructs an equivalent MemoryConfiguration.
    """
    policy = ExpirationPolicy(default_ttl=1800.0, cleanup_interval=90.0)
    original = MemoryConfiguration(
        backend_type="file",
        connection_params={"path": "/tmp"},
        default_scope=MemoryScope.GLOBAL,
        expiration_policy=policy,
        embedding_settings={"model": "ada"},
        credential_names=["key1"],
    )
    json_str = original.to_json()
    restored = MemoryConfiguration.from_json(json_str)
    assert original == restored, "from_json should reconstruct an equivalent MemoryConfiguration"
    return


# ---- File Loading Tests ----


def test_memoryconfiguration_from_json_file_loads_valid_file():
    """
        Verify that from_json_file loads a MemoryConfiguration from a JSON file.
    """
    config_data = {
        "backend_type": "file",
        "connection_params": {"directory": "/data/memory"},
        "default_scope": "SHARED",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(config_data, fh)
        temp_path = fh.name

    try:
        config = MemoryConfiguration.from_json_file(temp_path)
        assert config.backend_type == "file", "from_json_file should load backend_type"
        assert config.default_scope == MemoryScope.SHARED, "from_json_file should parse default_scope"
    finally:
        os.unlink(temp_path)
    return


def test_memoryconfiguration_from_json_file_raises_on_missing_file():
    """
        Verify that from_json_file raises ConfigurationError for a missing file.
    """
    raised = False
    try:
        MemoryConfiguration.from_json_file("/nonexistent/path/config.json")
    except ConfigurationError:
        raised = True
    assert raised is True, "from_json_file should raise ConfigurationError for missing file"
    return


def test_memoryconfiguration_from_yaml_file_loads_valid_file():
    """
        Verify that from_yaml_file loads a MemoryConfiguration from a YAML file.
    """
    import yaml

    config_data = {
        "backend_type": "redis",
        "connection_params": {"host": "localhost", "port": 6379},
        "default_scope": "GLOBAL",
        "expiration_policy": {"default_ttl": 3600.0, "cleanup_interval": 300.0},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as fh:
        yaml.dump(config_data, fh)
        temp_path = fh.name

    try:
        config = MemoryConfiguration.from_yaml_file(temp_path)
        assert config.backend_type == "redis", "from_yaml_file should load backend_type"
        assert config.default_scope == MemoryScope.GLOBAL, "from_yaml_file should parse default_scope"
        expected_policy = ExpirationPolicy(default_ttl=3600.0, cleanup_interval=300.0)
        assert config.expiration_policy == expected_policy, "from_yaml_file should parse expiration_policy"
    finally:
        os.unlink(temp_path)
    return


def test_memoryconfiguration_from_yaml_file_raises_on_missing_file():
    """
        Verify that from_yaml_file raises ConfigurationError for a missing file.
    """
    raised = False
    try:
        MemoryConfiguration.from_yaml_file("/nonexistent/path/config.yaml")
    except ConfigurationError:
        raised = True
    assert raised is True, "from_yaml_file should raise ConfigurationError for missing file"
    return


# ---- __repr__, __str__, __eq__ Tests ----


def test_memoryconfiguration_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    config = MemoryConfiguration(backend_type="inmemory")
    repr_str = repr(config)
    has_class_name = "MemoryConfiguration" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_memoryconfiguration_repr_contains_backend_type():
    """
        Verify that __repr__ contains the backend_type.
    """
    config = MemoryConfiguration(backend_type="file")
    repr_str = repr(config)
    has_backend = "file" in repr_str
    assert has_backend is True, "repr should contain the backend_type"
    return


def test_memoryconfiguration_repr_contains_default_scope():
    """
        Verify that __repr__ contains the default_scope.
    """
    config = MemoryConfiguration(backend_type="inmemory", default_scope=MemoryScope.GLOBAL)
    repr_str = repr(config)
    has_scope = "GLOBAL" in repr_str
    assert has_scope is True, "repr should contain the default_scope"
    return


def test_memoryconfiguration_str_contains_backend():
    """
        Verify that __str__ contains the backend type.
    """
    config = MemoryConfiguration(backend_type="redis")
    str_val = str(config)
    has_backend = "redis" in str_val
    assert has_backend is True, "__str__ should contain the backend type"
    return


def test_memoryconfiguration_str_contains_scope():
    """
        Verify that __str__ contains the scope.
    """
    config = MemoryConfiguration(backend_type="inmemory", default_scope=MemoryScope.SHARED)
    str_val = str(config)
    has_scope = "SHARED" in str_val
    assert has_scope is True, "__str__ should contain the scope"
    return


def test_memoryconfiguration_str_contains_expiration_info():
    """
        Verify that __str__ contains expiration information.
    """
    policy = ExpirationPolicy(default_ttl=600.0)
    config = MemoryConfiguration(backend_type="inmemory", expiration_policy=policy)
    str_val = str(config)
    has_expiration = "600.0" in str_val
    assert has_expiration is True, "__str__ should contain expiration info"
    return


def test_memoryconfiguration_str_shows_none_when_no_expiration():
    """
        Verify that __str__ shows 'none' when no expiration policy is set.
    """
    config = MemoryConfiguration(backend_type="inmemory")
    str_val = str(config)
    has_none = "none" in str_val
    assert has_none is True, "__str__ should show 'none' when no expiration policy"
    return


def test_memoryconfiguration_eq_returns_true_for_equivalent():
    """
        Verify that __eq__ returns True for equivalent configurations.
    """
    policy = ExpirationPolicy(default_ttl=100.0)
    config_a = MemoryConfiguration(
        backend_type="file",
        connection_params={"dir": "/tmp"},
        default_scope=MemoryScope.SHARED,
        expiration_policy=policy,
    )
    config_b = MemoryConfiguration(
        backend_type="file",
        connection_params={"dir": "/tmp"},
        default_scope=MemoryScope.SHARED,
        expiration_policy=policy,
    )
    assert config_a == config_b, "Equivalent configurations should be equal"
    return


def test_memoryconfiguration_eq_returns_false_for_different_backend():
    """
        Verify that __eq__ returns False when backend_type differs.
    """
    config_a = MemoryConfiguration(backend_type="inmemory")
    config_b = MemoryConfiguration(backend_type="file")
    result = config_a == config_b
    assert result is False, "Configurations with different backend_type should not be equal"
    return


def test_memoryconfiguration_eq_returns_false_for_non_config():
    """
        Verify that __eq__ returns False when compared to a non-MemoryConfiguration.
    """
    config = MemoryConfiguration(backend_type="inmemory")
    result = config == "not a config"
    assert result is False, "__eq__ should return False for non-MemoryConfiguration objects"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
