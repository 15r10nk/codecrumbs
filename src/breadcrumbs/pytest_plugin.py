import pytest
from breadcrumbs._rewrite_code import ChangeRecorder


def pytest_addoption(parser):
    group = parser.getgroup("breadcrumbs")
    group.addoption(
        "--breadcrumbs-fix",
        action="store_true",
        dest="breadcrumbs_fix",
        help="Fix all deprecated code which is annotated by breadcrumbs",
    )


class Plugin:
    def __init__(self):
        self.change_recorder = ChangeRecorder()


def pytest_load_initial_conftests(early_config, parser, args):
    early_config.pluginmanager.register(Plugin(), "_breadcrumbs")


@pytest.fixture(autouse=True)
def record_changes(request):
    plugin = request.config.pluginmanager.getplugin("_breadcrumbs")
    with plugin.change_recorder.activate():
        yield plugin.change_recorder


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    plugin = config.pluginmanager.getplugin("_breadcrumbs")

    if exitstatus == 0 and config.option.breadcrumbs_fix:
        num_fixes = plugin.change_recorder.num_fixes()
        plugin.change_recorder.fix_all()
        terminalreporter.section("breadcrumbs")
        terminalreporter.write(f"{num_fixes} fixes where done by breadcrumbs\n")
