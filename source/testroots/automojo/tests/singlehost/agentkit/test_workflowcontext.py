"""
    Unit tests for the WorkflowContext class in the Workflow &
    Orchestration feature.

    Tests construction, property access, get_input, get_step_output,
    set_step_output, get_metadata, set_metadata, as_dict, to_json,
    from_dict, __repr__, and __str__.

    Requirements: 5.1-5.15
"""

import json


from automojo.agentkit.workflowcontext import WorkflowContext


# =========================================================================
# Construction tests (Requirements 5.1, 5.7, 5.8)
# =========================================================================

def test_construction_with_inputs_agent_metadata():
    """
        Verify that WorkflowContext stores inputs, agent, and metadata
        provided at construction time.
    """
    inputs = {"url": "https://example.com", "timeout": 30}
    agent_ref = "agent-sentinel"
    metadata = {"run_id": "abc-123"}

    ctx = WorkflowContext(inputs=inputs, agent=agent_ref, metadata=metadata)

    assert ctx.inputs == {"url": "https://example.com", "timeout": 30}, \
        "inputs should match the provided dictionary"
    assert ctx.agent == "agent-sentinel", \
        "agent should match the provided reference"
    assert ctx.metadata == {"run_id": "abc-123"}, \
        "metadata should match the provided dictionary"
    return


def test_default_metadata_is_empty_dict():
    """
        Verify that metadata defaults to an empty dictionary when
        not provided.
    """
    ctx = WorkflowContext(inputs={"x": 1})

    assert ctx.metadata == {}, \
        "metadata should default to an empty dict"
    return


def test_default_step_outputs_is_empty_dict():
    """
        Verify that step_outputs defaults to an empty dictionary
        at construction time.
    """
    ctx = WorkflowContext(inputs={"x": 1})

    assert ctx.step_outputs == {}, \
        "step_outputs should default to an empty dict"
    return


# =========================================================================
# Property access tests (Requirements 5.7, 5.8, 5.9)
# =========================================================================

def test_inputs_property_returns_input_dict():
    """
        Verify that the inputs property returns the workflow input
        dictionary.
    """
    inputs = {"name": "workflow-a", "count": 5}
    ctx = WorkflowContext(inputs=inputs)

    assert ctx.inputs == {"name": "workflow-a", "count": 5}, \
        "inputs property should return the input dictionary"
    return


def test_agent_property_returns_agent_reference():
    """
        Verify that the agent property returns the agent reference
        provided at construction time.
    """
    agent_ref = {"id": "agent-007"}
    ctx = WorkflowContext(inputs={}, agent=agent_ref)

    assert ctx.agent == {"id": "agent-007"}, \
        "agent property should return the agent reference"
    return


# =========================================================================
# get_input tests (Requirements 5.4)
# =========================================================================

def test_get_input_returns_value_for_existing_field():
    """
        Verify that get_input returns the value for an existing
        input field.
    """
    ctx = WorkflowContext(inputs={"host": "localhost", "port": 8080})

    result = ctx.get_input("port")

    assert result == 8080, \
        "get_input should return 8080 for existing field 'port'"
    return


def test_get_input_returns_default_for_missing_field():
    """
        Verify that get_input returns the provided default value
        when the field is not present.
    """
    ctx = WorkflowContext(inputs={"host": "localhost"})

    result = ctx.get_input("port", default=3000)

    assert result == 3000, \
        "get_input should return the default value 3000 for missing field"
    return


def test_get_input_returns_none_for_missing_field_no_default():
    """
        Verify that get_input returns None when the field is not
        present and no default is provided.
    """
    ctx = WorkflowContext(inputs={"host": "localhost"})

    result = ctx.get_input("port")

    assert result is None, \
        "get_input should return None for missing field when no default"
    return


# =========================================================================
# get_step_output / set_step_output tests (Requirements 5.2, 5.3)
# =========================================================================

def test_get_step_output_returns_none_for_unexecuted_step():
    """
        Verify that get_step_output returns None when the step
        has not been executed.
    """
    ctx = WorkflowContext(inputs={})

    result = ctx.get_step_output("step-1")

    assert result is None, \
        "get_step_output should return None for unexecuted step"
    return


def test_set_step_output_stores_and_get_retrieves():
    """
        Verify that set_step_output stores the output and
        get_step_output retrieves it.
    """
    ctx = WorkflowContext(inputs={})
    output = {"result": "success", "value": 42}

    ctx.set_step_output("step-1", output)
    result = ctx.get_step_output("step-1")

    assert result == {"result": "success", "value": 42}, \
        "get_step_output should return the stored output"
    return


# =========================================================================
# get_metadata / set_metadata tests (Requirements 5.5, 5.6)
# =========================================================================

def test_get_metadata_returns_value_for_existing_key():
    """
        Verify that get_metadata returns the value for an existing
        metadata key.
    """
    ctx = WorkflowContext(inputs={}, metadata={"env": "production"})

    result = ctx.get_metadata("env")

    assert result == "production", \
        "get_metadata should return 'production' for existing key 'env'"
    return


def test_get_metadata_returns_default_for_missing_key():
    """
        Verify that get_metadata returns the provided default value
        when the key is not present.
    """
    ctx = WorkflowContext(inputs={}, metadata={"env": "production"})

    result = ctx.get_metadata("region", default="us-east-1")

    assert result == "us-east-1", \
        "get_metadata should return the default value for missing key"
    return


def test_set_metadata_stores_and_get_retrieves():
    """
        Verify that set_metadata stores the value and get_metadata
        retrieves it.
    """
    ctx = WorkflowContext(inputs={})

    ctx.set_metadata("trace_id", "trace-abc-123")
    result = ctx.get_metadata("trace_id")

    assert result == "trace-abc-123", \
        "get_metadata should return the stored metadata value"
    return


# =========================================================================
# as_dict tests (Requirement 5.10)
# =========================================================================

def test_as_dict_includes_inputs_step_outputs_metadata():
    """
        Verify that as_dict returns a dictionary containing inputs,
        step_outputs, and metadata but NOT the agent reference.
    """
    ctx = WorkflowContext(
        inputs={"x": 10},
        agent="agent-ref",
        metadata={"key": "val"}
    )
    ctx.set_step_output("step-a", {"out": 1})

    result = ctx.as_dict()

    assert "inputs" in result, "as_dict should include 'inputs'"
    assert "step_outputs" in result, "as_dict should include 'step_outputs'"
    assert "metadata" in result, "as_dict should include 'metadata'"
    assert "agent" not in result, "as_dict should NOT include 'agent'"
    assert result["inputs"] == {"x": 10}, "inputs should match"
    assert result["step_outputs"] == {"step-a": {"out": 1}}, \
        "step_outputs should match"
    assert result["metadata"] == {"key": "val"}, "metadata should match"
    return


# =========================================================================
# to_json tests (Requirement 5.11)
# =========================================================================

def test_to_json_produces_valid_json_matching_as_dict():
    """
        Verify that to_json produces a valid JSON string whose
        parsed content matches as_dict.
    """
    ctx = WorkflowContext(
        inputs={"a": 1, "b": "two"},
        metadata={"run": "test-run"}
    )
    ctx.set_step_output("s1", {"val": 100})

    json_str = ctx.to_json()
    parsed = json.loads(json_str)

    expected = ctx.as_dict()
    assert parsed == expected, \
        "Parsed JSON should match as_dict output"
    return


# =========================================================================
# from_dict tests (Requirement 5.12, 5.13)
# =========================================================================

def test_from_dict_reconstructs_equivalent_context():
    """
        Verify that from_dict reconstructs a WorkflowContext with
        equivalent inputs, step_outputs, and metadata.
    """
    original = WorkflowContext(
        inputs={"url": "https://example.com"},
        metadata={"env": "test"}
    )
    original.set_step_output("step-1", {"status": "ok"})
    original.set_step_output("step-2", {"count": 5})

    data = original.as_dict()
    restored = WorkflowContext.from_dict(data)

    assert restored.inputs == original.inputs, \
        "Restored inputs should match original"
    assert restored.step_outputs == original.step_outputs, \
        "Restored step_outputs should match original"
    assert restored.metadata == original.metadata, \
        "Restored metadata should match original"
    assert restored.agent is None, \
        "Restored agent should be None when not provided"
    return


def test_from_dict_with_agent_parameter():
    """
        Verify that from_dict accepts an agent parameter and stores
        it in the reconstructed context.
    """
    data = {
        "inputs": {"x": 42},
        "step_outputs": {},
        "metadata": {}
    }
    agent_ref = "my-agent"

    restored = WorkflowContext.from_dict(data, agent=agent_ref)

    assert restored.agent == "my-agent", \
        "Restored agent should match the provided agent parameter"
    assert restored.inputs == {"x": 42}, \
        "Restored inputs should match"
    return


# =========================================================================
# __repr__ tests (Requirement 5.14)
# =========================================================================

def test_repr_includes_class_name_and_counts():
    """
        Verify that __repr__ includes the class name, completed step
        count, and input field count.
    """
    ctx = WorkflowContext(inputs={"a": 1, "b": 2, "c": 3})
    ctx.set_step_output("s1", {"out": 1})
    ctx.set_step_output("s2", {"out": 2})

    repr_str = repr(ctx)

    assert "WorkflowContext" in repr_str, \
        "__repr__ should include the class name"
    assert "2" in repr_str, \
        "__repr__ should include the completed step count (2)"
    assert "3" in repr_str, \
        "__repr__ should include the input field count (3)"
    return


# =========================================================================
# __str__ tests (Requirement 5.15)
# =========================================================================

def test_str_includes_completed_count_and_input_names():
    """
        Verify that __str__ includes the completed step count and
        input field names.
    """
    ctx = WorkflowContext(inputs={"host": "localhost", "port": 8080})
    ctx.set_step_output("step-1", {"done": True})

    str_val = str(ctx)

    assert "1" in str_val, \
        "__str__ should include the completed step count (1)"
    assert "host" in str_val, \
        "__str__ should include input field name 'host'"
    assert "port" in str_val, \
        "__str__ should include input field name 'port'"
    return


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
