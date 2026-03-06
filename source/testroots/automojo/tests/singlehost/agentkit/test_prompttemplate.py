"""
    Unit tests for the automojo.agentkit.prompttemplate module.

    Tests PromptTemplate construction with no variables, single variable,
    and multiple variables. Tests render with complete values and missing
    values. Tests __repr__, __str__, __eq__, as_dict, to_json, from_dict,
    from_json, and the variables property.

    Feature: llm-integration, Task 10.4
    **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10, 17.7, 17.8, 17.12, 19.13, 19.14**
"""

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.prompttemplate import PromptTemplate


# ---------------------------------------------------------------------------
# Construction - no variables
# ---------------------------------------------------------------------------


def test_no_variables_template():
    """
        A PromptTemplate with no placeholders has an empty variables list.

        **Validates: Requirements 7.1, 7.2, 7.5**
    """
    pt = PromptTemplate(name="greeting", version="1.0", template="Hello world")

    assert pt.name == "greeting", (
        "name mismatch: {!r}".format(pt.name)
    )
    assert pt.version == "1.0", (
        "version mismatch: {!r}".format(pt.version)
    )
    assert pt.template == "Hello world", (
        "template mismatch: {!r}".format(pt.template)
    )
    assert pt.description == "", (
        "default description should be empty, got: {!r}".format(pt.description)
    )
    assert pt.variables == [], (
        "variables should be empty for no-placeholder template, got: {!r}".format(pt.variables)
    )

    return


# ---------------------------------------------------------------------------
# Construction - single variable
# ---------------------------------------------------------------------------


def test_single_variable_template():
    """
        A PromptTemplate with one placeholder extracts that variable.

        **Validates: Requirements 7.1, 7.2, 7.5**
    """
    pt = PromptTemplate(
        name="greet_user", version="1.0",
        template="Hello {name}!", description="Greets a user"
    )

    assert pt.variables == ["name"], (
        "variables should be ['name'], got: {!r}".format(pt.variables)
    )
    assert pt.description == "Greets a user", (
        "description mismatch: {!r}".format(pt.description)
    )

    return


# ---------------------------------------------------------------------------
# Construction - multiple variables
# ---------------------------------------------------------------------------


def test_multiple_variables_template():
    """
        A PromptTemplate with multiple placeholders extracts all unique variables.

        **Validates: Requirements 7.1, 7.2, 7.5**
    """
    pt = PromptTemplate(
        name="summary", version="2.0",
        template="Summarize {topic} for {audience} in {language}."
    )

    assert pt.variables == ["topic", "audience", "language"], (
        "variables mismatch: {!r}".format(pt.variables)
    )

    return


def test_duplicate_variable_extracted_once():
    """
        A PromptTemplate with repeated placeholders extracts each variable once.

        **Validates: Requirements 7.5**
    """
    pt = PromptTemplate(
        name="repeat", version="1.0",
        template="{name} says hello. {name} says goodbye."
    )

    assert pt.variables == ["name"], (
        "Duplicate variable should appear once, got: {!r}".format(pt.variables)
    )

    return


# ---------------------------------------------------------------------------
# Variables property returns a copy
# ---------------------------------------------------------------------------


def test_variables_returns_copy():
    """
        The variables property returns a copy, not the internal list.

        **Validates: Requirements 7.2, 7.5**
    """
    pt = PromptTemplate(
        name="test", version="1.0", template="Hello {name}"
    )

    vars_a = pt.variables
    vars_b = pt.variables

    assert vars_a is not vars_b, (
        "variables should return a new list each time"
    )
    assert vars_a == vars_b, (
        "variables copies should be equal"
    )

    return


# ---------------------------------------------------------------------------
# Render - complete values
# ---------------------------------------------------------------------------


def test_render_no_variables():
    """
        Rendering a template with no variables returns the template unchanged.

        **Validates: Requirements 7.3**
    """
    pt = PromptTemplate(name="static", version="1.0", template="Hello world")

    result = pt.render({})

    assert result == "Hello world", (
        "render mismatch: {!r}".format(result)
    )

    return


def test_render_single_variable():
    """
        Rendering a template with one variable replaces the placeholder.

        **Validates: Requirements 7.3**
    """
    pt = PromptTemplate(
        name="greet", version="1.0", template="Hello {name}!"
    )

    result = pt.render({"name": "Alice"})

    assert result == "Hello Alice!", (
        "render mismatch: {!r}".format(result)
    )

    return


def test_render_multiple_variables():
    """
        Rendering a template with multiple variables replaces all placeholders.

        **Validates: Requirements 7.3**
    """
    pt = PromptTemplate(
        name="summary", version="1.0",
        template="Summarize {topic} for {audience}."
    )

    result = pt.render({"topic": "AI safety", "audience": "engineers"})

    assert result == "Summarize AI safety for engineers.", (
        "render mismatch: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Render - missing values raises SemanticError
# ---------------------------------------------------------------------------


def test_render_missing_variable_raises_semantic_error():
    """
        Rendering with missing variables raises SemanticError.

        **Validates: Requirements 7.4**
    """
    pt = PromptTemplate(
        name="greet", version="1.0", template="Hello {name}!"
    )

    caught = False
    try:
        pt.render({})
    except SemanticError:
        caught = True

    assert caught is True, (
        "render with missing variables should raise SemanticError"
    )

    return


def test_render_partial_variables_raises_semantic_error():
    """
        Rendering with only some variables provided raises SemanticError.

        **Validates: Requirements 7.4**
    """
    pt = PromptTemplate(
        name="multi", version="1.0",
        template="{greeting} {name}, welcome to {place}."
    )

    caught = False
    try:
        pt.render({"greeting": "Hello"})
    except SemanticError:
        caught = True

    assert caught is True, (
        "render with partial variables should raise SemanticError"
    )

    return


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------


def test_repr_includes_class_name_and_fields():
    """
        __repr__ includes the class name, name, and version.

        **Validates: Requirements 19.13**
    """
    pt = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")

    result = repr(pt)

    assert "PromptTemplate" in result, (
        "repr should contain 'PromptTemplate', got: {!r}".format(result)
    )
    assert "greet" in result, (
        "repr should contain the name, got: {!r}".format(result)
    )
    assert "1.0" in result, (
        "repr should contain the version, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# __str__
# ---------------------------------------------------------------------------


def test_str_includes_name_version_variables():
    """
        __str__ includes the name, version, and variable names.

        **Validates: Requirements 19.14**
    """
    pt = PromptTemplate(
        name="summary", version="2.0",
        template="Summarize {topic} for {audience}."
    )

    result = str(pt)

    assert "summary" in result, (
        "str should contain the name, got: {!r}".format(result)
    )
    assert "2.0" in result, (
        "str should contain the version, got: {!r}".format(result)
    )
    assert "topic" in result, (
        "str should contain variable 'topic', got: {!r}".format(result)
    )
    assert "audience" in result, (
        "str should contain variable 'audience', got: {!r}".format(result)
    )

    return


def test_str_no_variables():
    """
        __str__ for a template with no variables shows empty variable list.

        **Validates: Requirements 19.14**
    """
    pt = PromptTemplate(name="static", version="1.0", template="Hello world")

    result = str(pt)

    assert "static" in result, (
        "str should contain the name, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# __eq__
# ---------------------------------------------------------------------------


def test_eq_same_fields():
    """
        Two PromptTemplates with identical fields are equal.

        **Validates: Requirements 7.1**
    """
    pt_a = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")
    pt_b = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")

    assert pt_a == pt_b, (
        "Templates with same fields should be equal"
    )

    return


def test_eq_different_version():
    """
        Two PromptTemplates with different versions are not equal.

        **Validates: Requirements 7.1**
    """
    pt_a = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")
    pt_b = PromptTemplate(name="greet", version="2.0", template="Hello {name}!")

    assert pt_a != pt_b, (
        "Templates with different versions should not be equal"
    )

    return


def test_eq_different_template():
    """
        Two PromptTemplates with different template strings are not equal.

        **Validates: Requirements 7.1**
    """
    pt_a = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")
    pt_b = PromptTemplate(name="greet", version="1.0", template="Hi {name}!")

    assert pt_a != pt_b, (
        "Templates with different template strings should not be equal"
    )

    return


def test_eq_non_prompttemplate():
    """
        A PromptTemplate is not equal to a non-PromptTemplate object.

        **Validates: Requirements 7.1**
    """
    pt = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")

    assert pt != "not a template", (
        "PromptTemplate should not equal a string"
    )

    return


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------


def test_as_dict():
    """
        as_dict returns a dictionary with name, version, template, description.

        **Validates: Requirements 7.6**
    """
    pt = PromptTemplate(
        name="greet", version="1.0",
        template="Hello {name}!", description="A greeting"
    )

    result = pt.as_dict()

    assert result["name"] == "greet", (
        "as_dict name mismatch: {!r}".format(result["name"])
    )
    assert result["version"] == "1.0", (
        "as_dict version mismatch: {!r}".format(result["version"])
    )
    assert result["template"] == "Hello {name}!", (
        "as_dict template mismatch: {!r}".format(result["template"])
    )
    assert result["description"] == "A greeting", (
        "as_dict description mismatch: {!r}".format(result["description"])
    )

    return


# ---------------------------------------------------------------------------
# to_json / from_json round-trip
# ---------------------------------------------------------------------------


def test_to_json_from_json_round_trip():
    """
        Serializing to JSON and deserializing produces an equivalent object.

        **Validates: Requirements 7.7, 7.9, 7.10, 17.7, 17.8, 17.12**
    """
    pt = PromptTemplate(
        name="summary", version="2.0",
        template="Summarize {topic} for {audience}.",
        description="Summary template"
    )

    json_str = pt.to_json()
    restored = PromptTemplate.from_json(json_str)

    assert pt == restored, (
        "Round-trip should produce equal object"
    )

    return


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------


def test_from_dict():
    """
        from_dict constructs a PromptTemplate from a dictionary.

        **Validates: Requirements 7.8**
    """
    data = {
        "name": "greet",
        "version": "1.0",
        "template": "Hello {name}!",
        "description": "A greeting"
    }

    pt = PromptTemplate.from_dict(data)

    assert pt.name == "greet", (
        "from_dict name mismatch: {!r}".format(pt.name)
    )
    assert pt.version == "1.0", (
        "from_dict version mismatch: {!r}".format(pt.version)
    )
    assert pt.template == "Hello {name}!", (
        "from_dict template mismatch: {!r}".format(pt.template)
    )
    assert pt.description == "A greeting", (
        "from_dict description mismatch: {!r}".format(pt.description)
    )

    return


def test_from_dict_no_description():
    """
        from_dict with no description key defaults to empty string.

        **Validates: Requirements 7.8**
    """
    data = {
        "name": "greet",
        "version": "1.0",
        "template": "Hello {name}!"
    }

    pt = PromptTemplate.from_dict(data)

    assert pt.description == "", (
        "from_dict missing description should default to empty, got: {!r}".format(pt.description)
    )

    return
