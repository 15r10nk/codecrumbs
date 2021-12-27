pytest_plugins = "pytester"

import pytest
import warnings
import sys


@pytest.fixture
def show_warning():

    try:
        with warnings.catch_warnings():

            def showwarning(message, category, filename, lineno, file=None, line=None):
                sys.stdout.write(
                    warnings.formatwarning(message, category, "file.py", lineno, line)
                )

            warnings.showwarning = showwarning

            yield
    except:
        raise
    finally:
        pass
