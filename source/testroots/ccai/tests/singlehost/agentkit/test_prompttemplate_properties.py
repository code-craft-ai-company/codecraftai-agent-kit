"""
    Property-based tests for the ccai.agentkit.prompttemplate and
    ccai.agentkit.prompttemplateregistry modules.

    Uses ccai.testbase.properties to verify:
    - Property 4: PromptTemplate JSON round-trip
    - Property 17: PromptTemplate render produces correct output
    - Property 18: PromptTemplate render rejects missing variables
    - Property 19: PromptTemplate variables property extracts all placeholders
    - Property 20: PromptTemplateRegistry registration, lookup, and enumeration

    **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 7.10,
                 7.11, 7.12, 7.13, 7.14, 7.15, 17.7, 17.8, 17.12**
"""

from ccai.testbase.properties import given, assume
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.agentkit.errors import SemanticError
from ccai.agentkit.prompttemplate import PromptTemplate
from ccai.agentkit.prompttemplateregistry import PromptTemplateRegistry


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_safe_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?-_",
    min_size=1,
    max_size=30,
)

_name_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=15,
)

_version_text = st.text(
    alphabet="0123456789.",
    min_size=1,
    max_size=8,
)

_variable_name = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz_",
    min_size=1,
    max_size=10,
)

_variable_value = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ",
    min_size=1,
    max_size=20,
)


@composite
def _prompt_template_no_vars(draw):
    """
        Draws a PromptTemplate with no placeholder variables.
        The template body uses only safe characters (no curly braces).
    """
    name = draw(_name_text)
    version = draw(_version_text)
    template_body = draw(_safe_text)
    description = draw(_safe_text)

    pt = PromptTemplate(
        name=name,
        version=version,
        template=template_body,
        description=description,
    )
    return pt


@composite
def _prompt_template_with_vars(draw):
    """
        Draws a PromptTemplate with 1-5 unique placeholder variables.
        The template is constructed by interleaving safe text segments
        with {variable_name} placeholders.
    """
    name = draw(_name_text)
    version = draw(_version_text)
    description = draw(_safe_text)

    num_vars = draw(st.integers(min_value=1, max_value=5))
    var_names = []
    seen = set()

    for _ in range(num_vars):
        vname = draw(_variable_name)
        if vname not in seen:
            seen.add(vname)
            var_names.append(vname)

    assume(len(var_names) > 0)

    # Build template by interleaving text segments with placeholders
    segments = []
    for vname in var_names:
        prefix = draw(_safe_text)
        segments.append(prefix)
        segments.append("{" + vname + "}")

    suffix = draw(_safe_text)
    segments.append(suffix)

    template_str = "".join(segments)

    pt = PromptTemplate(
        name=name,
        version=version,
        template=template_str,
        description=description,
    )
    return (pt, var_names)


@composite
def _prompt_template_any(draw):
    """
        Draws either a PromptTemplate with or without variables.
    """
    use_vars = draw(st.integers(min_value=0, max_value=1))

    if use_vars == 0:
        pt = draw(_prompt_template_no_vars())
    else:
        pt, _ = draw(_prompt_template_with_vars())

    return pt


@composite
def _unique_template_specs(draw, min_size=0, max_size=10):
    """
        Draws a list of PromptTemplate instances with unique (name, version)
        composite keys.
    """
    count = draw(st.integers(min_value=min_size, max_value=max_size))
    templates = []
    seen_keys = set()

    for _ in range(count):
        name = draw(_name_text)
        version = draw(_version_text)
        key = (name, version)

        if key in seen_keys:
            continue
        seen_keys.add(key)

        template_body = draw(_safe_text)
        description = draw(_safe_text)

        pt = PromptTemplate(
            name=name,
            version=version,
            template=template_body,
            description=description,
        )
        templates.append(pt)

    return templates


# ---------------------------------------------------------------------------
# Property 4: PromptTemplate JSON round-trip
# ---------------------------------------------------------------------------


@given(pt=_prompt_template_any(), constraints={"max_examples": 50})
def test_prompttemplate_json_roundtrip_preserves_all_fields(
    pt: PromptTemplate,
) -> None:
    """
        **Validates: Requirements 7.6, 7.7, 7.8, 7.9, 7.10, 17.7, 17.8, 17.12**

        For any valid PromptTemplate, calling to_json() and then from_json()
        shall produce a PromptTemplate whose name, version, template, and
        description are equal to the original.
    """
    json_str = pt.to_json()
    restored = PromptTemplate.from_json(json_str)

    assert restored.name == pt.name, (
        "name should be {!r}, got {!r}".format(pt.name, restored.name)
    )
    assert restored.version == pt.version, (
        "version should be {!r}, got {!r}".format(pt.version, restored.version)
    )
    assert restored.template == pt.template, (
        "template should be {!r}, got {!r}".format(pt.template, restored.template)
    )
    assert restored.description == pt.description, (
        "description should be {!r}, got {!r}".format(pt.description, restored.description)
    )
    assert restored == pt, (
        "round-tripped PromptTemplate should be equal to the original"
    )

    return


@given(pt=_prompt_template_any(), constraints={"max_examples": 50})
def test_prompttemplate_dict_roundtrip_preserves_all_fields(
    pt: PromptTemplate,
) -> None:
    """
        **Validates: Requirements 7.6, 7.7, 7.8, 7.9, 7.10**

        For any valid PromptTemplate, calling as_dict() and then from_dict()
        shall produce an equivalent PromptTemplate.
    """
    d = pt.as_dict()
    restored = PromptTemplate.from_dict(d)

    assert restored == pt, (
        "round-tripped PromptTemplate via dict should be equal to the original"
    )

    return


# ---------------------------------------------------------------------------
# Property 17: PromptTemplate render produces correct output
# ---------------------------------------------------------------------------


@given(data=_prompt_template_with_vars(), constraints={"max_examples": 50})
def test_prompttemplate_render_produces_correct_output(
    data: tuple,
) -> None:
    """
        **Validates: Requirements 7.3**

        For any valid PromptTemplate with placeholder variables and a
        complete dictionary of variable values, render(values) shall
        produce a string equal to the template with all placeholders
        replaced by their corresponding values.
    """
    pt, var_names = data

    # Build a values dictionary with generated values
    values = {}
    for vname in var_names:
        values[vname] = "val_" + vname

    rendered = pt.render(values)

    # Verify the rendered string matches manual replacement
    expected = pt.template.format(**values)

    assert rendered == expected, (
        "render should produce {!r}, got {!r}".format(expected, rendered)
    )

    return


# ---------------------------------------------------------------------------
# Property 18: PromptTemplate render rejects missing variables
# ---------------------------------------------------------------------------


@given(data=_prompt_template_with_vars(), constraints={"max_examples": 50})
def test_prompttemplate_render_rejects_missing_variables(
    data: tuple,
) -> None:
    """
        **Validates: Requirements 7.4**

        For any valid PromptTemplate with at least one placeholder variable
        and a values dictionary missing that variable, render(values) shall
        raise SemanticError identifying the missing variable names.
    """
    pt, var_names = data

    # Provide an empty values dict so all variables are missing
    empty_values = {}

    raised = False
    caught_error = None

    try:
        pt.render(empty_values)
    except SemanticError as se:
        raised = True
        caught_error = se

    assert raised is True, (
        "render with missing variables should raise SemanticError"
    )

    # Verify the error message mentions the missing variable names
    error_str = str(caught_error)
    for vname in var_names:
        assert vname in error_str, (
            "SemanticError message should mention missing variable {!r}, "
            "got: {!r}".format(vname, error_str)
        )

    return


@given(data=_prompt_template_with_vars(), constraints={"max_examples": 50})
def test_prompttemplate_render_rejects_partial_variables(
    data: tuple,
) -> None:
    """
        **Validates: Requirements 7.4**

        For any valid PromptTemplate with multiple placeholder variables,
        providing only a subset of the required values shall raise
        SemanticError.
    """
    pt, var_names = data

    assume(len(var_names) >= 2)

    # Provide only the first variable, omit the rest
    partial_values = {var_names[0]: "provided_value"}

    raised = False

    try:
        pt.render(partial_values)
    except SemanticError:
        raised = True

    assert raised is True, (
        "render with partial variables should raise SemanticError"
    )

    return


# ---------------------------------------------------------------------------
# Property 19: PromptTemplate variables property extracts all placeholders
# ---------------------------------------------------------------------------


@given(data=_prompt_template_with_vars(), constraints={"max_examples": 50})
def test_prompttemplate_variables_extracts_all_placeholders(
    data: tuple,
) -> None:
    """
        **Validates: Requirements 7.5**

        For any valid PromptTemplate, the variables property shall return
        a list containing exactly the placeholder variable names present
        in the template string.
    """
    pt, var_names = data

    extracted = pt.variables

    # All expected variable names should be present
    for vname in var_names:
        assert vname in extracted, (
            "variables should contain {!r}, got {}".format(vname, extracted)
        )

    # The extracted list should not contain extra names beyond what we put in
    assert len(extracted) == len(var_names), (
        "variables should have {} entries, got {}".format(
            len(var_names), len(extracted)
        )
    )

    return


@given(pt=_prompt_template_no_vars(), constraints={"max_examples": 50})
def test_prompttemplate_variables_empty_for_no_placeholders(
    pt: PromptTemplate,
) -> None:
    """
        **Validates: Requirements 7.5**

        For any valid PromptTemplate with no placeholder variables,
        the variables property shall return an empty list.
    """
    extracted = pt.variables

    assert len(extracted) == 0, (
        "variables should be empty for template without placeholders, got {}".format(
            extracted
        )
    )

    return


@given(pt=_prompt_template_any(), constraints={"max_examples": 50})
def test_prompttemplate_variables_returns_copy(
    pt: PromptTemplate,
) -> None:
    """
        **Validates: Requirements 7.5**

        The variables property shall return a copy, so modifying the
        returned list does not affect the PromptTemplate.
    """
    vars_a = pt.variables
    vars_b = pt.variables

    assert vars_a == vars_b, (
        "two calls to variables should return equal lists"
    )

    assert vars_a is not vars_b, (
        "two calls to variables should return different list objects"
    )

    return


# ---------------------------------------------------------------------------
# Property 20: PromptTemplateRegistry registration, lookup, and enumeration
# ---------------------------------------------------------------------------


@given(templates=_unique_template_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_count_equals_number_of_registered_templates(
    templates: list,
) -> None:
    """
        **Validates: Requirements 7.11, 7.15**

        For any set of N templates with unique (name, version) pairs,
        after registration count shall equal N.
    """
    registry = PromptTemplateRegistry()

    for pt in templates:
        registry.register(pt)

    assert registry.count == len(templates), (
        "count should be {}, got {}".format(len(templates), registry.count)
    )

    return


@given(templates=_unique_template_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_lookup_returns_correct_template(
    templates: list,
) -> None:
    """
        **Validates: Requirements 7.11, 7.13**

        For any registered template, lookup(name, version) shall return
        the correct template instance.
    """
    registry = PromptTemplateRegistry()

    for pt in templates:
        registry.register(pt)

    for pt in templates:
        result = registry.lookup(pt.name, pt.version)

        assert result is pt, (
            "lookup({!r}, {!r}) should return the registered template".format(
                pt.name, pt.version
            )
        )

    return


@given(templates=_unique_template_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_list_all_returns_all_templates(
    templates: list,
) -> None:
    """
        **Validates: Requirements 7.11, 7.14**

        list_all() shall return all N registered templates.
    """
    registry = PromptTemplateRegistry()

    for pt in templates:
        registry.register(pt)

    all_templates = registry.list_all()

    assert len(all_templates) == len(templates), (
        "list_all() should return {} templates, got {}".format(
            len(templates), len(all_templates)
        )
    )

    for pt in templates:
        assert pt in all_templates, (
            "list_all() should contain template ({!r}, {!r})".format(
                pt.name, pt.version
            )
        )

    return


@given(templates=_unique_template_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_duplicate_registration_raises_semantic_error(
    templates: list,
) -> None:
    """
        **Validates: Requirements 7.12**

        Registering a duplicate (name, version) shall raise SemanticError.
    """
    registry = PromptTemplateRegistry()

    for pt in templates:
        registry.register(pt)

    # Pick the first template and try to register a duplicate
    first = templates[0]
    duplicate = PromptTemplate(
        name=first.name,
        version=first.version,
        template=first.template,
        description=first.description,
    )

    raised = False

    try:
        registry.register(duplicate)
    except SemanticError:
        raised = True

    assert raised is True, (
        "Registering duplicate ({!r}, {!r}) should raise SemanticError".format(
            first.name, first.version
        )
    )

    return


@given(templates=_unique_template_specs(min_size=1, max_size=15), constraints={"max_examples": 50})
def test_registry_lookup_latest_version_returns_lexicographic_max(
    templates: list,
) -> None:
    """
        **Validates: Requirements 7.13**

        lookup(name) without version shall return the template with the
        lexicographically latest version string for that name.
    """
    registry = PromptTemplateRegistry()

    for pt in templates:
        registry.register(pt)

    # Group templates by name
    by_name = {}
    for pt in templates:
        if pt.name not in by_name:
            by_name[pt.name] = []
        by_name[pt.name].append(pt)

    for name, group in by_name.items():
        # The expected latest is the one with the lexicographically largest version
        expected_latest = sorted(group, key=lambda t: t.version)[-1]

        result = registry.lookup(name)

        assert result is expected_latest, (
            "lookup({!r}) should return template with version {!r}, "
            "got version {!r}".format(
                name, expected_latest.version,
                result.version if result is not None else None
            )
        )

    return


@given(templates=_unique_template_specs(min_size=0, max_size=15), constraints={"max_examples": 50})
def test_registry_lookup_returns_none_for_unregistered(
    templates: list,
) -> None:
    """
        **Validates: Requirements 7.13**

        lookup() shall return None for template names that are not registered.
    """
    registry = PromptTemplateRegistry()

    for pt in templates:
        registry.register(pt)

    result = registry.lookup("nonexistent_template_name", "99.99.99")

    assert result is None, (
        "lookup for unregistered template should return None, got {!r}".format(
            result
        )
    )

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
