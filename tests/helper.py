def never_called(*a, **ka):
    assert False, "this function should never be called"
