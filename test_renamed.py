from breadcrumes import renamed


class Example:
    oldprop = renamed("newprop")
    oldprop1 = renamed("newprop")
    oldprop2 = renamed("newprop")

    def __init__(self):
        self.newprop = 5


t = Example()


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


from calling_expression import calling_expression
import ast



def old():
    node = calling_expression().expr
    print("node:", ast.dump(node, include_attributes=True))
    return 5


def func():

    print(old() + 1)


func()
