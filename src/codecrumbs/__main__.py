import argparse
import re
import runpy
import sys
from pathlib import Path

from ._rewrite_code import ChangeRecorder


def main():
    parser = argparse.ArgumentParser(prog="codecrumbs")
    subparsers = parser.add_subparsers(dest="subcommand")
    run_parser = subparsers.add_parser("run", help="run a python script")
    run_parser.add_argument(
        "--fix",
        help="fix deprecated code after the command terminates",
        action="store_true",
    )
    run_parser.add_argument("command", nargs="*")

    args = parser.parse_args()
    if args.subcommand == "run":
        script, *cmd_args = args.command
        sys.argv = args.command
        run_name = re.sub("\\.py$", "", script)

        init_globals = {"__file__": Path(script).resolve(), "__package__": ""}

        change_recorder = ChangeRecorder()

        try:
            with change_recorder.activate():
                runpy.run_path(
                    str(Path(script).resolve()),
                    init_globals=init_globals,
                    run_name="__main__",
                )
        except:
            raise
        finally:
            if args.fix:
                change_recorder.fix_all()

        exit(0)

    else:
        print("refactor me")


if __name__ == "__main__":
    main()
