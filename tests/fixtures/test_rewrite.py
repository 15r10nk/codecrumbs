import inspect
import io
import re
from contextlib import redirect_stdout

import pytest

from breadcrumes._rewrite_code import rewrite


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
