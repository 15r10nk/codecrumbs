import inspect
import io
import warnings
from contextlib import redirect_stdout

import pytest
from codecrumbs._calling_expression import calling_expression
from codecrumbs._rewrite_code import replace
from codecrumbs._rewrite_code import rewrite


@pytest.fixture
def rewrite_test(tmp_path):
    idx = 0

    def test(old_code, new_code=None, statement=False):
        def internal(old_code, new_code):
            frame = inspect.currentframe().f_back.f_back

            nonlocal idx
            filename = tmp_path / f"test_{idx}.py"
            idx += 1

            filename.write_bytes(old_code.encode())
            assert old_code.encode() == filename.read_bytes()

            d = dict(frame.f_globals)
            l = dict(frame.f_locals)

            first_output = io.StringIO()
            with redirect_stdout(first_output):
                code = compile(filename.read_bytes(), str(filename), "exec")
                d["__file__"] = str(filename)
                exec(code, d, l)

            rewrite(filename)

            assert (
                filename.read_bytes() == new_code.encode()
            ), f"{filename.read_bytes()} != {new_code.encode()}"

        internal(old_code + "\n", new_code + "\n")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if not statement:
                internal(f"print({old_code})\n", f"print({new_code})\n")

            internal(old_code.strip(), new_code.strip())

    yield test


def inc_number(n):
    expr = calling_expression()
    expr.dump()
    replace(expr.expr.args[0], n + 1)
    return n


def test_inc_number(rewrite_test):
    rewrite_test(
        "inc_number(6)",
        "inc_number(7)",
    )
    rewrite_test(
        "inc_number(6)",
        "inc_number(7)",
    )
    rewrite_test(
        "inc_number(6)\r",
        "inc_number(7)\r",
    )
    rewrite_test(
        "inc_number(6)\rinc_number(6)\n\rinc_number(6)",
        "inc_number(7)\rinc_number(7)\n\rinc_number(7)",
        statement=True,
    )

    rewrite_test(
        "inc_number(6)#comment",
        "inc_number(7)#comment",
        statement=True,
    )


def test_overlapping(rewrite_test):
    with pytest.raises(AssertionError):
        rewrite_test(
            "inc_number(inc_number(6))",
            "inc_number(inc_number(7))",
        )
