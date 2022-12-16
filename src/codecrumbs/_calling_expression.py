import ast
import inspect
import io
import pathlib
import tokenize
from dataclasses import dataclass
from functools import cached_property


@dataclass
class code_offset:
    line_offset: int
    col_offset: int


@dataclass
class Token:
    filename: pathlib.Path
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
    ast_index: int
    code: str
    _offset: code_offset
    expr: ast.AST

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

    def dump(self):
        print(ast.dump(self.expr, include_attributes=True))


import executing


def calling_expression(back=1):
    frame = inspect.currentframe().f_back

    for _ in range(back):
        frame = frame.f_back

    source_file = inspect.getfile(frame)
    code = "".join(inspect.findsource(frame)[0])

    ex = executing.Source.executing(frame)

    if not hasattr(ex.node, "ast_index"):
        _orig_ast = ex.node

        for i, code_node in enumerate(ast.walk(_orig_ast)):
            code_node.ast_index = i
            code_node.filename = source_file

    return lookup_result(
        filename=pathlib.Path(source_file),
        expr=ex.node,
        ast_index=ex.node.ast_index,
        code=code,
        _offset=code_offset(0, 0),
    )
