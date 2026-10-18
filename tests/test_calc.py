import math

import pytest

from tsagent.calc import CalcError, safe_eval


@pytest.mark.parametrize("expr,val", [
    ("2+3*4", 14), ("(2+3)*4", 20), ("600/5*3.5", 420), ("ct_primary(600, 5, 3.5)", 420),
    ("pct_error(4.18, 4.00)", 4.5), ("p3(480, 52, 0.85)/1000", math.sqrt(3) * 480 * 52 * 0.85 / 1000),
    ("ohms_r(120, 0.25)", 480), ("ohms_v(2, 10)", 20), ("ohms_i(120, 480)", 0.25), ("330/150", 2.2),
    ("sqrt3*480", math.sqrt(3) * 480), ("2^10", 1024), ("-5 + abs(-2)", -3), ("12 × 2 ÷ 4", 6),
])
def test_values(expr, val):
    assert safe_eval(expr) == pytest.approx(val)


@pytest.mark.parametrize("expr", [
    "__import__('os').system('ls')", "open('/etc/passwd')", "x + 1", "primary = 600/5", "1/0",
    "9**9**9", "().__class__", "lambda: 1", "[1,2]", "pct_error(1, 0)", "'a'*3", "1" + "+1" * 150,
])
def test_rejects_unsafe_or_invalid(expr):
    with pytest.raises(CalcError):
        safe_eval(expr)
