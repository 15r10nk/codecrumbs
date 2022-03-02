import inspect
import io
import re
from contextlib import redirect_stdout

import pytest
from codecrumbs._rewrite_code import rewrite


def run_test(old_code, new_code, *, warning=None, output="", filename, frame):

    filename.write_bytes(old_code.encode())
    assert old_code.encode() == filename.read_bytes()

    print("old code:")
    print(filename.read_text())

    d = dict(frame.f_globals)
    l = dict(frame.f_locals)

    first_output = io.StringIO()
    with (
        pytest.warns(None)
        if warning is None
        else pytest.warns(DeprecationWarning, match=re.escape(warning))
    ):
        with redirect_stdout(first_output):
            code = compile(filename.read_bytes(), str(filename), "exec")
            d["__file__"] = str(filename)
            exec(code, d, l)
        print(first_output.getvalue())

        assert first_output.getvalue() == output, (first_output.getvalue(), output)

    rewrite(filename)

    print("new code:")
    print(filename.read_text())

    assert (
        filename.read_bytes() == new_code.encode()
    ), f"{filename.read_bytes()} != {new_code.encode()}"


def run_second_test(old_code, new_code, *, warning=None, output="", filename, frame):
    return run_test(
        new_code, new_code, warning=None, output=output, filename=filename, frame=frame
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


@pytest.fixture(
    params=["{}", "{}\n", "{}\r\n", "{}\r", "\n\n{}# comment\n", doctest_template]
)
def code_formatting(request):
    return request.param


@pytest.fixture(params=[run_test, run_second_test])
def test_rewrite(request, tmp_path, code_formatting):
    idx = 0

    def test(old_code, new_code, *, warning=None, output=""):
        nonlocal idx

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
