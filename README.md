[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# codecrumbs

Codecrumbs is a Python library (and pytest plugin) for source code refactoring across library boundaries.
It allows you to change the API of your library and to propagate this changes to every one who uses your library.


More can be found in the [documentation](https://15r10nk.github.io/codecrumbs/introduction/).

## Example

Simple example which renames one argument:

``` python
class Example:
    # old code ...
    # def method(self,v):
    #    print(v)

    @renamed_argument("v", "value")
    def method(self, value):
        print(value)


# some where else
e = Example()

e.method(v=5)
```

and apply the refactoring later

``` bash
# if you have a standalone script
codecrumbs example.py
# or if you have tests
pytest --codecrumbs-fix test_example.py
```

which will rename the argument

```python
e.method(value=5)
```

You can use `codecrumbs` instead of `python` to execute your code, or `pytest` to run your tests and apply the renamings automatically.

This can be used to fix the small things in your library you wanted to fix but never did,
because you wanted to stay backwards compatible or didn't wanted you user to fix 1000 renamings in their code.

## Installation

You can install `codecrumbs` via `pip` from [PyPI](https://pypi.org/project):

`pip install codecrumbs`

The pytest support comes out of the box and everyone who depends on your library can use `pytest --codecrumbs-fix` to apply the changes you declared.

## Features

With codecrumbs you can fix:
 * method / attribute names
 * rename named arguments of functions


## Contributing
Contributions are very welcome. Tests can be run with [tox](https://tox.readthedocs.io/en/latest/), please ensure
the coverage at least stays the same before you submit a pull request.

## Issues

If you encounter any problems, please [file an issue](https://github.com/15r10nk/pytest-codecrumbs/issues) along with a detailed description.

## License

Distributed under the terms of the [MIT](http://opensource.org/licenses/MIT) license, "pytest-codecrumbs" is free and open source software
