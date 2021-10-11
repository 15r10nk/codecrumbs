import inspect
import ast
import dis


def getInvokingAstNode():
    frame = inspect.currentframe()
    frame = frame.f_back.f_back
    source_file = inspect.getsourcefile(frame)
    nodes, it = iter_bc_mapping(open(source_file).read())

    for bc_a, bc_b in it:
        if bc_match(bc_b, list(dis.Bytecode(frame.f_code))):
            func_bytecode = bc_a
            break
    else:
        print("not found")
        return

    for i in func_bytecode:
        if i.offset == frame.f_lasti:
            last_instr = i
            break
    else:
        assert False

    ast_node = nodes[last_instr.starts_line]

    return ast_node


def bytecodes_mapping(code):

    code_ast = ast.parse(code)
    nodeindex_ast = ast.parse(code)
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


def iter_bc_mapping(code):
    nodes, bc_a, bc_b = bytecodes_mapping(code)

    return nodes, iter_matched_bytecodes(bc_a, bc_b)


import types
from itertools import zip_longest


def iter_bytecodes(code):
    bc = list(dis.Bytecode(code))
    yield bc
    for l in bc:
        if isinstance(l.argval, types.CodeType):
            yield from iter_bytecodes(l.argval)


from dataclasses import dataclass


@dataclass
class AstStructureError(Exception):
    line: int


def iter_matched_bytecodes(code_a, code_b):
    for bc_a, bc_b in zip_longest(iter_bytecodes(code_a),
                                  iter_bytecodes(code_b)):
        if bc_a is None or bc_b is None:
            raise AstStructureError(None)

        if not bc_match(bc_a, bc_b):
            raise AstStructureError(None)
        yield bc_a, bc_b


def bc_match(list_a, list_b):
    if len(list_a) != len(list_b):
        return False

    for a, b in zip(list_a, list_b):
        for attr in ("opcode", "opname", "arg", "is_jump_target"):
            if getattr(a, attr) != getattr(b, attr):
                return False
    return True
