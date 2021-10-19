import ast
from collections import defaultdict


def fix_code(code):
    r"""
    break lines before and after lambdas and comprehensions with
    line-contuniation character \ and newline
    """
    a = ast.parse(code)
    breaks = defaultdict(set)

    for node in ast.walk(a):
        if isinstance(
            node,
            (ast.GeneratorExp, ast.SetComp, ast.ListComp, ast.DictComp, ast.Lambda),
        ):
            breaks[node.lineno - 1].add(node.col_offset)
            breaks[node.end_lineno - 1].add(node.end_col_offset)

    new_code = []
    for line_number, line in enumerate(code.splitlines()):
        segments = sorted(breaks[line_number])
        if segments:
            parts = []
            last_i = 0
            for i in segments:
                parts.append(line[last_i:i])
                last_i = i
            parts.append(line[last_i:])
            line = "\\\n".join(parts)
        new_code.append(line)
    return "\n".join(new_code) + "\n#end"


def test_fix_generator():

    code = """a=sum(i for i in l)+sum(i for i in l)
foo"""
    new_code = """a=sum\\
(i for i in l)\\
+sum\\
(i for i in l)\\

foo
#end"""

    assert fix_code(code) == new_code
