import ast
import inspect
import warnings

from ._calling_expression import calling_expression
from ._rewrite_code import replace


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

    def clear(self):
        self.index = set()


class renamed:
    """
    specifies that all read and write accesses of an attribute should be renamed
    usage:

    >>> class Test:
    ...     old_attribute = renamed("new_attribute")
    ...     new_attribute = 5
    ...
    >>> Test.old_attribute
    file.py:1: DeprecationWarning: ".old_attribute" should be replaced with ".new_attribute" (fixable with breadcrumes)
    5

    An access to the old attribute results in a deprecation warning and the calling code is memorized for refacting.

    It can also be used to rename methods:

    >>> class Test:
    ...     old_method = renamed("new_method")
    ...
    ...     def new_method(self):
    ...         return 5
    ...
    >>> t = Test()
    >>> t.old_method()
    file.py:1: DeprecationWarning: ".old_method" should be replaced with ".new_method" (fixable with breadcrumes)
    5

    And also to rename instance attributes:

    >>> class Point:
    ...     data_x = renamed("x")
    ...     data_y = renamed("y")
    ...
    ...     def __init__(self, x, y):
    ...         self.data_x = x
    ...         self.data_y = y
    ...
    >>> p = Point(1, 2)
    file.py:6: DeprecationWarning: ".data_x" should be replaced with ".x" (fixable with breadcrumes)
    file.py:7: DeprecationWarning: ".data_y" should be replaced with ".y" (fixable with breadcrumes)
    >>> p.data_x
    file.py:1: DeprecationWarning: ".data_x" should be replaced with ".x" (fixable with breadcrumes)
    1

    It renames also has/get/set/delattr() calls if the argument is a Constant

    >>> class Test:
    ...     old_attribute = renamed("new_attribute")
    ...
    >>> t = Test()
    >>> assert not hasattr(t, "old_attribute")
    file.py:1: DeprecationWarning: hasattr(...,"old_attribute") should be replaced with hasattr(...,"new_attribute") (fixable with breadcrumes)

    """

    def __init__(self, newname):
        self.new_name = newname
        self.fixes = FixIndex()

    def __set_name__(self, owner, name):
        self.current_name = name

    def __generic_fix(self):

        expr = calling_expression(back=2)
        if self.fixes.is_first(expr):
            e = expr.expr

            if isinstance(e, ast.Call):
                e = e.func

            if isinstance(e, ast.Name) and e.id in (
                "getattr",
                "hasattr",
                "setattr",
                "delattr",
            ):
                namearg = expr.expr.args[1]
                if isinstance(namearg, ast.Constant):
                    # getattr(obj,"attr")
                    warnings.warn(
                        f'{e.id}(...,"{self.current_name}") should be replaced with {e.id}(...,"{self.new_name}") (fixable with breadcrumes)',
                        DeprecationWarning,
                        stacklevel=3,
                    )
                    replace(namearg, f'"{self.new_name}"')
                else:
                    # getattr(obj,attr_var)
                    warnings.warn(
                        f'{e.id}(...,attr) is called with attr="{self.current_name}" but should be called with "{self.new_name}" (please fix manual)',
                        DeprecationWarning,
                        stacklevel=3,
                    )
            else:
                assert isinstance(e, ast.Attribute), e
                # obj.attr
                warnings.warn(
                    f'".{self.current_name}" should be replaced with ".{self.new_name}" (fixable with breadcrumes)',
                    DeprecationWarning,
                    stacklevel=3,
                )
                replace(Range(end_of(e.value), end_of(e)), "." + self.new_name)

    def __get__(self, obj, objtype=None):
        if obj is None:
            obj = objtype

        self.__generic_fix()

        return getattr(obj, self.new_name)

    def __set__(self, obj, value):
        self.__generic_fix()

        return setattr(obj, self.new_name, value)

    def __delete__(self, obj):
        self.__generic_fix()

        delattr(obj, self.new_name)


def argument_renamed(since_version=None, **old_params):
    """
    `argument_renamed` is an decorator which can be used to rename argument names on the calling side of a method or fuction.

    example problem:

    >>> def function(old_name):
    ...     print(old_name)
    ...
    >>> function(old_name=5)
    5

    refactoring:

    >>> @argument_renamed(old_name="new_name")
    ... def function(new_name):
    ...     print(new_name)
    >>> function(old_name=5)
    file.py:1: DeprecationWarning: argument name "old_name=" should be replaced with "new_name=" (fixable with breadcrumes)
    5

    :raises TypeError: if the old named argument is still present in the signature

    """

    reverse_old_params = {v: k for k, v in old_params.items()}

    def w(f):
        # check misuse
        sig = inspect.signature(f)
        for old_param, new_param in old_params.items():
            if old_param in sig.parameters:
                if new_param in sig.parameters:
                    raise TypeError(
                        "parmeter 'old' should be removed from signature if it is renamed to 'new'"
                    )
                else:
                    raise TypeError(
                        "parmeter 'old' should be renamed to 'new' in the signature"
                    )

        def r(*a, **ka):
            new_ka = {}
            changed = False
            for key in ka:
                if key in old_params:
                    old_arg = key
                    new_arg = old_params[key]

                    if new_arg in ka:
                        raise TypeError(
                            f"{old_arg}=... and {new_arg}=... can not be used at the same time"
                        )

                    warnings.warn(
                        f'argument name "{old_arg}=" should be replaced with "{new_arg}=" (fixable with breadcrumes)',
                        DeprecationWarning,
                        stacklevel=2,
                    )

                    new_ka[new_arg] = ka[old_arg]
                    changed = True
                else:
                    new_ka[key] = ka[key]

            if changed:
                expr = calling_expression()
                import token

                tokens = expr.tokens

                for arg in expr.expr.keywords:
                    if arg.arg not in old_params:
                        continue

                    arg_value = arg.value
                    start = arg_value.lineno, arg_value.col_offset

                    mytokens = [
                        t
                        for t in tokens
                        if t.start < start and t.type in (token.NAME, token.OP)
                    ]

                    name, op = mytokens[-2:]
                    name.filename = expr.filename

                    assert op.string == "=", op.string
                    assert name.string == arg.arg

                    replace(name, old_params[arg.arg])

            f(*a, **new_ka)

        signature = inspect.signature(f)
        parameters = list(signature.parameters.values()) + [
            signature.parameters[v].replace(
                kind=inspect.Parameter.KEYWORD_ONLY,
                name=k,
            )
            for k, v in old_params.items()
        ]

        r.__signature__ = inspect.Signature(
            parameters, return_annotation=signature.return_annotation
        )

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
