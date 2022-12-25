def test_help_message(testdir):
    result = testdir.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "codecrumbs:",
            "*--codecrumbs-fix*Fix all deprecated code which is annotated*",
        ]
    )


def test_codecrumbs_fix(pytester):
    testdir = pytester
    file = testdir.makepyfile("test_one")

    file.write_text(
        """
from codecrumbs import attribute_renamed

class A:
    a=attribute_renamed("b")


def test_one(record_changes):
    x=A()
    x.b=5
    print(x.a)
    """,
        encoding="utf8",
    )
    pytester.run("git", "init")
    pytester.run("git", "add", file.name)

    result = testdir.runpytest("--codecrumbs-fix")
    source = file.read_text()
    assert "print(x.b)" in source

    result.assert_outcomes(passed=1)

    result.stdout.fnmatch_lines(["1 fixes where done by codecrumbs"])
