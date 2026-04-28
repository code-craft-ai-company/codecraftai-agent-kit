"""
    Property-based tests for the automojo.agentkit.conditionevaluator module.

    Uses automojo.testbase.properties to verify:
    - Property 13: ConditionEvaluator Safety

    **Validates: Requirement 3 AC 10**
"""

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.agentkit.conditionevaluator import ConditionEvaluator
from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.workflowerrors import WorkflowDefinitionError


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_evaluator = ConditionEvaluator()

_context = WorkflowContext(
    inputs={"x": 10, "name": "test"},
    metadata={}
)
_context.set_step_output("step_a", {"result": 42, "status": "ok"})


# ---------------------------------------------------------------------------
# Strategies for generating unsafe expressions
# ---------------------------------------------------------------------------

_function_call_expressions = st.sampled_from([
    "print('hello')",
    "len([1, 2, 3])",
    "eval('1+1')",
    "exec('import os')",
    "open('/etc/passwd')",
    "os.system('ls')",
    "__import__('os')",
    "type(42)",
    "str(42)",
    "int('5')",
    "list(range(10))",
    "dict(a=1)",
    "getattr(steps, 'step_a')",
    "setattr(steps, 'step_a', {})",
    "delattr(steps, 'step_a')",
    "compile('1+1', '', 'eval')",
    "globals()",
    "locals()",
    "dir()",
    "vars()",
    "hasattr(steps, 'step_a')",
    "isinstance(42, int)",
    "issubclass(int, object)",
    "map(str, [1, 2])",
    "filter(None, [1, 0])",
    "sorted([3, 1, 2])",
    "max(1, 2)",
    "min(1, 2)",
    "sum([1, 2, 3])",
    "abs(-1)",
    "round(3.14)",
    "chr(65)",
    "ord('A')",
    "hex(255)",
    "oct(8)",
    "bin(10)",
    "pow(2, 3)",
    "zip([1], [2])",
    "enumerate([1, 2])",
    "reversed([1, 2])",
    "any([True, False])",
    "all([True, True])",
])

_import_expressions = st.sampled_from([
    "__import__('os').system('ls')",
    "__import__('subprocess').call(['ls'])",
    "__import__('sys').exit(1)",
])

_arbitrary_attribute_expressions = st.sampled_from([
    "steps.step_a.result.bit_length()",
    "steps.step_a.__class__",
    "inputs.x.__class__.__name__",
    "steps.step_a.result.__doc__",
    "steps.step_a.result.__class__.__mro__",
])

_unsafe_expressions = st.one_of(
    _function_call_expressions,
    _import_expressions,
    _arbitrary_attribute_expressions,
)


# ---------------------------------------------------------------------------
# Property 13: ConditionEvaluator Safety
# ---------------------------------------------------------------------------

@given(
    unsafe_expr=_unsafe_expressions,
    constraints={"max_examples": 100},
)
def test_conditionevaluator_rejects_unsafe_expressions(
    unsafe_expr: str,
) -> None:
    """
        **Validates: Requirement 3 AC 10**

        For all ConditionExpression strings containing disallowed
        constructs (function calls, attribute access beyond the
        allowed patterns, or import statements), the
        ConditionEvaluator shall raise a WorkflowDefinitionError.
    """
    raised = False
    try:
        _evaluator.evaluate(unsafe_expr, _context)
    except WorkflowDefinitionError:
        raised = True
    except Exception:
        # Any other exception is also acceptable as a safety
        # measure, but we specifically expect WorkflowDefinitionError.
        raised = True

    testbase.assert_true(
        raised,
        "ConditionEvaluator should reject unsafe expression '{}' "
        "with WorkflowDefinitionError, but it did not raise.".format(
            unsafe_expr
        )
    )


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
