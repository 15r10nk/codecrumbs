import warnings


class renamed:
    def __init__(self, newname, since_version=None):
        self.new_name = newname

    def __set_name__(self, owner, name):
        self.current_name = name

    def warn(self):
        warnings.warn(
            f'".{self.current_name}" should be replaced with ".{self.new_name}" (fixable with breadcrumes)',
            DeprecationWarning,
            stacklevel=3,
        )

    def __get__(self, obj, objtype=None):
        self.warn()
        if obj is None:
            obj = objtype
        return getattr(obj, self.new_name)

    def __set__(self, obj, value):
        self.warn()
        return setattr(obj, self.new_name, value)


def parameter_renamed(since_version=None, **old_params):
    def w(f):
        def r(*a, **ka):
            new_ka = {}
            for key in ka:
                if key in old_params:
                    old_arg = key
                    new_arg = old_params[key]
                    warnings.warn(
                        f'argument name "{old_arg}=" should be replaced with "{new_arg}=" (fixable with breadcrumes)',
                        DeprecationWarning,
                        stacklevel=2,
                    )

                    assert (
                        new_arg not in ka
                    ), f"you can not specify {old_arg} and {new_arg} the same time"

                    new_ka[new_arg] = ka[old_arg]
                else:
                    new_ka[key] = ka[key]

            f(*a, **new_ka)

        return r

    return w


def inline_source(since_version=None):
    def w(f):
        def r(*a, **ka):
            warnings.warn(
                f"usage of this function is deprecated and should be replaced with the defined implementation (can be fixed with breadcrumes)",
                DeprecationWarning,
                stacklevel=2,
            )
            f(*a, **ka)

        return r

    return w
