import pytest
from codecrumbs._rewrite_code import ChangeRecorder


def pytest_addoption(parser):
    group = parser.getgroup("codecrumbs")
    group.addoption(
        "--codecrumbs-fix",
        action="store_true",
        dest="codecrumbs_fix",
        help="Fix all deprecated code which is annotated by codecrumbs",
    )


def pytest_configure(config):

    if config.option.codecrumbs_fix:
        import sys

        # hack to disable the assertion rewriting
        # I found no other way because the hook gets installed early
        sys.meta_path = [
            e for e in sys.meta_path if type(e).__name__ != "AssertionRewritingHook"
        ]


class Plugin:
    def __init__(self):
        self.change_recorder = ChangeRecorder()


def pytest_load_initial_conftests(early_config, parser, args):
    early_config.pluginmanager.register(Plugin(), "_codecrumbs")


@pytest.fixture(autouse=True)
def record_changes(request):
    plugin = request.config.pluginmanager.getplugin("_codecrumbs")
    with plugin.change_recorder.activate():
        yield plugin.change_recorder


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    plugin = config.pluginmanager.getplugin("_codecrumbs")

    if exitstatus == 0 and config.option.codecrumbs_fix:
        num_fixes = plugin.change_recorder.num_fixes()
        plugin.change_recorder.fix_all()
        terminalreporter.section("codecrumbs")
        terminalreporter.write(f"{num_fixes} fixes where done by codecrumbs\n")
