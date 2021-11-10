import inspect

import pytest

from breadcrumes._calling_expression import calling_expression
from breadcrumes._rewrite_code import replace, rewrite


def inc_number(n):
    expr = calling_expression()
    expr.dump()
    replace(expr.expr.args[0], n + 1)
    return n


@pytest.fixture
def rewrite_test(tmp_path):
    idx = 0

    def test(old_code, new_code=None):
        if new_code == None:
            new_code = old_code

        old_code += "\n"
        new_code += "\n"

        frame = inspect.currentframe().f_back
        nonlocal idx
        filename = tmp_path / f"test_{idx}.py"
        idx += 1

        filename.write_text(old_code)
        assert old_code.encode() == filename.read_bytes()

        code = compile(old_code, str(filename), "exec")
        d = dict(frame.f_globals)
        l = dict(frame.f_locals)
        d["__file__"] = str(filename)
        try:
            with pytest.warns(None):
                exec(code, d, l)
        except Exception as e:
            rewrite(filename)
            assert (
                filename.read_bytes() == old_code.encode()
            ), f"{filename.read_bytes()} != {new_code.encode()}"
            raise
        else:
            rewrite(filename)
            assert (
                filename.read_bytes() == new_code.encode()
            ), f"{filename.read_bytes()} != {new_code.encode()}"

    yield test


def test_inc_number(rewrite_test):
    rewrite_test("inc_number(6)", "inc_number(7)")
    rewrite_test("inc_number(6)", "inc_number(7)")
    rewrite_test("inc_number(6)\r", "inc_number(7)\r")
    rewrite_test(
        "inc_number(6)\rinc_number(6)\n\rinc_number(6)",
        "inc_number(7)\rinc_number(7)\n\rinc_number(7)",
    )

    rewrite_test("inc_number(6)#comment", "inc_number(7)#comment")


def test_overlapping(rewrite_test):
    with pytest.raises(AssertionError):
        rewrite_test("inc_number(inc_number(6))", "inc_number(inc_number(7))")
