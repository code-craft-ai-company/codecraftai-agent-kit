"""
    Unit tests for the ccai.agentkit.configurationvalidationresult module.

    Tests the ConfigurationValidationResult immutable data type including constructor,
    read-only properties, is_valid logic, as_dict serialization, defensive copies,
    and string representations.
"""

from ccai.agentkit.configurationvalidationresult import ConfigurationValidationResult


# ---- Constructor and Property Tests ----


def test_valid_property_returns_true_when_constructed_with_true():
    """
        Verify that the valid property returns True when constructed with valid=True.
    """
    result = ConfigurationValidationResult(valid=True)
    stored_valid = result.valid
    assert stored_valid is True, "valid property should return True when constructed with valid=True"
    return


def test_valid_property_returns_false_when_constructed_with_false():
    """
        Verify that the valid property returns False when constructed with valid=False.
    """
    result = ConfigurationValidationResult(valid=False)
    stored_valid = result.valid
    assert stored_valid is False, "valid property should return False when constructed with valid=False"
    return


def test_errors_property_returns_list_of_errors():
    """
        Verify that the errors property returns the list of error strings.
    """
    error_list = ["field 'name' is required", "field 'port' has invalid type"]
    result = ConfigurationValidationResult(valid=False, errors=error_list)
    stored_errors = result.errors
    assert stored_errors == ["field 'name' is required", "field 'port' has invalid type"], \
        "errors property should return the list of error strings"
    return


def test_warnings_property_returns_list_of_warnings():
    """
        Verify that the warnings property returns the list of warning strings.
    """
    warning_list = ["field 'timeout' uses deprecated default"]
    result = ConfigurationValidationResult(valid=True, warnings=warning_list)
    stored_warnings = result.warnings
    assert stored_warnings == ["field 'timeout' uses deprecated default"], \
        "warnings property should return the list of warning strings"
    return


def test_errors_defaults_to_empty_list_when_none():
    """
        Verify that errors defaults to an empty list when None is passed.
    """
    result = ConfigurationValidationResult(valid=True, errors=None)
    stored_errors = result.errors
    assert stored_errors == [], "errors should default to an empty list when None is passed"
    return


def test_warnings_defaults_to_empty_list_when_none():
    """
        Verify that warnings defaults to an empty list when None is passed.
    """
    result = ConfigurationValidationResult(valid=True, warnings=None)
    stored_warnings = result.warnings
    assert stored_warnings == [], "warnings should default to an empty list when None is passed"
    return


# ---- is_valid Property Tests ----


def test_is_valid_returns_true_when_valid_true_and_errors_empty():
    """
        Verify that is_valid returns True when valid=True and errors is empty.
    """
    result = ConfigurationValidationResult(valid=True, errors=[])
    is_valid_value = result.is_valid
    assert is_valid_value is True, \
        "is_valid should return True when valid=True and errors is empty"
    return


def test_is_valid_returns_false_when_valid_true_but_errors_non_empty():
    """
        Verify that is_valid returns False when valid=True but errors is non-empty.
    """
    result = ConfigurationValidationResult(
        valid=True,
        errors=["field 'host' has invalid type"]
    )
    is_valid_value = result.is_valid
    assert is_valid_value is False, \
        "is_valid should return False when valid=True but errors is non-empty"
    return


def test_is_valid_returns_false_when_valid_false_and_errors_empty():
    """
        Verify that is_valid returns False when valid=False and errors is empty.
    """
    result = ConfigurationValidationResult(valid=False, errors=[])
    is_valid_value = result.is_valid
    assert is_valid_value is False, \
        "is_valid should return False when valid=False and errors is empty"
    return


def test_is_valid_returns_false_when_valid_false_and_errors_non_empty():
    """
        Verify that is_valid returns False when valid=False and errors is non-empty.
    """
    result = ConfigurationValidationResult(
        valid=False,
        errors=["missing required field 'name'"]
    )
    is_valid_value = result.is_valid
    assert is_valid_value is False, \
        "is_valid should return False when valid=False and errors is non-empty"
    return


# ---- as_dict Tests ----


def test_as_dict_includes_valid_field():
    """
        Verify that as_dict includes the valid field.
    """
    result = ConfigurationValidationResult(valid=True)
    result_dict = result.as_dict()
    has_valid_key = "valid" in result_dict
    assert has_valid_key is True, "as_dict should include the 'valid' key"
    valid_value = result_dict["valid"]
    assert valid_value is True, "as_dict 'valid' value should match the constructor value"
    return


def test_as_dict_includes_errors_field():
    """
        Verify that as_dict includes the errors field.
    """
    error_list = ["error one", "error two"]
    result = ConfigurationValidationResult(valid=False, errors=error_list)
    result_dict = result.as_dict()
    has_errors_key = "errors" in result_dict
    assert has_errors_key is True, "as_dict should include the 'errors' key"
    errors_value = result_dict["errors"]
    assert errors_value == ["error one", "error two"], \
        "as_dict 'errors' value should match the constructor value"
    return


def test_as_dict_includes_warnings_field():
    """
        Verify that as_dict includes the warnings field.
    """
    warning_list = ["deprecated field used"]
    result = ConfigurationValidationResult(valid=True, warnings=warning_list)
    result_dict = result.as_dict()
    has_warnings_key = "warnings" in result_dict
    assert has_warnings_key is True, "as_dict should include the 'warnings' key"
    warnings_value = result_dict["warnings"]
    assert warnings_value == ["deprecated field used"], \
        "as_dict 'warnings' value should match the constructor value"
    return


def test_as_dict_includes_all_three_fields():
    """
        Verify that as_dict returns a dictionary with valid, errors, and warnings.
    """
    result = ConfigurationValidationResult(
        valid=False,
        errors=["missing field"],
        warnings=["deprecated usage"]
    )
    result_dict = result.as_dict()
    expected_keys = {"valid", "errors", "warnings"}
    actual_keys = set(result_dict.keys())
    assert actual_keys == expected_keys, \
        "as_dict should return a dictionary with exactly valid, errors, and warnings keys"
    return


# ---- Defensive Copy Tests ----


def test_errors_property_returns_defensive_copy():
    """
        Verify that the errors property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    result = ConfigurationValidationResult(
        valid=False,
        errors=["original error"]
    )
    first_copy = result.errors
    first_copy.append("injected error")

    second_copy = result.errors
    error_count = len(second_copy)
    assert error_count == 1, \
        "errors property should return a defensive copy; modifying the copy should not affect internal state"
    return


def test_warnings_property_returns_defensive_copy():
    """
        Verify that the warnings property returns a defensive copy,
        so modifying the returned list does not affect the internal state.
    """
    result = ConfigurationValidationResult(
        valid=True,
        warnings=["original warning"]
    )
    first_copy = result.warnings
    first_copy.append("injected warning")

    second_copy = result.warnings
    warning_count = len(second_copy)
    assert warning_count == 1, \
        "warnings property should return a defensive copy; modifying the copy should not affect internal state"
    return


# ---- __repr__ Tests ----


def test_repr_contains_class_name():
    """
        Verify that __repr__ contains the class name.
    """
    result = ConfigurationValidationResult(valid=True)
    repr_str = repr(result)
    has_class_name = "ConfigurationValidationResult" in repr_str
    assert has_class_name is True, "__repr__ should contain the class name"
    return


def test_repr_contains_valid_flag():
    """
        Verify that __repr__ contains the valid flag value.
    """
    result = ConfigurationValidationResult(valid=False)
    repr_str = repr(result)
    has_valid_flag = "valid=False" in repr_str
    assert has_valid_flag is True, "__repr__ should contain the valid flag value"
    return


def test_repr_contains_error_count():
    """
        Verify that __repr__ contains the error count.
    """
    result = ConfigurationValidationResult(
        valid=False,
        errors=["err1", "err2", "err3"]
    )
    repr_str = repr(result)
    has_error_count = "error_count=3" in repr_str
    assert has_error_count is True, "__repr__ should contain the error count"
    return


def test_repr_contains_warning_count():
    """
        Verify that __repr__ contains the warning count.
    """
    result = ConfigurationValidationResult(
        valid=True,
        warnings=["warn1", "warn2"]
    )
    repr_str = repr(result)
    has_warning_count = "warning_count=2" in repr_str
    assert has_warning_count is True, "__repr__ should contain the warning count"
    return


# ---- __str__ Tests ----


def test_str_contains_valid_flag():
    """
        Verify that __str__ contains the valid flag value.
    """
    result = ConfigurationValidationResult(valid=True)
    str_val = str(result)
    has_valid = "valid=True" in str_val
    assert has_valid is True, "__str__ should contain the valid flag value"
    return


def test_str_contains_error_count():
    """
        Verify that __str__ contains the error count.
    """
    result = ConfigurationValidationResult(
        valid=False,
        errors=["err1", "err2"]
    )
    str_val = str(result)
    has_errors = "errors=2" in str_val
    assert has_errors is True, "__str__ should contain the error count"
    return


def test_str_contains_warning_count():
    """
        Verify that __str__ contains the warning count.
    """
    result = ConfigurationValidationResult(
        valid=True,
        warnings=["warn1"]
    )
    str_val = str(result)
    has_warnings = "warnings=1" in str_val
    assert has_warnings is True, "__str__ should contain the warning count"
    return


def test_str_contains_first_error_when_errors_present():
    """
        Verify that __str__ contains the first error message when errors are present.
    """
    result = ConfigurationValidationResult(
        valid=False,
        errors=["missing required field 'name'", "invalid type for 'port'"]
    )
    str_val = str(result)
    has_first_error = "missing required field 'name'" in str_val
    assert has_first_error is True, \
        "__str__ should contain the first error message when errors are present"
    return


def test_str_does_not_contain_first_error_when_no_errors():
    """
        Verify that __str__ does not contain a first_error segment when errors is empty.
    """
    result = ConfigurationValidationResult(valid=True, errors=[])
    str_val = str(result)
    has_first_error = "first_error" in str_val
    assert has_first_error is False, \
        "__str__ should not contain a first_error segment when errors is empty"
    return
