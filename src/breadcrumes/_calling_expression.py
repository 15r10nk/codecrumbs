import ast
import copy
import dis
import functools
import inspect
import io
import pathlib
from collections import defaultdict
from dataclasses import dataclass
from itertools import zip_longest
from types import CodeType

if False:
    debug_log = open("/tmp/debug.log", "w")

    def debug(*args):
        print(*args, file=debug_log)

    def debug_code(code):
        import io

        s = io.StringIO()
        dis.dis(code, file=s)
        debug(s.getvalue())


class AstStructureError(Exception):
    pass


_rewrite_hooks = {"": (lambda ast, source: None)}

# the main reason for this rewrite hooks is pytest,
# because we want to support the rewritten asserts in tests
try:
    from _pytest.assertion.rewrite import rewrite_asserts
except:
    pass
else:

    def pytest_rewrite(ast, source):
        rewrite_asserts(ast, source)

    _rewrite_hooks["pytest_assert"] = pytest_rewrite

from functools import cached_property


import tokenize


@dataclass
class code_offset:
    line_offset: int
    col_offset: int


@dataclass
class Token:
    filename: str
    lineno: int
    end_lineno: int
    col_offset: int
    end_col_offset: int
    type: object
    string: str

    @property
    def start(self):
        return (self.lineno, self.col_offset)

    @property
    def end(self):
        return (self.end_lineno, self.end_col_offset)


@dataclass
class lookup_result:
    filename: pathlib.Path
    _orig_ast: ast.AST
    ast_index: int
    code: str
    _offset: code_offset

    @cached_property
    def ast(self):
        return copy.deepcopy(self._orig_ast)

    @cached_property
    def tokens(self):
        file = io.StringIO(self.code)
        return [
            Token(
                filename=self.filename,
                type=t.type,
                string=t.string,
                lineno=t.start[0] + self._offset.line_offset,
                end_lineno=t.end[0] + self._offset.line_offset,
                col_offset=t.start[1] + self._offset.col_offset,
                end_col_offset=t.end[1] + self._offset.col_offset,
            )
            for t in tokenize.generate_tokens(file.readline)
        ]

    @cached_property
    def expr(self):
        for node in ast.walk(self._orig_ast):
            if node.ast_index == self.ast_index:
                return copy.deepcopy(node)

    def dump(self):
        print(ast.dump(self.expr, include_attributes=True))


def code_to_node_index(code):
    """
    returns a dictonary which maps instruction offset to ast index
    """
    if code is None:
        return None

    result = {}
    last_instr = None

    for i in dis.Bytecode(code):
        if i.starts_line is not None:
            last_instr = i
        if last_instr != None:
            result[i.offset] = last_instr.starts_line

    return result


PRINT_EXPR = dis.opmap["PRINT_EXPR"]
POP_TOP = dis.opmap["POP_TOP"]


def bc_key(code):
    # return code
    def map_op(op):
        if op == PRINT_EXPR:
            return POP_TOP
        return op

    return tuple((map_op(i.opcode), i.arg, i.starts_line) for i in dis.Bytecode(code))


@functools.lru_cache(maxsize=None)
def nodes_map(source_file, code, rewrite_hook, move_ast):
    nodes, it = _iter_bc_mapping(source_file, code, rewrite_hook)
    move_ast(nodes)

    for node in ast.walk(nodes):
        node.filename = source_file

    bc_map = {bc_key(bc_b): code_to_node_index(bc_a) for bc_a, bc_b in it}
    return nodes, bc_map


import doctest
import sys


def calling_expression(back=1):
    frame = inspect.currentframe().f_back

    for _ in range(back):
        frame = frame.f_back

    source_file = inspect.getfile(frame)
    code = "".join(inspect.findsource(frame)[0])

    line_offset = 0
    col_offset = 0

    def move_ast(module):
        pass

    import re

    __LINECACHE_FILENAME_RE = re.compile(
        r"<doctest " r"(?P<name>.+)" r"\[(?P<examplenum>\d+)\]>$"
    )

    m = __LINECACHE_FILENAME_RE.fullmatch(source_file)

    if m is not None:
        doctest_frame = frame
        while not doctest_frame.f_code.co_filename.endswith("doctest.py"):
            doctest_frame = doctest_frame.f_back

        doctest_self = doctest_frame.f_locals["self"]

        assert isinstance(doctest_self, doctest.DocTestRunner)

        if m and m.group("name") == doctest_self.test.name:
            example = doctest_self.test.examples[int(m.group("examplenum"))]

        if doctest_self.test.filename is not None:
            line_offset = doctest_self.test.lineno + example.lineno
            col_offset = example.indent + 4  # 4 for prompt
            source_file = doctest_self.test.filename

        def move_ast(module):
            for node in ast.walk(module):
                if isinstance(node, (ast.expr, ast.stmt)):
                    node.lineno += line_offset
                    node.end_lineno += line_offset
                    node.col_offset += col_offset
                    node.end_col_offset += col_offset

    if sys.version_info >= (3, 11):  # pragma: nocov
        nodes = ast.parse(code)
        positions = list(frame.f_code.co_positions())
        code_index = frame.f_lasti // 2

        code_position = positions[code_index]

        ast_index = None
        for i, code_node in enumerate(ast.walk(nodes)):
            code_node.ast_index = i
            code_node.filename = source_file
            if (
                isinstance(code_node, (ast.expr, ast.stmt))
                and (
                    code_node.lineno,
                    code_node.end_lineno,
                    code_node.col_offset,
                    code_node.end_col_offset,
                )
                == code_position
            ):
                ast_index = i

        assert ast_index is not None
        move_ast(nodes)

        return lookup_result(
            filename=pathlib.Path(source_file),
            _orig_ast=nodes,
            ast_index=ast_index,
            code=code,
            _offset=code_offset(line_offset, col_offset),
        )

    for rewrite_hook in _rewrite_hooks:

        nodes, bc_map = nodes_map(source_file, code, rewrite_hook, move_ast)

        node_index = bc_map.get(bc_key(frame.f_code), None)
        if node_index is not None:
            break

    if node_index is None:
        raise AstStructureError()

    ast_index = node_index[frame.f_lasti]

    return lookup_result(
        filename=pathlib.Path(source_file),
        _orig_ast=nodes,
        ast_index=ast_index,
        code=code,
        _offset=code_offset(line_offset, col_offset),
    )


def _iter_bc_mapping(source_file, code, rewrite_hook=""):
    code_ast = ast.parse(code)
    _rewrite_hooks[rewrite_hook](code_ast, code)
    nodeindex_ast = copy.deepcopy(code_ast)

    for i, (parent_node, index_node) in enumerate(walk_parent_child(nodeindex_ast)):
        index_node.lineno = i
        index_node.col_offset = 0
        if (
            parent_node is not None
            and isinstance(parent_node, ast.Call)
            and parent_node.func is index_node
        ):
            index_node.end_lineno = parent_node.lineno
        else:
            index_node.end_lineno = i
        index_node.end_offset = 1

    for i, code_node in enumerate(ast.walk(code_ast)):
        code_node.ast_index = i

    return (
        code_ast,
        _iter_matched_bytecodes(
            compile(nodeindex_ast, source_file, mode="exec"),
            compile(code_ast, source_file, mode="exec"),
        ),
    )


def walk_parent_child(node):
    from collections import deque

    todo = deque([(None, node)])
    while todo:
        parent, node = todo.popleft()
        todo.extend([(node, child) for child in ast.iter_child_nodes(node)])
        yield parent, node


def sort_out(func, it):
    t = []
    f = []
    for e in it:
        if func(e):
            t.append(e)
        else:
            f.append(e)
    return t, f


def _match_consts(consts_a, consts_b):
    codes_a = [c for c in consts_a if isinstance(c, CodeType)]
    codes_b = [c for c in consts_b if isinstance(c, CodeType)]
    assert len(codes_a) >= len(codes_b)

    mapping = defaultdict(list)
    for code_b in codes_b:
        matching, codes_a = sort_out(lambda a: _bc_match(a, code_b), codes_a)
        mapping[code_b] = matching

    assert not codes_a
    if codes_a:
        return

    for code_b, codes_a in mapping.items():
        if len(codes_a) == 1:
            yield codes_a[0], code_b
        else:
            yield None, code_b


def _iter_matched_bytecodes(code_a: CodeType, code_b: CodeType):
    if _bc_match(code_a, code_b):
        yield code_a, code_b
    else:
        yield None, code_b
        yield from _match_consts(code_a.co_consts, code_b.co_consts)
        return

    for bc_a, bc_b in zip_longest(
        no_NOP(dis.Bytecode(code_a)), no_NOP(dis.Bytecode(code_b))
    ):
        assert not (bc_a is None or bc_b is None)

        if isinstance(bc_a.argval, CodeType):
            yield from _iter_matched_bytecodes(bc_a.argval, bc_b.argval)


def no_NOP(instruction_iter):
    for i in instruction_iter:
        if i.opname != "NOP":
            yield i


def _bc_match(code_a: CodeType, code_b: CodeType):
    for a, b in zip_longest(no_NOP(dis.Bytecode(code_a)), no_NOP(dis.Bytecode(code_b))):
        if a is None or b is None:
            # branches with different length have usually different entries
            # this is also almost impossible
            return False  # pragma: no cover

        for attr in ("opcode", "arg"):
            if getattr(a, attr) != getattr(b, attr):
                return False
        if isinstance(a.argval, (str, int)):
            if a.argval != b.argval:
                return False
    return True
