from calling_expression import (
    _iter_matched_bytecodes,
    AstStructureError,
    _iter_bc_mapping,
    _bytecodes_mapping,
)

import dis

import sys
import pathlib


def check_source(code, fix=False):
    if fix:
        code = fix_code(code)
    try:
        return all( a is not None for a,b in _iter_bc_mapping(code)[1])
    except AstStructureError as e:
        print(e)
        return False
    else:
        return True


def test_lambdas():
    assert not check_source("foo(lambda:a,lambda:a)")
    assert check_source("foo(lambda:a,lambda:a)", fix=True)
    assert check_source("foo(lambda:a,lambda:b)")


import types


def dump_code(code, file):
    bc = dis.Bytecode(code)
    file.write(bc.info() + "\n")
    print("consts", file=file)
    for c in bc.codeobj.co_consts:
        if isinstance(c, types.CodeType):
            dump_code(c, file)
    for l in bc:
        file.write(f"{l.opname} {l.arg} {l.offset}\n")
    for l in bc:
        if isinstance(l.argval, types.CodeType):
            dump_code(l.argval, file)


def diff_bytecodes(filename):

    if not filename.resolve().parent == pathlib.Path("examples").resolve():
        example_filename = pathlib.Path("examples") / ("_" + filename.name)
        shutil.copy(filename, example_filename)
        filename = example_filename
    code = open(filename).read()
    try:
        nodes, bc_a, bc_b = _bytecodes_mapping(code)
        dump_code(bc_a, file=open(f"{filename}_a", "w"))
        dump_code(bc_b, file=open(f"{filename}_b", "w"))
    except KeyboardInterrupt:
        raise
    except:
        pass


import shutil
from test_fix_code import fix_code

if __name__ == "__main__":
    dirname = sys.argv[1]
    done = set()

    for filename in pathlib.Path(dirname).rglob("*.py"):

        import ast

        try:
            code = open(filename).read()
            ast = ast.parse(code)
            compile(ast, "foo", "exec")
        except KeyboardInterrupt:
            raise
        except:
            continue

        if hash(code) in done:
            print("skip", filename)
            continue

        done.add(hash(code))

        if False:
            code = fix_code(code)
            with open(str(filename) + "_fixed", "w") as f:
                f.write(code)

        try:
            if not check_source(code):
                diff_bytecodes(filename)
                print("check", filename, "failed")

        except KeyboardInterrupt:
            raise
        except Exception as e:
            print("check raises", filename, "failed")
            print(e)
            diff_bytecodes(filename)
