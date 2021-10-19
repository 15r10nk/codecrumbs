import warnings

from rewrite_code import replace
from calling_expression import calling_expression
import ast


class start_of:
    def __init__(self, node):
        self.filename = node.filename
        self.lineno = node.lineno
        self.col_offset = node.col_offset


class end_of:
    def __init__(self, node):
        self.filename = node.filename
        self.lineno = node.end_lineno
        self.col_offset = node.end_col_offset


class Range:
    def __init__(self, start, end):
        assert start.filename == end.filename
        self.filename = start.filename
        self.lineno = start.lineno
        self.end_lineno = end.lineno
        self.col_offset = start.col_offset
        self.end_col_offset = end.col_offset


class FixIndex:
    def __init__(self):
        self.index = set()

    def is_first(self, expr):
        fix_id = (expr.filename, expr.ast_index)
        first = fix_id not in self.index
        self.index.add(fix_id)
        return first


class renamed:
    def __init__(self, newname, since_version=None):
        self.new_name = newname
        self.fixes = FixIndex()

    def __set_name__(self, owner, name):
        self.current_name = name

    def warn(self):
        warnings.warn(
            f'".{self.current_name}" should be replaced with ".{self.new_name}" (fixable with breadcrumes)',
            DeprecationWarning,
            stacklevel=3,
        )

    def __get__(self, obj, objtype=None):
        self.warn()
        if obj is None:
            obj = objtype

        expr = calling_expression()
        if self.fixes.is_first(expr):
            e = expr.expr

            if isinstance(e, ast.Call):
                e = e.func
            assert isinstance(e, ast.Attribute)
            replace(Range(end_of(e.value), end_of(e)), "." + self.new_name)

        return getattr(obj, self.new_name)

    def __set__(self, obj, value):
        self.warn()
        return setattr(obj, self.new_name, value)


def parameter_renamed(since_version=None, **old_params):
    def w(f):
        def r(*a, **ka):
            new_ka = {}
            for key in ka:
                if key in old_params:
                    old_arg = key
                    new_arg = old_params[key]

                    assert (
                        new_arg not in ka
                    ), f"you can not specify {old_arg} and {new_arg} the same time"

                    warnings.warn(
                        f'argument name "{old_arg}=" should be replaced with "{new_arg}=" (fixable with breadcrumes)',
                        DeprecationWarning,
                        stacklevel=2,
                    )

                    new_ka[new_arg] = ka[old_arg]
                else:
                    new_ka[key] = ka[key]

            f(*a, **new_ka)

        return r

    return w


def inline_source(since_version=None):
    def w(f):
        def r(*a, **ka):
            warnings.warn(
                f"usage of this function is deprecated and should be replaced with the defined implementation (can be fixed with breadcrumes)",
                DeprecationWarning,
                stacklevel=2,
            )
            f(*a, **ka)

        return r

    return w
