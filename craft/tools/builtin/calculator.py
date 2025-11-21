"""Calculator tool for safe mathematical expression evaluation."""

import ast
import operator
from typing import Union
from craft.tools import tool


# Safe operators for evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    """Safely evaluate an AST node."""
    if isinstance(node, ast.Constant):  # Python 3.8+
        return node.value
    elif isinstance(node, ast.Num):  # Python 3.7
        return node.n
    elif isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op = SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(operand)
    else:
        raise ValueError(f"Unsupported expression: {type(node).__name__}")


@tool
def calculate(expression: str) -> Union[int, float]:
    """
    Safely evaluate a mathematical expression.

    Supports basic arithmetic operations: +, -, *, /, //, %, **
    Does NOT support: function calls, variable assignment, imports, or any code execution

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2 * 3")

    Returns:
        Result of the calculation

    Raises:
        ValueError: If expression contains unsupported operations or syntax errors
    """
    try:
        # Parse the expression into an AST
        tree = ast.parse(expression, mode="eval")

        # Evaluate safely
        result = _safe_eval(tree.body)

        return result
    except SyntaxError as e:
        raise ValueError(f"Invalid expression syntax: {e}")
    except Exception as e:
        raise ValueError(f"Calculation error: {e}")
