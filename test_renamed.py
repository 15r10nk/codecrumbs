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


from ast_utils import getInvokingAstNode
import ast


def old():
    node = getInvokingAstNode()
    print("node:", ast.dump(node, include_attributes=True))
    return 5


def func():

    print(old() + 1)


func()
