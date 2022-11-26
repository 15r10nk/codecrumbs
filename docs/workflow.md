
# Workflow


The general idea behind codecrumbs is that you annotate your API changes in your code base.
This allows tooling to follow your annotations and fix the code which is using your API.


The annotation is done in a backward compatible manner.
This ensures that the applied refactoring does not change the behavior of your program.

A trivial example would be the renaming of a method.
Lets say you have the following class and want to change the name of the old method to new.

```python
class Example:
    def old(self):
        print("method called")
```

You can do this by changing the name and add an annotation which redirects the calls to the new method.


```python
class Example:
    old = codecrumbs.renamed_attribute("new")

    def new(self):
        print("method called")
```

Multiple of such API changes can be specified.
The fixes can be applied at a later point in time at a different place by a different developer.

Which means that you can change the API of your library and the users of your library can apply the changes to their codebases.
