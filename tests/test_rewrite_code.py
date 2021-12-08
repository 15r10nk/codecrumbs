import inspect
import io
from contextlib import redirect_stdout

import pytest

from breadcrumes._calling_expression import calling_expression
from breadcrumes._rewrite_code import replace, rewrite


@pytest.fixture
def rewrite_test(tmp_path):
    idx = 0

    def test(old_code, new_code=None, statement=False, cmp_output=True):
        def internal(old_code, new_code):
            frame = inspect.currentframe().f_back.f_back

            nonlocal idx
            filename = tmp_path / f"test_{idx}.py"
            idx += 1

            filename.write_text(old_code)
            assert old_code.encode() == filename.read_bytes()

            d = dict(frame.f_globals)
            l = dict(frame.f_locals)

            def run():
                code = compile(filename.read_bytes(), str(filename), "exec")
                d["__file__"] = str(filename)
                exec(code, d, l)

            def second_run():
                rewrite(filename)
                if cmp_output:
                    second_output = io.StringIO()
                    with redirect_stdout(second_output):
                        with pytest.warns(None):
                            run()
                    assert first_output.getvalue() == second_output.getvalue()

                assert (
                    filename.read_bytes() == new_code.encode()
                ), f"{filename.read_bytes()} != {new_code.encode()}"

            try:
                first_output = io.StringIO()
                with redirect_stdout(first_output):
                    run()

            except Exception as e:
                second_run()
                raise
            else:
                second_run()

        if new_code == None:
            new_code = old_code

        internal(old_code + "\n", new_code + "\n")
        with pytest.warns(None):
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
    rewrite_test("inc_number(6)", "inc_number(7)", cmp_output=False)
    rewrite_test("inc_number(6)", "inc_number(7)", cmp_output=False)
    rewrite_test("inc_number(6)\r", "inc_number(7)\r", cmp_output=False)
    rewrite_test(
        "inc_number(6)\rinc_number(6)\n\rinc_number(6)",
        "inc_number(7)\rinc_number(7)\n\rinc_number(7)",
        statement=True,
        cmp_output=False,
    )

    rewrite_test(
        "inc_number(6)#comment",
        "inc_number(7)#comment",
        statement=True,
        cmp_output=False,
    )


def test_overlapping(rewrite_test):
    with pytest.raises(AssertionError):
        rewrite_test(
            "inc_number(inc_number(6))", "inc_number(inc_number(7))", cmp_output=False
        )
