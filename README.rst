==================
pytest-codecrumbs
==================

.. image:: https://img.shields.io/pypi/v/pytest-codecrumbs.svg
    :target: https://pypi.org/project/pytest-codecrumbs
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pytest-codecrumbs.svg
    :target: https://pypi.org/project/pytest-codecrumbs
    :alt: Python versions

.. image:: https://ci.appveyor.com/api/projects/status/github/15r10nk/pytest-codecrumbs?branch=master
    :target: https://ci.appveyor.com/project/15r10nk/pytest-codecrumbs/branch/master
    :alt: See Build Status on AppVeyor

Codecrumbs divides refactoring in a declaration phase, where you leave codecrumbs behind
and an application step, where you or some one else follows the codecrumbs.

Example
-------

Simple example which renames one argument:

.. code:
    class Example:
        # old code ...
        # def method(self,v):
        #    print(v)

        @renamed_argument("v","value")
        def method(self,value):
            print(value)

    # some where else
    e=Example()

    e.method(v=5)

and apply the refactoring later

.. code:
    codecrumbs example.py
    # or
    pytest --codecrumbs-fix test_example.py

You can use `codecrumbs` instead of `python` to execute your code, or `pytest`_ to run your tests and apply the renamings automatically.

This can be used to fix the small things in your library you wanted to fix but never did,
because you wanted to stay backwards compatible or didn't wanted you user to fix 1000 renamings in their code.

Features
--------
with codecrumbs you can fix:
 * method / attribute names
 * rename named arguments of functions


Installation
------------

You can install "codecrumbs" via `pip`_ from `PyPI`_::

    $ pip install codecrumbs


Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-codecrumbs" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

.. _`Cookiecutter`: https://github.com/audreyr/cookiecutter
.. _`@hackebrot`: https://github.com/hackebrot
.. _`MIT`: http://opensource.org/licenses/MIT
.. _`BSD-3`: http://opensource.org/licenses/BSD-3-Clause
.. _`GNU GPL v3.0`: http://www.gnu.org/licenses/gpl-3.0.txt
.. _`Apache Software License 2.0`: http://www.apache.org/licenses/LICENSE-2.0
.. _`cookiecutter-pytest-plugin`: https://github.com/pytest-dev/cookiecutter-pytest-plugin
.. _`file an issue`: https://github.com/15r10nk/pytest-codecrumbs/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
