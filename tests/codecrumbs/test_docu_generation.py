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
        == """
some docu

.. versionchanged::
    parameter *old* was renamed to *new*
"""
    ), test.__doc__
