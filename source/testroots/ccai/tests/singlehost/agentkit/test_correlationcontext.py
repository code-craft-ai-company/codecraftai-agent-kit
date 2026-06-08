"""
    Unit tests for the ccai.agentkit.correlationcontext module.

    Tests the CorrelationContext class: auto-generated UUID, read-only
    properties, create_child, serialization (as_dict, to_json, from_dict,
    from_json), __repr__, and __str__.
"""

import json
import uuid

from ccai.agentkit.correlationcontext import CorrelationContext


def test_auto_generated_correlation_id_is_valid_uuid():
    """
        Verify that when no correlation_id is provided, a valid UUID is generated.
    """
    ctx = CorrelationContext()
    correlation_id = ctx.correlation_id

    parsed = uuid.UUID(correlation_id)
    round_tripped = str(parsed)
    assert round_tripped == correlation_id, "Auto-generated correlation_id should be a valid UUID string"
    return


def test_auto_generated_correlation_id_is_unique():
    """
        Verify that two CorrelationContext instances get different auto-generated IDs.
    """
    ctx1 = CorrelationContext()
    ctx2 = CorrelationContext()

    id1 = ctx1.correlation_id
    id2 = ctx2.correlation_id
    assert id1 != id2, "Each CorrelationContext should get a unique auto-generated ID"
    return


def test_explicit_correlation_id_is_preserved():
    """
        Verify that an explicitly provided correlation_id is used as-is.
    """
    ctx = CorrelationContext(correlation_id="my-custom-id")
    correlation_id = ctx.correlation_id
    assert correlation_id == "my-custom-id", "Explicit correlation_id should be preserved"
    return


def test_parent_correlation_id_is_none_by_default():
    """
        Verify that parent_correlation_id is None when not provided.
    """
    ctx = CorrelationContext()
    parent_id = ctx.parent_correlation_id
    assert parent_id is None, "parent_correlation_id should be None by default"
    return


def test_explicit_parent_correlation_id_is_preserved():
    """
        Verify that an explicitly provided parent_correlation_id is stored.
    """
    ctx = CorrelationContext(
        correlation_id="child-id",
        parent_correlation_id="parent-id"
    )
    parent_id = ctx.parent_correlation_id
    assert parent_id == "parent-id", "Explicit parent_correlation_id should be preserved"
    return


def test_correlation_id_property_is_read_only():
    """
        Verify that correlation_id cannot be set directly on the instance.
    """
    ctx = CorrelationContext(correlation_id="original-id")
    raised = False
    try:
        ctx.correlation_id = "new-id"
    except AttributeError:
        raised = True

    assert raised is True, "correlation_id should be read-only"
    return


def test_parent_correlation_id_property_is_read_only():
    """
        Verify that parent_correlation_id cannot be set directly on the instance.
    """
    ctx = CorrelationContext(parent_correlation_id="parent-id")
    raised = False
    try:
        ctx.parent_correlation_id = "new-parent"
    except AttributeError:
        raised = True

    assert raised is True, "parent_correlation_id should be read-only"
    return


def test_create_child_returns_new_context():
    """
        Verify that create_child returns a new CorrelationContext instance.
    """
    parent = CorrelationContext(correlation_id="parent-abc")
    child = parent.create_child()

    is_context = isinstance(child, CorrelationContext)
    assert is_context is True, "create_child should return a CorrelationContext"

    is_different = child is not parent
    assert is_different is True, "create_child should return a new instance"
    return


def test_create_child_sets_parent_id():
    """
        Verify that create_child sets the parent's correlation_id as the child's
        parent_correlation_id.
    """
    parent = CorrelationContext(correlation_id="parent-xyz")
    child = parent.create_child()

    child_parent_id = child.parent_correlation_id
    assert child_parent_id == "parent-xyz", "Child's parent_correlation_id should be parent's correlation_id"
    return


def test_create_child_generates_new_correlation_id():
    """
        Verify that create_child generates a new correlation_id for the child.
    """
    parent = CorrelationContext(correlation_id="parent-id")
    child = parent.create_child()

    child_id = child.correlation_id
    parent_id = parent.correlation_id
    assert child_id != parent_id, "Child should have a different correlation_id than parent"

    parsed = uuid.UUID(child_id)
    round_tripped = str(parsed)
    assert round_tripped == child_id, "Child's correlation_id should be a valid UUID"
    return


def test_as_dict_returns_dictionary():
    """
        Verify that as_dict returns a dictionary with the expected keys.
    """
    ctx = CorrelationContext(
        correlation_id="dict-id",
        parent_correlation_id="dict-parent"
    )
    result = ctx.as_dict()

    is_dict = isinstance(result, dict)
    assert is_dict is True, "as_dict should return a dictionary"

    correlation_id = result["correlation_id"]
    assert correlation_id == "dict-id", "as_dict should include correlation_id"

    parent_id = result["parent_correlation_id"]
    assert parent_id == "dict-parent", "as_dict should include parent_correlation_id"
    return


def test_as_dict_with_none_parent():
    """
        Verify that as_dict includes None for parent_correlation_id when not set.
    """
    ctx = CorrelationContext(correlation_id="no-parent-id")
    result = ctx.as_dict()

    parent_id = result["parent_correlation_id"]
    assert parent_id is None, "as_dict should include None for missing parent_correlation_id"
    return


def test_to_json_returns_valid_json_string():
    """
        Verify that to_json returns a valid JSON string.
    """
    ctx = CorrelationContext(
        correlation_id="json-id",
        parent_correlation_id="json-parent"
    )
    json_str = ctx.to_json()

    parsed = json.loads(json_str)
    correlation_id = parsed["correlation_id"]
    assert correlation_id == "json-id", "to_json should produce valid JSON with correlation_id"

    parent_id = parsed["parent_correlation_id"]
    assert parent_id == "json-parent", "to_json should produce valid JSON with parent_correlation_id"
    return


def test_from_dict_reconstructs_context():
    """
        Verify that from_dict constructs a CorrelationContext from a dictionary.
    """
    data = {
        "correlation_id": "from-dict-id",
        "parent_correlation_id": "from-dict-parent"
    }
    ctx = CorrelationContext.from_dict(data)

    correlation_id = ctx.correlation_id
    assert correlation_id == "from-dict-id", "from_dict should set correlation_id"

    parent_id = ctx.parent_correlation_id
    assert parent_id == "from-dict-parent", "from_dict should set parent_correlation_id"
    return


def test_from_dict_with_none_parent():
    """
        Verify that from_dict handles None parent_correlation_id.
    """
    data = {
        "correlation_id": "only-id",
        "parent_correlation_id": None
    }
    ctx = CorrelationContext.from_dict(data)

    parent_id = ctx.parent_correlation_id
    assert parent_id is None, "from_dict should handle None parent_correlation_id"
    return


def test_from_json_reconstructs_context():
    """
        Verify that from_json deserializes a JSON string into a CorrelationContext.
    """
    json_str = json.dumps({
        "correlation_id": "from-json-id",
        "parent_correlation_id": "from-json-parent"
    })
    ctx = CorrelationContext.from_json(json_str)

    correlation_id = ctx.correlation_id
    assert correlation_id == "from-json-id", "from_json should set correlation_id"

    parent_id = ctx.parent_correlation_id
    assert parent_id == "from-json-parent", "from_json should set parent_correlation_id"
    return


def test_json_round_trip():
    """
        Verify that to_json followed by from_json produces an equivalent context.
    """
    original = CorrelationContext(
        correlation_id="round-trip-id",
        parent_correlation_id="round-trip-parent"
    )
    json_str = original.to_json()
    restored = CorrelationContext.from_json(json_str)

    original_id = original.correlation_id
    restored_id = restored.correlation_id
    assert restored_id == original_id, "Round-trip should preserve correlation_id"

    original_parent = original.parent_correlation_id
    restored_parent = restored.parent_correlation_id
    assert restored_parent == original_parent, "Round-trip should preserve parent_correlation_id"
    return


def test_json_round_trip_with_none_parent():
    """
        Verify that JSON round-trip works when parent_correlation_id is None.
    """
    original = CorrelationContext(correlation_id="no-parent-round-trip")
    json_str = original.to_json()
    restored = CorrelationContext.from_json(json_str)

    restored_id = restored.correlation_id
    assert restored_id == "no-parent-round-trip", "Round-trip should preserve correlation_id"

    restored_parent = restored.parent_correlation_id
    assert restored_parent is None, "Round-trip should preserve None parent_correlation_id"
    return


def test_repr_contains_class_name():
    """
        Verify that __repr__ includes the class name CorrelationContext.
    """
    ctx = CorrelationContext(correlation_id="repr-id")
    repr_str = repr(ctx)
    has_class_name = "CorrelationContext" in repr_str
    assert has_class_name is True, "repr should contain the class name"
    return


def test_repr_contains_correlation_id():
    """
        Verify that __repr__ includes the correlation_id value.
    """
    ctx = CorrelationContext(correlation_id="repr-corr-id")
    repr_str = repr(ctx)
    has_id = "repr-corr-id" in repr_str
    assert has_id is True, "repr should contain the correlation_id"
    return


def test_repr_contains_parent_correlation_id():
    """
        Verify that __repr__ includes the parent_correlation_id value.
    """
    ctx = CorrelationContext(
        correlation_id="repr-id",
        parent_correlation_id="repr-parent-id"
    )
    repr_str = repr(ctx)
    has_parent = "repr-parent-id" in repr_str
    assert has_parent is True, "repr should contain the parent_correlation_id"
    return


def test_str_contains_correlation_id():
    """
        Verify that __str__ includes the correlation_id value.
    """
    ctx = CorrelationContext(correlation_id="str-corr-id")
    str_val = str(ctx)
    has_id = "str-corr-id" in str_val
    assert has_id is True, "str should contain the correlation_id"
    return


def test_str_contains_parent_correlation_id():
    """
        Verify that __str__ includes the parent_correlation_id value.
    """
    ctx = CorrelationContext(
        correlation_id="str-id",
        parent_correlation_id="str-parent-id"
    )
    str_val = str(ctx)
    has_parent = "str-parent-id" in str_val
    assert has_parent is True, "str should contain the parent_correlation_id"
    return


def test_str_is_human_readable():
    """
        Verify that __str__ returns a human-readable string format.
    """
    ctx = CorrelationContext(correlation_id="human-id")
    str_val = str(ctx)
    has_label = "CorrelationContext" in str_val
    assert has_label is True, "str should be human-readable with class context"
    return
