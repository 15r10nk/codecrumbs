import inspect
import ast
import dis

from dataclasses import dataclass

from types import CodeType
from itertools import zip_longest


@dataclass
class lookup_result:
    expr: ast.AST
    filename: str
    ast: ast.AST


def calling_expression():
    frame = inspect.currentframe()
    frame = frame.f_back.f_back
    source_file = inspect.getsourcefile(frame)
    nodes, it = iter_bc_mapping(open(source_file).read())

    for bc_a, bc_b in it:
        if bc_match(bc_b, frame.f_code):
            func_bytecode = bc_a
            break
    else:
        print("not found")
        return

    if func_bytecode is None:
        raise AstStructureError(bc_b.co_firstlineno)

    for i in dis.Bytecode(func_bytecode):
        print(i)
        if i.starts_line is not None:
            last_instr = i
        if i.offset == frame.f_lasti:
            break
    else:
        assert False

    ast_node = nodes[last_instr.starts_line]

    return lookup_result(ast_node, source_file, nodes)


import copy


def bytecodes_mapping(code):
    code_ast = ast.parse(code)
    nodeindex_ast = copy.deepcopy(code_ast)
    nodes = {}

    for i, (code_node, index_node) in enumerate(
        zip(ast.walk(code_ast), ast.walk(nodeindex_ast))
    ):
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


def iter_bc_mapping(code):
    nodes, bc_a, bc_b = bytecodes_mapping(code)

    return nodes, iter_matched_bytecodes(bc_a, bc_b)


@dataclass
class AstStructureError(Exception):
    line: int


def iter_matched_bytecodes(code_a: CodeType, code_b: CodeType):
    if bc_match(code_a, code_b):
        yield code_a, code_b
    else:
        yield None, code_b
        return
        # yield other non matching codes

    for bc_a, bc_b in zip_longest(dis.Bytecode(code_a), dis.Bytecode(code_b)):
        assert not (bc_a is None or bc_b is None)

        if isinstance(bc_a.argval, CodeType):
            yield from iter_matched_bytecodes(bc_a.argval, bc_b.argval)


def bc_match(code_a: CodeType, code_b: CodeType):
    for a, b in zip_longest(dis.Bytecode(code_a), dis.Bytecode(code_b)):
        if a is None or b is None:
            return False

        for attr in ("opcode", "arg"):
            if getattr(a, attr) != getattr(b, attr):
                return False
    return True
