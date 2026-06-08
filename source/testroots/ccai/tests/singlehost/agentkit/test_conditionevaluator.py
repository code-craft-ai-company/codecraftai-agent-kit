"""
    Unit tests for the ConditionEvaluator class in the Workflow &
    Orchestration feature.

    Tests step output references, input references, all comparison
    and logical operators, membership operator, rejection of unsafe
    expressions, WorkflowExecutionError for unresolved step
    references, and WorkflowDefinitionError for invalid syntax.

    Requirements: 3.3-3.12
"""

from ccai.agentkit.conditionevaluator import ConditionEvaluator
from ccai.agentkit.workflowcontext import WorkflowContext
from ccai.agentkit.workflowerrors import WorkflowDefinitionError
from ccai.agentkit.workflowerrors import WorkflowExecutionError


# =========================================================================
# Helper: shared evaluator and context
# =========================================================================

def _make_context():
    """
        Creates a WorkflowContext with sample inputs and step outputs
        for use across tests.
    """
    ctx = WorkflowContext(
        inputs={"threshold": 50, "mode": "fast", "items": [1, 2, 3]},
        metadata={}
    )
    ctx.set_step_output("step_a", {
        "score": 85,
        "status": "ok",
        "count": 3,
        "tags": ["alpha", "beta"]
    })
    ctx.set_step_output("step_b", {
        "score": 40,
        "status": "error",
        "value": 10.5
    })
    return ctx


_evaluator = ConditionEvaluator()


# =========================================================================
# Step output reference tests (Requirement 3.5)
# =========================================================================

def test_step_output_field_reference():
    """
        Verify that steps.<step_id>.<field> resolves to the correct
        value from the context.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.score == 85", ctx)

    assert result is True, \
        "steps.step_a.score should resolve to 85"
    return


def test_step_output_string_field_reference():
    """
        Verify that string step output fields can be compared.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.status == 'ok'", ctx)

    assert result is True, \
        "steps.step_a.status should resolve to 'ok'"
    return


# =========================================================================
# Input reference tests (Requirement 3.6)
# =========================================================================

def test_input_field_reference():
    """
        Verify that inputs.<field> resolves to the correct value
        from the context inputs.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("inputs.threshold == 50", ctx)

    assert result is True, \
        "inputs.threshold should resolve to 50"
    return


def test_input_string_field_reference():
    """
        Verify that string input fields can be compared.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("inputs.mode == 'fast'", ctx)

    assert result is True, \
        "inputs.mode should resolve to 'fast'"
    return


# =========================================================================
# Comparison operator tests (Requirement 3.7)
# =========================================================================

def test_equality_operator():
    """
        Verify the == operator evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.score == 85", ctx)

    assert result is True, "== should return True for equal values"
    return


def test_inequality_operator():
    """
        Verify the != operator evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.score != 100", ctx)

    assert result is True, "!= should return True for unequal values"
    return


def test_less_than_operator():
    """
        Verify the < operator evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_b.score < 50", ctx)

    assert result is True, "< should return True when left < right"
    return


def test_greater_than_operator():
    """
        Verify the > operator evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.score > 50", ctx)

    assert result is True, "> should return True when left > right"
    return


def test_less_than_or_equal_operator():
    """
        Verify the <= operator evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_b.score <= 40", ctx)

    assert result is True, "<= should return True when left <= right"
    return


def test_greater_than_or_equal_operator():
    """
        Verify the >= operator evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.score >= 85", ctx)

    assert result is True, ">= should return True when left >= right"
    return


def test_comparison_returns_false():
    """
        Verify that a comparison returns False when the condition
        is not met.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("steps.step_a.score < 50", ctx)

    assert result is False, \
        "< should return False when left is not less than right"
    return


# =========================================================================
# Logical operator tests (Requirement 3.8)
# =========================================================================

def test_and_operator_both_true():
    """
        Verify the 'and' operator returns True when both operands
        are True.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "steps.step_a.score > 50 and steps.step_b.score < 50", ctx
    )

    assert result is True, \
        "and should return True when both conditions are True"
    return


def test_and_operator_one_false():
    """
        Verify the 'and' operator returns False when one operand
        is False.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "steps.step_a.score > 50 and steps.step_b.score > 50", ctx
    )

    assert result is False, \
        "and should return False when one condition is False"
    return


def test_or_operator_one_true():
    """
        Verify the 'or' operator returns True when at least one
        operand is True.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "steps.step_a.score > 100 or steps.step_b.score < 50", ctx
    )

    assert result is True, \
        "or should return True when at least one condition is True"
    return


def test_or_operator_both_false():
    """
        Verify the 'or' operator returns False when both operands
        are False.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "steps.step_a.score > 100 or steps.step_b.score > 100", ctx
    )

    assert result is False, \
        "or should return False when both conditions are False"
    return


def test_not_operator():
    """
        Verify the 'not' operator negates the operand.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "not steps.step_b.score > 50", ctx
    )

    assert result is True, \
        "not should negate the operand"
    return


# =========================================================================
# Membership operator tests (Requirement 3.9)
# =========================================================================

def test_in_operator_with_list_literal():
    """
        Verify the 'in' operator works with list literals.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "steps.step_a.status in ['ok', 'done']", ctx
    )

    assert result is True, \
        "in should return True when value is in the list"
    return


def test_in_operator_not_in_list():
    """
        Verify the 'in' operator returns False when value is not
        in the list.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "steps.step_a.status in ['error', 'failed']", ctx
    )

    assert result is False, \
        "in should return False when value is not in the list"
    return


def test_in_operator_with_step_output_list():
    """
        Verify the 'in' operator works with step output lists.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "'alpha' in steps.step_a.tags", ctx
    )

    assert result is True, \
        "in should return True when value is in step output list"
    return


# =========================================================================
# Unsafe expression rejection tests (Requirement 3.10)
# =========================================================================

def test_rejects_function_call():
    """
        Verify that function calls are rejected with
        WorkflowDefinitionError.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate("len([1, 2, 3]) > 0", ctx)
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "Function calls should raise WorkflowDefinitionError"
    return


def test_rejects_import_expression():
    """
        Verify that import-like expressions are rejected.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate("__import__('os')", ctx)
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "Import expressions should raise WorkflowDefinitionError"
    return


def test_rejects_arbitrary_attribute_access():
    """
        Verify that attribute access beyond allowed patterns is
        rejected.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate(
            "steps.step_a.score.__class__.__name__ == 'int'", ctx
        )
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "Deep attribute access should raise WorkflowDefinitionError"
    return


def test_rejects_dunder_attribute():
    """
        Verify that dunder attributes on step outputs are rejected.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate("steps.step_a.__class__", ctx)
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "Dunder attributes should raise WorkflowDefinitionError"
    return


def test_rejects_eval_call():
    """
        Verify that eval() calls are rejected.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate("eval('1+1')", ctx)
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "eval() calls should raise WorkflowDefinitionError"
    return


# =========================================================================
# WorkflowExecutionError for unresolved step references (Req 3.11)
# =========================================================================

def test_unresolved_step_reference_raises_execution_error():
    """
        Verify that referencing a step that has not been executed
        raises WorkflowExecutionError.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate(
            "steps.nonexistent_step.result == 'ok'", ctx
        )
    except WorkflowExecutionError:
        raised = True

    assert raised is True, \
        "Unresolved step reference should raise WorkflowExecutionError"
    return


# =========================================================================
# WorkflowDefinitionError for invalid syntax (Requirement 3.12)
# =========================================================================

def test_invalid_syntax_raises_definition_error():
    """
        Verify that invalid expression syntax raises
        WorkflowDefinitionError.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate("steps.step_a.score ==", ctx)
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "Invalid syntax should raise WorkflowDefinitionError"
    return


def test_empty_expression_raises_definition_error():
    """
        Verify that an empty expression raises
        WorkflowDefinitionError.
    """
    ctx = _make_context()
    raised = False

    try:
        _evaluator.evaluate("", ctx)
    except WorkflowDefinitionError:
        raised = True

    assert raised is True, \
        "Empty expression should raise WorkflowDefinitionError"
    return


# =========================================================================
# __repr__ and __str__ tests
# =========================================================================

def test_repr():
    """
        Verify that __repr__ returns the expected format.
    """
    evaluator = ConditionEvaluator()
    repr_str = repr(evaluator)

    assert "ConditionEvaluator" in repr_str, \
        "__repr__ should contain the class name"
    return


def test_str():
    """
        Verify that __str__ returns a human-readable summary.
    """
    evaluator = ConditionEvaluator()
    str_val = str(evaluator)

    assert "ConditionEvaluator" in str_val, \
        "__str__ should contain the class name"
    return


# =========================================================================
# Combined expression tests
# =========================================================================

def test_combined_and_or_not():
    """
        Verify that combined logical operators work correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate(
        "(steps.step_a.score > 50 and inputs.mode == 'fast') "
        "or not steps.step_b.score > 100",
        ctx
    )

    assert result is True, \
        "Combined logical expression should evaluate correctly"
    return


def test_literal_boolean_true():
    """
        Verify that literal True evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("True", ctx)

    assert result is True, \
        "Literal True should evaluate to True"
    return


def test_literal_boolean_false():
    """
        Verify that literal False evaluates correctly.
    """
    ctx = _make_context()
    result = _evaluator.evaluate("False", ctx)

    assert result is False, \
        "Literal False should evaluate to False"
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
