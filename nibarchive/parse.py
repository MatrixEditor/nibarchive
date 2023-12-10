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

# For more information about the file format, visit:
# https://github.com/matsmattsson/nibsqueeze/blob/master/NibArchive.md
from __future__ import annotations

import struct
import io

from nibarchive import (
    NIBArchive,
    NIBArchiveHeader,
    NIBObject,
    NIBKey,
    NIBValue,
    NIBValueType,
    ClassName
)

MAGIC_BYTES = b"NIBArchive"
"""Magic bytes at the start of all NIB archives."""

__all__ = [
    "NIBFormatError",
    "is_nib",
    "varint",
    "NIBArchiveParser",
    "MAGIC_BYTES",
]

class NIBFormatError(Exception):
    """Exception raised for errors related to NIB format.

    This exception is raised when there is an error or inconsistency in the parsed NIB archive.
    """


def is_nib(fp) -> bool:
    """
    Check if the given file or byte array represents a NIB archive.

    This function reads the first 10 bytes of the file or byte array and compares it
    with the expected magic bytes to determine if it is a NIB archive.

    :param fp: File or byte array to check.
    :type fp: Union[io.IOBase, bytes, bytearray]
    :return: True if the file or byte array is a NIB archive, False otherwise.
    :rtype: bool
    :raises TypeError: If the input is not a file object or byte array.
    :raises ValueError: If the length of the input is not 10 bytes.
    """
    if isinstance(fp, io.IOBase):
        fp.seek(0)
        data = fp.read(10)  # magic has 10 bytes
    elif isinstance(fp, (bytes, bytearray)):
        data = fp
    else:
        raise TypeError(f"Invalid input type: (IOBase or bytes) - got {type(fp)}")

    if len(data) != 10:
        raise ValueError(f"Expected 10-byte array - got {len(data)} bytes")

    return MAGIC_BYTES == data


def varint(buf: bytes | io.IOBase, offset: int = 0) -> tuple[int, int]:
    """Decode a variable-length integer (varint) from a byte buffer.

    This function decodes a varint from the given byte buffer and returns the decoded
    integer value. A variable integer can consume up to two bytes and is compressed into
    the first 7 bits only.

    :param buf: Byte buffer containing the varint.
    :type buf: bytes
    :param offset: Offset in the byte buffer to start decoding (default: 0).
    :type offset: int
    :return: The decoded integer value and its byte count
    :rtype: int
    """
    result = 0
    shift = 0
    count = 0
    while True:
        count += 1
        if isinstance(buf, io.IOBase):
            current_byte, = buf.read(1)
        else:
            current_byte, = buf[offset:offset+1]

        result |= (current_byte & 0x7F) << shift
        shift += 7
        if current_byte & 128:
            break

    return result, count



class NIBArchiveParser:
    """A simple parser for NIB archives.

    :param verify: Flag indicating whether to perform verification checks during parsing (default: True).
    :type verify: bool
    """

    def __init__(self, verify: bool = True) -> None:
        """
        Initialize the NIBArchiveParser.

        :param verify: Flag indicating whether to perform verification checks during parsing.
        :type verify: bool
        """
        self.archive: NIBArchive = None
        self.verify = verify

    def parse(self, fp: io.IOBase) -> NIBArchive:
        """Parses the NIB archive.

        This method reads the NIB archive from the given file object (fp) and
        constructs a NIBArchive object representing the parsed contents.

        :param fp: File object containing the NIB archive.
        :type fp: io.IOBase
        :return: The parsed NIBArchive object.
        :rtype: NIBArchive
        :raises TypeError: If the input is not a file object.
        :raises NIBFormatError: If a verification check fails.
        """
        if not fp or not isinstance(fp, io.IOBase):
            raise TypeError(f"Invalid input type: {type(fp)} is not an instance of IOBase")

        offset = self.parse_header(fp)
        header = self.archive.header
        if offset != header.offset_objects and self.verify:
            raise NIBFormatError(f"Expected object offset at {offset} - got {header.offset_objects}")

        offset = self.parse_objects(fp, offset)
        if offset != header.offset_keys and self.verify:
            raise NIBFormatError(f"Expected keys offset at {offset} - got {header.offset_keys}")

        offset = self.parse_keys(fp, offset)
        if offset != header.offset_values and self.verify:
            raise NIBFormatError(f"Expected values offset at {offset} - got {header.offset_values}")

        offset = self.parse_values(fp, offset)
        if offset != header.offset_class_names and self.verify:
            raise NIBFormatError(f"Expected class names' offset at {offset} - got {header.offset_class_names}")

        self.parse_class_names(fp, offset)
        return self.archive


    def parse_header(self, fp: io.IOBase) -> int:
        if not is_nib(fp):
            raise NIBFormatError("Expected b'NIBArchive' magic at byte 0")

        header = NIBArchiveHeader(*struct.unpack("<iiiiiiiiii", fp.read(40)))
        self.archive = NIBArchive(header)
        return len(MAGIC_BYTES) + 40

    def parse_objects(self, fp: io.IOBase, offset: int) -> int:
        for _ in range(self.archive.header.object_count):
            cni, byte_cnt = varint(fp)
            offset += byte_cnt
            vi, byte_cnt = varint(fp)
            offset += byte_cnt
            vc, byte_cnt = varint(fp)
            offset += byte_cnt

            obj = NIBObject(cni, vi, vc)
            self.archive.objects.append(obj)
        return offset

    def parse_keys(self, fp: io.IOBase, offset: int) -> int:
        for _ in range(self.archive.header.key_count):
            length, cnt = varint(fp)
            offset += cnt + length
            key = NIBKey(length, fp.read(length).decode("utf-8"))
            self.archive.keys.append(key)
        return offset

    def parse_class_names(self, fp: io.IOBase, offset: int) -> int:
        for _ in range(self.archive.header.class_name_count):
            length, count = varint(fp)
            offset += length + count
            extras_count, bytes_count = varint(fp)
            offset += 4*extras_count + bytes_count

            extras = struct.unpack(
                "<%s" % "i"*extras_count, fp.read(4*extras_count))
            # Name is \0 terminated, so we have to remove the trailing \0
            name = fp.read(length)
            class_name = ClassName(
                length, extras_count, extras=list(extras), name=name[:-1].decode("utf-8")
            )
            self.archive.class_names.append(class_name)
        return offset

    def parse_values(self, fp: io.IOBase, offset: int) -> int:
        for _ in range(self.archive.header.value_count):
            key_index, bytes_count = varint(fp)
            offset += bytes_count + 1
            value_type = NIBValueType.from_byte(*fp.read(1))

            value = NIBValue(key_index, value_type)
            attr_name = f"_parse_{value_type.name.lower()}"
            if value_type != NIBValueType.NIL:
                if hasattr(self, attr_name):
                    offset = getattr(self, attr_name)(fp, value, offset)
                else:
                    raise ValueError(f"Unknown data type: {value_type}")
            self.archive.values.append(value)
        return offset

    def _parse_int8(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data, = fp.read(1)
        return offset + 1

    def _parse_int16(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data, = struct.unpack("<h", fp.read(2))
        return offset + 2

    def _parse_int32(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data, = struct.unpack("<i", fp.read(4))
        return offset + 4

    def _parse_int64(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data, = struct.unpack("<q", fp.read(8))
        return offset + 8

    def _parse_bool_true(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data = True
        return offset

    def _parse_bool_false(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data = False
        return offset

    def _parse_float(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data, = struct.unpack("<f", fp.read(4))
        return offset + 4

    def _parse_double(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        value.data, = struct.unpack("<d", fp.read(8))
        return offset + 8

    def _parse_object_ref(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        return self._parse_int32(fp, value, offset)

    def _parse_data(self, fp: io.IOBase, value: NIBValue, offset: int) -> int:
        length, bytes_count = varint(fp)
        value.data = fp.read(length)

        if length > 10 and is_nib(io.BytesIO(value.data)):
            parser = NIBArchiveParser(verify=self.verify)
            value.data = parser.parse(io.BytesIO(value.data))
            value.type = NIBValueType.NIBARCHIVE

        elif length and value.data[0] == 0x07:
            if length == 17:
                value.data = list(struct.unpack("<dd", value.data[1:]))
            elif length == 33:
                value.data = list(struct.unpack("<dddd", value.data[1:]))

        return offset + bytes_count + length

