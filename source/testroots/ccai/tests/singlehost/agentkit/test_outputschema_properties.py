"""
    Property-based tests for the ccai.agentkit output schema and parser modules.

    Uses ccai.testbase.properties to verify:
    - Property 5: OutputSchema JSON round-trip
    - Property 21: OutputSchema validates correct objects as valid
    - Property 22: OutputSchema reports missing required fields and type mismatches
    - Property 23: JsonOutputParser parses valid JSON and rejects invalid JSON
    - Property 24: RegexOutputParser extracts named groups and rejects non-matching text
    - Property 25: OutputParser validates parsed output against OutputSchema
"""

import json

from ccai.testbase.properties import given, assume
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.jsonoutputparser import JsonOutputParser
from ccai.agentkit.llmerrors import LLMResponseParsingError
from ccai.agentkit.outputschema import OutputSchema
from ccai.agentkit.regexoutputparser import RegexOutputParser


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_field_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=10,
)

_field_type = st.sampled_from(["string", "integer", "float", "boolean", "list", "dictionary"])

_required_flag = st.booleans()


@composite
def _field_definition(draw):
    """
        Draws a single field definition dictionary with name, type, and required.
    """
    name = draw(_field_name)
    ftype = draw(_field_type)
    required = draw(_required_flag)

    rtnval = {"name": name, "type": ftype, "required": required}
    return rtnval


def _unique_field_list():
    """
        Returns a strategy that produces a list of field definitions with unique names.
    """
    rtnval = st.lists(_field_definition(), min_size=0, max_size=8).map(
        lambda flds: list({f["name"]: f for f in flds}.values())
    )
    return rtnval


_TYPE_VALUE_STRATEGY = {
    "string": st.text(min_size=0, max_size=20),
    "integer": st.integers(min_value=-1000, max_value=1000),
    "float": st.floats(min_value=-1000.0, max_value=1000.0),
    "boolean": st.booleans(),
    "list": st.lists(st.integers(min_value=0, max_value=10), min_size=0, max_size=5),
    "dictionary": st.dictionaries(
        keys=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5),
        values=st.integers(min_value=0, max_value=100),
        min_size=0,
        max_size=3,
    ),
}

_WRONG_TYPE_VALUE = {
    "string": st.just(12345),
    "integer": st.just("not_an_int"),
    "float": st.just("not_a_float"),
    "boolean": st.just("not_a_bool"),
    "list": st.just("not_a_list"),
    "dictionary": st.just("not_a_dict"),
}


@composite
def _schema_with_valid_object(draw):
    """
        Draws an OutputSchema and a dictionary that satisfies all field constraints.
    """
    fields = draw(st.lists(_field_definition(), min_size=1, max_size=8).map(
        lambda flds: list({f["name"]: f for f in flds}.values())
    ))
    assume(len(fields) > 0)

    schema = OutputSchema(fields=fields)
    obj = {}

    for field_def in fields:
        value = draw(_TYPE_VALUE_STRATEGY[field_def["type"]])
        obj[field_def["name"]] = value

    return (schema, obj)


@composite
def _schema_with_required_field(draw):
    """
        Draws an OutputSchema that has at least one required field.
        Returns the schema and the name of a required field.
    """
    # Generate at least one required field to avoid UnsatisfiedAssumption
    required_field = draw(_field_definition())
    required_field = {**required_field, "required": True}

    other_fields = draw(st.lists(_field_definition(), min_size=0, max_size=7).map(
        lambda flds: list({f["name"]: f for f in flds}.values())
    ))

    # Combine and deduplicate by name, ensuring the required field is present
    all_fields_map = {f["name"]: f for f in other_fields}
    all_fields_map[required_field["name"]] = required_field
    fields = list(all_fields_map.values())

    schema = OutputSchema(fields=fields)
    required_name = required_field["name"]

    return (schema, fields, required_name)


@composite
def _schema_with_type_mismatch(draw):
    """
        Draws an OutputSchema and a dictionary where one field has a wrong type.
    """
    fields = draw(st.lists(_field_definition(), min_size=1, max_size=8).map(
        lambda flds: list({f["name"]: f for f in flds}.values())
    ))
    assume(len(fields) > 0)

    schema = OutputSchema(fields=fields)
    target_field = draw(st.sampled_from(fields))

    obj = {}
    for field_def in fields:
        if field_def["name"] == target_field["name"]:
            wrong_value = draw(_WRONG_TYPE_VALUE[field_def["type"]])
            obj[field_def["name"]] = wrong_value
        else:
            value = draw(_TYPE_VALUE_STRATEGY[field_def["type"]])
            obj[field_def["name"]] = value

    return (schema, obj, target_field["name"], target_field["type"])


# ---------------------------------------------------------------------------
# Strategies for JSON and regex parsers
# ---------------------------------------------------------------------------

_simple_json_value = st.one_of(
    st.text(min_size=0, max_size=20),
    st.integers(min_value=-1000, max_value=1000),
    st.floats(min_value=-1000.0, max_value=1000.0),
    st.booleans(),
    st.none(),
)

_json_dict = st.dictionaries(
    keys=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8),
    values=_simple_json_value,
    min_size=0,
    max_size=5,
)


def _is_not_valid_json(s: str) -> bool:
    """
        Returns True if the string is not valid JSON.
    """
    try:
        json.loads(s)
        return False
    except (json.JSONDecodeError, ValueError):
        return True


_invalid_json_text = st.text(min_size=1, max_size=50).filter(
    _is_not_valid_json
)


_group_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=8,
)

_group_value = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=10,
)


@composite
def _regex_pattern_and_matching_text(draw):
    """
        Draws a regex pattern with named groups and text that matches it.
    """
    name_set = draw(st.sets(_group_name, min_size=1, max_size=3))
    names = list(name_set)
    values = [draw(_group_value) for _ in names]

    pattern_parts = []
    text_parts = []

    for name, value in zip(names, values):
        pattern_parts.append("(?P<{}>\\w+)".format(name))
        text_parts.append(value)

    separator = ":"
    pattern = separator.join(pattern_parts)
    matching_text = separator.join(text_parts)

    return (pattern, matching_text, dict(zip(names, values)))


# ---------------------------------------------------------------------------
# Property 5: OutputSchema JSON round-trip
# ---------------------------------------------------------------------------

@given(fields=_unique_field_list(), constraints={"max_examples": 50})
def test_outputschema_json_roundtrip(fields: list) -> None:
    """
        **Validates: Requirements 8.13, 8.14, 8.15, 8.16, 8.17**

        For any valid OutputSchema instance, calling to_json() and then
        from_json() on the resulting string shall produce an OutputSchema
        whose fields list is equal to the original.
    """
    schema = OutputSchema(fields=fields)

    json_str = schema.to_json()
    restored = OutputSchema.from_json(json_str)

    assert schema == restored, (
        "OutputSchema round-trip failed: original fields={}, restored fields={}".format(
            schema.fields, restored.fields
        )
    )

    return


# ---------------------------------------------------------------------------
# Property 21: OutputSchema validates correct objects as valid
# ---------------------------------------------------------------------------

@given(data=_schema_with_valid_object(), constraints={"max_examples": 50})
def test_outputschema_validates_correct_objects_as_valid(data: tuple) -> None:
    """
        **Validates: Requirements 8.10, 8.11, 8.12**

        For any valid OutputSchema and any dictionary that includes all
        required fields with values matching their declared type constraints,
        validate() shall return an empty list.
    """
    schema, obj = data

    errors = schema.validate(obj)

    assert errors == [], (
        "Expected no validation errors for conforming object, got: {}".format(errors)
    )

    return


# ---------------------------------------------------------------------------
# Property 22: OutputSchema reports missing required fields and type mismatches
# ---------------------------------------------------------------------------

@given(data=_schema_with_required_field(), constraints={"max_examples": 50})
def test_outputschema_reports_missing_required_fields(data: tuple) -> None:
    """
        **Validates: Requirements 8.10, 8.11, 8.12**

        For any valid OutputSchema with at least one required field, and any
        dictionary missing that field, validate() shall return a non-empty list.
    """
    schema, fields, required_name = data

    obj = {}
    for field_def in fields:
        if field_def["name"] != required_name:
            obj[field_def["name"]] = "placeholder"

    errors = schema.validate(obj)

    assert len(errors) > 0, (
        "Expected validation errors for missing required field {!r}, got empty list".format(
            required_name
        )
    )

    return


@given(data=_schema_with_type_mismatch(), constraints={"max_examples": 50})
def test_outputschema_reports_type_mismatches(data: tuple) -> None:
    """
        **Validates: Requirements 8.10, 8.11, 8.12**

        For any field with a declared type constraint and a value of a
        different type, validate() shall return a non-empty list containing
        an error identifying the field and type mismatch.
    """
    schema, obj, field_name, field_type = data

    errors = schema.validate(obj)

    assert len(errors) > 0, (
        "Expected validation errors for type mismatch on field {!r} "
        "(expected {}, got {}), got empty list".format(
            field_name, field_type, type(obj[field_name]).__name__
        )
    )

    field_error_found = False
    for err in errors:
        if field_name in err:
            field_error_found = True
            break

    assert field_error_found, (
        "Expected an error mentioning field {!r}, got: {}".format(field_name, errors)
    )

    return


# ---------------------------------------------------------------------------
# Property 23: JsonOutputParser parses valid JSON and rejects invalid JSON
# ---------------------------------------------------------------------------

@given(obj=_json_dict, constraints={"max_examples": 50})
def test_jsonoutputparser_parses_valid_json(obj: dict) -> None:
    """
        **Validates: Requirements 8.3, 8.4**

        For any valid JSON string, JsonOutputParser.parse() shall return
        the corresponding Python object.
    """
    parser = JsonOutputParser()
    json_str = json.dumps(obj)

    result = parser.parse(json_str)

    assert result == obj, (
        "JsonOutputParser should parse valid JSON correctly, expected {}, got {}".format(
            obj, result
        )
    )

    return


@given(bad_text=_invalid_json_text, constraints={"max_examples": 50})
def test_jsonoutputparser_rejects_invalid_json(bad_text: str) -> None:
    """
        **Validates: Requirements 8.3, 8.4**

        For any string that is not valid JSON, JsonOutputParser.parse()
        shall raise LLMResponseParsingError containing the raw text.
    """
    parser = JsonOutputParser()

    raised = False
    try:
        parser.parse(bad_text)
    except LLMResponseParsingError as exc:
        raised = True
        assert exc.raw_text == bad_text, (
            "LLMResponseParsingError raw_text should be the input text"
        )

    assert raised, (
        "Expected LLMResponseParsingError for invalid JSON: {!r}".format(bad_text)
    )

    return


# ---------------------------------------------------------------------------
# Property 24: RegexOutputParser extracts named groups and rejects non-matching text
# ---------------------------------------------------------------------------

@given(data=_regex_pattern_and_matching_text(), constraints={"max_examples": 50})
def test_regexoutputparser_extracts_named_groups(data: tuple) -> None:
    """
        **Validates: Requirements 8.5, 8.6**

        For any regex pattern with named capture groups and any text that
        matches the pattern, RegexOutputParser.parse() shall return a
        dictionary of the named group matches.
    """
    pattern, matching_text, expected_groups = data

    parser = RegexOutputParser(pattern=pattern)
    result = parser.parse(matching_text)

    assert isinstance(result, dict), (
        "RegexOutputParser should return a dict, got {}".format(type(result).__name__)
    )

    for name, expected_value in expected_groups.items():
        assert name in result, (
            "Expected named group {!r} in result, got keys: {}".format(
                name, list(result.keys())
            )
        )
        assert result[name] == expected_value, (
            "Named group {!r} should be {!r}, got {!r}".format(
                name, expected_value, result[name]
            )
        )

    return


@given(
    data=_regex_pattern_and_matching_text(),
    noise=st.text(alphabet="!@#$%^&*()", min_size=5, max_size=20),
    constraints={"max_examples": 50},
)
def test_regexoutputparser_rejects_non_matching_text(
    data: tuple,
    noise: str,
) -> None:
    """
        **Validates: Requirements 8.5, 8.6**

        For any text that does not match the pattern, RegexOutputParser.parse()
        shall raise LLMResponseParsingError containing the raw text and pattern.
    """
    pattern, _, _ = data

    parser = RegexOutputParser(pattern=pattern)

    raised = False
    try:
        parser.parse(noise)
    except LLMResponseParsingError as exc:
        raised = True
        assert exc.raw_text == noise, (
            "LLMResponseParsingError raw_text should be the input text"
        )

    assert raised, (
        "Expected LLMResponseParsingError for non-matching text: {!r}".format(noise)
    )

    return


# ---------------------------------------------------------------------------
# Property 25: OutputParser validates parsed output against OutputSchema
# ---------------------------------------------------------------------------

@given(data=_schema_with_required_field(), constraints={"max_examples": 50})
def test_outputparser_validates_parsed_output_against_schema(
    data: tuple,
) -> None:
    """
        **Validates: Requirements 8.7, 8.8, 8.9**

        For any OutputParser with an OutputSchema, and any raw text that
        parses successfully but produces output that does not conform to
        the schema, parse() shall raise LLMResponseParsingError with
        validation error details.
    """
    schema, fields, required_name = data

    # Build a dict missing the required field, then serialize as JSON
    obj = {}
    for field_def in fields:
        if field_def["name"] != required_name:
            obj[field_def["name"]] = "placeholder"

    raw_json = json.dumps(obj)

    parser = JsonOutputParser(schema=schema)

    raised = False
    try:
        parser.parse(raw_json)
    except LLMResponseParsingError as exc:
        raised = True
        assert exc.raw_text == raw_json, (
            "LLMResponseParsingError raw_text should be the input JSON"
        )
        assert "validation" in exc.error_message.lower() or required_name in str(exc), (
            "Error should mention validation failure or the missing field {!r}".format(
                required_name
            )
        )

    assert raised, (
        "Expected LLMResponseParsingError when parsed output violates schema "
        "(missing required field {!r})".format(required_name)
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
