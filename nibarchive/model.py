# Copyright (C) 2023 MatrixEditor

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import annotations

import enum

from typing import Any
from dataclasses import dataclass, field

__all__ = [
    "NIBArchiveHeader",
    "ClassName",
    "NIBKey",
    "NIBValueType",
    "NIBValue",
    "NIBObject",
    "NIBArchive",
]


@dataclass
class NIBArchiveHeader:
    """Represents the header of a NIB archive.

    The header contains information about the archive, such as the number of objects,
    keys, values, and class names present in the archive.

    :param unknown_1: Unknown value 1.
    :type unknown_1: int
    :param unknown_2: Unknown value 2.
    :type unknown_2: int
    :param object_count: Number of objects in the archive.
    :type object_count: int
    :param offset_objects: Offset to the objects in the archive.
    :type offset_objects: int
    :param key_count: Number of keys in the archive.
    :type key_count: int
    :param offset_keys: Offset to the keys in the archive.
    :type offset_keys: int
    :param value_count: Number of values in the archive.
    :type value_count: int
    :param offset_values: Offset to the values in the archive.
    :type offset_values: int
    :param class_name_count: Number of class names in the archive.
    :type class_name_count: int
    :param offset_class_names: Offset to the class names in the archive.
    :type offset_class_names: int
    """
    unknown_1: int
    unknown_2: int
    object_count: int
    offset_objects: int
    key_count: int
    offset_keys: int
    value_count: int
    offset_values: int
    class_name_count: int
    offset_class_names: int


@dataclass
class ClassName:
    """Represents a class name in a NIB archive.

    Class names are used to identify the class type of objects in the archive.

    :param length: Length of the class name (varint).
    :type length: int
    :param extras_count: Number of extra integers following the name (varint).
    :type extras_count: int
    :param name: Name of the class.
    :type name: str
    :param extras: Extra integers associated with the class (default: empty list).
    :type extras: list[int]
    """
    length: int  # varint
    extras_count: int  # varint
    name: str  # name definition comes after extra integers
    extras: list[int] = field(default_factory=list)


@dataclass
class NIBKey:
    """Represents a key in a NIB archive.

    Keys are used to identify the values associated with objects.

    :param length: Length of the key (varint).
    :type length: int
    :param name: Name of the key.
    :type name: str
    """
    length: int  # varint
    name: str

    def __hash__(self) -> int:
        return hash(self.name)


class NIBValueType(enum.IntEnum):
    """Enum representing the possible value types in a NIB archive.

    The value types define the type of data stored in a :class:`NIBValue` object.

    :param INT8: 8-bit integer.
    :param INT16: 16-bit integer.
    :param INT32: 32-bit integer.
    :param INT64: 64-bit integer.
    :param BOOL_TRUE: Boolean value true.
    :param BOOL_FALSE: Boolean value false.
    :param FLOAT: Single-precision floating-point number.
    :param DOUBLE: Double-precision floating-point number.
    :param DATA: Data object.
    :param NIL: Nil value.
    :param OBJECT_REF: Object reference.
    """
    NIBARCHIVE = -1
    INT8 = 0
    INT16 = 1
    INT32 = 2
    INT64 = 3
    BOOL_TRUE = 4
    BOOL_FALSE = 5
    FLOAT = 6
    DOUBLE = 7
    DATA = 8
    NIL = 9
    OBJECT_REF = 10

    @staticmethod
    def from_byte(value: int) -> "NIBValueType":
        """
        Get the NIBValueType enum value from a byte representation.

        :param value: Byte value representing the NIBValueType.
        :type value: int
        :return: Corresponding NIBValueType enum value.
        :rtype: NIBValueType
        :raises ValueError: If the byte value does not match any NIBValueType.
        """
        for value_type in NIBValueType:
            if value == value_type.value:
                return value_type

        raise ValueError(f"Unknown value type: {value:#x}")


@dataclass
class NIBValue:
    """Represents a value in a NIB archive.

    Values are associated with keys and hold data for objects.

    :param key_index: Index of the associated :class:`NIBKey` (varint).
    :type key_index: int
    :param type: Type of the value.
    :type type: :class`NIBValueType`
    :param data: Data associated with the value (default: None).
    :type data: Any
    """
    key_index: int  # varint
    type: NIBValueType
    data: Any = None


@dataclass
class NIBObject:
    """Represents an object in a NIB archive.

    Objects are instances of classes defined in the archive.

    :param class_name_index: Index of the associated :class:`ClassName` (varint).
    :type class_name_index: int
    :param values_index: Index of the first associated :class:`NIBValue` (varint).
    :type values_index: int
    :param value_count: Number of associated values (varint).
    :type value_count: int
    """
    class_name_index: int  # varint
    values_index: int  # varint
    value_count: int  # varint


@dataclass
class NIBArchive:
    """A simple NIB archive dataclass.

    :param header: Header of the NIB archive.
    :type header: :class:`NIBArchiveHeader`
    :param objects: List of NIBObject instances (default: empty list).
    :type objects: list[:class:`NIBObject`]
    :param keys: List of NIBKey instances (default: empty list).
    :type keys: list[:class:`NIBKey`]
    :param values: List of NIBValue instances (default: empty list).
    :type values: list[:class:`NIBValue`]
    :param class_names: List of ClassName instances (default: empty list).
    :type class_names: list[:class:`ClassName`]
    """
    header: NIBArchiveHeader
    objects: list[NIBObject] = field(default_factory=list)
    keys: list[NIBKey] = field(default_factory=list)
    values: list[NIBValue] = field(default_factory=list)
    class_names: list[ClassName] = field(default_factory=list)

    def get_object_values(self, obj: NIBObject) -> list[NIBValue]:
        """
        Get the list of NIBValues associated with a given NIBObject.

        :param obj: The NIBObject.
        :type obj: NIBObject
        :return: The list of NIBValues associated with the object.
        :rtype: List[NIBValue]
        """
        return self.values[obj.values_index:obj.values_index+obj.value_count]

    def get_object_items(self, obj: NIBObject) -> dict[NIBKey, NIBValue]:
        """
        Get a dictionary of NIBKey-NIBValue pairs associated with a given NIBObject.

        :param obj: The NIBObject.
        :type obj: NIBObject
        :return: The dictionary of NIBKey-NIBValue pairs associated with the object.
        :rtype: Dict[NIBKey, NIBValue]
        """
        items = {}
        for value in self.get_object_values(obj):
            items[self.get_value_key(value)] = value
        return items

    def get_value_key(self, value: NIBValue) -> NIBKey:
        """
        Get the NIBKey associated with a given NIBValue.

        :param value: The NIBValue.
        :type value: NIBValue
        :return: The associated NIBKey.
        :rtype: NIBKey
        """
        return self.keys[value.key_index]

    def get_class_name(self, obj: NIBObject) -> ClassName:
        """
        Get the ClassName associated with a given NIBObject.

        :param obj: The NIBObject.
        :type obj: NIBObject
        :return: The associated ClassName.
        :rtype: ClassName
        """
        return self.class_names[obj.class_name_index]
