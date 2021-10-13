import inspect
import ast
import dis

from dataclasses import dataclass

from types import CodeType
from itertools import zip_longest
import copy
import functools


@dataclass
class AstStructureError(Exception):
    line: int


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


@dataclass
class lookup_result:
    expr: ast.AST
    filename: str
    ast: ast.AST


def code_to_node_index(code):
    if code is None:
        return None

    result = {}
    for i in dis.Bytecode(code):
        if i.starts_line is not None:
            last_instr = i
        result[i.offset] = last_instr.starts_line

    return result


def bc_key(code):
    # return code
    return tuple((i.opcode, i.arg, i.starts_line) for i in dis.Bytecode(code))


@functools.lru_cache(maxsize=None)
def nodes_map(source_file, rewrite_hook):
    nodes, it = _iter_bc_mapping(open(source_file).read(), rewrite_hook)
    it = list(it)

    bc_map = {bc_key(bc_b): code_to_node_index(bc_a) for bc_a, bc_b in it}
    return nodes, bc_map


def calling_expression():
    frame = inspect.currentframe().f_back.f_back

    source_file = inspect.getsourcefile(frame)

    node_index = None

    for rewrite_hook in _rewrite_hooks:
        nodes, bc_map = nodes_map(source_file, rewrite_hook)

        node_index = bc_map.get(bc_key(frame.f_code), None)
        if node_index is not None:
            break

    if node_index is None:
        raise AstStructureError(frame.f_code.co_firstlineno)

    ast_node = nodes[node_index[frame.f_lasti]]

    return lookup_result(ast_node, source_file, nodes)


def _iter_bc_mapping(code, rewrite_hook=""):
    nodes, bc_a, bc_b = _bytecodes_mapping(code, rewrite_hook)
    return nodes, _iter_matched_bytecodes(bc_a, bc_b)


def _bytecodes_mapping(code, rewrite_hook):
    code_ast = ast.parse(code)
    _rewrite_hooks[rewrite_hook](code_ast, code)
    nodeindex_ast = copy.deepcopy(code_ast)
    nodes = {}

    for i, (code_node, index_node) in enumerate(
            zip(ast.walk(code_ast), ast.walk(nodeindex_ast))):
        index_node.lineno = i
        index_node.col_offset = 0
        index_node.end_lineno = i
        index_node.end_offset = 1
        nodes[i] = code_node

    return (
        nodes,
        compile(nodeindex_ast, "foo", mode="exec"),
        compile(code_ast, "foo", mode="exec"),
    )


from collections import defaultdict


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
        assert matching
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

    # yield every code arg
    for bc_a, bc_b in zip_longest(dis.Bytecode(code_a), dis.Bytecode(code_b)):
        assert not (bc_a is None or bc_b is None)

        if isinstance(bc_a.argval, CodeType):
            yield from _iter_matched_bytecodes(bc_a.argval, bc_b.argval)


def _bc_match(code_a: CodeType, code_b: CodeType):
    for a, b in zip_longest(dis.Bytecode(code_a), dis.Bytecode(code_b)):
        if a is None or b is None:
            return False

        for attr in ("opcode", "arg"):
            if getattr(a, attr) != getattr(b, attr):
                return False
    return True
