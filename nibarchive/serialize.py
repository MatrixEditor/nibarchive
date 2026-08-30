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

import struct

from nibarchive import (
    NIBArchive,
    NIBObject,
    NIBKey,
    NIBValue,
    NIBValueType,
    ClassName,
)

__all__ = [
    "hexint",
    "NIBArchiveSerializer",
]

MAGIC_BYTES = b"NIBArchive"

_STRUCT_FORMATS = {
    NIBValueType.INT8:       "B",
    NIBValueType.INT16:      "<h",
    NIBValueType.INT32:      "<i",
    NIBValueType.INT64:      "<q",
    NIBValueType.FLOAT:      "<f",
    NIBValueType.DOUBLE:     "<d",
    NIBValueType.OBJECT_REF: "<i",
}


def hexint(value: int) -> bytes:
    """Encode an integer as a NIB-style varint.

    High bit (0x80) marks the **last** byte (opposite of protobuf convention).
    """
    if value < 0:
        raise ValueError(f"Cannot encode negative varint: {value}")
    buf = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            buf.append(byte | 0x80)
            break
        buf.append(byte)
    return bytes(buf)


class NIBArchiveSerializer:
    """Serializer for NIB archives — mirrors :class:`NIBArchiveParser`."""

    def serialize(self, archive: NIBArchive) -> bytes:
        """Serialize a :class:`NIBArchive` to its binary representation.

        :param archive: The archive to serialize.
        :type archive: NIBArchive
        :return: Binary NIB archive data.
        :rtype: bytes
        """
        sections = [
            self.serialize_objects(archive.objects),
            self.serialize_keys(archive.keys),
            self.serialize_values(archive.values),
            self.serialize_class_names(archive.class_names),
        ]
        counts = [len(archive.objects), len(archive.keys),
                  len(archive.values), len(archive.class_names)]

        header_size = len(MAGIC_BYTES) + 40
        offsets = [header_size]
        for section in sections[:-1]:
            offsets.append(offsets[-1] + len(section))

        header_fields = [archive.header.unknown_1, archive.header.unknown_2]
        for count, offset in zip(counts, offsets):
            header_fields += [count, offset]

        header = struct.pack("<iiiiiiiiii", *header_fields)
        return MAGIC_BYTES + header + b"".join(sections)

    def serialize_objects(self, objects: list[NIBObject]) -> bytes:
        return b"".join(
            hexint(obj.class_name_index)
            + hexint(obj.values_index)
            + hexint(obj.value_count)
            for obj in objects
        )

    def serialize_keys(self, keys: list[NIBKey]) -> bytes:
        parts = []
        for key in keys:
            name_bytes = key.name.encode("utf-8")
            parts.append(hexint(len(name_bytes)) + name_bytes)
        return b"".join(parts)

    def serialize_values(self, values: list[NIBValue]) -> bytes:
        return b"".join(
            hexint(v.key_index) + self._serialize_value(v)
            for v in values
        )

    def serialize_class_names(self, class_names: list[ClassName]) -> bytes:
        parts = []
        for cn in class_names:
            name_bytes = cn.name.encode("utf-8") + b"\x00"
            extras_bytes = struct.pack(f"<{cn.extras_count}i", *cn.extras) if cn.extras_count else b""
            parts.append(
                hexint(len(name_bytes))
                + hexint(cn.extras_count)
                + extras_bytes
                + name_bytes
            )
        return b"".join(parts)

    def _serialize_value(self, value: NIBValue) -> bytes:
        vt = value.type

        if vt == NIBValueType.NIBARCHIVE:
            inner = self.serialize(value.data)
            return bytes([NIBValueType.DATA.value]) + hexint(len(inner)) + inner

        if vt in (NIBValueType.BOOL_TRUE, NIBValueType.BOOL_FALSE, NIBValueType.NIL):
            return bytes([vt.value])

        if vt in _STRUCT_FORMATS:
            return bytes([vt.value]) + struct.pack(_STRUCT_FORMATS[vt], value.data)

        if vt == NIBValueType.DATA:
            data_bytes = self._serialize_data(value.data)
            return bytes([vt.value]) + hexint(len(data_bytes)) + data_bytes

        raise ValueError(f"Unknown value type: {vt}")

    def _serialize_data(self, data) -> bytes:
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        if isinstance(data, list) and len(data) in (2, 4):
            return b"\x07" + struct.pack(f"<{len(data)}d", *data)
        raise ValueError(f"Cannot encode DATA payload: {type(data)}")
