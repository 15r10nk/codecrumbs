import warnings


class renamed:
    def __init__(self, newname, since_version=None):
        self.new_name = newname

    def __set_name__(self, owner, name):
        self.current_name = name

    def __get__(self, obj, objtype=None):
        print(obj, objtype)
        warnings.warn(
            f'usage of "{self.current_name}" is deprecated and should be replaced with "{self.new_name}" (can be fixed with breadcrumes)',
            DeprecationWarning,
            stacklevel=2,
        )
        if obj is None:
            obj = objtype
        return getattr(obj, self.new_name)

    def __set__(self, obj, value):
        warnings.warn(
            f'usage of "{self.current_name}" is deprecated and should be replaced with "{self.new_name}" (can be fixed with breadcrumes)',
            DeprecationWarning,
            stacklevel=2,
        )
        print("set", obj, value)
        return setattr(obj, self.new_name, value)


def parameter_renamed(since_version=None, **old_params):
    def w(f):
        def r(*a, **ka):
            for key in ka:
                if key in old_params:
                    old_arg = key
                    new_arg = old_params[key]
                    warnings.warn(
                        f'usage of named argument "{old_arg}" is deprecated and should be replaced with "{new_arg}" (can be fixed with breadcrumes)',
                        DeprecationWarning,
                        stacklevel=2,
                    )

                    assert (
                        new_param not in ka
                    ), f"you can not specify new and deprecated arguments the same time"

                    value = ka[old_param]
                    del ka[old_param]
                    ka[new_param] = value

            f(*a, **ka)

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
