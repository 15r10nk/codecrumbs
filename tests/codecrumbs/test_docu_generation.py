from codecrumbs import argument_renamed


def test_argument_renamed():
    @argument_renamed(old="new")
    def test(new):
        """
        some docu

        """
        print(new)

    assert (
        test.__doc__
        =='\nsome docu\n\n.. versionchanged:: <next>\n\n    parameter *old* was renamed to *new*\n' 
    ), test.__doc__
