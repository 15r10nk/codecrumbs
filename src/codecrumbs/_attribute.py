import ast
import warnings

from ._calling_expression import calling_expression
from ._rewrite_code import replace


class FixIndex:
    def __init__(self):
        self.index = set()

    def is_first(self, expr):
        fix_id = (expr.filename, expr.ast_index)
        first = fix_id not in self.index
        self.index.add(fix_id)
        return first


def attribute_renamed(new_name, *, since=None):
    """
    Specifies that all read and write accesses of an attribute should be renamed.

    Usage:

    ```pycon
    >>> class Point:
    ...     data_x = attribute_renamed("x")
    ...     data_y = attribute_renamed("y")
    ...     def __init__(self, x, y):
    ...         self.data_x = x
    ...         self.data_y = y
    ...
    >>> p = Point(1, 2)
    file.py:5: DeprecationWarning: ".data_x" should be replaced with ".x" (fixable with codecrumbs)
    file.py:6: DeprecationWarning: ".data_y" should be replaced with ".y" (fixable with codecrumbs)
    >>> p.data_x
    file.py:1: DeprecationWarning: ".data_x" should be replaced with ".x" (fixable with codecrumbs)
    1

    ```

    An access to the old attribute results in a deprecation warning and the calling code is memorized for refactoring.

    It renames also `has/get/set/delattr()` calls if the argument is a literal string:

    ```pycon
    >>> class Test:
    ...     old_attribute = attribute_renamed("new_attribute")
    ...
    >>> t = Test()
    >>> assert not hasattr(t, "old_attribute")
    file.py:1: DeprecationWarning: hasattr(..., "old_attribute") should be replaced with hasattr(..., "new_attribute") (fixable with codecrumbs)

    ```

    Read access to class attributes can also be renamed:

    ```pycon
    >>> class Test:
    ...     old_attribute = attribute_renamed("new_attribute")
    ...     new_attribute = 5
    ...
    >>> Test.old_attribute
    file.py:1: DeprecationWarning: ".old_attribute" should be replaced with ".new_attribute" (fixable with codecrumbs)
    5

    ```

    It can also be used to rename methods:

    ```pycon
    >>> class Test:
    ...     old_method = attribute_renamed("new_method")
    ...
    ...     def new_method(self):
    ...         return 5
    ...
    >>> t = Test()
    >>> t.old_method()
    file.py:1: DeprecationWarning: ".old_method" should be replaced with ".new_method" (fixable with codecrumbs)
    5

    ```


    """

    return RenameAttribute(new_name, since)


class RenameAttribute:
    def __init__(self, newname, since):
        self.new_name = newname
        self.fixes = FixIndex()
        self.since_version = since

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
                        f'{e.id}(..., "{self.current_name}") should be replaced with {e.id}(..., "{self.new_name}") (fixable with codecrumbs)',
                        DeprecationWarning,
                        stacklevel=3,
                    )
                    replace(namearg, f'"{self.new_name}"')
                else:
                    # getattr(obj,attr_var)
                    warnings.warn(
                        f'{e.id}(..., attr) is called with attr="{self.current_name}" but should be called with "{self.new_name}" (please fix manual)',
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

    def __set__(self, obj, value):
        self.__generic_fix()

        return setattr(obj, self.new_name, value)

    def __delete__(self, obj):
        self.__generic_fix()

        delattr(obj, self.new_name)
