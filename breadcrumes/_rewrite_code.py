import ast
import contextlib
import pathlib
from collections import defaultdict
from dataclasses import dataclass

try:
    from itertools import pairwise
except:
    from itertools import tee

    def pairwise(iterable):
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)


@dataclass(order=True)
class Replacement:
    start: (int, int)
    end: (int, int)
    text: str
    change_id: int = 0


class Change:
    _next_change_id = 0

    def __init__(self):
        self.change_id = self._next_change_id
        type(self)._next_change_id += 1

    def replace(self, node, new_contend):
        if isinstance(new_contend, ast.AST):
            new_contend = ast.unparse(new_contend)

        # remove this
        if not isinstance(new_contend, str):
            new_contend = repr(new_contend)

        start = node.start if hasattr(node, "start") else (node.lineno, node.col_offset)
        end = (
            node.end if hasattr(node, "end") else (node.end_lineno, node.end_col_offset)
        )

        self._replace(
            node.filename,
            start,
            end,
            new_contend,
        )

    def _replace(self, filename, start, end, new_contend):

        if isinstance(new_contend, ast.AST):
            new_contend = ast.unparse(new_contend)

        get_source_file(filename).replacements.append(
            Replacement(
                start=start, end=end, text=new_contend, change_id=self.change_id
            )
        )


class SourceFile:
    def __init__(self, filename):
        self.replacements = []
        self.filename = filename

    def rewrite(self):

        replacements = list(self.replacements)
        replacements.sort()

        for r in replacements:
            assert r.start < r.end

        print(replacements)
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

        with open(self.filename, "bw") as code:
            code.write(new_code.encode())


def get_source_file(filename):
    filename = pathlib.Path(filename)

    if filename not in ChangeRecorder.current._source_files:
        ChangeRecorder.current._source_files[filename] = SourceFile(filename)

    return ChangeRecorder.current._source_files[filename]


def replace(node, new_contend):
    Change().replace(node, new_contend)


def insert_before(node, new_contend):
    if isinstance(new_contend, ast.AST):
        new_contend = ast.unparse(new_contend)
    new_contend += "\n"

    _replace(
        node.filename,
        (node.lineno, node.col_offset),
        (node.lineno, node.col_offset),
        new_contend,
    )


class ChangeRecorder:
    current = None

    def __init__(self):

        self._source_files = defaultdict(SourceFile)

    @contextlib.contextmanager
    def activate(self):
        old_recorder = ChangeRecorder.current
        ChangeRecorder.current = self
        yield
        ChangeRecorder.current = old_recorder

    def num_fixes(self):
        changes = set()
        for file in self._source_files.values():
            changes.update(change.change_id for change in file.replacements)
        return len(changes)

    def fix_all(self):
        for file in self._source_files.values():
            file.rewrite()

    def dump(self):
        for file in self._source_files.values():
            print("file:", file.filename)
            for change in file.replacements:
                print("  change:", change)


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


def rewrite(filename=None):
    if filename is None:
        for file in ChangeRecorder.current._source_files.values:
            file.rewrite()
    else:
        if filename in ChangeRecorder.current._source_files:
            ChangeRecorder.current._source_files[filename].rewrite()
