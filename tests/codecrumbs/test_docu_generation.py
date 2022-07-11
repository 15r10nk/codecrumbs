from codecrumbs import argument_renamed


def test_argument_renamed_no_since():
    @argument_renamed("old", "new")
    def test(new):
        """
        some docu

        """
        print(new)

    assert (
        test.__doc__
        == "\nsome docu\n\n.. versionchanged:: <next>\n\n    parameter *old* was renamed to *new*\n"
    ), test.__doc__


def test_argument_renamed_since():
    @argument_renamed("old", "new", since="5.0")
    def test(new):
        """
        some docu

        """
        print(new)

    assert (
        test.__doc__
        == "\nsome docu\n\n.. versionchanged:: 5.0\n\n    parameter *old* was renamed to *new*\n"
    ), test.__doc__


def test_version_sorting():
    @argument_renamed("old1", "new1", since="1.0")
    @argument_renamed("old2", "new2", since="3.0")
    @argument_renamed("old3", "new3", since="2.0")
    def test(new1, new2, new3):
        """
        some docu

        """
        print(new)

    assert (
        test.__doc__
        == "\nsome docu\n\n"
        + ".. versionchanged:: 1.0\n\n    parameter *old1* was renamed to *new1*\n\n"
        + ".. versionchanged:: 2.0\n\n    parameter *old3* was renamed to *new3*\n\n"
        + ".. versionchanged:: 3.0\n\n    parameter *old2* was renamed to *new2*\n"
    ), test.__doc__
