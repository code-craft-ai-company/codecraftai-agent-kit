"""
    Defines the ConditionEvaluator class for safe evaluation of
    condition expression strings against a WorkflowContext.

    The ConditionEvaluator parses expressions using the Python ast
    module and validates that only allowed constructs are present
    before evaluating. Supported constructs include step output
    references (steps.<step_id>.<field>), workflow input references
    (inputs.<field>), comparison operators, logical operators, and
    the membership operator.

    Any expression containing disallowed constructs such as function
    calls, import statements, or arbitrary attribute access raises a
    WorkflowDefinitionError. References to steps that have not been
    executed raise a WorkflowExecutionError.

    Requirements: 3.3-3.12
"""

import ast
import operator

from typing import Any

from automojo.agentkit.workflowcontext import WorkflowContext
from automojo.agentkit.workflowerrors import WorkflowDefinitionError
from automojo.agentkit.workflowerrors import WorkflowExecutionError


# Mapping of AST comparison operator types to Python operator functions.
_COMPARISON_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.Gt: operator.gt,
    ast.LtE: operator.le,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
}

# Mapping of AST boolean operator types to Python logical functions.
_BOOL_OPS = {
    ast.And: all,
    ast.Or: any,
}

# Mapping of AST unary operator types to Python unary functions.
_UNARY_OPS = {
    ast.Not: operator.not_,
}

# The set of AST node types that are allowed in condition expressions.
_ALLOWED_NODE_TYPES = frozenset({
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.UnaryOp,
    ast.Not,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.Gt,
    ast.LtE,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Attribute,
    ast.Name,
    ast.Constant,
    ast.Load,
    ast.List,
    ast.Tuple,
})



class ConditionEvaluator:
    """
        Evaluates ConditionExpression strings against a WorkflowContext.

        The evaluator restricts evaluation to a safe subset of Python
        expressions. It parses the expression into an AST, validates
        that only allowed node types are present, resolves step output
        and workflow input references from the context, and evaluates
        the expression to produce a boolean result.

        Supported constructs:

        - Step output references: ``steps.<step_id>.<output_field>``
        - Workflow input references: ``inputs.<field_name>``
        - Comparison operators: ``==``, ``!=``, ``<``, ``>``, ``<=``, ``>=``
        - Logical operators: ``and``, ``or``, ``not``
        - Membership operator: ``in``
        - Literal values: strings, integers, floats, booleans, None
        - List and tuple literals containing allowed values

        Disallowed constructs include function calls, import statements,
        subscript access, assignment, augmented assignment, and attribute
        access beyond the allowed patterns.

        :raises WorkflowDefinitionError: When the expression contains
            invalid syntax or disallowed constructs.
        :raises WorkflowExecutionError: When the expression references
            a step that has not been executed.
    """

    ALLOWED_OPERATORS = {
        "==", "!=", "<", ">", "<=", ">=",
        "and", "or", "not", "in"
    }

    def evaluate(self, expression: str, context: WorkflowContext) -> bool:
        """
            Evaluates a condition expression against the workflow context.

            Parses the expression string into an AST, validates that
            only allowed constructs are present, resolves step output
            and workflow input references from the context, and
            evaluates the expression to produce a boolean result.

            :param expression: The condition expression string to
                evaluate.
            :param context: The WorkflowContext containing inputs
                and step outputs to resolve references against.

            :returns: True when the condition is satisfied, False
                otherwise.

            :raises WorkflowDefinitionError: When the expression
                contains invalid syntax or disallowed constructs.
            :raises WorkflowExecutionError: When the expression
                references a step identifier that has not been
                executed.
        """
        tree = self._parse_expression(expression)
        self._validate_ast(tree, expression)
        result = self._evaluate_node(tree.body, context, expression)
        return bool(result)

    def _parse_expression(self, expression: str) -> ast.Expression:
        """
            Parses the expression string into an AST Expression node.

            :param expression: The condition expression string.

            :returns: An ast.Expression node representing the parsed
                expression.

            :raises WorkflowDefinitionError: When the expression
                contains invalid Python syntax.
        """
        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError as syn_err:
            detail = "Invalid expression syntax '{}': {}".format(
                expression, syn_err.msg
            )
            raise WorkflowDefinitionError(
                workflow_name="(condition)", detail=detail
            ) from syn_err

        return tree

    def _validate_ast(self, tree: ast.Expression,
                      expression: str) -> None:
        """
            Walks the AST and validates that every node is an allowed
            type. Raises WorkflowDefinitionError when a disallowed
            construct is found.

            :param tree: The parsed AST Expression node.
            :param expression: The original expression string for
                error reporting.

            :raises WorkflowDefinitionError: When the AST contains
                disallowed node types.
        """
        for node in ast.walk(tree):
            node_type = type(node)

            if node_type not in _ALLOWED_NODE_TYPES:
                detail = (
                    "Expression '{}' contains disallowed construct: "
                    "{}".format(expression, node_type.__name__)
                )
                raise WorkflowDefinitionError(
                    workflow_name="(condition)", detail=detail
                )

            # Validate that Attribute nodes only access allowed
            # patterns: steps.<id>.<field> or inputs.<field>.
            if node_type is ast.Attribute:
                self._validate_attribute_access(node, expression)

        return

    def _validate_attribute_access(self, node: ast.Attribute,
                                   expression: str) -> None:
        """
            Validates that an Attribute node conforms to one of the
            allowed access patterns:

            - ``steps.<step_id>.<output_field>`` (three-level)
            - ``inputs.<field_name>`` (two-level)
            - ``steps.<step_id>`` (intermediate two-level for the
              three-level pattern)

            :param node: The ast.Attribute node to validate.
            :param expression: The original expression string for
                error reporting.

            :raises WorkflowDefinitionError: When the attribute
                access does not match an allowed pattern.
        """
        chain = self._resolve_attribute_chain(node)

        if chain is None:
            detail = (
                "Expression '{}' contains disallowed attribute "
                "access".format(expression)
            )
            raise WorkflowDefinitionError(
                workflow_name="(condition)", detail=detail
            )

        root_name = chain[0]
        depth = len(chain)

        if root_name == "inputs" and depth == 2:
            # inputs.<field_name> — valid two-level access, but
            # reject dunder attributes.
            field_name = chain[1]
            if field_name.startswith("__") and field_name.endswith("__"):
                detail = (
                    "Expression '{}' contains disallowed dunder "
                    "attribute access: {}".format(
                        expression, ".".join(chain)
                    )
                )
                raise WorkflowDefinitionError(
                    workflow_name="(condition)", detail=detail
                )
            return

        if root_name == "steps" and depth in (2, 3):
            # steps.<step_id> or steps.<step_id>.<field> — valid,
            # but reject dunder attributes which could access
            # internal Python machinery.
            for part in chain[1:]:
                if part.startswith("__") and part.endswith("__"):
                    detail = (
                        "Expression '{}' contains disallowed dunder "
                        "attribute access: {}".format(
                            expression, ".".join(chain)
                        )
                    )
                    raise WorkflowDefinitionError(
                        workflow_name="(condition)", detail=detail
                    )
            return

        detail = (
            "Expression '{}' contains disallowed attribute access "
            "pattern: {}".format(expression, ".".join(chain))
        )
        raise WorkflowDefinitionError(
            workflow_name="(condition)", detail=detail
        )

    def _resolve_attribute_chain(self, node: ast.Attribute):
        """
            Resolves an Attribute node into a list of name strings
            representing the dotted access chain.

            For example, ``steps.step_a.result`` resolves to
            ``["steps", "step_a", "result"]``.

            :param node: The ast.Attribute node to resolve.

            :returns: A list of name strings, or None when the chain
                contains non-Name/Attribute nodes.
        """
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)
            parts.reverse()
            return parts

        return None

    def _evaluate_node(self, node: ast.AST,
                       context: WorkflowContext,
                       expression: str) -> Any:
        """
            Recursively evaluates an AST node against the workflow
            context.

            :param node: The AST node to evaluate.
            :param context: The WorkflowContext for resolving
                references.
            :param expression: The original expression string for
                error reporting.

            :returns: The evaluated value of the node.

            :raises WorkflowExecutionError: When a step reference
                cannot be resolved.
            :raises WorkflowDefinitionError: When an unexpected
                node type is encountered.
        """
        node_type = type(node)

        if node_type is ast.Constant:
            return node.value

        if node_type is ast.Name:
            return self._resolve_name(node, context, expression)

        if node_type is ast.Attribute:
            return self._resolve_attribute(node, context, expression)

        if node_type is ast.Compare:
            return self._evaluate_compare(node, context, expression)

        if node_type is ast.BoolOp:
            return self._evaluate_boolop(node, context, expression)

        if node_type is ast.UnaryOp:
            return self._evaluate_unaryop(node, context, expression)

        if node_type is ast.List:
            return [
                self._evaluate_node(elt, context, expression)
                for elt in node.elts
            ]

        if node_type is ast.Tuple:
            return tuple(
                self._evaluate_node(elt, context, expression)
                for elt in node.elts
            )

        detail = (
            "Expression '{}' contains unsupported construct: "
            "{}".format(expression, node_type.__name__)
        )
        raise WorkflowDefinitionError(
            workflow_name="(condition)", detail=detail
        )

    def _resolve_name(self, node: ast.Name,
                      context: WorkflowContext,
                      expression: str) -> Any:
        """
            Resolves a bare Name node. Only ``True``, ``False``, and
            ``None`` are allowed as standalone names. The names
            ``steps`` and ``inputs`` are not valid as standalone
            references — they must be followed by attribute access.

            :param node: The ast.Name node to resolve.
            :param context: The WorkflowContext (unused for literal
                names).
            :param expression: The original expression string for
                error reporting.

            :returns: The resolved value.

            :raises WorkflowDefinitionError: When the name is not
                an allowed literal.
        """
        name = node.id

        if name == "True":
            return True
        if name == "False":
            return False
        if name == "None":
            return None

        detail = (
            "Expression '{}' contains unresolved name: "
            "'{}'".format(expression, name)
        )
        raise WorkflowDefinitionError(
            workflow_name="(condition)", detail=detail
        )

    def _resolve_attribute(self, node: ast.Attribute,
                           context: WorkflowContext,
                           expression: str) -> Any:
        """
            Resolves an Attribute node against the workflow context.

            Handles the patterns:
            - ``inputs.<field_name>`` — returns the input value.
            - ``steps.<step_id>.<output_field>`` — returns the step
              output field value.

            :param node: The ast.Attribute node to resolve.
            :param context: The WorkflowContext for resolving
                references.
            :param expression: The original expression string for
                error reporting.

            :returns: The resolved value from the context.

            :raises WorkflowExecutionError: When a step reference
                cannot be resolved.
        """
        chain = self._resolve_attribute_chain(node)
        root_name = chain[0]

        if root_name == "inputs":
            field_name = chain[1]
            value = context.get_input(field_name)
            return value

        if root_name == "steps":
            step_id = chain[1]
            step_output = context.get_step_output(step_id)

            if step_output is None:
                raise WorkflowExecutionError(
                    workflow_name="(condition)",
                    step_id=step_id,
                    cause=ValueError(
                        "Step '{}' has not been executed; cannot "
                        "resolve reference in expression "
                        "'{}'".format(step_id, expression)
                    )
                )

            if len(chain) == 3:
                field_name = chain[2]
                value = step_output.get(field_name)
                return value

            # Two-level steps.<step_id> returns the full output dict.
            return step_output

        detail = (
            "Expression '{}' contains unresolved reference: "
            "'{}'".format(expression, ".".join(chain))
        )
        raise WorkflowDefinitionError(
            workflow_name="(condition)", detail=detail
        )

    def _evaluate_compare(self, node: ast.Compare,
                          context: WorkflowContext,
                          expression: str) -> bool:
        """
            Evaluates a Compare node (e.g. ``a == b``, ``a < b < c``,
            ``x in [1, 2, 3]``).

            Supports chained comparisons by evaluating each pair of
            operands with the corresponding operator.

            :param node: The ast.Compare node to evaluate.
            :param context: The WorkflowContext for resolving
                references.
            :param expression: The original expression string for
                error reporting.

            :returns: True when all comparisons are satisfied.
        """
        left = self._evaluate_node(node.left, context, expression)

        for cmp_op, comparator in zip(node.ops, node.comparators):
            right = self._evaluate_node(
                comparator, context, expression
            )
            op_func = _COMPARISON_OPS.get(type(cmp_op))

            if op_func is None:
                detail = (
                    "Expression '{}' contains unsupported comparison "
                    "operator: {}".format(
                        expression, type(cmp_op).__name__
                    )
                )
                raise WorkflowDefinitionError(
                    workflow_name="(condition)", detail=detail
                )

            if not op_func(left, right):
                return False

            left = right

        return True

    def _evaluate_boolop(self, node: ast.BoolOp,
                         context: WorkflowContext,
                         expression: str) -> bool:
        """
            Evaluates a BoolOp node (``and`` / ``or``).

            Uses short-circuit evaluation: for ``and``, returns False
            as soon as a falsy value is found; for ``or``, returns
            True as soon as a truthy value is found.

            :param node: The ast.BoolOp node to evaluate.
            :param context: The WorkflowContext for resolving
                references.
            :param expression: The original expression string for
                error reporting.

            :returns: The boolean result of the logical operation.
        """
        if isinstance(node.op, ast.And):
            for value_node in node.values:
                result = self._evaluate_node(
                    value_node, context, expression
                )
                if not result:
                    return False
            return True

        if isinstance(node.op, ast.Or):
            for value_node in node.values:
                result = self._evaluate_node(
                    value_node, context, expression
                )
                if result:
                    return True
            return False

        detail = (
            "Expression '{}' contains unsupported boolean "
            "operator: {}".format(
                expression, type(node.op).__name__
            )
        )
        raise WorkflowDefinitionError(
            workflow_name="(condition)", detail=detail
        )

    def _evaluate_unaryop(self, node: ast.UnaryOp,
                          context: WorkflowContext,
                          expression: str) -> Any:
        """
            Evaluates a UnaryOp node (``not``).

            :param node: The ast.UnaryOp node to evaluate.
            :param context: The WorkflowContext for resolving
                references.
            :param expression: The original expression string for
                error reporting.

            :returns: The result of applying the unary operator.
        """
        operand = self._evaluate_node(
            node.operand, context, expression
        )
        op_func = _UNARY_OPS.get(type(node.op))

        if op_func is None:
            detail = (
                "Expression '{}' contains unsupported unary "
                "operator: {}".format(
                    expression, type(node.op).__name__
                )
            )
            raise WorkflowDefinitionError(
                workflow_name="(condition)", detail=detail
            )

        result = op_func(operand)
        return result

    def __repr__(self) -> str:
        """
            Returns a detailed string representation of the
            ConditionEvaluator.

            :returns: A repr string for debugging.
        """
        repr_str = "{}()".format(self.__class__.__name__)
        return repr_str

    def __str__(self) -> str:
        """
            Returns a human-readable summary of the
            ConditionEvaluator.

            :returns: A human-readable string describing the
                evaluator.
        """
        str_val = "ConditionEvaluator: safe expression evaluator"
        return str_val
