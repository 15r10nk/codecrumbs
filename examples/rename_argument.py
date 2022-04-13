from codecrumbs import renamed_argument


@renamed_argument(old="new")
@renamed_argument(older="newer").since("1.1")
def function(new, newer):
    """
    this is the function with the new argument
    """
    return new


@renamed_argument(old="new")
def undocumented_function(new):
    return new
