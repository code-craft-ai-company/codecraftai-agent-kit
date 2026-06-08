"""
    Unit tests for the ccai.agentkit.regexoutputparser module.

    Tests RegexOutputParser with matching and non-matching patterns,
    named groups, pattern property, and schema validation integration.

    Feature: llm-integration, Task 11.6
    **Validates: Requirements 8.5, 8.6**
"""

from ccai.agentkit.llmerrors import LLMResponseParsingError
from ccai.agentkit.outputschema import OutputSchema
from ccai.agentkit.regexoutputparser import RegexOutputParser


# ---------------------------------------------------------------------------
# Pattern property
# ---------------------------------------------------------------------------


def test_pattern_property():
    """
        The pattern property returns the regex pattern string.

        **Validates: Requirements 8.5**
    """
    pattern = r"(?P<name>\w+)"
    parser = RegexOutputParser(pattern=pattern)

    assert parser.pattern == pattern, (
        "Expected pattern {!r}, got: {!r}".format(pattern, parser.pattern)
    )

    return


# ---------------------------------------------------------------------------
# Matching patterns with named groups
# ---------------------------------------------------------------------------


def test_parse_single_named_group():
    """
        Parsing text that matches a single named group returns a dict
        with the group name and matched value.

        **Validates: Requirements 8.5**
    """
    parser = RegexOutputParser(pattern=r"Name: (?P<name>\w+)")

    result = parser.parse("Name: Alice")

    assert result == {"name": "Alice"}, (
        "Expected {{'name': 'Alice'}}, got: {!r}".format(result)
    )

    return


def test_parse_multiple_named_groups():
    """
        Parsing text that matches multiple named groups returns a dict
        with all group names and matched values.

        **Validates: Requirements 8.5**
    """
    parser = RegexOutputParser(
        pattern=r"Name: (?P<name>\w+), Age: (?P<age>\d+)"
    )

    result = parser.parse("Name: Alice, Age: 30")

    assert result["name"] == "Alice", (
        "Expected name 'Alice', got: {!r}".format(result["name"])
    )
    assert result["age"] == "30", (
        "Expected age '30' (string from regex), got: {!r}".format(result["age"])
    )

    return


def test_parse_pattern_matches_within_larger_text():
    """
        The regex search finds a match within a larger text body.

        **Validates: Requirements 8.5**
    """
    parser = RegexOutputParser(pattern=r"Result: (?P<value>\d+)")

    result = parser.parse("Some prefix text. Result: 42. Some suffix text.")

    assert result == {"value": "42"}, (
        "Expected {{'value': '42'}}, got: {!r}".format(result)
    )

    return


def test_parse_pattern_with_no_named_groups():
    """
        A pattern with no named groups returns an empty dict on match.

        **Validates: Requirements 8.5**
    """
    parser = RegexOutputParser(pattern=r"hello")

    result = parser.parse("hello world")

    assert result == {}, (
        "Expected empty dict for pattern with no named groups, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Non-matching patterns
# ---------------------------------------------------------------------------


def test_parse_no_match_raises_error():
    """
        Parsing text that does not match the pattern raises
        LLMResponseParsingError.

        **Validates: Requirements 8.6**
    """
    parser = RegexOutputParser(pattern=r"Name: (?P<name>\w+)")

    raised = False
    caught_error = None

    try:
        parser.parse("no match here")
    except LLMResponseParsingError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "Should raise LLMResponseParsingError when pattern does not match"
    )
    assert caught_error.parser_name == "RegexOutputParser", (
        "parser_name should be 'RegexOutputParser', got: {!r}".format(
            caught_error.parser_name
        )
    )
    assert caught_error.raw_text == "no match here", (
        "raw_text should contain the original input"
    )

    return


def test_parse_no_match_error_includes_pattern():
    """
        The LLMResponseParsingError for a non-matching pattern includes
        the pattern in the error_message.

        **Validates: Requirements 8.6**
    """
    pattern = r"Name: (?P<name>\w+)"
    parser = RegexOutputParser(pattern=pattern)

    caught_error = None

    try:
        parser.parse("no match")
    except LLMResponseParsingError as err:
        caught_error = err

    assert caught_error is not None, "Should have raised LLMResponseParsingError"
    assert "did not match" in caught_error.error_message, (
        "Error message should indicate no match, got: {!r}".format(
            caught_error.error_message
        )
    )
    assert "Name:" in caught_error.error_message, (
        "Error message should reference the pattern, got: {!r}".format(
            caught_error.error_message
        )
    )

    return


def test_parse_empty_string_no_match():
    """
        Parsing an empty string with a non-trivial pattern raises
        LLMResponseParsingError.

        **Validates: Requirements 8.6**
    """
    parser = RegexOutputParser(pattern=r"Name: (?P<name>\w+)")

    raised = False

    try:
        parser.parse("")
    except LLMResponseParsingError:
        raised = True

    assert raised is True, (
        "Should raise LLMResponseParsingError for empty string"
    )

    return


# ---------------------------------------------------------------------------
# Schema validation integration
# ---------------------------------------------------------------------------


def test_parse_with_schema_valid():
    """
        RegexOutputParser with a schema validates successfully when
        the parsed groups conform to the schema.

        **Validates: Requirements 8.5, 8.7, 8.8**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
    ])
    parser = RegexOutputParser(
        pattern=r"Name: (?P<name>\w+)",
        schema=schema
    )

    result = parser.parse("Name: Alice")

    assert result == {"name": "Alice"}, (
        "Valid parse with valid schema should return result"
    )

    return


def test_parse_with_schema_missing_field_raises_error():
    """
        RegexOutputParser with a schema raises LLMResponseParsingError
        when the parsed groups do not satisfy the schema.

        **Validates: Requirements 8.8, 8.9**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
        {"name": "age", "type": "string", "required": True},
    ])
    parser = RegexOutputParser(
        pattern=r"Name: (?P<name>\w+)",
        schema=schema
    )

    raised = False

    try:
        parser.parse("Name: Alice")
    except LLMResponseParsingError:
        raised = True

    assert raised is True, (
        "Should raise LLMResponseParsingError when schema validation fails"
    )

    return
