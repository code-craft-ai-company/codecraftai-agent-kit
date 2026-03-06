"""
    Unit tests for the automojo.agentkit.prompttemplateregistry module.

    Tests PromptTemplateRegistry construction, registration, lookup by
    name and version, lookup latest version, duplicate registration,
    list_all, count, load_from_json_file, and load_from_yaml_file.

    Feature: llm-integration, Task 10.4
    **Validates: Requirements 7.11, 7.12, 7.13, 7.14, 7.15, 7.16, 7.17**
"""

import json
import os
import tempfile

from automojo.agentkit.errors import SemanticError
from automojo.agentkit.prompttemplate import PromptTemplate
from automojo.agentkit.prompttemplateregistry import PromptTemplateRegistry


# ---------------------------------------------------------------------------
# Empty registry
# ---------------------------------------------------------------------------


def test_empty_registry_count_is_zero():
    """
        A new PromptTemplateRegistry has count 0.

        **Validates: Requirements 7.15**
    """
    registry = PromptTemplateRegistry()

    assert registry.count == 0, (
        "Empty registry count should be 0, got: {}".format(registry.count)
    )

    return


def test_empty_registry_list_all_is_empty():
    """
        A new PromptTemplateRegistry returns an empty list from list_all.

        **Validates: Requirements 7.14**
    """
    registry = PromptTemplateRegistry()

    result = registry.list_all()

    assert result == [], (
        "Empty registry list_all should return [], got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Register and lookup
# ---------------------------------------------------------------------------


def test_register_and_lookup_by_name_and_version():
    """
        Registering a template and looking it up by name+version returns
        the same instance.

        **Validates: Requirements 7.11, 7.13**
    """
    registry = PromptTemplateRegistry()
    pt = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")

    registry.register(pt)
    result = registry.lookup("greet", version="1.0")

    assert result is pt, (
        "lookup should return the registered template instance"
    )

    return


def test_register_increments_count():
    """
        Registering a template increments the count.

        **Validates: Requirements 7.11, 7.15**
    """
    registry = PromptTemplateRegistry()
    pt = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")

    registry.register(pt)

    assert registry.count == 1, (
        "Count should be 1 after registering one template, got: {}".format(registry.count)
    )

    return


def test_register_multiple_templates():
    """
        Registering multiple templates with different keys works correctly.

        **Validates: Requirements 7.11, 7.14, 7.15**
    """
    registry = PromptTemplateRegistry()
    pt_a = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")
    pt_b = PromptTemplate(name="summary", version="1.0", template="Summarize {topic}.")

    registry.register(pt_a)
    registry.register(pt_b)

    assert registry.count == 2, (
        "Count should be 2 after registering two templates, got: {}".format(registry.count)
    )

    all_templates = registry.list_all()
    assert len(all_templates) == 2, (
        "list_all should return 2 templates, got: {}".format(len(all_templates))
    )

    return


# ---------------------------------------------------------------------------
# Lookup - not found
# ---------------------------------------------------------------------------


def test_lookup_not_found_returns_none():
    """
        Looking up a non-existent template returns None.

        **Validates: Requirements 7.13**
    """
    registry = PromptTemplateRegistry()

    result = registry.lookup("nonexistent", version="1.0")

    assert result is None, (
        "lookup for non-existent template should return None, got: {!r}".format(result)
    )

    return


def test_lookup_by_name_only_not_found_returns_none():
    """
        Looking up by name only when no templates match returns None.

        **Validates: Requirements 7.13**
    """
    registry = PromptTemplateRegistry()

    result = registry.lookup("nonexistent")

    assert result is None, (
        "lookup by name for non-existent template should return None, got: {!r}".format(result)
    )

    return


# ---------------------------------------------------------------------------
# Lookup - latest version
# ---------------------------------------------------------------------------


def test_lookup_latest_version():
    """
        Looking up by name without version returns the latest version
        based on lexicographic sort.

        **Validates: Requirements 7.13**
    """
    registry = PromptTemplateRegistry()
    pt_v1 = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")
    pt_v2 = PromptTemplate(name="greet", version="2.0", template="Hi {name}!")

    registry.register(pt_v1)
    registry.register(pt_v2)

    result = registry.lookup("greet")

    assert result is pt_v2, (
        "lookup without version should return the latest version"
    )

    return


def test_lookup_latest_version_registration_order_independent():
    """
        Latest version lookup works regardless of registration order.

        **Validates: Requirements 7.13**
    """
    registry = PromptTemplateRegistry()
    pt_v2 = PromptTemplate(name="greet", version="2.0", template="Hi {name}!")
    pt_v1 = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")

    registry.register(pt_v2)
    registry.register(pt_v1)

    result = registry.lookup("greet")

    assert result is pt_v2, (
        "lookup should return latest version regardless of registration order"
    )

    return


# ---------------------------------------------------------------------------
# Duplicate registration raises SemanticError
# ---------------------------------------------------------------------------


def test_duplicate_registration_raises_semantic_error():
    """
        Registering a template with the same name and version raises SemanticError.

        **Validates: Requirements 7.12**
    """
    registry = PromptTemplateRegistry()
    pt_a = PromptTemplate(name="greet", version="1.0", template="Hello {name}!")
    pt_b = PromptTemplate(name="greet", version="1.0", template="Hi {name}!")

    registry.register(pt_a)

    caught = False
    error_message = ""
    try:
        registry.register(pt_b)
    except SemanticError as err:
        caught = True
        error_message = str(err)

    assert caught is True, (
        "Duplicate registration should raise SemanticError"
    )
    assert "greet" in error_message, (
        "Error message should include the template name, got: {!r}".format(error_message)
    )
    assert "1.0" in error_message, (
        "Error message should include the version, got: {!r}".format(error_message)
    )

    return


# ---------------------------------------------------------------------------
# load_from_json_file
# ---------------------------------------------------------------------------


def test_load_from_json_file():
    """
        load_from_json_file loads templates from a JSON file and registers them.

        **Validates: Requirements 7.16**
    """
    data = {
        "templates": [
            {
                "name": "greet",
                "version": "1.0",
                "template": "Hello {name}!",
                "description": "A greeting"
            },
            {
                "name": "summary",
                "version": "1.0",
                "template": "Summarize {topic}.",
                "description": "A summary"
            }
        ]
    }

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w") as fhandle:
            json.dump(data, fhandle)

        registry = PromptTemplateRegistry()
        registry.load_from_json_file(tmp_path)

        assert registry.count == 2, (
            "Registry should have 2 templates after loading JSON, got: {}".format(registry.count)
        )

        greet = registry.lookup("greet", version="1.0")
        assert greet is not None, (
            "Should find 'greet' v1.0 after loading from JSON"
        )
        assert greet.template == "Hello {name}!", (
            "Loaded template mismatch: {!r}".format(greet.template)
        )

        summary = registry.lookup("summary", version="1.0")
        assert summary is not None, (
            "Should find 'summary' v1.0 after loading from JSON"
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return


# ---------------------------------------------------------------------------
# load_from_yaml_file
# ---------------------------------------------------------------------------


def test_load_from_yaml_file():
    """
        load_from_yaml_file loads templates from a YAML file and registers them.

        **Validates: Requirements 7.17**
    """
    yaml_content = (
        "templates:\n"
        "  - name: greet\n"
        "    version: '1.0'\n"
        "    template: 'Hello {name}!'\n"
        "    description: A greeting\n"
        "  - name: summary\n"
        "    version: '1.0'\n"
        "    template: 'Summarize {topic}.'\n"
        "    description: A summary\n"
    )

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".yaml")
    try:
        with os.fdopen(tmp_fd, "w") as fhandle:
            fhandle.write(yaml_content)

        registry = PromptTemplateRegistry()
        registry.load_from_yaml_file(tmp_path)

        assert registry.count == 2, (
            "Registry should have 2 templates after loading YAML, got: {}".format(registry.count)
        )

        greet = registry.lookup("greet", version="1.0")
        assert greet is not None, (
            "Should find 'greet' v1.0 after loading from YAML"
        )
        assert greet.template == "Hello {name}!", (
            "Loaded template mismatch: {!r}".format(greet.template)
        )

        summary = registry.lookup("summary", version="1.0")
        assert summary is not None, (
            "Should find 'summary' v1.0 after loading from YAML"
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return


# ---------------------------------------------------------------------------
# load_from_json_file with existing registry
# ---------------------------------------------------------------------------


def test_load_from_json_file_adds_to_existing():
    """
        load_from_json_file adds templates to an already-populated registry.

        **Validates: Requirements 7.16**
    """
    existing = PromptTemplate(name="existing", version="1.0", template="I exist.")

    data = {
        "templates": [
            {
                "name": "loaded",
                "version": "1.0",
                "template": "I was loaded."
            }
        ]
    }

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w") as fhandle:
            json.dump(data, fhandle)

        registry = PromptTemplateRegistry()
        registry.register(existing)
        registry.load_from_json_file(tmp_path)

        assert registry.count == 2, (
            "Registry should have 2 templates, got: {}".format(registry.count)
        )
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return
