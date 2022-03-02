import inspect

import pytest
from codecrumbs import argument_renamed

from .helper import never_called


def test_preserve_signature():
    class Test:
        @argument_renamed(old="new")
        def a(self, new: str) -> None:
            never_called()

        def b(self, new: str, *, old: str) -> None:
            never_called()

    assert inspect.signature(Test.a) == inspect.signature(Test.b)


def test_parameter_renames(test_rewrite):
    class Method:
        @argument_renamed(old="new")
        def method(self, other=2, new=1):
            print(other, new)

    m = Method()

    error_msg = ""

    test_rewrite(
        "m.method(old=5)", "m.method(new=5)", warning=error_msg, output="2 5\n"
    )

    test_rewrite(
        "m.method(other=3,old=5)",
        "m.method(other=3,new=5)",
        warning=error_msg,
        output="3 5\n",
    )

    test_rewrite(
        "m.method(old=5,other=3)",
        "m.method(new=5,other=3)",
        warning=error_msg,
        output="3 5\n",
    )

    test_rewrite(
        "m.method(3,old=5)", "m.method(3,new=5)", warning=error_msg, output="3 5\n"
    )

    test_rewrite(
        "m.method(**{'old':5})",
        "m.method(**{'old':5})",
        warning=error_msg,
        output="2 5\n",
    )

    m.method(other=5)

    m.method(1, 2)

    with pytest.raises(TypeError):
        m.method(old=5, new=3)


def test_parameter_renamed_misuse():

    with pytest.raises(
        TypeError,
        match="parmeter 'old' should be removed from signature if it is renamed to 'new'",
    ):

        @argument_renamed(old="new")
        def function(old=2, new=1):
            never_called()

    with pytest.raises(
        TypeError, match="parmeter 'old' should be renamed to 'new' in the signature"
    ):

        @argument_renamed(old="new")
        def function(old=2):
            never_called()
