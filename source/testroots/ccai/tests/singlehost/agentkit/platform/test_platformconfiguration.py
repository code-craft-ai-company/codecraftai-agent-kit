"""
    Tests for the ccai.agentkit.platform.platformconfiguration module.

    Contains unit tests for PlatformConfiguration construction, read-only
    properties, serialization round-trips, credential resolution, file
    loading, and repr/str output.

    Feature: cross-platform-runtime

    .. module:: ccai.tests.singlehost.agentkit.platform.test_platformconfiguration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for PlatformConfiguration.
"""

import json
import os
import tempfile

import yaml

from ccai.agentkit.errors import ConfigurationError
from ccai.agentkit.platform.platformconfiguration import PlatformConfiguration
from ccai.agentkit.platform.platformtype import PlatformType
from ccai.testbase.mocking import Mock


# ---------------------------------------------------------------------------
# Construction and read-only properties
# ---------------------------------------------------------------------------

def test_construction_with_all_fields():
    """
        Verify that PlatformConfiguration stores all constructor fields.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        region="us-east-1",
        credential_references=["aws-main", "aws-backup"],
        service_endpoint_overrides={"s3": "http://localhost:4566"},
        options={"timeout": 30}
    )

    assert config.platform_type is PlatformType.AWS, (
        "platform_type should be AWS, got: {!r}".format(config.platform_type)
    )
    assert config.region == "us-east-1", (
        "region should be 'us-east-1', got: {!r}".format(config.region)
    )
    assert config.credential_references == ["aws-main", "aws-backup"], (
        "credential_references mismatch, got: {!r}".format(config.credential_references)
    )
    assert config.service_endpoint_overrides == {"s3": "http://localhost:4566"}, (
        "service_endpoint_overrides mismatch, got: {!r}".format(config.service_endpoint_overrides)
    )
    assert config.options == {"timeout": 30}, (
        "options mismatch, got: {!r}".format(config.options)
    )
    return


def test_construction_with_defaults():
    """
        Verify that PlatformConfiguration defaults optional fields correctly.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)

    assert config.platform_type is PlatformType.LOCAL, (
        "platform_type should be LOCAL, got: {!r}".format(config.platform_type)
    )
    assert config.region is None, (
        "region should default to None, got: {!r}".format(config.region)
    )
    assert config.credential_references == [], (
        "credential_references should default to empty list, got: {!r}".format(config.credential_references)
    )
    assert config.service_endpoint_overrides == {}, (
        "service_endpoint_overrides should default to empty dict, got: {!r}".format(config.service_endpoint_overrides)
    )
    assert config.options == {}, (
        "options should default to empty dict, got: {!r}".format(config.options)
    )
    return


def test_properties_return_defensive_copies():
    """
        Verify that properties return copies, not references to internal state.
    """
    cred_refs = ["cred-a"]
    overrides = {"sqs": "http://localhost:9324"}
    opts = {"key": "value"}

    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        credential_references=cred_refs,
        service_endpoint_overrides=overrides,
        options=opts
    )

    returned_creds = config.credential_references
    returned_creds.append("cred-b")
    assert config.credential_references == ["cred-a"], (
        "Modifying returned credential_references should not affect internal state"
    )

    returned_overrides = config.service_endpoint_overrides
    returned_overrides["lambda"] = "http://localhost:9999"
    assert "lambda" not in config.service_endpoint_overrides, (
        "Modifying returned service_endpoint_overrides should not affect internal state"
    )

    returned_opts = config.options
    returned_opts["new_key"] = "new_value"
    assert "new_key" not in config.options, (
        "Modifying returned options should not affect internal state"
    )
    return


# ---------------------------------------------------------------------------
# from_dict tests
# ---------------------------------------------------------------------------

def test_from_dict_with_valid_data():
    """
        Verify that from_dict constructs a PlatformConfiguration from a valid dict.
    """
    data = {
        "platform_type": "azure",
        "region": "westus2",
        "credential_references": ["azure-cred"],
        "service_endpoint_overrides": {"blob": "http://localhost:10000"},
        "options": {"retry": 3}
    }

    config = PlatformConfiguration.from_dict(data)

    assert config.platform_type is PlatformType.AZURE, (
        "platform_type should be AZURE, got: {!r}".format(config.platform_type)
    )
    assert config.region == "westus2", (
        "region should be 'westus2', got: {!r}".format(config.region)
    )
    assert config.credential_references == ["azure-cred"], (
        "credential_references mismatch, got: {!r}".format(config.credential_references)
    )
    return


def test_from_dict_with_minimal_data():
    """
        Verify that from_dict works with only required fields.
    """
    data = {"platform_type": "local"}

    config = PlatformConfiguration.from_dict(data)

    assert config.platform_type is PlatformType.LOCAL, (
        "platform_type should be LOCAL, got: {!r}".format(config.platform_type)
    )
    assert config.region is None, (
        "region should be None, got: {!r}".format(config.region)
    )
    return


def test_from_dict_missing_platform_type_raises_configuration_error():
    """
        Verify that from_dict raises ConfigurationError when platform_type is missing.
    """
    data = {"region": "us-east-1"}

    caught = False
    error_message = ""
    try:
        PlatformConfiguration.from_dict(data)
    except ConfigurationError as err:
        caught = True
        error_message = str(err)

    assert caught is True, (
        "from_dict should raise ConfigurationError when platform_type is missing"
    )
    assert "platform_type" in error_message, (
        "Error message should mention 'platform_type', got: {!r}".format(error_message)
    )
    return


def test_from_dict_invalid_platform_type_raises_configuration_error():
    """
        Verify that from_dict raises ConfigurationError for an invalid platform_type value.
    """
    data = {"platform_type": "invalid-cloud"}

    caught = False
    try:
        PlatformConfiguration.from_dict(data)
    except ConfigurationError:
        caught = True

    assert caught is True, (
        "from_dict should raise ConfigurationError for invalid platform_type"
    )
    return


# ---------------------------------------------------------------------------
# JSON round-trip tests
# ---------------------------------------------------------------------------

def test_to_json_from_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent configuration.
    """
    original = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        region="eu-west-1",
        credential_references=["cred-1", "cred-2"],
        service_endpoint_overrides={"s3": "http://localhost:4566"},
        options={"debug": True}
    )

    json_str = original.to_json()
    restored = PlatformConfiguration.from_json(json_str)

    assert restored.platform_type is original.platform_type, (
        "platform_type mismatch after JSON round-trip"
    )
    assert restored.region == original.region, (
        "region mismatch after JSON round-trip"
    )
    assert restored.credential_references == original.credential_references, (
        "credential_references mismatch after JSON round-trip"
    )
    assert restored.service_endpoint_overrides == original.service_endpoint_overrides, (
        "service_endpoint_overrides mismatch after JSON round-trip"
    )
    assert restored.options == original.options, (
        "options mismatch after JSON round-trip"
    )
    return


def test_from_json_invalid_json_raises_configuration_error():
    """
        Verify that from_json raises ConfigurationError for invalid JSON.
    """
    caught = False
    try:
        PlatformConfiguration.from_json("{not valid json")
    except ConfigurationError:
        caught = True

    assert caught is True, (
        "from_json should raise ConfigurationError for invalid JSON"
    )
    return


# ---------------------------------------------------------------------------
# YAML round-trip tests
# ---------------------------------------------------------------------------

def test_to_yaml_from_yaml_round_trip():
    """
        Verify that to_yaml followed by from_yaml produces an equivalent configuration.
    """
    original = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        region="us-central1",
        credential_references=["gcp-sa"],
        service_endpoint_overrides={"pubsub": "http://localhost:8085"},
        options={"project_id": "my-project"}
    )

    yaml_str = original.to_yaml()
    restored = PlatformConfiguration.from_yaml(yaml_str)

    assert restored.platform_type is original.platform_type, (
        "platform_type mismatch after YAML round-trip"
    )
    assert restored.region == original.region, (
        "region mismatch after YAML round-trip"
    )
    assert restored.credential_references == original.credential_references, (
        "credential_references mismatch after YAML round-trip"
    )
    assert restored.service_endpoint_overrides == original.service_endpoint_overrides, (
        "service_endpoint_overrides mismatch after YAML round-trip"
    )
    assert restored.options == original.options, (
        "options mismatch after YAML round-trip"
    )
    return


def test_from_yaml_invalid_yaml_raises_configuration_error():
    """
        Verify that from_yaml raises ConfigurationError for invalid YAML.
    """
    caught = False
    try:
        PlatformConfiguration.from_yaml(":\n  :\n    - [invalid")
    except ConfigurationError:
        caught = True

    assert caught is True, (
        "from_yaml should raise ConfigurationError for invalid YAML"
    )
    return


# ---------------------------------------------------------------------------
# as_dict tests
# ---------------------------------------------------------------------------

def test_as_dict_excludes_resolved_credentials():
    """
        Verify that as_dict does not include resolved credential values.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        region="us-east-1",
        credential_references=["aws-cred"]
    )

    mock_resolver = Mock()
    mock_resolver.configure(recursive=True)
    mock_resolver.mock_context().mock_method("lookup_credential", return_value="secret-value")

    config.resolve_credentials(mock_resolver)

    result = config.as_dict()

    assert "resolved_credentials" not in result, (
        "as_dict should not include resolved_credentials key"
    )
    assert result["platform_type"] == "aws", (
        "as_dict should include platform_type, got: {!r}".format(result.get("platform_type"))
    )
    assert result["credential_references"] == ["aws-cred"], (
        "as_dict should include credential_references names"
    )
    return


def test_as_dict_omits_empty_optional_fields():
    """
        Verify that as_dict omits optional fields when they are empty or None.
    """
    config = PlatformConfiguration(platform_type=PlatformType.LOCAL)

    result = config.as_dict()

    assert "region" not in result, (
        "as_dict should omit region when None"
    )
    assert "credential_references" not in result, (
        "as_dict should omit credential_references when empty"
    )
    assert "service_endpoint_overrides" not in result, (
        "as_dict should omit service_endpoint_overrides when empty"
    )
    assert "options" not in result, (
        "as_dict should omit options when empty"
    )
    return


# ---------------------------------------------------------------------------
# resolve_credentials tests
# ---------------------------------------------------------------------------

def test_resolve_credentials_with_mock_resolver():
    """
        Verify that resolve_credentials resolves each credential reference.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        credential_references=["cred-a", "cred-b"]
    )

    call_log = []

    def mock_lookup(name):
        call_log.append(name)
        return "resolved-{}".format(name)

    mock_resolver = Mock()
    mock_resolver.configure(recursive=True)
    mock_resolver.mock_context().mock_method("lookup_credential", side_effect=mock_lookup)

    config.resolve_credentials(mock_resolver)

    resolved = config.resolved_credentials
    assert resolved["cred-a"] == "resolved-cred-a", (
        "cred-a should be resolved, got: {!r}".format(resolved.get("cred-a"))
    )
    assert resolved["cred-b"] == "resolved-cred-b", (
        "cred-b should be resolved, got: {!r}".format(resolved.get("cred-b"))
    )
    assert "cred-a" in call_log, "lookup_credential should be called with 'cred-a'"
    assert "cred-b" in call_log, "lookup_credential should be called with 'cred-b'"
    return


def test_resolve_credentials_unresolvable_raises_configuration_error():
    """
        Verify that resolve_credentials raises ConfigurationError when a
        credential cannot be resolved (returns None).
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AZURE,
        credential_references=["missing-cred"]
    )

    mock_resolver = Mock()
    mock_resolver.configure(recursive=True)
    mock_resolver.mock_context().mock_method("lookup_credential", return_value=None)

    caught = False
    error_message = ""
    try:
        config.resolve_credentials(mock_resolver)
    except ConfigurationError as err:
        caught = True
        error_message = str(err)

    assert caught is True, (
        "resolve_credentials should raise ConfigurationError for unresolvable credential"
    )
    assert "missing-cred" in error_message, (
        "Error message should mention the credential name, got: {!r}".format(error_message)
    )
    return


def test_resolve_credentials_credential_manager_missing_key_raises_configuration_error():
    """
        Verify that a real CredentialManager missing the key is translated
        into the kit's ConfigurationError (the manager raises the core
        ConfigurationError, a BaseException subclass).
    """
    from ccai.credentials.credentialmanager import CredentialManager

    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        credential_references=["bad-cred"]
    )

    caught = None
    try:
        config.resolve_credentials(CredentialManager())
    except ConfigurationError as exc:
        caught = exc

    assert caught is not None, (
        "resolve_credentials should raise the kit's ConfigurationError when "
        "the CredentialManager has no such key"
    )
    assert "bad-cred" in caught.message
    return


def test_resolve_credentials_resolver_exception_raises_configuration_error():
    """
        Verify that resolve_credentials raises ConfigurationError when the
        resolver raises an exception.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.GCP,
        credential_references=["bad-cred"]
    )

    def failing_lookup(name):
        raise RuntimeError("resolver unavailable")

    mock_resolver = Mock()
    mock_resolver.configure(recursive=True)
    mock_resolver.mock_context().mock_method("lookup_credential", side_effect=failing_lookup)

    caught = False
    try:
        config.resolve_credentials(mock_resolver)
    except ConfigurationError:
        caught = True

    assert caught is True, (
        "resolve_credentials should raise ConfigurationError when resolver fails"
    )
    return


# ---------------------------------------------------------------------------
# from_json_file and from_yaml_file tests
# ---------------------------------------------------------------------------

def test_from_json_file_loads_configuration():
    """
        Verify that from_json_file loads a PlatformConfiguration from a JSON file.
    """
    config_data = {
        "platform_type": "aws",
        "region": "us-west-2"
    }

    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "platform.json")

    with open(file_path, "w") as fh:
        json.dump(config_data, fh)

    config = PlatformConfiguration.from_json_file(file_path)

    assert config.platform_type is PlatformType.AWS, (
        "platform_type should be AWS, got: {!r}".format(config.platform_type)
    )
    assert config.region == "us-west-2", (
        "region should be 'us-west-2', got: {!r}".format(config.region)
    )
    return


def test_from_yaml_file_loads_configuration():
    """
        Verify that from_yaml_file loads a PlatformConfiguration from a YAML file.
    """
    config_data = {
        "platform_type": "gcp",
        "region": "europe-west1"
    }

    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "platform.yaml")

    with open(file_path, "w") as fh:
        yaml.dump(config_data, fh)

    config = PlatformConfiguration.from_yaml_file(file_path)

    assert config.platform_type is PlatformType.GCP, (
        "platform_type should be GCP, got: {!r}".format(config.platform_type)
    )
    assert config.region == "europe-west1", (
        "region should be 'europe-west1', got: {!r}".format(config.region)
    )
    return


def test_from_json_file_with_app_context_resolves_path():
    """
        Verify that from_json_file resolves the file path relative to
        the AppContext directory.
    """
    config_data = {
        "platform_type": "local"
    }

    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "config.json")

    with open(file_path, "w") as fh:
        json.dump(config_data, fh)

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_context.mock_context().set_attribute("directory", tmp_dir)

    config = PlatformConfiguration.from_json_file("config.json", app_context=mock_app_context)

    assert config.platform_type is PlatformType.LOCAL, (
        "platform_type should be LOCAL, got: {!r}".format(config.platform_type)
    )
    return


def test_from_yaml_file_with_app_context_resolves_path():
    """
        Verify that from_yaml_file resolves the file path relative to
        the AppContext directory.
    """
    config_data = {
        "platform_type": "azure",
        "region": "eastus"
    }

    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, "config.yaml")

    with open(file_path, "w") as fh:
        yaml.dump(config_data, fh)

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    mock_app_context.mock_context().set_attribute("directory", tmp_dir)

    config = PlatformConfiguration.from_yaml_file("config.yaml", app_context=mock_app_context)

    assert config.platform_type is PlatformType.AZURE, (
        "platform_type should be AZURE, got: {!r}".format(config.platform_type)
    )
    assert config.region == "eastus", (
        "region should be 'eastus', got: {!r}".format(config.region)
    )
    return


def test_from_json_file_nonexistent_raises_configuration_error():
    """
        Verify that from_json_file raises ConfigurationError for a nonexistent file.
    """
    caught = False
    try:
        PlatformConfiguration.from_json_file("/nonexistent/path/config.json")
    except ConfigurationError:
        caught = True

    assert caught is True, (
        "from_json_file should raise ConfigurationError for nonexistent file"
    )
    return


def test_from_yaml_file_nonexistent_raises_configuration_error():
    """
        Verify that from_yaml_file raises ConfigurationError for a nonexistent file.
    """
    caught = False
    try:
        PlatformConfiguration.from_yaml_file("/nonexistent/path/config.yaml")
    except ConfigurationError:
        caught = True

    assert caught is True, (
        "from_yaml_file should raise ConfigurationError for nonexistent file"
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_includes_class_name_and_platform_type():
    """
        Verify that __repr__ includes the class name, platform type, and region.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AWS,
        region="us-east-1"
    )

    repr_str = repr(config)

    assert "PlatformConfiguration" in repr_str, (
        "repr should contain 'PlatformConfiguration', got: {!r}".format(repr_str)
    )
    assert "aws" in repr_str, (
        "repr should contain 'aws', got: {!r}".format(repr_str)
    )
    assert "us-east-1" in repr_str, (
        "repr should contain 'us-east-1', got: {!r}".format(repr_str)
    )
    return


def test_str_includes_endpoint_override_count():
    """
        Verify that __str__ includes the endpoint override count.
    """
    config = PlatformConfiguration(
        platform_type=PlatformType.AZURE,
        region="westus2",
        service_endpoint_overrides={"blob": "http://localhost:10000", "queue": "http://localhost:10001"}
    )

    str_val = str(config)

    assert "PlatformConfiguration" in str_val, (
        "str should contain 'PlatformConfiguration', got: {!r}".format(str_val)
    )
    assert "azure" in str_val, (
        "str should contain 'azure', got: {!r}".format(str_val)
    )
    assert "2" in str_val, (
        "str should contain endpoint override count '2', got: {!r}".format(str_val)
    )
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
