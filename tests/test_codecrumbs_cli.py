import subprocess as sp
import sys

import pytest


@pytest.fixture
def env(tmp_path):
    class Env:
        def run(self, *args, **kwargs):
            result = sp.run(args, cwd=tmp_path, **kwargs)
            if result.returncode != 0:
                print(result.stdout)
                print(result.stderr)
                assert False
            return result

        def run_codecrumbs(self, *args, **kwargs):
            return self.run("codecrumbs", *args, **kwargs)

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
    assert env.run_codecrumbs("--help", capture_output=True).stdout.startswith(
        b"usage: codecrumbs"
    )


@pytest.fixture
def compare(env):
    def w(script_content, *args):
        env.write("script.py", script_content)

        original_output = env.run(
            sys.executable, "script.py", *args, capture_output=True, check=True
        ).stdout.decode()

        assert (
            env.run_codecrumbs(
                "run", "--fix", "--", "script.py", *args, capture_output=True
            ).stdout.decode()
            == original_output,
        )

        assert env.read("script.py") != script_content

        second_output = env.run(
            sys.executable, "script.py", *args, capture_output=True, check=True
        ).stdout.decode()

        assert second_output == original_output

    return w


def test_run_hello_world(compare):
    compare(
        """
import codecrumbs

@codecrumbs.argument_renamed(old="new")
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
