import sys
import warnings

import pytest
from _pytest.doctest import DoctestItem


@pytest.fixture(autouse=True)
def show_warning(request):
    if isinstance(request.node, DoctestItem):

        with warnings.catch_warnings():

            def showwarning(message, category, filename, lineno, file=None, line=None):
                sys.stdout.write(
                    warnings.formatwarning(message, category, "file.py", lineno, line)
                )

            warnings.showwarning = showwarning

            yield
    else:
        yield
