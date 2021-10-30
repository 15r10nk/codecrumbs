def test_help_message(testdir):
    result = testdir.runpytest(
        "--help",
    )
    # fnmatch_lines does an assertion internally
    result.stdout.fnmatch_lines(
        [
            "breadcrumes:",
            "*--breadcrumes-fix*Fix all deprecated code which is annotated by",
        ]
    )


def test_breadcrumes_fix(pytester):
    testdir = pytester
    file = testdir.makepyfile("test_one")

    file.write_text(
        """
from breadcrumes import renamed

class A:
    a=renamed("b")


def test_one(record_changes):
    x=A()
    x.b=5
    print(x.a)
    """,
        encoding="utf8",
    )
    result = testdir.runpytest("--breadcrumes-fix")
    source = file.read_text()
    assert "print(x.b)" in source

    result.assert_outcomes(passed=1)

    result.stdout.fnmatch_lines(["1 fixes where done by breadcrumes"])
