
# Introduction

Codecrumbs is a Python library (and pytest plugin) for source code refactoring across library boundaries.
It allows you to change the API of your library and to propagate this changes to every one who uses your library.

The invocation of deprecated API is detected at runtime and fixes can be generated.

This removes the pain of fixing upstream API changes manually.
The developer can now rename all the functions who need an better name without to fear that he drives his users crazy because they have to fix thousands of lines of code.
This saves valuable developer time.
However it is not 100% save and the refactoring may break your code (see [Limitations](#Limitations))


!!! note
    codecrumbs is currently limited to refactor attribute names and function argument names,
    but more options are planned.

## Requirements

codecrumbs requires Python *3.8*, *3.9* or *3.10*.

## Limitations

* expressions inside assert statements can not be fixed if pytest is used.
* expressions inside identical code blocks in the same line can not be fixed.

```python
lambdas = (lambda a: x, lambda a: x)
lists = all(len(e) > 5 for e in l1) and all(len(e) > 5 for e in l2)
```

I'm currently working on the migration to [executing](https://github.com/alexmojaki/executing).
It will take some time, but I hope to remove some of these limitations.

## Installation

Install or add codecrumbs as a dependency to your library::

```bash
pip install codecrumbs
```

This includes the pytest plugin which allows the user of your library to
fix the deprecated API calls without to install additional libraries.


## Quick Start

Annotate your refactoring first

```python
import codecrumbs


class Example:
    # cfgmod was renamed to config_module
    cfgmod = codecrumbs.renamed_attribute("config_module")

    def config_module(self, some_arg):
        print("some code", some_arg)
```


Calling `cfgmod` now triggers an `DeprecationWarning` and redirects to `config_module`


You can fix code which is using `cfgmod` in two ways:

* If you have tests for your code which calling the deprecated API:

    ```bash
    pytest --codecrumbs-fix test_of_your_code.py
    ```

* if you have a small script without tests.

    ```bash
    codecrumbs run your_script.python
    ```
