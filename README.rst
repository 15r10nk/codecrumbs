==================
pytest-breadcrumes
==================

.. image:: https://img.shields.io/pypi/v/pytest-breadcrumes.svg
    :target: https://pypi.org/project/pytest-breadcrumes
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pytest-breadcrumes.svg
    :target: https://pypi.org/project/pytest-breadcrumes
    :alt: Python versions

.. image:: https://ci.appveyor.com/api/projects/status/github/15r10nk/pytest-breadcrumes?branch=master
    :target: https://ci.appveyor.com/project/15r10nk/pytest-breadcrumes/branch/master
    :alt: See Build Status on AppVeyor

Breadcrumes devides refactorings in a declaration phase, where you leave breadcrumes behind
and an application step, where you or some one else follows the breadcrumes.

simple example which renames one method:

.. code:
    class Example:
        # delete old code ...
        # def old_method(self):
        #    pass
        
        old_method= breadcrumes.renamed("new_method")

        def new_method(self):
            print("new stuff ...")
    
    # some where else
    e=Example()

    e.old_method()

and apply the refactorings later

.. code:
    breadcrumes example.py
    # or 
    pytest --breadcrumes-fix test_example.py

You can use breadcrumes instead of python to execute your code, or pytest to run your tests and apply the renamings automatically.

This can be used to fix the small things in your library you wanted to fix but never did,
 because you wanted to stay backwards compatible or didn't wanted you user to fix 1000 renamings in their code.

with breadcrumes you can fix.
 * method / attribute names 
 * rename named arguments of functions

----

This `pytest`_ plugin was generated with `Cookiecutter`_ along with `@hackebrot`_'s `cookiecutter-pytest-plugin`_ template.


Features
--------

* TODO


Requirements
------------

* TODO


Installation
------------

You can install "pytest-breadcrumes" via `pip`_ from `PyPI`_::

    $ pip install pytest-breadcrumes


Usage
-----

* TODO

Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-breadcrumes" is free and open source software


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
.. _`file an issue`: https://github.com/15r10nk/pytest-breadcrumes/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
