# NIBArchive-Parser

[![python](https://img.shields.io/badge/python-3.9+-blue.svg?logo=python&labelColor=grey)](https://www.python.org/downloads/)
![Codestyle](https://img.shields.io:/static/v1?label=Codestyle&message=black&color=black)
![License](https://img.shields.io:/static/v1?label=License&message=GNU+GPLv3&color=blue)
[![PyPI](https://img.shields.io/pypi/v/nibarchive)](https://pypi.org/project/nibarchive/)
[![Build and Deploy Sphinx Documentation](https://github.com/MatrixEditor/nibarchive/actions/workflows/sphinx.yml/badge.svg)](https://github.com/MatrixEditor/nibarchive/actions/workflows/sphinx.yml)


Parser implementation of NeXTSTEP Interface Builder (NIB) files in Python3.

## NIBArchive

The `.nib` file is primarily associated with Interface Builder, a graphical user interface (GUI) design tool used to
create the visual layout of user interfaces for applications. The purpose of a NIB file is to store the information
about the user interface elements, their properties, and their relationships with each other.

The file format has been described in detail in the [nibsqueeze](https://github.com/matsmattsson/nibsqueeze) repository.

## Installation

Just use pip:
```console
$ pip install nibarchive
```

and to build the docs you need `make` to be installed:
```console
$ pip install -r docs/requirements.txt
$ cd docs && make html
```

## Usage

The python package provided with this repository supports parsing NIB archives into an object model. More detailed information about the implementation and fields of each class, please refer to the documentation available on [Github-Pages](https://matrixeditor.github.io/nibarchive/).

### Parsing NIB files

As the `NIBArchiveParser` only accepts `IOBase` objects, we can either parse opened files directly or use `io.BytesIO` for a reader on existing byte structures.

```python
from nibarchive import NIBArchiveParser

# Create the parser instance
parser = NIBArchiveParser(verify=True)

# Parse an input file from scratch
with open("path/to/file.nib", "rb") as fp:
    archive: NIBArchive = parser.parse(fp)
```

Or with `BytesIO`:

```python
from io import BytesIO

# assue the file content is stored here
buffer = bytes(...)
parser = NIBArchiveParser()

# parse using BytesIO wrapper class
archive = parser.parse(BytesIO(buffer))
```

### Working with NIBArchive objects

At this point we can use the returned object to inspect the files content. *But*, the parser does **not** organize the returned archive, so we have to do it afterwards:

```python
# Get an object
obj: NIBObject = archive.objects[0]

# Get the object's class name
class_name: ClassName = archive.get_class_name(obj)

# Retrieve the object's values
values: list[NIBValue] = archive.get_object_values(obj)
for value in values:
    # Each value is mapped to a NIBKey
    key: NIBKey = archive.get_value_key(value)
```

There is a convienient method named `get_object_items` which automatically maps all values of an object to their corresponding keys. The return value is of type `dict[NIBKey, NIBValue]`

## License

Distributed under the GNU GPLv3. See `LICENSE` for more information.

[^1]: https://github.com/matsmattsson/nibsqueeze/blob/master/NibArchive.md
