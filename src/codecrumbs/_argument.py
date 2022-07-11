import inspect
import textwrap
import token
import warnings
from dataclasses import dataclass
from functools import partial

from ._calling_expression import calling_expression
from ._rewrite_code import replace


@dataclass
class DeprecationRenaming:
    since: str
    old_name: str
    new_name: str

    def get_documentation(self):
        directive = f".. versionchanged:: {self.since or '<next>'}"
        return f"\n{directive}\n\n    parameter *{self.old_name}* was renamed to *{self.new_name}*\n"


class FunctionWrapper:
    @staticmethod
    def of(obj):
        if isinstance(obj, FunctionWrapper):
            return obj
        return FunctionWrapper(obj)

    def __init__(self, function) -> None:
        self.f = function
        self.old_params = {}
        self.deprecations = []
        self.since_version = None

    def _set_since(self, version):
        self.since_version = version
        return self

    @property
    def reverse_old_params(self):
        return {v: k for k, v in self.items()}

    def __get__(self, obj, cls):
        if obj is not None:
            return partial(self, obj)
        else:
            return self

    def __call__(self, *a, **ka):
        new_ka = {}
        changed = False
        for key in ka:
            if key in self.old_params:
                old_arg = key
                new_arg = self.old_params[key]

                if new_arg in ka:
                    raise TypeError(
                        f"{old_arg}=... and {new_arg}=... can not be used at the same time"
                    )

                warnings.warn(
                    f'argument name "{old_arg}=" should be replaced with "{new_arg}=" (fixable with codecrumbs)',
                    DeprecationWarning,
                    stacklevel=2,
                )

                new_ka[new_arg] = ka[old_arg]
                changed = True
            else:
                new_ka[key] = ka[key]

        if changed:
            expr = calling_expression()

            tokens = expr.tokens

            for arg in expr.expr.keywords:
                if arg.arg not in self.old_params:
                    continue

                arg_value = arg.value
                start = arg_value.lineno, arg_value.col_offset

                mytokens = [
                    t
                    for t in tokens
                    if t.start < start and t.type in (token.NAME, token.OP)
                ]

                name, op = mytokens[-2:]
                name.filename = expr.filename

                assert op.string == "=", op.string
                assert name.string == arg.arg

                replace(name, self.old_params[arg.arg])

        return self.f(*a, **new_ka)

    def _add_renaming(self, old_param, new_param, since):
        # check missuse
        signature = inspect.signature(self.f)
        if old_param in signature.parameters:
            if new_param in signature.parameters:
                raise TypeError(
                    "parameter 'old' should be removed from signature if it is renamed to 'new'"
                )
            else:
                raise TypeError(
                    "parameter 'old' should be renamed to 'new' in the signature"
                )
        self.old_params[old_param] = new_param
        self.deprecations.append(
            DeprecationRenaming(since=since, old_name=old_param, new_name=new_param)
        )

    @property
    def __signature__(self):
        signature = inspect.signature(self.f)
        parameters = list(signature.parameters.values()) + [
            signature.parameters[v].replace(
                kind=inspect.Parameter.KEYWORD_ONLY,
                name=k,
            )
            for k, v in self.old_params.items()
        ]

        return inspect.Signature(
            parameters, return_annotation=signature.return_annotation
        )

    @property
    def __doc__(self):
        doc = self.f.__doc__ or ""
        if doc:
            doc = textwrap.dedent(doc).rstrip() + "\n"
            for deprecation in sorted(self.deprecations, key=lambda d: d.since or ""):
                doc += deprecation.get_documentation()

        return doc


def argument_renamed(old_name: str, new_name: str, *, since=None):
    def w(f):
        wrapper = FunctionWrapper.of(f)
        wrapper._add_renaming(old_name, new_name, since)

        return wrapper

    return w
