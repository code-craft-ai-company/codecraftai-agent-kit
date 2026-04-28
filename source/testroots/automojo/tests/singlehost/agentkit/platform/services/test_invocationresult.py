"""
    Tests for the automojo.agentkit.platform.services.invocationresult module.

    Contains unit tests for the InvocationResult immutable data transfer
    object including read-only properties, valid statuses, as_dict
    serialization, JSON round-trip, and __repr__/__str__ output.

    Feature: cross-platform-runtime
"""

import json

from automojo.agentkit.platform.services.invocationresult import InvocationResult


# ---------------------------------------------------------------------------
# Helper fixtures
# ---------------------------------------------------------------------------

def _create_sample_success_result() -> InvocationResult:
    """
        Creates a sample successful InvocationResult for testing.

        :returns: An InvocationResult instance with known test values.
    """
    result = InvocationResult(
        status="success",
        response={"data": [1, 2, 3]},
        error_message=None,
        duration=1.234,
        request_id="req-abc-001"
    )
    return result


def _create_sample_error_result() -> InvocationResult:
    """
        Creates a sample error InvocationResult for testing.

        :returns: An InvocationResult instance with error status.
    """
    result = InvocationResult(
        status="error",
        response=None,
        error_message="Function not found",
        duration=0.5,
        request_id="req-err-002"
    )
    return result


# ---------------------------------------------------------------------------
# VALID_STATUSES tests
# ---------------------------------------------------------------------------

def test_valid_statuses_contains_expected_values():
    """
        Verify that VALID_STATUSES contains "success", "error", and "timeout".
    """
    statuses = InvocationResult.VALID_STATUSES

    has_success = "success" in statuses
    has_error = "error" in statuses
    has_timeout = "timeout" in statuses

    assert has_success is True, "VALID_STATUSES should contain 'success'"
    assert has_error is True, "VALID_STATUSES should contain 'error'"
    assert has_timeout is True, "VALID_STATUSES should contain 'timeout'"

    status_count = len(statuses)
    assert status_count == 3, (
        "VALID_STATUSES should have exactly 3 entries, got: {}".format(status_count)
    )
    return


# ---------------------------------------------------------------------------
# Read-only property tests
# ---------------------------------------------------------------------------

def test_status_property_returns_correct_value():
    """
        Verify that the status property returns the value passed at construction.
    """
    result = _create_sample_success_result()

    actual = result.status

    assert actual == "success", (
        "status should be 'success', got: {!r}".format(actual)
    )
    return


def test_response_property_returns_correct_value():
    """
        Verify that the response property returns the object passed at construction.
    """
    result = _create_sample_success_result()

    actual = result.response

    expected = {"data": [1, 2, 3]}
    assert actual == expected, (
        "response should be {!r}, got: {!r}".format(expected, actual)
    )
    return


def test_error_message_property_returns_none_for_success():
    """
        Verify that the error_message property returns None for a successful result.
    """
    result = _create_sample_success_result()

    actual = result.error_message

    assert actual is None, (
        "error_message should be None for success, got: {!r}".format(actual)
    )
    return


def test_error_message_property_returns_message_for_error():
    """
        Verify that the error_message property returns the message for an error result.
    """
    result = _create_sample_error_result()

    actual = result.error_message

    assert actual == "Function not found", (
        "error_message should be 'Function not found', got: {!r}".format(actual)
    )
    return


def test_duration_property_returns_correct_value():
    """
        Verify that the duration property returns the float passed at construction.
    """
    result = _create_sample_success_result()

    actual = result.duration

    assert abs(actual - 1.234) < 1e-9, (
        "duration should be 1.234, got: {!r}".format(actual)
    )
    return


def test_request_id_property_returns_correct_value():
    """
        Verify that the request_id property returns the value passed at construction.
    """
    result = _create_sample_success_result()

    actual = result.request_id

    assert actual == "req-abc-001", (
        "request_id should be 'req-abc-001', got: {!r}".format(actual)
    )
    return


def test_default_duration_is_zero():
    """
        Verify that the default duration is 0.0 when not specified.
    """
    result = InvocationResult(status="success", response=None)

    actual = result.duration

    assert abs(actual - 0.0) < 1e-9, (
        "default duration should be 0.0, got: {!r}".format(actual)
    )
    return


def test_default_request_id_is_empty_string():
    """
        Verify that the default request_id is an empty string when not specified.
    """
    result = InvocationResult(status="success", response=None)

    actual = result.request_id

    assert actual == "", (
        "default request_id should be empty string, got: {!r}".format(actual)
    )
    return


# ---------------------------------------------------------------------------
# as_dict tests
# ---------------------------------------------------------------------------

def test_as_dict_contains_all_fields():
    """
        Verify that as_dict returns a dictionary with all expected keys.
    """
    result = _create_sample_success_result()

    data = result.as_dict()

    expected_keys = {"status", "response", "error_message", "duration", "request_id"}
    actual_keys = set(data.keys())

    assert actual_keys == expected_keys, (
        "as_dict should contain keys {}, got: {}".format(expected_keys, actual_keys)
    )
    return


def test_as_dict_values_match_properties():
    """
        Verify that as_dict values match the property values.
    """
    result = _create_sample_success_result()

    data = result.as_dict()

    assert data["status"] == result.status, (
        "as_dict status mismatch: {!r} != {!r}".format(data["status"], result.status)
    )
    assert data["response"] == result.response, (
        "as_dict response mismatch: {!r} != {!r}".format(data["response"], result.response)
    )
    assert data["error_message"] == result.error_message, (
        "as_dict error_message mismatch"
    )
    assert abs(data["duration"] - result.duration) < 1e-9, (
        "as_dict duration mismatch"
    )
    assert data["request_id"] == result.request_id, (
        "as_dict request_id mismatch"
    )
    return


# ---------------------------------------------------------------------------
# JSON round-trip tests
# ---------------------------------------------------------------------------

def test_to_json_produces_valid_json():
    """
        Verify that to_json returns a valid JSON string.
    """
    result = _create_sample_success_result()

    json_str = result.to_json()
    parsed = json.loads(json_str)

    has_status = "status" in parsed
    assert has_status is True, "JSON should contain 'status' field"
    return


def test_json_round_trip_preserves_all_fields_success():
    """
        Verify that serializing a success result to JSON and deserializing
        back produces an equivalent InvocationResult.
    """
    original = _create_sample_success_result()

    json_str = original.to_json()
    restored = InvocationResult.from_json(json_str)

    assert restored.status == original.status, (
        "Round-trip status mismatch: {!r} != {!r}".format(
            restored.status, original.status)
    )
    assert restored.response == original.response, (
        "Round-trip response mismatch: {!r} != {!r}".format(
            restored.response, original.response)
    )
    assert restored.error_message == original.error_message, (
        "Round-trip error_message mismatch: {!r} != {!r}".format(
            restored.error_message, original.error_message)
    )
    assert abs(restored.duration - original.duration) < 1e-9, (
        "Round-trip duration mismatch: {!r} != {!r}".format(
            restored.duration, original.duration)
    )
    assert restored.request_id == original.request_id, (
        "Round-trip request_id mismatch: {!r} != {!r}".format(
            restored.request_id, original.request_id)
    )
    return


def test_json_round_trip_preserves_all_fields_error():
    """
        Verify that serializing an error result to JSON and deserializing
        back produces an equivalent InvocationResult.
    """
    original = _create_sample_error_result()

    json_str = original.to_json()
    restored = InvocationResult.from_json(json_str)

    assert restored.status == original.status, (
        "Round-trip status mismatch: {!r} != {!r}".format(
            restored.status, original.status)
    )
    assert restored.error_message == original.error_message, (
        "Round-trip error_message mismatch: {!r} != {!r}".format(
            restored.error_message, original.error_message)
    )
    return


def test_json_round_trip_timeout_status():
    """
        Verify that a timeout result round-trips correctly through JSON.
    """
    original = InvocationResult(
        status="timeout",
        response=None,
        error_message="Exceeded 30s timeout",
        duration=30.0,
        request_id="req-timeout-003"
    )

    json_str = original.to_json()
    restored = InvocationResult.from_json(json_str)

    assert restored.status == "timeout", (
        "Round-trip status should be 'timeout', got: {!r}".format(restored.status)
    )
    assert restored.error_message == "Exceeded 30s timeout", (
        "Round-trip error_message mismatch"
    )
    return


# ---------------------------------------------------------------------------
# __repr__ and __str__ tests
# ---------------------------------------------------------------------------

def test_repr_contains_class_name_status_request_id():
    """
        Verify that __repr__ includes the class name, status, and request id.
    """
    result = _create_sample_success_result()

    repr_str = repr(result)

    has_class_name = "InvocationResult" in repr_str
    has_status = "success" in repr_str
    has_request_id = "req-abc-001" in repr_str

    assert has_class_name is True, "repr should contain 'InvocationResult'"
    assert has_status is True, "repr should contain the status"
    assert has_request_id is True, "repr should contain the request_id"
    return


def test_str_contains_status_request_id_duration():
    """
        Verify that __str__ returns a human-readable summary with status,
        request id, and duration.
    """
    result = _create_sample_success_result()

    str_val = str(result)

    has_status = "success" in str_val
    has_request_id = "req-abc-001" in str_val
    has_duration = "1.234" in str_val

    assert has_status is True, "str should contain the status"
    assert has_request_id is True, "str should contain the request_id"
    assert has_duration is True, "str should contain the duration"
    return


def test_str_formats_duration_to_three_decimal_places():
    """
        Verify that __str__ formats the duration to three decimal places.
    """
    result = InvocationResult(
        status="success",
        response=None,
        duration=2.1,
        request_id="req-fmt"
    )

    str_val = str(result)

    has_formatted_duration = "2.100s" in str_val
    assert has_formatted_duration is True, (
        "str should format duration to 3 decimal places, got: {!r}".format(str_val)
    )
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
