import ast
import copy
import dis
import functools
import inspect
from collections import defaultdict
from dataclasses import dataclass
from itertools import zip_longest
from types import CodeType


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

try:
    from functools import cached_property
except:
    cached_property = property
    if False:

        class cached_property:
            def __init__(self, f):
                self.f = f

            def __get__(self, obj, typ=None):
                value = self.f(obj)
                setattr(self, self.f.__name__, value)
                return value


@dataclass
class lookup_result:
    filename: str
    _orig_ast: ast.AST
    ast_index: int

    @cached_property
    def ast(self):
        return copy.deepcopy(self._orig_ast)

    @cached_property
    def expr(self):
        for node in ast.walk(self._orig_ast):
            if node.ast_index == self.ast_index:
                return copy.deepcopy(node)

    def dump(self):
        print(ast.dump(self.expr))


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


def bc_key(code):
    # return code
    return tuple((i.opcode, i.arg, i.starts_line) for i in dis.Bytecode(code))


@functools.lru_cache(maxsize=None)
def nodes_map(source_file, rewrite_hook):
    with open(source_file) as code:
        nodes, it = _iter_bc_mapping(source_file, code.read(), rewrite_hook)

    for node in ast.walk(nodes):
        node.filename = source_file

    bc_map = {bc_key(bc_b): code_to_node_index(bc_a) for bc_a, bc_b in it}
    return nodes, bc_map


def calling_expression():
    frame = inspect.currentframe().f_back.f_back

    source_file = inspect.getsourcefile(frame)
    print(source_file, inspect.getfile(frame))

    for rewrite_hook in _rewrite_hooks:
        nodes, bc_map = nodes_map(source_file, rewrite_hook)

        node_index = bc_map.get(bc_key(frame.f_code), None)
        if node_index is not None:
            break

    if node_index is None:
        raise AstStructureError()

    ast_index = node_index[frame.f_lasti]

    return lookup_result(filename=source_file, _orig_ast=nodes, ast_index=ast_index)


def _iter_bc_mapping(source_file, code, rewrite_hook=""):
    code_ast = ast.parse(code)
    _rewrite_hooks[rewrite_hook](code_ast, code)
    nodeindex_ast = copy.deepcopy(code_ast)
    nodes = []

    for i, (parent_node, index_node) in enumerate(walk_parent_child(nodeindex_ast)):
        index_node.lineno = i
        index_node.col_offset = 0
        if parent_node is not None and isinstance(parent_node, ast.Call):
            index_node.end_lineno = parent_node.lineno
        else:
            index_node.end_lineno = i
        index_node.end_offset = 1

    for i, code_node in enumerate(ast.walk(code_ast)):
        code_node.ast_index = i
        nodes.append(code_node)

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
