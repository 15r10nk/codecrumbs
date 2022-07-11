from codecrumbs import argument_renamed


@argument_renamed("old", "new")
@argument_renamed("older", "newer", since="1.1")
def function(new, newer):
    """
    this is the function with the new argument
    """
    return new


@argument_renamed("old", "new")
def undocumented_function(new):
    return new
