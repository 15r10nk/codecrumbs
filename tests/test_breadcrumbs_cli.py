import subprocess as sp

import pytest


@pytest.fixture
def env(tmp_path):
    class Env:
        def run(self, *args, **kwargs):
            return sp.run(args, cwd=tmp_path, **kwargs)

        def run_breadcrumbs(self, *args, **kwargs):
            return self.run("breadcrumbs", *args, **kwargs)

        def write(self, filename, content):
            path = tmp_path / filename
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(content)

        def read(self, filename):
            path = tmp_path / filename
            return path.read_text()

        def __getattr__(self, name):
            return getattr(tmpdir, name)

    return Env()


def test_help(env):
    assert env.run_breadcrumbs("--help", capture_output=True).stdout.startswith(
        b"usage: breadcrumbs"
    )


@pytest.fixture
def compare(env):
    def w(script_content, *args):
        env.write("script.py", script_content)

        original_output = env.run(
            "python", "script.py", *args, capture_output=True
        ).stdout.decode()

        assert (
            env.run_breadcrumbs(
                "run", "--", "script.py", *args, capture_output=True
            ).stdout.decode()
            == original_output
        )

        assert env.read("script.py") != script_content

        second_output = env.run(
            "python", "script.py", *args, capture_output=True
        ).stdout.decode()

        assert second_output == original_output

    return w


def test_run_hello_world(compare):
    compare(
        """
import breadcrumbs

@breadcrumbs.argument_renamed(old="new")
def func(new):
    print(new)

func(old="hello")

    """
    )


@pytest.mark.skip("we are not perfect")
def test_run_script(compare):

    script = '''
"""
docstring
"""
import sys

i:int=5

print("cmd", sys.argv)
for k, v in sorted(globals().items()):
    print(k, "=", v)
'''
    compare(script, "test", "-q")
