.. NIBArchive Parser documentation master file, created by
   sphinx-quickstart on Mon Jul 10 20:45:39 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to NIBArchive Parser's documentation!
=============================================

This small python package provides a parser implementation of NeXTSTEP Interface Builder (NIB) files
in Python3.

.. toctree::
   :maxdepth: 1
   :caption: Documentation

   model
   parser


NIBArchive
==========

The ``.nib`` file is primarily associated with Interface Builder, a graphical user interface (GUI) design tool used to
create the visual layout of user interfaces for applications. The purpose of a NIB file is to store the information
about the user interface elements, their properties, and their relationships with each other.

The file format has been described in detail in the `nibsqueeze <https://github.com/matsmattsson/nibsqueeze>`_ repository.


Installation
============

.. code-block:: shell

   $ pip install nibarchive

Parsing NIB files
-----------------

As the ``NIBArchiveParser`` only accepts ``IOBase`` objects, we can either parse opened files directly or use ``io.BytesIO`` for a
reader on existing byte structures.

.. code-block:: python
   :linenos:

   from nibarchive import NIBArchiveParser

   # Create the parser instance
   parser = NIBArchiveParser(verify=True)

   # Parse an input file from scratch
   with open("path/to/file.nib", "rb") as fp:
      archive: NIBArchive = parser.parse(fp)

Or with ``BytesIO``:

.. code-block:: python
   :linenos:

   from io import BytesIO

   # assue the file content is stored here
   buffer = bytes(...)
   parser = NIBArchiveParser()

   # parse using BytesIO wrapper class
   archive = parser.parse(BytesIO(buffer))

Working with NIBArchive objects
-------------------------------

At this point we can use the returned object to inspect the files content. *But*, the parser does **not** organize the returned archive, so we have to do it afterwards:

.. code-block:: python
   :linenos:

   # Get an object
   obj: NIBObject = archive.objects[0]

   # Get the object's class name
   class_name: ClassName = archive.get_class_name(obj)

   # Retrieve the object's values
   values: list[NIBValue] = archive.get_object_values(obj)
   for value in values:
      # Each value is mapped to a NIBKey
      key: NIBKey = archive.get_value_key(value)

   # equal to steps above
   items: dict[NIBKey, NIBValue] = archive.get_object_items(obj)

There is a convienient method named `get_object_items` which automatically maps all values of an object to their corresponding keys. The return value is of type ``dict[NIBKey, NIBValue]``.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
