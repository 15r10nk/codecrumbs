import inspect
import io
import warnings
from contextlib import redirect_stdout

import pytest
from codecrumbs._rewrite_code import ChangeRecorder


def run_test(old_code, new_code, *, warning=None, output="", filename, frame):

    filename.write_bytes(old_code.encode())
    assert old_code.encode() == filename.read_bytes()

    print("old code:")
    print(filename.read_text())

    d = dict(frame.f_globals)
    l = dict(frame.f_locals)

    first_output = io.StringIO()
    with ChangeRecorder().activate() as changes:
        with warnings.catch_warnings(record=True) as record:

            with redirect_stdout(first_output):
                code = compile(filename.read_bytes(), str(filename), "exec")
                d["__file__"] = str(filename)
                exec(code, d, l)
            print(first_output.getvalue())

            assert first_output.getvalue() == output, (first_output.getvalue(), output)

        if warning is None:
            assert not record, record
        else:
            assert (
                len(record) == 1
                and record[0].category is DeprecationWarning
                and str(record[0].message) == warning
            ), record

    changes.fix_all(check_git=False)

    print("new code:")
    print(filename.read_text())

    assert (
        filename.read_bytes() == new_code.encode()
    ), f"{filename.read_bytes()} != {new_code.encode()}"


def run_second_test(old_code, new_code, *, warning=None, output="", filename, frame):
    """
    fixing the new_code again should result in no warnings and no changes
    """
    return run_test(
        new_code,
        new_code,
        warning=None if new_code != old_code else warning,
        output=output,
        filename=filename,
        frame=frame,
    )


doctest_template = '''
import doctest

def func():
    """
    >>> def doctest_helper():
    ...     {}
    ...
    >>> doctest_helper()
    {output}

    """
    pass

doctest.testfile(__file__,module_relative=False,globs=locals())
'''

# a complicated way to say that doctest are not supported for python 3.11
@pytest.fixture(
    params=[
        pytest.param(
            (t, c),
            id=f"{t.__name__}-{c_id}",
            marks=(pytest.mark.xfail if c_id == "docstring" and t is run_test else []),
        )
        for t in (run_test, run_second_test)
        for (c, c_id) in [
            ("{}", "plain"),
            ("{}\n", "newline"),
            ("{}\r\n", "windows"),
            ("{}\r", "r-only"),
            ("\n\n{}# comment\n", "comment"),
            (doctest_template, "docstring"),
        ]
    ]
)
def test_rewrite(request, tmp_path):
    """
    fixture which return a function which can be used to check the refactoring of some sourcecode in the current scope


    """

    run_test, code_formatting = request.param

    idx = 0

    def test(old_code, new_code, *, warning, output=""):
        """
        checks that:
            * old_code gets fixet to new_code
            * a DeprecationWarning warning is raised
            * that output matches stdout
        """
        nonlocal idx

        assert warning is not None

        def indent_of(pattern):

            code_idx = code_formatting.find(pattern)
            code_begin = code_formatting.rfind("\n", 0, code_idx)
            return code_formatting[code_begin:code_idx].replace(">>>", "...")

        code_prefix = indent_of("{}")

        if "{output}" in code_formatting:
            output_prefix = indent_of("{output}")
            output = output.replace("\n", output_prefix)

        old_code = code_formatting.format(
            old_code.replace("\n", code_prefix), output=output
        )
        new_code = code_formatting.format(
            new_code.replace("\n", code_prefix), output=output
        )

        if "{output}" in code_formatting:
            # output check in source (doctest)
            output = ""

        frame = inspect.currentframe().f_back
        filename = tmp_path / f"{run_test.__name__}_{idx}.py"
        idx += 1
        run_test(
            old_code,
            new_code,
            warning=warning,
            output=output,
            filename=filename,
            frame=frame,
        )

    yield test
