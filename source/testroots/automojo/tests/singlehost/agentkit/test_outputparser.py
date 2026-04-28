"""
    Unit tests for the automojo.agentkit.outputparser module.

    Tests OutputParser abstract interface enforcement and schema validation
    integration through a concrete subclass.

    Feature: llm-integration, Task 11.6
    **Validates: Requirements 8.1, 8.2, 8.7, 8.8, 8.9**
"""

from automojo.agentkit.llmerrors import LLMResponseParsingError
from automojo.agentkit.outputparser import OutputParser
from automojo.agentkit.outputschema import OutputSchema


# ---------------------------------------------------------------------------
# Concrete test subclass
# ---------------------------------------------------------------------------


class _DictOutputParser(OutputParser):
    """
        Minimal concrete subclass that returns a fixed dictionary
        for testing the base class schema validation logic.
    """

    def __init__(self, fixed_result, schema=None):
        super().__init__(schema=schema)
        self._fixed_result = fixed_result
        return

    def _parse_raw(self, raw_text):
        return self._fixed_result


# ---------------------------------------------------------------------------
# Abstract interface enforcement
# ---------------------------------------------------------------------------


def test_cannot_instantiate_abstract_outputparser():
    """
        OutputParser cannot be instantiated directly because _parse_raw
        is abstract.

        **Validates: Requirements 8.1, 8.2**
    """
    raised = False

    try:
        OutputParser()
    except TypeError:
        raised = True

    assert raised is True, (
        "Instantiating OutputParser directly should raise TypeError"
    )

    return


# ---------------------------------------------------------------------------
# Schema property
# ---------------------------------------------------------------------------


def test_schema_property_none():
    """
        When no schema is provided, the schema property returns None.

        **Validates: Requirements 8.7**
    """
    parser = _DictOutputParser(fixed_result={}, schema=None)

    assert parser.schema is None, (
        "Schema should be None when not provided"
    )

    return


def test_schema_property_returns_schema():
    """
        When a schema is provided, the schema property returns it.

        **Validates: Requirements 8.7**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
    ])
    parser = _DictOutputParser(fixed_result={}, schema=schema)

    assert parser.schema is schema, (
        "Schema property should return the provided OutputSchema"
    )

    return


# ---------------------------------------------------------------------------
# Parse without schema
# ---------------------------------------------------------------------------


def test_parse_without_schema_returns_parsed():
    """
        Parsing without a schema returns the parsed result directly.

        **Validates: Requirements 8.1**
    """
    expected = {"name": "Alice", "age": 30}
    parser = _DictOutputParser(fixed_result=expected, schema=None)

    result = parser.parse("ignored raw text")

    assert result == expected, (
        "Parse without schema should return parsed result, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Parse with schema validation - valid
# ---------------------------------------------------------------------------


def test_parse_with_schema_valid_object():
    """
        Parsing with a schema that validates successfully returns the
        parsed result.

        **Validates: Requirements 8.7, 8.8**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
    ])
    parser = _DictOutputParser(
        fixed_result={"name": "Alice"},
        schema=schema
    )

    result = parser.parse("ignored")

    assert result == {"name": "Alice"}, (
        "Valid parse should return the result, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Parse with schema validation - invalid
# ---------------------------------------------------------------------------


def test_parse_with_schema_missing_required_field():
    """
        Parsing with a schema that detects a missing required field
        raises LLMResponseParsingError.

        **Validates: Requirements 8.8, 8.9**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
    ])
    parser = _DictOutputParser(
        fixed_result={},
        schema=schema
    )

    raised = False
    caught_error = None

    try:
        parser.parse("some raw text")
    except LLMResponseParsingError as err:
        raised = True
        caught_error = err

    assert raised is True, (
        "Should raise LLMResponseParsingError for missing required field"
    )
    assert caught_error.parser_name == "_DictOutputParser", (
        "parser_name should be the subclass name, got: {!r}".format(
            caught_error.parser_name
        )
    )
    assert caught_error.raw_text == "some raw text", (
        "raw_text should be the input text, got: {!r}".format(
            caught_error.raw_text
        )
    )

    return


def test_parse_with_schema_type_mismatch():
    """
        Parsing with a schema that detects a type mismatch raises
        LLMResponseParsingError.

        **Validates: Requirements 8.8, 8.9**
    """
    schema = OutputSchema(fields=[
        {"name": "count", "type": "integer", "required": True},
    ])
    parser = _DictOutputParser(
        fixed_result={"count": "not-an-int"},
        schema=schema
    )

    raised = False

    try:
        parser.parse("raw")
    except LLMResponseParsingError:
        raised = True

    assert raised is True, (
        "Should raise LLMResponseParsingError for type mismatch"
    )

    return


def test_parse_with_schema_error_includes_validation_details():
    """
        The LLMResponseParsingError raised on validation failure includes
        the validation error details in the error_message.

        **Validates: Requirements 8.9**
    """
    schema = OutputSchema(fields=[
        {"name": "name", "type": "string", "required": True},
        {"name": "age", "type": "integer", "required": True},
    ])
    parser = _DictOutputParser(
        fixed_result={"name": 123},
        schema=schema
    )

    caught_error = None

    try:
        parser.parse("raw text")
    except LLMResponseParsingError as err:
        caught_error = err

    assert caught_error is not None, "Should have raised LLMResponseParsingError"
    assert "age" in caught_error.error_message, (
        "Error message should mention missing field 'age'"
    )
    assert "name" in caught_error.error_message, (
        "Error message should mention type mismatch for 'name'"
    )

    return
