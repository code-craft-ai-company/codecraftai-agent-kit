"""
    Unit tests for the automojo.agentkit.configurationlayersource module.

    Tests that all five ConfigurationLayerSource enum values exist and have
    the expected string values, and that the from_string class method works
    correctly for valid and invalid inputs.
"""

import enum

from automojo.agentkit.configurationlayersource import ConfigurationLayerSource
from automojo.agentkit.errors import SemanticError


def test_configurationlayersource_is_enum():
    """
        Verify that ConfigurationLayerSource is an Enum class.
    """
    is_enum = issubclass(ConfigurationLayerSource, enum.Enum)
    assert is_enum is True, "ConfigurationLayerSource should be an Enum"
    return


def test_configurationlayersource_has_defaults():
    """
        Verify that the DEFAULTS member exists with value 'DEFAULTS'.
    """
    source = ConfigurationLayerSource.DEFAULTS
    assert source.value == "DEFAULTS", "DEFAULTS member should have value 'DEFAULTS'"
    return


def test_configurationlayersource_has_file():
    """
        Verify that the FILE member exists with value 'FILE'.
    """
    source = ConfigurationLayerSource.FILE
    assert source.value == "FILE", "FILE member should have value 'FILE'"
    return


def test_configurationlayersource_has_environment():
    """
        Verify that the ENVIRONMENT member exists with value 'ENVIRONMENT'.
    """
    source = ConfigurationLayerSource.ENVIRONMENT
    assert source.value == "ENVIRONMENT", "ENVIRONMENT member should have value 'ENVIRONMENT'"
    return


def test_configurationlayersource_has_runtime():
    """
        Verify that the RUNTIME member exists with value 'RUNTIME'.
    """
    source = ConfigurationLayerSource.RUNTIME
    assert source.value == "RUNTIME", "RUNTIME member should have value 'RUNTIME'"
    return


def test_configurationlayersource_has_override():
    """
        Verify that the OVERRIDE member exists with value 'OVERRIDE'.
    """
    source = ConfigurationLayerSource.OVERRIDE
    assert source.value == "OVERRIDE", "OVERRIDE member should have value 'OVERRIDE'"
    return


def test_configurationlayersource_has_exactly_five_members():
    """
        Verify that ConfigurationLayerSource has exactly five members.
    """
    member_count = len(ConfigurationLayerSource)
    assert member_count == 5, "ConfigurationLayerSource should have exactly 5 members, got {}".format(member_count)
    return


def test_configurationlayersource_members_are_correct_set():
    """
        Verify that the set of member names matches the expected set.
    """
    expected_names = {"DEFAULTS", "FILE", "ENVIRONMENT", "RUNTIME", "OVERRIDE"}
    actual_names = {member.name for member in ConfigurationLayerSource}
    assert actual_names == expected_names, "ConfigurationLayerSource members should be {}".format(expected_names)
    return


def test_from_string_defaults():
    """
        Verify that from_string returns DEFAULTS for 'DEFAULTS'.
    """
    result = ConfigurationLayerSource.from_string("DEFAULTS")
    assert result is ConfigurationLayerSource.DEFAULTS, "from_string('DEFAULTS') should return DEFAULTS"
    return


def test_from_string_file():
    """
        Verify that from_string returns FILE for 'FILE'.
    """
    result = ConfigurationLayerSource.from_string("FILE")
    assert result is ConfigurationLayerSource.FILE, "from_string('FILE') should return FILE"
    return


def test_from_string_environment():
    """
        Verify that from_string returns ENVIRONMENT for 'ENVIRONMENT'.
    """
    result = ConfigurationLayerSource.from_string("ENVIRONMENT")
    assert result is ConfigurationLayerSource.ENVIRONMENT, "from_string('ENVIRONMENT') should return ENVIRONMENT"
    return


def test_from_string_runtime():
    """
        Verify that from_string returns RUNTIME for 'RUNTIME'.
    """
    result = ConfigurationLayerSource.from_string("RUNTIME")
    assert result is ConfigurationLayerSource.RUNTIME, "from_string('RUNTIME') should return RUNTIME"
    return


def test_from_string_override():
    """
        Verify that from_string returns OVERRIDE for 'OVERRIDE'.
    """
    result = ConfigurationLayerSource.from_string("OVERRIDE")
    assert result is ConfigurationLayerSource.OVERRIDE, "from_string('OVERRIDE') should return OVERRIDE"
    return


def test_from_string_lowercase_input():
    """
        Verify that from_string handles lowercase input by converting to uppercase.
    """
    result = ConfigurationLayerSource.from_string("defaults")
    assert result is ConfigurationLayerSource.DEFAULTS, "from_string('defaults') should return DEFAULTS"
    return


def test_from_string_mixed_case_input():
    """
        Verify that from_string handles mixed case input by converting to uppercase.
    """
    result = ConfigurationLayerSource.from_string("Runtime")
    assert result is ConfigurationLayerSource.RUNTIME, "from_string('Runtime') should return RUNTIME"
    return


def test_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an invalid string value.
    """
    raised = False
    error_message = ""

    try:
        ConfigurationLayerSource.from_string("INVALID")
    except SemanticError as err:
        raised = True
        error_message = str(err)

    assert raised is True, "from_string('INVALID') should raise SemanticError"
    contains_invalid = "INVALID" in error_message
    assert contains_invalid is True, "Error message should contain the invalid value 'INVALID'"
    return


def test_from_string_invalid_error_lists_valid_values():
    """
        Verify that the SemanticError message for an invalid value lists all valid values.
    """
    error_message = ""

    try:
        ConfigurationLayerSource.from_string("BOGUS")
    except SemanticError as err:
        error_message = str(err)

    contains_defaults = "DEFAULTS" in error_message
    contains_file = "FILE" in error_message
    contains_environment = "ENVIRONMENT" in error_message
    contains_runtime = "RUNTIME" in error_message
    contains_override = "OVERRIDE" in error_message

    assert contains_defaults is True, "Error message should list DEFAULTS as a valid value"
    assert contains_file is True, "Error message should list FILE as a valid value"
    assert contains_environment is True, "Error message should list ENVIRONMENT as a valid value"
    assert contains_runtime is True, "Error message should list RUNTIME as a valid value"
    assert contains_override is True, "Error message should list OVERRIDE as a valid value"
    return


def test_from_string_empty_string_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an empty string.
    """
    raised = False

    try:
        ConfigurationLayerSource.from_string("")
    except SemanticError:
        raised = True

    assert raised is True, "from_string('') should raise SemanticError"
    return


def test_from_string_error_is_semantic_error_type():
    """
        Verify that the exception raised by from_string for invalid input
        is specifically a SemanticError instance.
    """
    caught_exception = None

    try:
        ConfigurationLayerSource.from_string("NOT_A_SOURCE")
    except SemanticError as err:
        caught_exception = err

    is_semantic_error = isinstance(caught_exception, SemanticError)
    assert is_semantic_error is True, "Exception should be an instance of SemanticError"
    return
