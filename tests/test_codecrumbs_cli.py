import sys

import patch  # type: ignore
import pytest


@pytest.fixture
def env(pytester):
    class Env:
        def run(self, *args, **kwargs):
            result = pytester.run(*args, **kwargs)
            return result

        def run_codecrumbs(self, *args, **kwargs):
            return self.run("codecrumbs", *args, **kwargs)

        def write(self, filename, content):
            path = pytester.path / filename
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text(content)

        def read(self, filename):
            path = pytester.path / filename
            return path.read_text()

    print(f"work in {pytester.path}")
    return Env()


def test_help(env):
    env.run_codecrumbs("--help").stdout.fnmatch_lines(["usage: codecrumbs*"])


def test_python_module_help(env):
    env.run("python", "-m", "codecrumbs", "--help").stdout.fnmatch_lines(
        ["usage: codecrumbs*"]
    )


@pytest.fixture
def compare(env):
    def w(script_content, *args):

        # generate patch file
        env.run("git", "init")
        env.write("script.py", script_content)
        env.run("git", "add", "script.py")

        def result_equal(result_a, result_b):
            assert result_a.stdout.str() == result_b.stdout.str()
            # assert result_a.stderr.decode() == result_b.stderr.decode()
            assert result_a.ret == result_b.ret

        original_result = env.run(sys.executable, "script.py", *args)

        codecrumbs_result = env.run_codecrumbs("run", "script.py", *args)

        result_equal(codecrumbs_result, original_result)

        patch.fromfile("script_codecrumbs.patch").apply()

        patched_script = env.read("script.py")

        # direct fix
        env.write("script.py", script_content)
        env.run("git", "add", "script.py")

        codecrumbs_fix_result = env.run_codecrumbs(
            "run", "--fix", "--", "script.py", *args
        )
        result_equal(codecrumbs_fix_result, original_result)

        env.run("git", "add", "script.py")

        assert patched_script == env.read("script.py") != script_content

        # run again and compare output
        second_result = env.run(sys.executable, "script.py", *args)

        result_equal(second_result, original_result)

        assert patched_script == env.read("script.py")

    return w


def test_run_hello_world(compare):
    compare(
        """
import codecrumbs

@codecrumbs.argument_renamed("old","new")
def func(new):
    print(new)

func(old="hello")

"""
    )


def test_run_exception(compare):
    compare(
        """
import codecrumbs

@codecrumbs.argument_renamed("old","new")
def func(new):
    print(new)

func(old="hello")

raise ValueError

"""
    )


@pytest.mark.xfail(reason="we are not perfect")
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
