"""
    Unit tests for the automojo.agentkit.pluginstatus module.

    Tests that all six PluginStatus enum values exist and have
    the expected string values, and that the from_string class method works
    correctly for valid and invalid inputs.
"""

import enum

from automojo.agentkit.pluginstatus import PluginStatus
from automojo.agentkit.errors import SemanticError


def test_pluginstatus_is_enum():
    """
        Verify that PluginStatus is an Enum class.
    """
    is_enum = issubclass(PluginStatus, enum.Enum)
    assert is_enum is True, "PluginStatus should be an Enum"
    return


def test_pluginstatus_has_discovered():
    """
        Verify that the DISCOVERED member exists with value 'DISCOVERED'.
    """
    status = PluginStatus.DISCOVERED
    assert status.value == "DISCOVERED", "DISCOVERED member should have value 'DISCOVERED'"
    return


def test_pluginstatus_has_loading():
    """
        Verify that the LOADING member exists with value 'LOADING'.
    """
    status = PluginStatus.LOADING
    assert status.value == "LOADING", "LOADING member should have value 'LOADING'"
    return


def test_pluginstatus_has_loaded():
    """
        Verify that the LOADED member exists with value 'LOADED'.
    """
    status = PluginStatus.LOADED
    assert status.value == "LOADED", "LOADED member should have value 'LOADED'"
    return


def test_pluginstatus_has_active():
    """
        Verify that the ACTIVE member exists with value 'ACTIVE'.
    """
    status = PluginStatus.ACTIVE
    assert status.value == "ACTIVE", "ACTIVE member should have value 'ACTIVE'"
    return


def test_pluginstatus_has_failed():
    """
        Verify that the FAILED member exists with value 'FAILED'.
    """
    status = PluginStatus.FAILED
    assert status.value == "FAILED", "FAILED member should have value 'FAILED'"
    return


def test_pluginstatus_has_disabled():
    """
        Verify that the DISABLED member exists with value 'DISABLED'.
    """
    status = PluginStatus.DISABLED
    assert status.value == "DISABLED", "DISABLED member should have value 'DISABLED'"
    return


def test_pluginstatus_has_exactly_six_members():
    """
        Verify that PluginStatus has exactly six members.
    """
    member_count = len(PluginStatus)
    assert member_count == 6, "PluginStatus should have exactly 6 members, got {}".format(member_count)
    return


def test_pluginstatus_members_are_correct_set():
    """
        Verify that the set of member names matches the expected set.
    """
    expected_names = {"DISCOVERED", "LOADING", "LOADED", "ACTIVE", "FAILED", "DISABLED"}
    actual_names = {member.name for member in PluginStatus}
    assert actual_names == expected_names, "PluginStatus members should be {}".format(expected_names)
    return


def test_from_string_discovered():
    """
        Verify that from_string returns DISCOVERED for 'DISCOVERED'.
    """
    result = PluginStatus.from_string("DISCOVERED")
    assert result is PluginStatus.DISCOVERED, "from_string('DISCOVERED') should return DISCOVERED"
    return


def test_from_string_loading():
    """
        Verify that from_string returns LOADING for 'LOADING'.
    """
    result = PluginStatus.from_string("LOADING")
    assert result is PluginStatus.LOADING, "from_string('LOADING') should return LOADING"
    return


def test_from_string_loaded():
    """
        Verify that from_string returns LOADED for 'LOADED'.
    """
    result = PluginStatus.from_string("LOADED")
    assert result is PluginStatus.LOADED, "from_string('LOADED') should return LOADED"
    return


def test_from_string_active():
    """
        Verify that from_string returns ACTIVE for 'ACTIVE'.
    """
    result = PluginStatus.from_string("ACTIVE")
    assert result is PluginStatus.ACTIVE, "from_string('ACTIVE') should return ACTIVE"
    return


def test_from_string_failed():
    """
        Verify that from_string returns FAILED for 'FAILED'.
    """
    result = PluginStatus.from_string("FAILED")
    assert result is PluginStatus.FAILED, "from_string('FAILED') should return FAILED"
    return


def test_from_string_disabled():
    """
        Verify that from_string returns DISABLED for 'DISABLED'.
    """
    result = PluginStatus.from_string("DISABLED")
    assert result is PluginStatus.DISABLED, "from_string('DISABLED') should return DISABLED"
    return


def test_from_string_lowercase_input():
    """
        Verify that from_string handles lowercase input by converting to uppercase.
    """
    result = PluginStatus.from_string("discovered")
    assert result is PluginStatus.DISCOVERED, "from_string('discovered') should return DISCOVERED"
    return


def test_from_string_mixed_case_input():
    """
        Verify that from_string handles mixed case input by converting to uppercase.
    """
    result = PluginStatus.from_string("Active")
    assert result is PluginStatus.ACTIVE, "from_string('Active') should return ACTIVE"
    return


def test_from_string_invalid_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an invalid string value.
    """
    raised = False
    error_message = ""

    try:
        PluginStatus.from_string("INVALID")
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
        PluginStatus.from_string("BOGUS")
    except SemanticError as err:
        error_message = str(err)

    contains_discovered = "DISCOVERED" in error_message
    contains_loading = "LOADING" in error_message
    contains_loaded = "LOADED" in error_message
    contains_active = "ACTIVE" in error_message
    contains_failed = "FAILED" in error_message
    contains_disabled = "DISABLED" in error_message

    assert contains_discovered is True, "Error message should list DISCOVERED as a valid value"
    assert contains_loading is True, "Error message should list LOADING as a valid value"
    assert contains_loaded is True, "Error message should list LOADED as a valid value"
    assert contains_active is True, "Error message should list ACTIVE as a valid value"
    assert contains_failed is True, "Error message should list FAILED as a valid value"
    assert contains_disabled is True, "Error message should list DISABLED as a valid value"
    return


def test_from_string_empty_string_raises_semantic_error():
    """
        Verify that from_string raises SemanticError for an empty string.
    """
    raised = False

    try:
        PluginStatus.from_string("")
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
        PluginStatus.from_string("NOT_A_STATUS")
    except SemanticError as err:
        caught_exception = err

    is_semantic_error = isinstance(caught_exception, SemanticError)
    assert is_semantic_error is True, "Exception should be an instance of SemanticError"
    return
