from calling_expression import calling_expression, AstStructureError

import ast
import pytest


def test_lambda_problem1():
    [lambda: 1, lambda: 1]

    def foo():
        expr = calling_expression().expr
        assert expr.func.id == "foo"

    with pytest.raises(AstStructureError):
        foo()


def test_lambda_problem2():
    [lambda: 1, lambda: 1]

    def w():
        def foo():
            expr = calling_expression().expr
            assert expr.func.id == "foo"

        foo()

    with pytest.raises(AstStructureError):
        w()


def test_function():
    def foo():
        expr = calling_expression().expr
        assert expr.func.id == "foo"

    foo()


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
            expr = calling_expression().expr
            assert isinstance(expr, ast.Call)
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
            assert isinstance(expr, ast.Attribute)
            assert expr.value.id == "f"
            assert expr.attr == "m"

    f = foo()
    f.m
