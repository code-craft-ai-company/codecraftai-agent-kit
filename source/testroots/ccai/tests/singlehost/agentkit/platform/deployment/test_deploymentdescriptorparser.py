"""
    Tests for the ccai.agentkit.platform.deployment.deploymentdescriptorparser module.

    Contains unit tests for the DeploymentDescriptorParser including
    parse_json, parse_yaml, parse_file with various extensions, missing
    required fields, and unrecognized extensions.

    Feature: cross-platform-runtime
"""

import json
import os
import tempfile

import yaml

from ccai.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from ccai.agentkit.platform.deployment.deploymentdescriptorparser import DeploymentDescriptorParser
from ccai.agentkit.platform.errors import DeploymentDescriptorError
from ccai.agentkit.platform.platformtype import PlatformType


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _create_valid_descriptor_dict() -> dict:
    """
        Creates a valid descriptor dictionary for testing.

        :returns: A dictionary with all required and optional fields.
    """
    data = {
        "name": "test-deploy",
        "target_platform": "aws",
        "compute_config": {"memory": 256},
        "storage_config": {"bucket": "test-bucket"},
        "messaging_config": {},
        "environment_variables": {"KEY": "value"},
        "scaling_parameters": {"min_instances": 1}
    }
    return data


# ---------------------------------------------------------------------------
# parse_json tests
# ---------------------------------------------------------------------------

def test_parse_json_with_valid_data():
    """
        Verify that parse_json returns a DeploymentDescriptor from valid JSON.
    """
    parser = DeploymentDescriptorParser()
    data = _create_valid_descriptor_dict()
    json_str = json.dumps(data)

    result = parser.parse_json(json_str)

    assert result.name == "test-deploy", (
        "name should be 'test-deploy', got: {!r}".format(result.name)
    )
    assert result.target_platform == PlatformType.AWS, (
        "target_platform should be AWS, got: {!r}".format(result.target_platform)
    )
    return


def test_parse_json_missing_name_raises_error():
    """
        Verify that parse_json raises DeploymentDescriptorError when the
        name field is missing.
    """
    parser = DeploymentDescriptorParser()
    data = {"target_platform": "aws"}
    json_str = json.dumps(data)

    caught = False
    try:
        parser.parse_json(json_str)
    except DeploymentDescriptorError:
        caught = True

    assert caught is True, (
        "parse_json should raise DeploymentDescriptorError for missing 'name'"
    )
    return


def test_parse_json_missing_target_platform_raises_error():
    """
        Verify that parse_json raises DeploymentDescriptorError when the
        target_platform field is missing.
    """
    parser = DeploymentDescriptorParser()
    data = {"name": "test-deploy"}
    json_str = json.dumps(data)

    caught = False
    try:
        parser.parse_json(json_str)
    except DeploymentDescriptorError:
        caught = True

    assert caught is True, (
        "parse_json should raise DeploymentDescriptorError for missing 'target_platform'"
    )
    return


# ---------------------------------------------------------------------------
# parse_yaml tests
# ---------------------------------------------------------------------------

def test_parse_yaml_with_valid_data():
    """
        Verify that parse_yaml returns a DeploymentDescriptor from valid YAML.
    """
    parser = DeploymentDescriptorParser()
    data = _create_valid_descriptor_dict()
    yaml_str = yaml.dump(data, default_flow_style=False)

    result = parser.parse_yaml(yaml_str)

    assert result.name == "test-deploy", (
        "name should be 'test-deploy', got: {!r}".format(result.name)
    )
    assert result.target_platform == PlatformType.AWS, (
        "target_platform should be AWS, got: {!r}".format(result.target_platform)
    )
    return


def test_parse_yaml_missing_required_field_raises_error():
    """
        Verify that parse_yaml raises DeploymentDescriptorError when a
        required field is missing.
    """
    parser = DeploymentDescriptorParser()
    yaml_str = yaml.dump({"name": "test-deploy"}, default_flow_style=False)

    caught = False
    try:
        parser.parse_yaml(yaml_str)
    except DeploymentDescriptorError:
        caught = True

    assert caught is True, (
        "parse_yaml should raise DeploymentDescriptorError for missing required field"
    )
    return


# ---------------------------------------------------------------------------
# parse_file tests
# ---------------------------------------------------------------------------

def test_parse_file_with_json_extension():
    """
        Verify that parse_file correctly parses a .json file.
    """
    parser = DeploymentDescriptorParser()
    data = _create_valid_descriptor_dict()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name

    try:
        result = parser.parse_file(tmp_path)

        assert result.name == "test-deploy", (
            "name should be 'test-deploy', got: {!r}".format(result.name)
        )
    finally:
        os.unlink(tmp_path)

    return


def test_parse_file_with_yaml_extension():
    """
        Verify that parse_file correctly parses a .yaml file.
    """
    parser = DeploymentDescriptorParser()
    data = _create_valid_descriptor_dict()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        yaml.dump(data, tmp, default_flow_style=False)
        tmp_path = tmp.name

    try:
        result = parser.parse_file(tmp_path)

        assert result.name == "test-deploy", (
            "name should be 'test-deploy', got: {!r}".format(result.name)
        )
    finally:
        os.unlink(tmp_path)

    return


def test_parse_file_with_yml_extension():
    """
        Verify that parse_file correctly parses a .yml file.
    """
    parser = DeploymentDescriptorParser()
    data = _create_valid_descriptor_dict()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
        yaml.dump(data, tmp, default_flow_style=False)
        tmp_path = tmp.name

    try:
        result = parser.parse_file(tmp_path)

        assert result.name == "test-deploy", (
            "name should be 'test-deploy', got: {!r}".format(result.name)
        )
    finally:
        os.unlink(tmp_path)

    return


def test_parse_file_unrecognized_extension_raises_error():
    """
        Verify that parse_file raises DeploymentDescriptorError for an
        unrecognized file extension.
    """
    parser = DeploymentDescriptorParser()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp.write("some content")
        tmp_path = tmp.name

    caught = False
    try:
        parser.parse_file(tmp_path)
    except DeploymentDescriptorError:
        caught = True
    finally:
        os.unlink(tmp_path)

    assert caught is True, (
        "parse_file should raise DeploymentDescriptorError for .txt extension"
    )
    return


def test_parse_file_with_app_context_resolves_path():
    """
        Verify that parse_file resolves the file path relative to the
        AppContext directory when provided.
    """
    from ccai.testbase.mocking import Mock

    parser = DeploymentDescriptorParser()
    data = _create_valid_descriptor_dict()

    tmp_dir = tempfile.mkdtemp()
    file_name = "deploy.json"
    full_path = os.path.join(tmp_dir, file_name)

    with open(full_path, "w") as fh:
        json.dump(data, fh)

    mock_app_context = Mock()
    mock_app_context.configure(recursive=True)
    ctx = mock_app_context.mock_context()
    ctx.set_attribute("directory", tmp_dir)

    try:
        result = parser.parse_file(file_name, app_context=mock_app_context)

        assert result.name == "test-deploy", (
            "name should be 'test-deploy', got: {!r}".format(result.name)
        )
    finally:
        os.unlink(full_path)
        os.rmdir(tmp_dir)

    return


# ---------------------------------------------------------------------------
# __repr__ test
# ---------------------------------------------------------------------------

def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    parser = DeploymentDescriptorParser()

    repr_str = repr(parser)

    has_class_name = "DeploymentDescriptorParser" in repr_str
    assert has_class_name is True, "repr should contain 'DeploymentDescriptorParser'"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
