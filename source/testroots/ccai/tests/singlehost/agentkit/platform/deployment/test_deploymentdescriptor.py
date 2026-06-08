"""
    Tests for the ccai.agentkit.platform.deployment.deploymentdescriptor module.

    Contains unit tests for the DeploymentDescriptor immutable configuration
    object including read-only properties, as_dict, JSON and YAML round-trip
    serialization, and __repr__/__str__ output.

    Feature: cross-platform-runtime
"""

import json

import yaml

from ccai.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from ccai.agentkit.platform.platformtype import PlatformType


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _create_sample_descriptor() -> DeploymentDescriptor:
    """
        Creates a sample DeploymentDescriptor for testing.

        :returns: A DeploymentDescriptor instance with known test values.
    """
    descriptor = DeploymentDescriptor(
        name="my-agent-deploy",
        target_platform=PlatformType.AWS,
        compute_config={"memory": 512, "timeout": 60},
        storage_config={"bucket": "my-bucket"},
        messaging_config={"queue_prefix": "agent-"},
        environment_variables={"ENV": "production", "LOG_LEVEL": "INFO"},
        scaling_parameters={"min_instances": 1, "max_instances": 10}
    )
    return descriptor


# ---------------------------------------------------------------------------
# Read-only property tests
# ---------------------------------------------------------------------------

def test_name_property_returns_correct_value():
    """
        Verify that the name property returns the name passed at construction.
    """
    descriptor = _create_sample_descriptor()

    actual = descriptor.name

    assert actual == "my-agent-deploy", (
        "name should be 'my-agent-deploy', got: {!r}".format(actual)
    )
    return


def test_target_platform_property_returns_correct_value():
    """
        Verify that the target_platform property returns the PlatformType
        passed at construction.
    """
    descriptor = _create_sample_descriptor()

    actual = descriptor.target_platform

    assert actual == PlatformType.AWS, (
        "target_platform should be PlatformType.AWS, got: {!r}".format(actual)
    )
    return


def test_compute_config_property_returns_defensive_copy():
    """
        Verify that the compute_config property returns a copy and modifying
        it does not affect the internal state.
    """
    descriptor = _create_sample_descriptor()

    config_copy = descriptor.compute_config
    config_copy["injected"] = "bad-value"

    original = descriptor.compute_config
    has_injected = "injected" in original

    assert has_injected is False, (
        "Modifying returned compute_config should not affect internal state"
    )
    return


def test_storage_config_property_returns_correct_value():
    """
        Verify that the storage_config property returns the value passed
        at construction.
    """
    descriptor = _create_sample_descriptor()

    actual = descriptor.storage_config

    assert actual == {"bucket": "my-bucket"}, (
        "storage_config should be {{'bucket': 'my-bucket'}}, got: {!r}".format(actual)
    )
    return


def test_messaging_config_property_returns_correct_value():
    """
        Verify that the messaging_config property returns the value passed
        at construction.
    """
    descriptor = _create_sample_descriptor()

    actual = descriptor.messaging_config

    assert actual == {"queue_prefix": "agent-"}, (
        "messaging_config should be {{'queue_prefix': 'agent-'}}, got: {!r}".format(actual)
    )
    return


def test_environment_variables_property_returns_correct_value():
    """
        Verify that the environment_variables property returns the value
        passed at construction.
    """
    descriptor = _create_sample_descriptor()

    actual = descriptor.environment_variables

    expected = {"ENV": "production", "LOG_LEVEL": "INFO"}
    assert actual == expected, (
        "environment_variables mismatch, got: {!r}".format(actual)
    )
    return


def test_scaling_parameters_property_returns_correct_value():
    """
        Verify that the scaling_parameters property returns the value
        passed at construction.
    """
    descriptor = _create_sample_descriptor()

    actual = descriptor.scaling_parameters

    expected = {"min_instances": 1, "max_instances": 10}
    assert actual == expected, (
        "scaling_parameters mismatch, got: {!r}".format(actual)
    )
    return


def test_none_optional_fields_default_to_empty_dicts():
    """
        Verify that passing None for optional fields results in empty
        dictionaries.
    """
    descriptor = DeploymentDescriptor(
        name="minimal",
        target_platform=PlatformType.LOCAL
    )

    assert descriptor.compute_config == {}, (
        "None compute_config should default to empty dict"
    )
    assert descriptor.storage_config == {}, (
        "None storage_config should default to empty dict"
    )
    assert descriptor.messaging_config == {}, (
        "None messaging_config should default to empty dict"
    )
    assert descriptor.environment_variables == {}, (
        "None environment_variables should default to empty dict"
    )
    assert descriptor.scaling_parameters == {}, (
        "None scaling_parameters should default to empty dict"
    )
    return


# ---------------------------------------------------------------------------
# as_dict tests
# ---------------------------------------------------------------------------

def test_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all expected keys.
    """
    descriptor = _create_sample_descriptor()

    result = descriptor.as_dict()

    expected_keys = {
        "name", "target_platform", "compute_config", "storage_config",
        "messaging_config", "environment_variables", "scaling_parameters"
    }
    actual_keys = set(result.keys())

    assert actual_keys == expected_keys, (
        "as_dict should contain keys {}, got: {}".format(expected_keys, actual_keys)
    )
    return


def test_as_dict_target_platform_is_lowercase_string():
    """
        Verify that as_dict serializes target_platform as a lowercase string.
    """
    descriptor = _create_sample_descriptor()

    result = descriptor.as_dict()

    actual = result["target_platform"]

    assert actual == "aws", (
        "target_platform should be 'aws', got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# JSON round-trip tests
# ---------------------------------------------------------------------------

def test_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    descriptor = _create_sample_descriptor()

    json_str = descriptor.to_json()
    parsed = json.loads(json_str)

    has_name = "name" in parsed
    assert has_name is True, "JSON should contain 'name' field"
    return


def test_json_round_trip_preserves_all_fields():
    """
        Verify that serializing to JSON and deserializing back produces
        an equivalent DeploymentDescriptor.
    """
    original = _create_sample_descriptor()

    json_str = original.to_json()
    restored = DeploymentDescriptor.from_json(json_str)

    assert restored.name == original.name, (
        "Round-trip name mismatch: {!r} != {!r}".format(restored.name, original.name)
    )
    assert restored.target_platform == original.target_platform, (
        "Round-trip target_platform mismatch: {!r} != {!r}".format(
            restored.target_platform, original.target_platform)
    )
    assert restored.compute_config == original.compute_config, (
        "Round-trip compute_config mismatch: {!r} != {!r}".format(
            restored.compute_config, original.compute_config)
    )
    assert restored.storage_config == original.storage_config, (
        "Round-trip storage_config mismatch: {!r} != {!r}".format(
            restored.storage_config, original.storage_config)
    )
    assert restored.messaging_config == original.messaging_config, (
        "Round-trip messaging_config mismatch: {!r} != {!r}".format(
            restored.messaging_config, original.messaging_config)
    )
    assert restored.environment_variables == original.environment_variables, (
        "Round-trip environment_variables mismatch: {!r} != {!r}".format(
            restored.environment_variables, original.environment_variables)
    )
    assert restored.scaling_parameters == original.scaling_parameters, (
        "Round-trip scaling_parameters mismatch: {!r} != {!r}".format(
            restored.scaling_parameters, original.scaling_parameters)
    )
    return


# ---------------------------------------------------------------------------
# YAML round-trip tests
# ---------------------------------------------------------------------------

def test_to_yaml_produces_valid_yaml():
    """
        Verify that to_yaml returns a valid YAML string.
    """
    descriptor = _create_sample_descriptor()

    yaml_str = descriptor.to_yaml()
    parsed = yaml.safe_load(yaml_str)

    has_name = "name" in parsed
    assert has_name is True, "YAML should contain 'name' field"
    return


def test_yaml_round_trip_preserves_all_fields():
    """
        Verify that serializing to YAML and deserializing back produces
        an equivalent DeploymentDescriptor.
    """
    original = _create_sample_descriptor()

    yaml_str = original.to_yaml()
    restored = DeploymentDescriptor.from_yaml(yaml_str)

    assert restored.name == original.name, (
        "Round-trip name mismatch: {!r} != {!r}".format(restored.name, original.name)
    )
    assert restored.target_platform == original.target_platform, (
        "Round-trip target_platform mismatch: {!r} != {!r}".format(
            restored.target_platform, original.target_platform)
    )
    assert restored.compute_config == original.compute_config, (
        "Round-trip compute_config mismatch"
    )
    assert restored.storage_config == original.storage_config, (
        "Round-trip storage_config mismatch"
    )
    assert restored.messaging_config == original.messaging_config, (
        "Round-trip messaging_config mismatch"
    )
    assert restored.environment_variables == original.environment_variables, (
        "Round-trip environment_variables mismatch"
    )
    assert restored.scaling_parameters == original.scaling_parameters, (
        "Round-trip scaling_parameters mismatch"
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_contains_class_name_and_name_and_platform():
    """
        Verify that __repr__ includes the class name, descriptor name,
        and target platform type.
    """
    descriptor = _create_sample_descriptor()

    repr_str = repr(descriptor)

    has_class_name = "DeploymentDescriptor" in repr_str
    has_name = "my-agent-deploy" in repr_str
    has_platform = "aws" in repr_str

    assert has_class_name is True, "repr should contain 'DeploymentDescriptor'"
    assert has_name is True, "repr should contain the descriptor name"
    assert has_platform is True, "repr should contain the platform type"
    return


def test_str_contains_name_platform_and_scaling():
    """
        Verify that __str__ returns a human-readable summary with name,
        platform type, and scaling parameters.
    """
    descriptor = _create_sample_descriptor()

    str_val = str(descriptor)

    has_name = "my-agent-deploy" in str_val
    has_platform = "aws" in str_val
    has_scaling = "min_instances" in str_val

    assert has_name is True, "str should contain the descriptor name"
    assert has_platform is True, "str should contain the platform type"
    assert has_scaling is True, "str should contain scaling parameters"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
