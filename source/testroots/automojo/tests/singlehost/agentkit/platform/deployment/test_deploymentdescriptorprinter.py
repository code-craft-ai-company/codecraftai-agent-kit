"""
    Tests for the automojo.agentkit.platform.deployment.deploymentdescriptorprinter module.

    Contains unit tests for the DeploymentDescriptorPrinter including
    print_json, print_yaml, print_file with various extensions,
    unrecognized extensions, and round-trip with the parser.

    Feature: cross-platform-runtime
"""

import json
import os
import tempfile

import yaml

from automojo.agentkit.platform.deployment.deploymentdescriptor import DeploymentDescriptor
from automojo.agentkit.platform.deployment.deploymentdescriptorparser import DeploymentDescriptorParser
from automojo.agentkit.platform.deployment.deploymentdescriptorprinter import DeploymentDescriptorPrinter
from automojo.agentkit.platform.errors import DeploymentDescriptorError
from automojo.agentkit.platform.platformtype import PlatformType


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _create_sample_descriptor() -> DeploymentDescriptor:
    """
        Creates a sample DeploymentDescriptor for testing.

        :returns: A DeploymentDescriptor instance with known test values.
    """
    descriptor = DeploymentDescriptor(
        name="printer-test",
        target_platform=PlatformType.GCP,
        compute_config={"runtime": "python39"},
        storage_config={"bucket": "gcp-bucket"},
        messaging_config={"topic": "agent-events"},
        environment_variables={"REGION": "us-central1"},
        scaling_parameters={"max_instances": 5}
    )
    return descriptor


# ---------------------------------------------------------------------------
# print_json tests
# ---------------------------------------------------------------------------

def test_print_json_returns_valid_json():
    """
        Verify that print_json returns a valid JSON string.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    json_str = printer.print_json(descriptor)
    parsed = json.loads(json_str)

    has_name = "name" in parsed
    assert has_name is True, "print_json output should contain 'name' field"
    return


def test_print_json_contains_correct_name():
    """
        Verify that print_json output contains the correct descriptor name.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    json_str = printer.print_json(descriptor)
    parsed = json.loads(json_str)

    actual = parsed["name"]
    assert actual == "printer-test", (
        "name should be 'printer-test', got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# print_yaml tests
# ---------------------------------------------------------------------------

def test_print_yaml_returns_valid_yaml():
    """
        Verify that print_yaml returns a valid YAML string.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    yaml_str = printer.print_yaml(descriptor)
    parsed = yaml.safe_load(yaml_str)

    has_name = "name" in parsed
    assert has_name is True, "print_yaml output should contain 'name' field"
    return


def test_print_yaml_contains_correct_platform():
    """
        Verify that print_yaml output contains the correct target platform.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    yaml_str = printer.print_yaml(descriptor)
    parsed = yaml.safe_load(yaml_str)

    actual = parsed["target_platform"]
    assert actual == "gcp", (
        "target_platform should be 'gcp', got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# print_file tests
# ---------------------------------------------------------------------------

def test_print_file_writes_json_file():
    """
        Verify that print_file writes a valid JSON file for .json extension.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        printer.print_file(descriptor, tmp_path)

        with open(tmp_path, "r") as fh:
            content = fh.read()
        parsed = json.loads(content)

        assert parsed["name"] == "printer-test", (
            "Written JSON should contain name 'printer-test'"
        )
    finally:
        os.unlink(tmp_path)

    return


def test_print_file_writes_yaml_file():
    """
        Verify that print_file writes a valid YAML file for .yaml extension.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        printer.print_file(descriptor, tmp_path)

        with open(tmp_path, "r") as fh:
            content = fh.read()
        parsed = yaml.safe_load(content)

        assert parsed["name"] == "printer-test", (
            "Written YAML should contain name 'printer-test'"
        )
    finally:
        os.unlink(tmp_path)

    return


def test_print_file_writes_yml_file():
    """
        Verify that print_file writes a valid YAML file for .yml extension.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        printer.print_file(descriptor, tmp_path)

        with open(tmp_path, "r") as fh:
            content = fh.read()
        parsed = yaml.safe_load(content)

        assert parsed["name"] == "printer-test", (
            "Written YML should contain name 'printer-test'"
        )
    finally:
        os.unlink(tmp_path)

    return


def test_print_file_unrecognized_extension_raises_error():
    """
        Verify that print_file raises DeploymentDescriptorError for an
        unrecognized file extension.
    """
    printer = DeploymentDescriptorPrinter()
    descriptor = _create_sample_descriptor()

    caught = False
    try:
        printer.print_file(descriptor, "/tmp/deploy.xml")
    except DeploymentDescriptorError:
        caught = True

    assert caught is True, (
        "print_file should raise DeploymentDescriptorError for .xml extension"
    )
    return


# ---------------------------------------------------------------------------
# Round-trip tests (printer -> parser)
# ---------------------------------------------------------------------------

def test_round_trip_json_printer_to_parser():
    """
        Verify that printing to JSON and parsing back produces an equivalent
        DeploymentDescriptor.
    """
    printer = DeploymentDescriptorPrinter()
    parser = DeploymentDescriptorParser()
    original = _create_sample_descriptor()

    json_str = printer.print_json(original)
    restored = parser.parse_json(json_str)

    assert restored.name == original.name, (
        "Round-trip name mismatch: {!r} != {!r}".format(restored.name, original.name)
    )
    assert restored.target_platform == original.target_platform, (
        "Round-trip target_platform mismatch"
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


def test_round_trip_yaml_printer_to_parser():
    """
        Verify that printing to YAML and parsing back produces an equivalent
        DeploymentDescriptor.
    """
    printer = DeploymentDescriptorPrinter()
    parser = DeploymentDescriptorParser()
    original = _create_sample_descriptor()

    yaml_str = printer.print_yaml(original)
    restored = parser.parse_yaml(yaml_str)

    assert restored.name == original.name, (
        "Round-trip name mismatch: {!r} != {!r}".format(restored.name, original.name)
    )
    assert restored.target_platform == original.target_platform, (
        "Round-trip target_platform mismatch"
    )
    assert restored.compute_config == original.compute_config, (
        "Round-trip compute_config mismatch"
    )
    assert restored.scaling_parameters == original.scaling_parameters, (
        "Round-trip scaling_parameters mismatch"
    )
    return


# ---------------------------------------------------------------------------
# __repr__ test
# ---------------------------------------------------------------------------

def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name.
    """
    printer = DeploymentDescriptorPrinter()

    repr_str = repr(printer)

    has_class_name = "DeploymentDescriptorPrinter" in repr_str
    assert has_class_name is True, "repr should contain 'DeploymentDescriptorPrinter'"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
