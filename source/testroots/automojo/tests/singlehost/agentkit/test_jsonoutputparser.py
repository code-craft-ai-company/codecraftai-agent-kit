"""
    Unit tests for the automojo.agentkit.jsonoutputparser module.

    Tests JsonOutputParser with valid JSON (dict, list, nested),
    invalid JSON, and schema validation integration.

    Feature: llm-integration, Task 11.6
    **Validates: Requirements 8.3, 8.4**
"""

import json

from automojo.agentkit.jsonoutputparser import JsonOutputParser
from automojo.agentkit.llmerrors import LLMResponseParsingError
from automojo.agentkit.outputschema import OutputSchema


# ---------------------------------------------------------------------------
# Valid JSON parsing
# ---------------------------------------------------------------------------


def test_parse_valid_json_dict():
    """
        Parsing a valid JSON dictionary returns a Python dict.

        **Validates: Requirements 8.3**
    """
    parser = JsonOutputParser()
    raw = json.dumps({"name": "Alice", "age": 30})

    result = parser.parse(raw)

    assert isinstance(result, dict), (
        "Expected dict, got: {}".format(type(result).__name__)
    )
    assert result["name"] == "Alice", (
        "Expected name 'Alice', got: {!r}".format(result["name"])
    )
    assert result["age"] == 30, (
        "Expected age 30, got: {!r}".format(result["age"])
    )

    return


def test_parse_valid_json_list():
    """
        Parsing a valid JSON list returns a Python list.

        **Validates: Requirements 8.3**
    """
    parser = JsonOutputParser()
    raw = json.dumps([1, 2, 3])

    result = parser.parse(raw)

    assert isinstance(result, list), (
        "Expected list, got: {}".format(type(result).__name__)
    )
    assert result == [1, 2, 3], (
        "Expected [1, 2, 3], got: {!r}".format(result)
    )

    return


def test_parse_valid_json_nested():
    """
        Parsing valid nested JSON returns the correct nested structure.

        **Validates: Requirements 8.3**
    """
    parser = JsonOutputParser()
    data = {
        "user": {
            "name": "Alice",
            "scores": [95, 87, 92],
        },
        "active": True,
    }
    raw = json.dumps(data)

    result = parser.parse(raw)

    assert result["user"]["name"] == "Alice", (
        "Expected nested name 'Alice'"
    )
    assert result["user"]["scores"] == [95, 87, 92], (
        "Expected nested scores list"
    )
    assert result["active"] is True, (
        "Expected active to be True"
    )

    return


def test_parse_valid_json_empty_dict():
    """
        Parsing an empty JSON object returns an empty dict.

        **Validates: Requirements 8.3**
    """
    parser = JsonOutputParser()

    result = parser.parse("{}")

    assert result == {}, (
        "Expected empty dict, got: {!r}".format(result)
    )

    return


def test_parse_valid_json_empty_list():
    """
        Parsing an empty JSON array returns an empty list.

        **Validates: Requirements 8.3**
    """
    parser = JsonOutputParser()

    result = parser.parse("[]")

    assert result == [], (
        "Expected empty list, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Invalid JSON parsing
# ---------------------------------------------------------------------------


def test_parse_invalid_json_raises_error():
    """
        Parsing invalid JSON raises LLMResponseParsingError.

        **Validates: Requirements 8.4**
    """
    parser = JsonOutputParser()

    raised = False
    caught_error = None

    try:
        parser.parse("not valid json {{{")
    except LLMResponseParsingError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "Should raise LLMResponseParsingError for invalid JSON"
    )
    assert caught_error.parser_name == "JsonOutputParser", (
        "parser_name should be 'JsonOutputParser', got: {!r}".format(
            caught_error.parser_name
        )
    )
    assert caught_error.raw_text == "not valid json {{{", (
        "raw_text should contain the original input"
    )

    return


def test_parse_empty_string_raises_error():
    """
        Parsing an empty string raises LLMResponseParsingError.

        **Validates: Requirements 8.4**
    """
    parser = JsonOutputParser()

    raised = False

    try:
        parser.parse("")
    except LLMResponseParsingError:
        raised = True

    assert raised is True, (
        "Should raise LLMResponseParsingError for empty string"
    )

    return


def test_parse_invalid_json_error_includes_detail():
    """
        The LLMResponseParsingError for invalid JSON includes the
        JSON parsing error detail in the error_message.

        **Validates: Requirements 8.4**
    """
    parser = JsonOutputParser()

    caught_error = None

    try:
        parser.parse("{bad json}")
    except LLMResponseParsingError as err:
        caught_error = err

    assert caught_error is not None, "Should have raised LLMResponseParsingError"
    assert "JSON" in caught_error.error_message or "json" in caught_error.error_message.lower(), (
        "Error message should mention JSON, got: {!r}".format(
            caught_error.error_message
        )
    )

    return


# ---------------------------------------------------------------------------
# Schema validation integration
# ---------------------------------------------------------------------------


def test_parse_with_schema_valid():
    """
        JsonOutputParser with a schema validates successfully for
        conforming JSON.

        **Validates: Requirements 8.3, 8.7, 8.8**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
    ])
    parser = JsonOutputParser(schema=schema)
    raw = json.dumps({"name": "Alice"})

    result = parser.parse(raw)

    assert result == {"name": "Alice"}, (
        "Valid JSON with valid schema should return parsed result"
    )

    return


def test_parse_with_schema_invalid_raises_error():
    """
        JsonOutputParser with a schema raises LLMResponseParsingError
        when the parsed JSON does not conform to the schema.

        **Validates: Requirements 8.8, 8.9**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
    ])
    parser = JsonOutputParser(schema=schema)
    raw = json.dumps({"other": "value"})

    raised = False

    try:
        parser.parse(raw)
    except LLMResponseParsingError:
        raised = True

    assert raised is True, (
        "Should raise LLMResponseParsingError when schema validation fails"
    )

    return
