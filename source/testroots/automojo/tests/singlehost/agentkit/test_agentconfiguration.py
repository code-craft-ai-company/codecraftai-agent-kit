"""
    Tests for the automojo.agentkit.agentconfiguration module.

    Contains property-based tests (using automojo.testbase.properties) and unit tests
    for the AgentConfiguration class.

    Feature: core-agent-framework
"""

import json
import os

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st
from automojo.testbase.properties.strategies import composite

from automojo.agentkit.agentconfiguration import AgentConfiguration
from automojo.agentkit.errors import ConfigurationError
from automojo.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# testbase property strategies for generating AgentConfiguration inputs
# ---------------------------------------------------------------------------

# Strategy for generating non-empty printable text suitable for name/version
name_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=50
).filter(lambda s: len(s.strip()) > 0)

version_strategy = st.text(
    alphabet=st.characters(categories=("L", "N", "P")),
    min_size=1,
    max_size=20
).filter(lambda s: len(s.strip()) > 0)

# Strategy for generating tag dictionaries
tags_strategy = st.dictionaries(
    keys=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=20
    ),
    values=st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z")),
        min_size=0,
        max_size=50
    ),
    max_size=5
)

# Strategy for generating settings dictionaries (simple string values for round-trip safety)
settings_strategy = st.dictionaries(
    keys=st.text(
        alphabet=st.characters(categories=("L", "N")),
        min_size=1,
        max_size=20
    ),
    values=st.text(
        alphabet=st.characters(categories=("L", "N", "P", "Z")),
        min_size=0,
        max_size=50
    ),
    max_size=5
)

# Strategy for generating optional identifier
@composite
def _uuid_string(draw):
    """
        Generates a valid UUID v4 string.

        :returns: A UUID v4 formatted string.
    """
    segments = [
        draw(st.integers(min_value=0, max_value=0xFFFFFFFF)),
        draw(st.integers(min_value=0, max_value=0xFFFF)),
        draw(st.integers(min_value=0x4000, max_value=0x4FFF)),
        draw(st.integers(min_value=0x8000, max_value=0xBFFF)),
        draw(st.integers(min_value=0, max_value=0xFFFFFFFFFFFF)),
    ]
    return f"{segments[0]:08x}-{segments[1]:04x}-{segments[2]:04x}-{segments[3]:04x}-{segments[4]:012x}"


optional_identifier_strategy = st.one_of(
    st.none(),
    _uuid_string()
)


def build_identity_dict(name, version, tags=None, identifier=None):
    """
        Builds an identity dictionary from the given parameters.

        :param name: The agent name.
        :param version: The agent version.
        :param tags: Optional tags dictionary.
        :param identifier: Optional identifier string.

        :returns: A dictionary containing identity fields.
    """
    identity = {
        "name": name,
        "version": version
    }

    if tags is not None and len(tags) > 0:
        identity["tags"] = tags

    if identifier is not None:
        identity["identifier"] = identifier

    return identity


# Strategy for generating valid config dicts without credentials/data_profiles
valid_config_strategy = st.fixed_dictionaries({
    "name": name_strategy,
    "version": version_strategy,
    "tags": tags_strategy,
    "identifier": optional_identifier_strategy,
    "settings": settings_strategy
})


# ---------------------------------------------------------------------------
# Property 4: AgentConfiguration JSON round-trip
# **Validates: Requirements 3.12, 12.8**
# ---------------------------------------------------------------------------

@given(data=valid_config_strategy, constraints={"max_examples": 100})
def test_property_4_json_round_trip(data):
    """
        Property 4: AgentConfiguration JSON round-trip.

        For any valid AgentConfiguration instance (without credential references),
        calling to_json() and then from_json() produces an AgentConfiguration
        whose as_dict() output equals the original.

        **Validates: Requirements 3.12, 12.8**
    """
    identity = build_identity_dict(
        name=data["name"],
        version=data["version"],
        tags=data["tags"],
        identifier=data["identifier"]
    )

    config_data = {
        "identity": identity
    }

    has_settings = len(data["settings"]) > 0
    if has_settings is True:
        config_data["settings"] = data["settings"]

    original = AgentConfiguration.from_dict(config_data, app_context=None)
    original_dict = original.as_dict()

    json_str = original.to_json()
    restored = AgentConfiguration.from_json(json_str, app_context=None)
    restored_dict = restored.as_dict()

    assert restored_dict == original_dict, (
        "JSON round-trip as_dict mismatch:\n  original={!r}\n  restored={!r}".format(
            original_dict, restored_dict
        )
    )
    return


# ---------------------------------------------------------------------------
# Property 5: AgentConfiguration YAML round-trip
# **Validates: Requirements 3.13, 12.9**
# ---------------------------------------------------------------------------

@given(data=valid_config_strategy, constraints={"max_examples": 100})
def test_property_5_yaml_round_trip(data):
    """
        Property 5: AgentConfiguration YAML round-trip.

        For any valid AgentConfiguration instance (without credential references),
        calling to_yaml() and then from_yaml() produces an AgentConfiguration
        whose as_dict() output equals the original.

        **Validates: Requirements 3.13, 12.9**
    """
    identity = build_identity_dict(
        name=data["name"],
        version=data["version"],
        tags=data["tags"],
        identifier=data["identifier"]
    )

    config_data = {
        "identity": identity
    }

    has_settings = len(data["settings"]) > 0
    if has_settings is True:
        config_data["settings"] = data["settings"]

    original = AgentConfiguration.from_dict(config_data, app_context=None)
    original_dict = original.as_dict()

    yaml_str = original.to_yaml()
    restored = AgentConfiguration.from_yaml(yaml_str, app_context=None)
    restored_dict = restored.as_dict()

    assert restored_dict == original_dict, (
        "YAML round-trip as_dict mismatch:\n  original={!r}\n  restored={!r}".format(
            original_dict, restored_dict
        )
    )
    return


# ---------------------------------------------------------------------------
# Property 6: AgentConfiguration validation rejects invalid configs
# **Validates: Requirements 3.5, 3.8**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy, constraints={"max_examples": 100})
def test_property_6_validation_rejects_missing_identity(name, version):
    """
        Property 6: AgentConfiguration validation rejects invalid configs
        (missing identity field).

        For any configuration dictionary missing the required 'identity' field,
        calling from_dict() raises ConfigurationError.

        **Validates: Requirements 3.5, 3.8**
    """
    config_data = {
        "settings": {"key": "value"}
    }

    raised = False
    try:
        AgentConfiguration.from_dict(config_data, app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for missing 'identity' field"
    )
    return


@given(name=name_strategy, constraints={"max_examples": 100})
def test_property_6_validation_rejects_missing_identity_name(name):
    """
        Property 6: AgentConfiguration validation rejects invalid configs
        (missing name in identity).

        For any configuration dictionary with identity missing 'name',
        calling from_dict() raises ConfigurationError.

        **Validates: Requirements 3.5, 3.8**
    """
    config_data = {
        "identity": {
            "version": "1.0"
        }
    }

    raised = False
    try:
        AgentConfiguration.from_dict(config_data, app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for missing 'name' in identity"
    )
    return


@given(version=version_strategy, constraints={"max_examples": 100})
def test_property_6_validation_rejects_missing_identity_version(version):
    """
        Property 6: AgentConfiguration validation rejects invalid configs
        (missing version in identity).

        For any configuration dictionary with identity missing 'version',
        calling from_dict() raises ConfigurationError.

        **Validates: Requirements 3.5, 3.8**
    """
    config_data = {
        "identity": {
            "name": "test-agent"
        }
    }

    raised = False
    try:
        AgentConfiguration.from_dict(config_data, app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for missing 'version' in identity"
    )
    return


@given(
    name=name_strategy,
    version=version_strategy, constraints={"max_examples": 100})
def test_property_6_validation_rejects_non_dict_identity(name, version):
    """
        Property 6: AgentConfiguration validation rejects invalid configs
        (identity is not a dict).

        For any configuration dictionary where identity is not a dict,
        calling from_dict() raises ConfigurationError.

        **Validates: Requirements 3.5, 3.8**
    """
    config_data = {
        "identity": "not-a-dict"
    }

    raised = False
    try:
        AgentConfiguration.from_dict(config_data, app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for non-dict identity"
    )
    return


# ---------------------------------------------------------------------------
# Property 7: AgentConfiguration serialization excludes credentials
# **Validates: Requirements 9.3, 3.9, 3.10, 3.11**
# ---------------------------------------------------------------------------

@given(
    name=name_strategy,
    version=version_strategy, constraints={"max_examples": 100})
def test_property_7_serialization_excludes_credentials(name, version):
    """
        Property 7: AgentConfiguration serialization excludes credentials.

        For any valid AgentConfiguration with CredentialReference entries,
        the output of as_dict(), to_json(), and to_yaml() does not contain
        resolved credential secret values.

        **Validates: Requirements 9.3, 3.9, 3.10, 3.11**
    """
    # Use a secret value that is guaranteed to not appear in the config data
    # by using a unique prefix that cannot collide with name, version, or
    # the fixed credential reference fields
    secret_value = "RESOLVED_SECRET_{}_{}_xyz987".format(len(name), len(version))

    # Create a mock credential object with a secret value
    mock_credential = Mock()
    mock_credential.configure(recursive=True)
    mock_cred_ctx = mock_credential.mock_context()
    mock_cred_ctx.set_attribute("secret", secret_value)
    mock_cred_ctx.set_attribute("value", secret_value)

    # Create a mock credential manager
    mock_cred_manager = Mock()
    mock_cred_manager.configure(recursive=True)
    mock_cred_manager_ctx = mock_cred_manager.mock_context()
    mock_cred_manager_ctx.mock_method("lookup_credential", return_value=mock_credential)

    # Create a mock app context
    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("credential_manager", mock_cred_manager)

    config_data = {
        "identity": {
            "name": name,
            "version": version
        },
        "credentials": {
            "db_cred": {
                "provider": "vault",
                "key": "db-password"
            }
        }
    }

    configuration = AgentConfiguration.from_dict(config_data, app_context=mock_app_context)

    # Check as_dict does not contain the secret value
    config_dict = configuration.as_dict()
    dict_str = str(config_dict)
    has_secret_in_dict = secret_value in dict_str
    assert has_secret_in_dict is False, (
        "as_dict() should not contain resolved secret value {!r}".format(secret_value)
    )

    # Check to_json does not contain the secret value
    json_str = configuration.to_json()
    has_secret_in_json = secret_value in json_str
    assert has_secret_in_json is False, (
        "to_json() should not contain resolved secret value {!r}".format(secret_value)
    )

    # Check to_yaml does not contain the secret value
    yaml_str = configuration.to_yaml()
    has_secret_in_yaml = secret_value in yaml_str
    assert has_secret_in_yaml is False, (
        "to_yaml() should not contain resolved secret value {!r}".format(secret_value)
    )
    return


# ---------------------------------------------------------------------------
# Property 21: AgentConfiguration from_dict produces valid configuration
# **Validates: Requirements 3.1**
# ---------------------------------------------------------------------------

@given(data=valid_config_strategy, constraints={"max_examples": 100})
def test_property_21_from_dict_produces_valid_configuration(data):
    """
        Property 21: AgentConfiguration from_dict produces valid configuration.

        For any valid configuration dictionary with all required fields,
        from_dict() produces an AgentConfiguration whose as_dict() contains
        the same identity, settings, and reference names.

        **Validates: Requirements 3.1**
    """
    identity = build_identity_dict(
        name=data["name"],
        version=data["version"],
        tags=data["tags"],
        identifier=data["identifier"]
    )

    config_data = {
        "identity": identity
    }

    has_settings = len(data["settings"]) > 0
    if has_settings is True:
        config_data["settings"] = data["settings"]

    configuration = AgentConfiguration.from_dict(config_data, app_context=None)
    result_dict = configuration.as_dict()

    # Verify identity is preserved
    result_identity = result_dict["identity"]
    assert result_identity["name"] == data["name"], (
        "Identity name mismatch: {!r} != {!r}".format(
            result_identity["name"], data["name"]
        )
    )
    assert result_identity["version"] == data["version"], (
        "Identity version mismatch: {!r} != {!r}".format(
            result_identity["version"], data["version"]
        )
    )

    # Verify settings are preserved
    if has_settings is True:
        has_settings_key = "settings" in result_dict
        assert has_settings_key is True, "as_dict should contain 'settings' key"
        assert result_dict["settings"] == data["settings"], (
            "Settings mismatch: {!r} != {!r}".format(
                result_dict["settings"], data["settings"]
            )
        )

    return


# ---------------------------------------------------------------------------
# Unit tests for AgentConfiguration edge cases (Task 5.7)
# **Validates: Requirements 8.1, 8.2, 8.3, 9.1, 9.2, 10.1, 10.2, 16.7, 16.8**
# ---------------------------------------------------------------------------

def test_missing_app_context_raises_error_when_credentials_need_resolving():
    """
        Verify that missing AppContext raises ConfigurationError when
        credentials need resolving.
    """
    config_data = {
        "identity": {
            "name": "test-agent",
            "version": "1.0"
        },
        "credentials": {
            "db_cred": {
                "provider": "vault",
                "key": "db-password"
            }
        }
    }

    raised = False
    error_message = ""
    try:
        AgentConfiguration.from_dict(config_data, app_context=None)
    except ConfigurationError as exc:
        raised = True
        error_message = exc.message

    assert raised is True, (
        "Expected ConfigurationError when credentials need resolving without app_context"
    )

    has_app_context_msg = "automojo-this-app" in error_message
    assert has_app_context_msg is True, (
        "Error message should mention automojo-this-app, got: {!r}".format(error_message)
    )
    return


def test_unresolvable_credential_reference_raises_error():
    """
        Verify that an unresolvable CredentialReference raises ConfigurationError.
    """
    # Create a mock credential manager that returns None
    mock_cred_manager = Mock()
    mock_cred_manager.configure(recursive=True)
    mock_cred_manager_ctx = mock_cred_manager.mock_context()
    mock_cred_manager_ctx.mock_method("lookup_credential", return_value=None)

    # Create a mock app context
    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("credential_manager", mock_cred_manager)

    config_data = {
        "identity": {
            "name": "test-agent",
            "version": "1.0"
        },
        "credentials": {
            "missing_cred": {
                "provider": "vault",
                "key": "nonexistent-key"
            }
        }
    }

    raised = False
    error_message = ""
    try:
        AgentConfiguration.from_dict(config_data, app_context=mock_app_context)
    except ConfigurationError as exc:
        raised = True
        error_message = exc.message

    assert raised is True, (
        "Expected ConfigurationError for unresolvable credential reference"
    )

    has_cred_name = "missing_cred" in error_message
    assert has_cred_name is True, (
        "Error message should identify the unresolvable credential name, got: {!r}".format(
            error_message
        )
    )
    return


def test_unresolvable_data_profile_reference_raises_error():
    """
        Verify that an unresolvable DataProfileReference raises ConfigurationError.
    """
    # Create a mock data profile manager that returns None
    mock_dp_manager = Mock()
    mock_dp_manager.configure(recursive=True)
    mock_dp_manager_ctx = mock_dp_manager.mock_context()
    mock_dp_manager_ctx.mock_method("lookup_data_profile", return_value=None)

    # Create a mock app context
    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("data_profile_manager", mock_dp_manager)

    config_data = {
        "identity": {
            "name": "test-agent",
            "version": "1.0"
        },
        "data_profiles": {
            "missing_profile": {
                "provider": "db",
                "key": "nonexistent-profile"
            }
        }
    }

    raised = False
    error_message = ""
    try:
        AgentConfiguration.from_dict(config_data, app_context=mock_app_context)
    except ConfigurationError as exc:
        raised = True
        error_message = exc.message

    assert raised is True, (
        "Expected ConfigurationError for unresolvable data profile reference"
    )

    has_profile_name = "missing_profile" in error_message
    assert has_profile_name is True, (
        "Error message should identify the unresolvable data profile name, got: {!r}".format(
            error_message
        )
    )
    return


def test_file_path_resolution_relative_to_app_context_directory():
    """
        Verify that file paths are resolved relative to the AppContext directory.
    """
    import tempfile

    # Create a temporary directory and config file
    temp_dir = tempfile.mkdtemp()
    config_content = json.dumps({
        "identity": {
            "name": "file-agent",
            "version": "1.0"
        }
    })

    config_filename = "agent_config.json"
    config_path = os.path.join(temp_dir, config_filename)

    with open(config_path, "w") as fh:
        fh.write(config_content)

    # Create a mock app context with directory
    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("directory", temp_dir)

    configuration = AgentConfiguration.from_json_file(
        config_filename, app_context=mock_app_context
    )

    result_dict = configuration.as_dict()
    result_name = result_dict["identity"]["name"]

    assert result_name == "file-agent", (
        "File path resolution should load config from AppContext directory, got name: {!r}".format(
            result_name
        )
    )

    # Cleanup
    os.remove(config_path)
    os.rmdir(temp_dir)
    return


def test_yaml_file_path_resolution_relative_to_app_context_directory():
    """
        Verify that YAML file paths are resolved relative to the AppContext directory.
    """
    import tempfile
    import yaml

    # Create a temporary directory and config file
    temp_dir = tempfile.mkdtemp()
    config_data = {
        "identity": {
            "name": "yaml-agent",
            "version": "2.0"
        }
    }
    config_content = yaml.dump(config_data, default_flow_style=False)

    config_filename = "agent_config.yaml"
    config_path = os.path.join(temp_dir, config_filename)

    with open(config_path, "w") as fh:
        fh.write(config_content)

    # Create a mock app context with directory
    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("directory", temp_dir)

    configuration = AgentConfiguration.from_yaml_file(
        config_filename, app_context=mock_app_context
    )

    result_dict = configuration.as_dict()
    result_name = result_dict["identity"]["name"]

    assert result_name == "yaml-agent", (
        "YAML file path resolution should load config from AppContext directory, got name: {!r}".format(
            result_name
        )
    )

    # Cleanup
    os.remove(config_path)
    os.rmdir(temp_dir)
    return


def test_repr_excludes_credential_values():
    """
        Verify that __repr__ excludes resolved credential values.
    """
    # Create a mock credential with a secret
    secret_value = "super_secret_password_12345"

    mock_credential = Mock()
    mock_credential.configure(recursive=True)
    mock_cred_ctx = mock_credential.mock_context()
    mock_cred_ctx.set_attribute("secret", secret_value)

    mock_cred_manager = Mock()
    mock_cred_manager.configure(recursive=True)
    mock_cred_manager_ctx = mock_cred_manager.mock_context()
    mock_cred_manager_ctx.mock_method("lookup_credential", return_value=mock_credential)

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("credential_manager", mock_cred_manager)

    config_data = {
        "identity": {
            "name": "repr-agent",
            "version": "1.0"
        },
        "credentials": {
            "db_cred": {
                "provider": "vault",
                "key": "db-password"
            }
        }
    }

    configuration = AgentConfiguration.from_dict(config_data, app_context=mock_app_context)

    repr_str = repr(configuration)
    has_secret = secret_value in repr_str

    assert has_secret is False, (
        "__repr__ should not contain resolved credential secret value"
    )

    has_class_name = "AgentConfiguration" in repr_str
    assert has_class_name is True, (
        "__repr__ should contain class name 'AgentConfiguration'"
    )
    return


def test_str_excludes_credential_values():
    """
        Verify that __str__ excludes resolved credential values.
    """
    secret_value = "another_secret_value_67890"

    mock_credential = Mock()
    mock_credential.configure(recursive=True)
    mock_cred_ctx = mock_credential.mock_context()
    mock_cred_ctx.set_attribute("secret", secret_value)

    mock_cred_manager = Mock()
    mock_cred_manager.configure(recursive=True)
    mock_cred_manager_ctx = mock_cred_manager.mock_context()
    mock_cred_manager_ctx.mock_method("lookup_credential", return_value=mock_credential)

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_ctx = mock_app_context.mock_context()
    mock_app_ctx.set_attribute("credential_manager", mock_cred_manager)

    config_data = {
        "identity": {
            "name": "str-agent",
            "version": "2.0"
        },
        "credentials": {
            "api_key": {
                "provider": "env",
                "key": "api-secret"
            }
        }
    }

    configuration = AgentConfiguration.from_dict(config_data, app_context=mock_app_context)

    str_val = str(configuration)
    has_secret = secret_value in str_val

    assert has_secret is False, (
        "__str__ should not contain resolved credential secret value"
    )

    has_name = "str-agent" in str_val
    assert has_name is True, (
        "__str__ should contain the agent name"
    )
    return


def test_no_app_context_works_without_credentials_or_data_profiles():
    """
        Verify that AgentConfiguration works without app_context when
        there are no credentials or data profiles to resolve.
    """
    config_data = {
        "identity": {
            "name": "simple-agent",
            "version": "1.0"
        },
        "settings": {
            "timeout": "30"
        }
    }

    configuration = AgentConfiguration.from_dict(config_data, app_context=None)
    result_dict = configuration.as_dict()

    result_name = result_dict["identity"]["name"]
    assert result_name == "simple-agent", (
        "Should create config without app_context when no resolution needed"
    )
    return


def test_non_dict_config_data_raises_error():
    """
        Verify that passing a non-dict config_data raises ConfigurationError.
    """
    raised = False
    try:
        AgentConfiguration.from_dict("not-a-dict", app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for non-dict config_data"
    )
    return


def test_invalid_json_string_raises_error():
    """
        Verify that an invalid JSON string raises ConfigurationError.
    """
    raised = False
    try:
        AgentConfiguration.from_json("not valid json {{{", app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for invalid JSON string"
    )
    return


def test_invalid_yaml_string_raises_error():
    """
        Verify that an invalid YAML string raises ConfigurationError.
    """
    raised = False
    try:
        AgentConfiguration.from_yaml(":\n  :\n    - [invalid", app_context=None)
    except ConfigurationError:
        raised = True

    assert raised is True, (
        "Expected ConfigurationError for invalid YAML string"
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
