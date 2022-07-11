import ast
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


class ClassObjectProperty:
    def __init__(self, func):
        self._func = func

    def __get__(self, obj, objtype=None):

        if obj is None:
            return self._func(objtype, on_class=True)
        else:
            return self._func(obj, on_class=False)


class renamed_attribute:
    _class_doc = """
    specifies that all read and write accesses of an attribute should be renamed
    usage:

    >>> class Test:
    ...     old_attribute = renamed_attribute("new_attribute")
    ...     new_attribute = 5
    ...
    >>> Test.old_attribute
    file.py:1: DeprecationWarning: ".old_attribute" should be replaced with ".new_attribute" (fixable with codecrumbs)
    5

    An access to the old attribute results in a deprecation warning and the calling code is memorized for refacting.

    It can also be used to rename methods:

    >>> class Test:
    ...     old_method = renamed_attribute("new_method")
    ...
    ...     def new_method(self):
    ...         return 5
    ...
    >>> t = Test()
    >>> t.old_method()
    file.py:1: DeprecationWarning: ".old_method" should be replaced with ".new_method" (fixable with codecrumbs)
    5

    And also to rename instance attributes:

    >>> class Point:
    ...     data_x = renamed_attribute("x")
    ...     data_y = renamed_attribute("y")
    ...
    ...     def __init__(self, x, y):
    ...         self.data_x = x
    ...         self.data_y = y
    ...
    >>> p = Point(1, 2)
    file.py:6: DeprecationWarning: ".data_x" should be replaced with ".x" (fixable with codecrumbs)
    file.py:7: DeprecationWarning: ".data_y" should be replaced with ".y" (fixable with codecrumbs)
    >>> p.data_x
    file.py:1: DeprecationWarning: ".data_x" should be replaced with ".x" (fixable with codecrumbs)
    1

    It renames also has/get/set/delattr() calls if the argument is a Constant

    >>> class Test:
    ...     old_attribute = renamed_attribute("new_attribute")
    ...
    >>> t = Test()
    >>> assert not hasattr(t, "old_attribute")
    file.py:1: DeprecationWarning: hasattr(...,"old_attribute") should be replaced with hasattr(...,"new_attribute") (fixable with codecrumbs)

    """

    def __init__(self, newname):
        self.new_name = newname
        self.fixes = FixIndex()
        self.since_version = None

    def __set_name__(self, owner, name):
        self._owner = owner
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
                        f'{e.id}(...,"{self.current_name}") should be replaced with {e.id}(...,"{self.new_name}") (fixable with codecrumbs)',
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
                    f'".{self.current_name}" should be replaced with ".{self.new_name}" (fixable with codecrumbs)',
                    DeprecationWarning,
                    stacklevel=3,
                )

                start = e.value.end_lineno, e.value.end_col_offset

                tokens = expr.tokens
                mytokens = [t for t in tokens if t.start >= start]

                dot, name = mytokens[:2]

                assert dot.string == "."
                assert name.string == self.current_name

                replace(name, self.new_name)

    def __get__(self, obj, objtype=None):
        if obj is None:
            obj = objtype

        self.__generic_fix()

        return getattr(obj, self.new_name)

    @ClassObjectProperty
    def __doc__(self, on_class):

        if on_class:
            return self._class_doc
        elif getattr(getattr(self._owner, self.new_name), "__doc__", "").strip():
            since = self.since_version or "<next>"
            return f".. deprecated:: {since} this attribute was renamed to :attr:`{self.new_name}`"

    def __set__(self, obj, value):
        self.__generic_fix()

        return setattr(obj, self.new_name, value)

    def __delete__(self, obj):
        self.__generic_fix()

        delattr(obj, self.new_name)


def inline_source(since_version=None):
    def w(f):
        def r(*a, **ka):
            warnings.warn(
                f"usage of this function is deprecated and should be replaced with the defined implementation (can be fixed with codecrumbs)",
                DeprecationWarning,
                stacklevel=2,
            )
            f(*a, **ka)

        return r

    return w
