"""
PYTEST_DONT_REWRITE
"""
import ast
import sys

import pytest
from codecrumbs._calling_expression import calling_expression


def test_lambda_problem():
    [lambda: never_called(), lambda: never_called()]

    def foo():
        expr = calling_expression().expr
        # assert expr.func.id == "foo"

    foo()


def test_lambda_in_parent_function():
    [lambda: never_called(), lambda: never_called()]

    def w():
        def foo():
            expr = calling_expression().expr
            assert expr.func.id == "foo"

        foo()

    w()


def test_function():
    def foo():
        expr = calling_expression().expr
        assert expr.func.id == "foo"

    foo()


def test_pytest_assert_rewriting():
    def linenumber():
        return calling_expression().expr.lineno

    lineno = linenumber()

    def foo():
        expr = calling_expression().expr
        assert expr.func.id == "foo"
        assert expr.lineno == lineno + 8
        return 1

    assert foo() in [5, 8, 1, 7] and "lge" in "lfcgflgeaegleg"


def test_add():
    class foo:
        def __add__(self, other):
            expr = calling_expression().expr
            expr = calling_expression().expr
            assert isinstance(expr, ast.BinOp)
            assert isinstance(expr.op, ast.Add)
            assert expr.left.id == "f"
            assert expr.right.value == 1

    f = foo()
    f + 1


@pytest.mark.xfail(
    sys.version_info < (3, 11), reason="iadd does not work with old executing algo"
)
def test_iadd():
    class foo:
        def __iadd__(self, other):
            expr = calling_expression().expr
            assert isinstance(expr, ast.AugAssign)
            assert isinstance(expr.op, ast.Add)
            assert expr.target.id == "f"
            assert expr.value.value == 1

    f = foo()
    f += 1


def test_method():
    class foo:
        def m(self, i):
            expr = calling_expression()
            expr.dump()
            expr = expr.expr
            assert isinstance(expr, ast.Call), expr
            assert expr.args[0].value == i
            assert expr.func.attr == "m"

    f = foo()
    f.m(1)


def test_init():
    class foo:
        def __init__(self, i):
            expr = calling_expression().expr
            assert isinstance(expr, ast.Call)
            assert expr.args[0].value == i
            assert expr.func.id == "foo"

    f = foo(1)


def test_property():
    class foo:
        @property
        def m(self):
            expr = calling_expression().expr
            calling_expression().dump()
            assert isinstance(expr, ast.Attribute)
            assert expr.value.id == "f"
            assert expr.attr == "m"

            return 5

    f = foo()
    f.m
    print(f.m)
