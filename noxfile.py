import nox

nox.options.sessions = ["clean", "test", "report", "docs"]


@nox.session(python="python3.10")
def clean(session):
    session.install("coverage")
    session.run("coverage", "erase")


@nox.session(python="python3.10")
def mypy(session):
    session.install("poetry")
    session.run("poetry", "install", "--with=dev")
    session.run("mypy", "src", "tests")


@nox.session(python="python3.11")
def py311(session):
    session.install("poetry")
    session.run("poetry", "install", "--with=dev")
    session.run(
        "pytest", "--assert=plain", "tests", "--doctest-modules", "src/codecrumbs"
    )


@nox.session(python=["3.8", "3.9", "3.10"])
def test(session):
    session.install("poetry")
    session.run("poetry", "install", "--with=dev")
    session.run(
        "coverage",
        "run",
        "--source=src,tests",
        "--parallel-mode",
        "--branch",
        "-m",
        "pytest",
        "--doctest-modules",
        "src/codecrumbs",
        "tests",
        "--assert=plain",
    )


@nox.session(python="python3.10")
def report(session):
    session.install("coverage")
    session.run("coverage", "combine")
    session.run("coverage", "html")
    session.run("coverage", "report", "--fail-under", "86")


@nox.session(python="python3.10")
def docs(session):
    session.install("poetry")
    session.run("poetry", "install", "--with=doc")
    session.run("mkdocs", "build")
