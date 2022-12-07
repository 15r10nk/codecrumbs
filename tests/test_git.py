def test_git_safety_check(pytester):

    file = pytester.makepyfile("test_one")

    source = """
from codecrumbs import renamed_attribute

class A:
    a=renamed_attribute("b")


def test_one(record_changes):
    x=A()
    x.b=5
    #assert x.a == 5
    print(x.a)
    """

    file.write_text(
        source,
        encoding="utf8",
    )

    pytester.run("git", "init")
    pytester.run("git", "add", file.name)

    result = pytester.runpytest("--codecrumbs-fix")

    assert source != file.read_text()

    result.assert_outcomes(passed=1)

    # assert "print(x.b)" in source
    # result.stdout.fnmatch_lines(["1 fixes where done by codecrumbs"])
