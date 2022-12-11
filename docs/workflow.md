# Workflow

The general idea behind codecrumbs is that you annotate your API changes in your code base.
This allows tooling to follow your annotations and fix the code which is using your API.

Every deprecation by codecrumbs is done in a backward compatible manner.
The applied refactoring does not change the behavior of your program.

## Step 1: Refactor your code

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
    old = codecrumbs.attribute_renamed("new")

    def new(self):
        print("method called")
```

Multiple of such API changes can be specified until you want to release a new version of your library.

## Step 2: add since attribute for the next release

Every refactoring annotation has a `since` argument, which specifies the version when the deprecation occurred.
This is used to generate docstrings. The refactoring logic works fine without this attribute.

This attribute can not be defined when the deprecation is added to the codebase, because it is not known if the next version will be a major, minor or patch release.
Therefor it has to be defined during the release process.

The example might then look like this:
```python
class Example:
    old = codecrumbs.attribute_renamed("new", since="2.1.0")

    def new(self):
        print("method called")
```

!!! note "planned feature: codecrumbs add-since "
    `codecrumbs add-since [version] [...files]` should allow to add the `since=...` attribute to every annotation which is missing it.
    This can be used to set the correct version when a new release is created.
    It has to be done by hand for now.

## Step 3: give everyone time to fix their code

The fixes can be applied at a later point in time at a different place by a different developer.

Which means that you can change the API of your library and the users of your library can apply the changes to their code base.
This can be done with `pytest --codecrumbs-fix` or `codecrumbs run`.
`codecrumbs` get mentioned in the deprecation warnings, which makes it likely that the user of your library will use it to fix his code.
If `pytest` is used `--codecrumbs-fix` will work out of the box, because the codecrumbs pytest plugin is part of the codecrumbs package.

## Step 4: time to die

Every deprecated API has to be removed sometime.

!!! warning
    This is an API breaking change and should only be done for major releases.

Knowing when you can make a deprecation permanent is difficult:
* are there users still using versions of your library before the deprecation occurred?
* are your user apply the code changes?

You should make clear in your documentation that you are using codecrumbs and under which conditions you make API breaking changes.

The example might then look like this:
```python
class Example:
    def new(self):
        print("method called")
```

!!! question "why not declare the version in which a deprecation will be removed?"
    This might seem like a god idea, but there are problems:

    * If the user know that something gets removed in X years/month, he might thing that there is still plenty time, which might actually delay code changes.
    * Specifying the version when a feature will be removed does not give much information, because the user don't know when this version will be released.
    * There might be good reasons that this version/date will change. Why specifying it then in the first place?

    Knowing that something might be removed with the next major release should be enough.

!!! note "planned feature: codecrumbs purge"
    `codecrumbs purge [version] [...files]` removes old deprecations from the codebase.

    It might change some source code/documentation if necessary.
    It will become useful later when there are a lot of deprecated APIs, but there is no urgency to implement it now.
