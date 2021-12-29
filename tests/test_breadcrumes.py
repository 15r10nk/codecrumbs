import inspect
import io
import re
from contextlib import redirect_stdout

import pytest

from breadcrumes import argument_renamed
from breadcrumes import renamed
from breadcrumes._rewrite_code import rewrite


def replace_warning(old, new):
    return f'".{old}" should be replaced with ".{new}" (fixable with breadcrumes)'


def run_test(old_code, new_code, *, warning=None, output="", filename, frame):

    filename.write_bytes(old_code.encode())
    assert old_code.encode() == filename.read_bytes()

    d = dict(frame.f_globals)
    l = dict(frame.f_locals)

    first_output = io.StringIO()
    with redirect_stdout(first_output):
        with (
            pytest.warns(None)
            if warning is None
            else pytest.warns(DeprecationWarning, match=re.escape(warning))
        ):
            code = compile(filename.read_bytes(), str(filename), "exec")
            d["__file__"] = str(filename)
            exec(code, d, l)
    rewrite(filename)

    assert (
        filename.read_bytes() == new_code.encode()
    ), f"{filename.read_bytes()} != {new_code.encode()}"

    if isinstance(output, str):
        assert first_output.getvalue() == output, (first_output.getvalue(), output)
    else:
        assert output.fullmatch(first_output.getvalue()), (
            first_output.getvalue(),
            output,
        )


def run_second_test(old_code, new_code, *, warning=None, output="", filename, frame):
    return run_test(
        new_code, new_code, warning=None, output=output, filename=filename, frame=frame
    )


@pytest.fixture(params=["{}", "{}\n", "{}\r\n", "{}\r", "\n\n{}# comment\n"])
def code_formatting(request):
    return request.param.format


@pytest.fixture(params=[run_test, run_second_test])
def test_rewrite(request, tmp_path, code_formatting):
    idx = 0

    def test(old_code, new_code, *, warning=None, output=""):
        nonlocal idx

        old_code = code_formatting(old_code)
        new_code = code_formatting(new_code)

        frame = inspect.currentframe().f_back
        filename = tmp_path / f"{request.param.__name__}_{idx}.py"
        idx += 1
        request.param(
            old_code,
            new_code,
            warning=warning,
            output=output,
            filename=filename,
            frame=frame,
        )

    yield test


def test_renamed_attribute(test_rewrite):
    class Example:
        old = renamed("new")

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
        old = renamed("new")
        no_attr = renamed("new_no_attr")

        def __init__(self):
            self.new = 1

    e = Example()
    assert e.new == 1
    test_rewrite(
        'assert getattr(e,"old") == 1',
        'assert getattr(e,"new") == 1',
        warning='getattr(...,"old") should be replaced with getattr(...,"new") (fixable with breadcrumes)',
    )

    test_rewrite(
        'assert hasattr(e,"old")',
        'assert hasattr(e,"new")',
        warning='hasattr(...,"old") should be replaced with hasattr(...,"new") (fixable with breadcrumes)',
    )

    test_rewrite(
        'assert not hasattr(e,"no_attr")',
        'assert not hasattr(e,"new_no_attr")',
        warning='hasattr(...,"no_attr") should be replaced with hasattr(...,"new_no_attr") (fixable with breadcrumes)',
    )

    test_rewrite(
        'setattr(e,"old",3)',
        'setattr(e,"new",3)',
        warning='setattr(...,"old") should be replaced with setattr(...,"new") (fixable with breadcrumes)',
    )
    assert e.new == 3

    test_rewrite(
        'delattr(e,"old")',
        'delattr(e,"new")',
        warning='delattr(...,"old") should be replaced with delattr(...,"new") (fixable with breadcrumes)',
    )

    assert not hasattr(e, "new")

    old_attr = "old"
    test_rewrite(
        "setattr(e,old_attr,5)",
        "setattr(e,old_attr,5)",
        warning='setattr(...,attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )
    test_rewrite(
        "assert getattr(e,old_attr)==5",
        "assert getattr(e,old_attr)==5",
        warning='getattr(...,attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )
    test_rewrite(
        "assert hasattr(e,old_attr)",
        "assert hasattr(e,old_attr)",
        warning='hasattr(...,attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )
    test_rewrite(
        "delattr(e,old_attr)",
        "delattr(e,old_attr)",
        warning='delattr(...,attr) is called with attr="old" but should be called with "new" (please fix manual)',
    )


def test_renamed_method(test_rewrite):
    class Example:
        old = renamed("new")

        def new(self):
            return 1

    e = Example()

    assert e.new() == 1
    test_rewrite(
        "assert e.old()==1", "assert e.new()==1", warning=replace_warning("old", "new")
    )


def test_renamed_classmethod(test_rewrite):
    class Example:
        old = renamed("new")

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
        @argument_renamed(old="new")
        def method(self, new):
            assert new == 5
            print(new)

    e = Example()

    e.method(new=5)
    test_rewrite(
        "e.method(old=5)",
        "e.method(new=5)",
        warning='argument name "old=" should be replaced with "new=" (fixable with breadcrumes)',
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
        old_method = renamed("new_method")
        old_attr = renamed("new_attr")

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
        output=re.compile("<bound method .*", re.DOTALL),
    )

    test_rewrite(
        f"{obj}.old_method",
        f"{obj}.new_method",
        warning=replace_warning("old_method", "new_method"),
    )
    test_rewrite(
        f"{obj}.  old_method",
        f"{obj}.new_method",
        warning=replace_warning("old_method", "new_method"),
    )
    test_rewrite(
        f"{obj}  .old_method",
        f"{obj}.new_method",
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
            pass  # pragma: no cover

    with pytest.raises(
        TypeError, match="parmeter 'old' should be renamed to 'new' in the signature"
    ):

        @argument_renamed(old="new")
        def function(old=2):
            pass  # pragma: no cover
