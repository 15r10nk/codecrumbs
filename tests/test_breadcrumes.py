from contextlib import contextmanager

import pytest
from test_rewrite_code import rewrite_test  # noqa

from breadcrumes import parameter_renamed, renamed
from breadcrumes._calling_expression import calling_expression


class snapshot:
    def __init__(self, value=None):
        self.loc = calling_expression()
        self.value = value

    def __eq__(self, other):
        if self.value != other:
            print("cmp", other)
        return False


@contextmanager
def deprecation(msg):

    with pytest.warns(DeprecationWarning) as records:
        yield
    assert len(records) == 1, [r.message for r in records]
    assert records[0].message.args[0] == msg


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


def test_parameter_renamed_method():
    class Example:
        @parameter_renamed(old="new")
        def method(self, new):
            assert new == 5

    e = Example()

    e.method(new=5)
    with deprecation(
        'argument name "old=" should be replaced with "new=" (fixable with breadcrumes)'
    ):
        e.method(old=5)

    with pytest.raises(
        TypeError, match="old=... and new=... can not be used at the same time"
    ):
        e.method(old=5, new=5)


def test_rename_replacements(rewrite_test):
    class Method:
        old_method = renamed("new_method")

        def new_method(self):
            print("new")

    rewrite_test("m=Method()\nm.old_method()\n", "m=Method()\nm.new_method()\n")

    rewrite_test("m=Method()\nm.old_method\n", "m=Method()\nm.new_method\n")
    rewrite_test("m=Method()\nm.  old_method\n", "m=Method()\nm.new_method\n")
    rewrite_test("m=Method()\nm  .old_method\n", "m=Method()\nm.new_method\n")

    rewrite_test(
        "m=Method()\nfor i in range(2):m.old_method\n",
        "m=Method()\nfor i in range(2):m.new_method\n",
    )


def test_parameter_renames(rewrite_test):
    class Method:
        @parameter_renamed(old="new")
        def method(self, other=2, new=1):
            print("new")

    rewrite_test("m=Method()\nm.method(old=5)\n", "m=Method()\nm.method(new=5)\n")

    rewrite_test(
        "m=Method()\nm.method(other=3,old=5)\n", "m=Method()\nm.method(other=3,new=5)\n"
    )

    rewrite_test(
        "m=Method()\nm.method(old=5,other=3)\n", "m=Method()\nm.method(new=5,other=3)\n"
    )

    rewrite_test("m=Method()\nm.method(3,old=5)\n", "m=Method()\nm.method(3,new=5)\n")

    rewrite_test("m=Method()\nm.method({'old':5})\n")

    rewrite_test("m=Method()\nm.method({'old':5})\n")

    rewrite_test("m=Method()\nm.method(other=5)\n")

    rewrite_test("m=Method()\nm.method(1,2)\n")

    with pytest.raises(TypeError):
        rewrite_test("m=Method()\nm.method(old=5,new=3)\n")


def test_parameter_renamed_misuse(rewrite_test):

    with pytest.raises(
        TypeError,
        match="parmeter 'old' should be removed from signature if it is renamed to 'new'",
    ):

        @parameter_renamed(old="new")
        def function(old=2, new=1):
            print("new")

    with pytest.raises(
        TypeError, match="parmeter 'old' should be renamed to 'new' in the signature"
    ):

        @parameter_renamed(old="new")
        def function(old=2):
            print("old")