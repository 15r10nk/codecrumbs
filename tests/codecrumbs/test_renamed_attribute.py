import pytest
from codecrumbs import argument_renamed
from codecrumbs import renamed_attribute

from ..helper import never_called


def replace_warning(old, new):
    return f'".{old}" should be replaced with ".{new}" (fixable with codecrumbs)'


import inspect


def test_preserve_signature():
    class Test:
        a = renamed_attribute("b")

        def b(a, b):
            never_called()

    with pytest.warns(DeprecationWarning):
        assert inspect.signature(Test.a) == inspect.signature(Test.b)


def test_renamed_attribute(test_rewrite):
    class Example:
        old = renamed_attribute("new")

        def __init__(self):
            self.new = 1

    e = Example()
    test_rewrite(
        "assert e.old == 1", "assert e.new == 1", warning=replace_warning("old", "new")
    )

    e.new = 2
    test_rewrite(
        "assert e.old == 2", "assert e.new == 2", warning=replace_warning("old", "new")
    )

    test_rewrite("e.old = 3", "e.new = 3", warning=replace_warning("old", "new"))

    test_rewrite(
        "assert e.old == 3", "assert e.new == 3", warning=replace_warning("old", "new")
    )

    test_rewrite("del e.old", "del e.new", warning=replace_warning("old", "new"))


def test_renamed_hasattr_getattr(test_rewrite):
    class Example:
        old = renamed_attribute("new")
        no_attr = renamed_attribute("new_no_attr")

        def __init__(self):
            self.new = 1

    e = Example()
    assert e.new == 1
    test_rewrite(
        'assert getattr(e,"old") == 1',
        'assert getattr(e,"new") == 1',
        warning='getattr(..., "old") should be replaced with getattr(..., "new") (fixable with codecrumbs)',
    )

    test_rewrite(
        'assert hasattr(e,"old")',
        'assert hasattr(e,"new")',
        warning='hasattr(..., "old") should be replaced with hasattr(..., "new") (fixable with codecrumbs)',
    )

    test_rewrite(
        'assert not hasattr(e,"no_attr")',
        'assert not hasattr(e,"new_no_attr")',
        warning='hasattr(..., "no_attr") should be replaced with hasattr(..., "new_no_attr") (fixable with codecrumbs)',
    )

    test_rewrite(
        'setattr(e,"old",3)',
        'setattr(e,"new",3)',
        warning='setattr(..., "old") should be replaced with setattr(..., "new") (fixable with codecrumbs)',
    )
    assert e.new == 3

    test_rewrite(
        'delattr(e,"old")',
        'delattr(e,"new")',
        warning='delattr(..., "old") should be replaced with delattr(..., "new") (fixable with codecrumbs)',
    )

    assert not hasattr(e, "new")

    old_attr = "old"
    test_rewrite(
        "setattr(e,old_attr,5)",
        "setattr(e,old_attr,5)",
        warning='setattr(..., attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )
    test_rewrite(
        "assert getattr(e,old_attr)==5",
        "assert getattr(e,old_attr)==5",
        warning='getattr(..., attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )
    test_rewrite(
        "assert hasattr(e,old_attr)",
        "assert hasattr(e,old_attr)",
        warning='hasattr(..., attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )
    test_rewrite(
        "delattr(e,old_attr)",
        "delattr(e,old_attr)",
        warning='delattr(..., attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )


def test_renamed_method(test_rewrite):
    class Example:
        old = renamed_attribute("new")

        def new(self):
            return 1

    e = Example()

    assert e.new() == 1
    test_rewrite(
        "assert e.old()==1", "assert e.new()==1", warning=replace_warning("old", "new")
    )


def test_renamed_classmethod(test_rewrite):
    class Example:
        old = renamed_attribute("new")

        @classmethod
        def new(cls):
            return 1

    e = Example()

    test_rewrite(
        "assert e.old()==1", "assert e.new()==1", warning=replace_warning("old", "new")
    )

    test_rewrite(
        "assert Example.old()==1",
        "assert Example.new()==1",
        warning=replace_warning("old", "new"),
    )


def test_parameter_renamed_method(test_rewrite):
    class Example:
        @argument_renamed("old", "new")
        def method(self, new):
            assert new == 5
            print(new)

    e = Example()

    e.method(new=5)
    test_rewrite(
        "e.method(old=5)",
        "e.method(new=5)",
        warning='argument name "old=" should be replaced with "new=" (fixable with codecrumbs)',
        output="5\n",
    )

    with pytest.raises(
        TypeError, match="old=... and new=... can not be used at the same time"
    ):
        e.method(old=5, new=5)


#    e.method(**{"old":5})


@pytest.mark.parametrize("obj", ["m", "ma[0]", "f()"])
def test_rename_replacements(test_rewrite, obj):
    class Method:
        old_method = renamed_attribute("new_method")
        old_attr = renamed_attribute("new_attr")

        def new_method(self):
            print("new")

    m = Method()
    ma = [m, m]

    def f():
        return m

    test_rewrite(
        f"{obj}.old_method()",
        f"{obj}.new_method()",
        warning=replace_warning("old_method", "new_method"),
        output="new\n",
    )
    test_rewrite(
        f"{obj}.old_method",
        f"{obj}.new_method",
        warning=replace_warning("old_method", "new_method"),
    )
    test_rewrite(
        f"print({obj}.old_method)",
        f"print({obj}.new_method)",
        warning=replace_warning("old_method", "new_method"),
        output=repr(m.new_method) + "\n",
    )

    test_rewrite(
        f"{obj}.old_method",
        f"{obj}.new_method",
        warning=replace_warning("old_method", "new_method"),
    )
    test_rewrite(
        f"{obj}.  old_method",
        f"{obj}.  new_method",
        warning=replace_warning("old_method", "new_method"),
    )
    test_rewrite(
        f"{obj}  .old_method",
        f"{obj}  .new_method",
        warning=replace_warning("old_method", "new_method"),
    )

    test_rewrite(
        f"{obj}.old_attr=5",
        f"{obj}.new_attr=5",
        warning=replace_warning("old_attr", "new_attr"),
    )

    test_rewrite(
        f"for i in range(3):{obj}.old_method()",
        f"for i in range(3):{obj}.new_method()",
        warning=replace_warning("old_method", "new_method"),
        output="new\n" * 3,
    )
