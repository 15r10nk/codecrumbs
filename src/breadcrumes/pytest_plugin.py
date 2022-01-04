import pytest
from breadcrumes._rewrite_code import ChangeRecorder


def pytest_addoption(parser):
    group = parser.getgroup("breadcrumes")
    group.addoption(
        "--breadcrumes-fix",
        action="store_true",
        dest="breadcrumes_fix",
        help="Fix all deprecated code which is annotated by breadcrumes",
    )


class Plugin:
    def __init__(self):
        self.change_recorder = ChangeRecorder()


def pytest_load_initial_conftests(early_config, parser, args):
    early_config.pluginmanager.register(Plugin(), "_breadcrumes")


@pytest.fixture(autouse=True)
def record_changes(request):
    plugin = request.config.pluginmanager.getplugin("_breadcrumes")
    with plugin.change_recorder.activate():
        yield plugin.change_recorder


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    plugin = config.pluginmanager.getplugin("_breadcrumes")

    if exitstatus == 0 and config.option.breadcrumes_fix:
        num_fixes = plugin.change_recorder.num_fixes()
        plugin.change_recorder.fix_all()
        terminalreporter.section("breadcrumes")
        terminalreporter.write(f"{num_fixes} fixes where done by breadcrumes\n")
