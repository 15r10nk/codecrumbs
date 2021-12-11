from contextlib import contextmanager

import pytest
from test_rewrite_code import rewrite_test  # noqa

from breadcrumes import argument_renamed
from breadcrumes import renamed


@contextmanager
def deprecation(warning=1):

    with pytest.warns(DeprecationWarning) as records:
        yield

    if isinstance(warning, int):
        assert len(records) == warning
    elif isinstance(warning, str):
        assert len(records) == 1
        assert records[0].message.args[0] == warning


@contextmanager
def warn_replace(old, new):
    with deprecation(
        f'".{old}" should be replaced with ".{new}" (fixable with breadcrumes)'
    ):
        yield


def test_renamed_attribute():
    class Example:
        old = renamed("new")

        def __init__(self):
            self.new = 1

    e = Example()
    assert e.new == 1
    with warn_replace("old", "new"):
        assert e.old == 1

    e.new = 2
    assert e.new == 2
    with warn_replace("old", "new"):
        assert e.old == 2

    with warn_replace("old", "new"):
        e.old = 3

    assert e.new == 3
    with warn_replace("old", "new"):
        assert e.old == 3


def test_renamed_method():
    class Example:
        old = renamed("new")

        def new(self):
            return 1

    e = Example()

    assert e.new() == 1
    with warn_replace("old", "new"):
        assert e.old() == 1


def test_renamed_classmethod():
    class Example:
        old = renamed("new")

        @classmethod
        def new(cls):
            return 1

    e = Example()

    assert e.new() == 1
    with warn_replace("old", "new"):
        assert e.old() == 1

    assert Example.new() == 1
    with warn_replace("old", "new"):
        assert Example.old() == 1


def test_parameter_renamed_method(rewrite_test):
    class Example:
        @argument_renamed(old="new")
        def method(self, new):
            assert new == 5
            print(new)

    e = Example()

    e.method(new=5)
    with deprecation(
        'argument name "old=" should be replaced with "new=" (fixable with breadcrumes)'
    ):
        e.method(old=5)

    with pytest.raises(
        TypeError, match="old=... and new=... can not be used at the same time"
    ):
        rewrite_test("e.method(old=5, new=5)")


#    e.method(**{"old":5})


@pytest.mark.parametrize("obj", ["m", "ma[0]", "f()"])
def test_rename_replacements(rewrite_test, obj):
    class Method:
        old_method = renamed("new_method")
        old_attr = renamed("new_attr")

        def new_method(self):
            print("new")

    m = Method()
    ma = [m, m]

    def f():
        return m

    with deprecation():
        rewrite_test(f"{obj}.old_method()", f"{obj}.new_method()")
    with deprecation():
        rewrite_test(f"{obj}.old_method", f"{obj}.new_method")
    with deprecation():
        rewrite_test(f"print({obj}.old_method)", f"print({obj}.new_method)")

    with deprecation():
        rewrite_test(f"{obj}.old_method", f"{obj}.new_method")
    with deprecation():
        rewrite_test(f"{obj}.  old_method", f"{obj}.new_method")
    with deprecation():
        rewrite_test(f"{obj}  .old_method", f"{obj}.new_method")

    with deprecation():
        rewrite_test(f"{obj}.old_attr=5", f"{obj}.new_attr=5", statement=True)

    with deprecation(3):
        rewrite_test(
            f"for i in range(3):{obj}.old_method",
            f"for i in range(3):{obj}.new_method",
            statement=True,
        )


def test_parameter_renames(rewrite_test):
    class Method:
        @argument_renamed(old="new")
        def method(self, other=2, new=1):
            print("new")

    m = Method()

    with deprecation():
        rewrite_test("m.method(old=5)", "m.method(new=5)")

    with deprecation():
        rewrite_test("m.method(other=3,old=5)", "m.method(other=3,new=5)")

    with deprecation():
        rewrite_test("m.method(old=5,other=3)", "m.method(new=5,other=3)")

    with deprecation():
        rewrite_test("m.method(3,old=5)", "m.method(3,new=5)")

    with deprecation():
        rewrite_test("m.method(**{'old':5})")

    rewrite_test("m.method(other=5)")

    rewrite_test("m.method(1,2)")

    with pytest.raises(TypeError):
        rewrite_test("m.method(old=5,new=3)")


def test_parameter_renamed_misuse(rewrite_test):

    with pytest.raises(
        TypeError,
        match="parmeter 'old' should be removed from signature if it is renamed to 'new'",
    ):

        @argument_renamed(old="new")
        def function(old=2, new=1):
            pass  # pragma: no cover

    with pytest.raises(
        TypeError, match="parmeter 'old' should be renamed to 'new' in the signature"
    ):

        @argument_renamed(old="new")
        def function(old=2):
            pass  # pragma: no cover
