
References
==========

Rename class attributes
-----------------------


.. automodule:: codecrumbs
    :members: renamed_attribute


The redirection to the new attribute is documented in the docstring, if the target is also documented.

Example:

.. literalinclude:: ../examples/rename_attribute.py

The generated documentation looks like follow:

.. automodule:: examples.rename_attribute
    :members: Test





Rename function arguments
-------------------------


.. autodecorator:: codecrumbs.argument_renamed

   .. automethod:: codecrumbs.argument_renamed.since


The changed signature is added to the docstring, if the function is documented.

Example:

.. literalinclude:: ../examples/rename_argument.py

And the generated documentation looks like follow:

.. automodule:: examples.rename_argument
    :members: function, undocumented_function
