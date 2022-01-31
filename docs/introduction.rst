
Introduction
============

Breadcrumes is a Python library (and pytest plugin) for source code refactoring.
It allows you to change the API of your library and to propagate this changes to every one who uses your libaray.

The invocation of deprecated API is detected at runtime and fixes can be generated.

This removes the pain of fixing upstream API changes manually.
The developer can now rename all the functions who need an better name without to fear that he drives his users crazy because they have to fix thousands of lines of code.
This saves valuable developer time.
However it is not 100% save and the refactorings may break your code (see `known problems`)


.. note::
   breadcrumbs is currently limited to refactor attribute names and function argument names,
   but more options are planned.

Requirements
------------

breadcrumbs requires Python 3.8 and above.

It has no (and will never have) dependencies to other libraries, to allow it to be used by any library without cyclic dependencies.

Installation
------------

Install or add breadcrumbs as a dependency to your library::

   pip install breadcrumbs

This includes the pytest plugin which allows the user of your library to
fix the deprecated API calls without to install additional libraries.


Quick Start
-----------

Annotate your refactorings first

.. code::

    import breadcrumbs


    class Example:
        # cfgmod was renamed to config_module
        cfgmod = breadcrumbs.renamed("config_module")

        def config_module(self, some_arg):
            print("some code", some_arg)

Calling `cfgmod` now triggers an `DeprecationWarning` and redirects to `config_module`

The code can be fixed by with::

    pytest --breadcrumbs-fix test_of_your_code.py

if you have tests for your code which calling the deprecated API or::

    breadcrumbs run your_script.py

if you have a small script without tests.
