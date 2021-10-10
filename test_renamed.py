from breadcrumes import renamed


class Test:
    oldprop = renamed("newprop")
    oldprop1 = renamed("newprop")
    oldprop2 = renamed("newprop")

    def __init__(self):
        self.newprop = 5


t = Test()


def foo(*a):
    pass


print(t.oldprop)
t.oldprop = 3


def a():
    foo(
        t.oldprop1,
        t.oldprop2,
    )


def b():
    foo(t.oldprop1, t.oldprop2)


def c():
    foo((t.oldprop1 + t.oldprop3))


import inspect
import ast
import dis


def getInvokingAstNode():

    c = func
    frame = inspect.currentframe()
    frame = frame.f_back.f_back
    code = inspect.getsource(frame)

    code_ast = ast.parse(code)
    nodes = {}

    for i, node in enumerate(ast.walk(code_ast)):
        node.lineno = i
        node.col_offset = 0
        node.end_lineno = i
        node.end_offset = 1
        nodes[i] = node

    compiled = compile(code_ast, "foo", mode="exec")

    module_bytecode = dis.Bytecode(compiled)
    func_bytecode = dis.Bytecode(next(iter(module_bytecode)).argval)

    for i in func_bytecode:
        if i.offset == frame.f_lasti:
            last_instr = i
            break
    else:
        assert False

    ast_node = nodes[last_instr.starts_line]

    return ast_node


def old():
    node = getInvokingAstNode()
    print("node:", ast.dump(node, include_attributes=True))
    return 5


def func():

    print(old() + 1)


func()
