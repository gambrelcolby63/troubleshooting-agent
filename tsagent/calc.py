"""Safe arithmetic evaluator (AST whitelist, no eval/exec) with a few electrical helper functions."""
from __future__ import annotations

import ast
import math
import operator

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.FloorDiv: operator.floordiv}
_UN = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def pct_error(measured, expected):
    """(measured - expected) / expected * 100"""
    if expected == 0:
        raise ValueError("expected value must be non-zero")
    return (measured - expected) / expected * 100


def ct_primary(ratio_primary, ratio_secondary, secondary_amps):
    """Primary current from a CT ratio such as 600:5 and a measured secondary current."""
    return secondary_amps * ratio_primary / ratio_secondary


def p3(volts_ll, amps, pf=1.0):
    """Three-phase real power in watts: sqrt(3) * V_LL * I * pf."""
    return math.sqrt(3) * volts_ll * amps * pf


def ohms_v(i, r): return i * r          # V = I R
def ohms_i(v, r): return v / r          # I = V / R
def ohms_r(v, i): return v / i          # R = V / I


FUNCS = {"sqrt": math.sqrt, "abs": abs, "round": round, "min": min, "max": max, "log10": math.log10,
         "pct_error": pct_error, "ct_primary": ct_primary, "p3": p3, "ohms_v": ohms_v, "ohms_i": ohms_i,
         "ohms_r": ohms_r}
CONSTS = {"pi": math.pi, "sqrt3": math.sqrt(3)}


class CalcError(ValueError):
    pass


def _ev(node):
    if isinstance(node, ast.Expression):
        return _ev(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _ev(node.left), _ev(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > 100 or abs(left) > 1e6):
            raise CalcError("exponent too large")
        return _BIN[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
        return _UN[type(node.op)](_ev(node.operand))
    if isinstance(node, ast.Name) and node.id in CONSTS:
        return CONSTS[node.id]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
        return FUNCS[node.func.id](*[_ev(a) for a in node.args])
    raise CalcError(f"unsupported expression element: {type(node).__name__}")


def safe_eval(expr: str) -> float:
    expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**").strip()
    if len(expr) > 200:
        raise CalcError("expression too long")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise CalcError("syntax error") from None
    try:
        val = _ev(tree)
    except ZeroDivisionError:
        raise CalcError("division by zero") from None
    except (TypeError, ValueError) as e:
        if isinstance(e, CalcError):
            raise
        raise CalcError(str(e)) from None
    if isinstance(val, complex):
        raise CalcError("complex result")
    return val
