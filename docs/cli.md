# Command line interfaces



codecrumbs provides several command line interfaces to fix your code.
It is recommended to use the pytest-plugin, but you can also use `codecrumbs run` if you want to fix a stand alone script

!!! info
    Codecrumbs fixes only files which are versioned by git and have no unstaged changes.



## pytest
codecrumbs comes with pytest support out of the box.

* `pytest --codecrumbs-fix` fixes all deprecations which where used during the test.
  The files have to be versioned with git and can not have unstaged changes.




## breadcrumbs run [script] [...arguments]

`codecrumbs run` can be used to run and fix a stand alone script.
Just use `codecrumbs run` instead of `python` to run your script and codecrumbs will fix all  deprecations which where used.
