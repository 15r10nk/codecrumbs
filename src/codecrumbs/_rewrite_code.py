from __future__ import annotations

import contextlib
import pathlib
import subprocess as sp
from collections import defaultdict
from dataclasses import dataclass

try:
    from itertools import pairwise
except ImportError:
    from itertools import tee

    def pairwise(iterable):  # type: ignore
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)


# copied from pathlib to support python < 3.9
def is_relative_to(path, *other):
    """Return True if the path is relative to another path or False."""
    try:
        path.relative_to(*other)
        return True
    except ValueError:
        return False


@dataclass(order=True)
class Replacement:
    start: tuple[int, int]
    end: tuple[int, int]
    text: str
    change_id: int = 0


class Change:
    _next_change_id = 0

    def __init__(self):
        self.change_id = self._next_change_id
        type(self)._next_change_id += 1

    def replace(self, node, new_contend):

        # remove this
        if not isinstance(new_contend, str):
            new_contend = repr(new_contend)

        start = node.start if hasattr(node, "start") else (node.lineno, node.col_offset)
        end = (
            node.end if hasattr(node, "end") else (node.end_lineno, node.end_col_offset)
        )

        get_source_file(node.filename).replacements.append(
            Replacement(
                start=start, end=end, text=new_contend, change_id=self.change_id
            )
        )


class SourceFile:
    def __init__(self, filename):
        self.replacements = []
        self.filename = filename

    def rewrite(self):

        new_code = self.new_code()

        if new_code is not None:

            with open(self.filename, "bw") as code:
                code.write(new_code.encode())

    def new_code(self):
        replacements = list(self.replacements)
        replacements.sort()

        for r in replacements:
            assert r.start < r.end

        # TODO check for overlapping replacements
        for lhs, rhs in pairwise(replacements):
            assert lhs.end <= rhs.start

        if not replacements:
            return

        with open(self.filename, newline="") as code:
            code = code.read()

        new_code = ""
        last_i = 0
        add_end = True

        for pos, i, c in code_stream(code):
            if replacements:
                r = replacements[0]
                if pos == r.start:
                    new_code += code[last_i:i] + r.text
                    add_end = False
                if pos == r.end:
                    last_i = i
                    add_end = True
                    replacements.pop(0)
            else:
                break

        if add_end:
            new_code += code[last_i:]

        return new_code

    def generate_patch(self, basedir):

        filename = self.filename
        if is_relative_to(filename, basedir):
            filename = filename.relative_to(basedir)

        with open(self.filename, newline="") as code:
            old_code = code.read().splitlines(keepends=True)

        new_code = self.new_code().splitlines(keepends=True)

        import difflib

        yield from difflib.unified_diff(
            old_code, new_code, fromfile=str(filename), tofile=str(filename)
        )


def get_source_file(filename):
    filename = pathlib.Path(filename)

    if filename not in ChangeRecorder.current._source_files:
        ChangeRecorder.current._source_files[filename] = SourceFile(filename)

    return ChangeRecorder.current._source_files[filename]


def replace(node, new_contend):
    Change().replace(node, new_contend)


class ChangeRecorder:
    current: ChangeRecorder | None = None

    def __init__(self):

        self._source_files = defaultdict(SourceFile)

    @contextlib.contextmanager
    def activate(self):
        old_recorder = ChangeRecorder.current
        ChangeRecorder.current = self
        yield self
        ChangeRecorder.current = old_recorder

    def num_fixes(self):
        changes = set()
        for file in self._source_files.values():
            changes.update(change.change_id for change in file.replacements)
        return len(changes)

    def fix_all(self, *, check_git=True):
        for file in self._source_files.values():
            filename = file.filename
            if check_git:
                if (
                    sp.run(
                        ["git", "ls-files", "--error-unmatch", str(filename.name)],
                        cwd=filename.parent,
                        stdout=sp.DEVNULL,
                    ).returncode
                    != 0
                ):
                    print(
                        f"{filename}: skip fixing, because the file is not in a git repository"
                    )
                    continue

                if (
                    sp.run(
                        ["git", "diff", "--quiet", str(filename.name)],
                        cwd=filename.parent,
                        stdout=sp.DEVNULL,
                    ).returncode
                    != 0
                ):
                    print(
                        f"{filename}: skip fixing, because the file has unstaged changes"
                    )
                    continue

                if (
                    sp.run(
                        ["git", "check-ignore", "--quiet", str(filename.name)],
                        cwd=filename.parent,
                        stdout=sp.DEVNULL,
                    ).returncode
                    == 0
                ):
                    print(
                        f"{filename}: skip fixing, because the file is ignored by git"
                    )
                    continue

            file.rewrite()

    def generate_patchfile(self, filename):
        with open(filename, "w") as patch:
            for line in self.generate_patch(filename.parent):
                patch.write(line)

    def generate_patch(self, basedir):
        for file in self._source_files.values():
            if is_relative_to(file.filename, basedir):
                yield from file.generate_patch(basedir)


global_recorder = ChangeRecorder()
ChangeRecorder.current = global_recorder


def code_stream(source):
    idx = 0
    p_line = 1
    p_col = 0
    while idx < len(source):
        c = source[idx]
        if c == "\r" and idx + 1 < len(source) and source[idx + 1] == "\n":
            # \r\n
            yield (p_line, p_col), idx, "\r\n"
            idx += 1
            p_line += 1
            p_col = 0
        elif c in "\r\n":
            # \r or \n
            yield (p_line, p_col), idx, c
            p_line += 1
            p_col = 0
        else:
            yield (p_line, p_col), idx, c
            p_col += 1
        idx += 1
