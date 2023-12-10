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
import os
import argparse
import pathlib
import json
import datetime
import dataclasses
from typing import Any

from nibarchive import NIBArchive, NIBObject, NIBValueType, NIBArchiveParser

# This class contains a simplistic implementation of a NIB-to-Swift converter. It
# is meant to be used to understand/inspect the structure of stored UI objects.
#
# The classes will take @property annotations first - they contain the NIBHeader's
# values. Next, the struct definition follows:
#   struct <file_name>: NIBArchive {
#       var <class_name> = @<index> // specifies a variable
#       let #<index> = <class_name>(
#           <key_name>: <class_name OR value>
#       )
#   }
class NIBObjectPrinter:
    def __init__(
        self,
        archive: NIBArchive,
        handler=print,
        indent: str = None,
        print_empty: bool = False,
        max_depth: int = 3,
    ) -> None:
        self.archive = archive
        self.indent = indent or " "
        self.print_empty = print_empty
        self.max_depth = max_depth
        self.handler = handler

    def print_object(self, obj: NIBObject) -> None:
        self._print(self.archive.objects.index(obj), obj, 3)

    def _print(
        self,
        index: int,
        obj: NIBObject,
        indent_level: int,
        inner=False,
        depth=0,
        key_def=None,
    ) -> None:
        items = self.archive.get_object_items(obj)
        class_name = self.archive.get_class_name(obj)
        if len(items) == 0 and self.print_empty:
            if inner:
                # The following line prints: __name__: __class__()@__index__
                self.handler(
                    self.indent * indent_level,
                    f"{key_def.name}: {class_name.name}()@{index},",
                )
            else:
                # Almost same as above: var __class__ = @__index__
                self.handler(
                    self.indent * indent_level, f"var {class_name.name} = @{index}"
                )

        if len(items) > 0:
            if not inner:
                # prints: let #__index__ = __class__(
                self.handler(
                    self.indent * indent_level, f"let #{index} = {class_name.name}("
                )
            else:
                # prints: __name__: __class__(
                self.handler(
                    self.indent * indent_level, f"{key_def.name}: {class_name.name}("
                )

            for key in items:
                value = items[key]
                if value.type == NIBValueType.OBJECT_REF:
                    ref = self.archive.objects[value.data]
                    ref_index = self.archive.objects.index(ref)
                    if index != ref_index and depth < self.max_depth:
                        # Print objects recursively
                        self._print(
                            ref_index,
                            ref,
                            indent_level + 4,
                            inner=True,
                            depth=depth + 1,
                            key_def=key,
                        )
                    else:
                        ref_name = self.archive.get_class_name(ref).name
                        # prints: __name__: [__class__@__index__]
                        self.handler(
                            self.indent * (indent_level + 4),
                            f"{key.name}: [{ref_name}@{ref_index}],",
                        )

                elif value.type == NIBValueType.NIBARCHIVE:
                    self.handler(
                        self.indent * (indent_level + 4), f"{key.name}: [NIBArchive: ...],"
                    )
                else:
                    # prints: __name__: __value__
                    self.handler(
                        self.indent * (indent_level + 4), f"{key.name}: {value.data},"
                    )

            self.handler(self.indent * indent_level, ")" + ("," if inner else ""))


class FileWriter:
    def __init__(self, fp) -> None:
        self.fp = fp

    def __call__(self, *args):
        self.fp.write(" ".join(list(args)) + "\n")


class JSONBytesEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, bytes):
            return o.decode("utf-8", errors="replace")
        return super().default(o)


def write_swift(src_name: str, out_path: str, archive: NIBArchive, print_empty) -> None:
    print(f"> Converting {src_name}.nib... ", end="")
    with open(str(out_path), "w", encoding="utf-8") as ofp:
        writer = FileWriter(ofp)
        printer = NIBObjectPrinter(archive, writer, print_empty=print_empty)
        for key, value in archive.header.__dict__.items():
            ofp.write(f"@property({key} = {value})\n")

        ofp.write(f"struct {src_name}: NIBArchive {{\n")
        for obj in archive.objects:
            printer.print_object(obj)
        ofp.write("}\n")
    print("Ok")


def dump_swift(args: dict):
    files = args["path"]
    parser = NIBArchiveParser(verify=True)

    if len(files) == 1 and not os.path.isdir(files[0]):
        output = pathlib.Path(args.get("output") or ".")
        if output.is_dir():
            output = output / f"nibarchive-{datetime.datetime.now()}.swift"

        with open(files[0], "rb") as fp:
            archive = parser.parse(fp)
        write_swift(pathlib.Path(files[0]).stem, output, archive, args["print_empty"])
    else:
        for file_path in map(pathlib.Path, files):
            if not file_path.is_dir():
                output = file_path.parent / f"{file_path.stem}.swift"
                with open(str(file_path), "rb") as fp:
                    archive = parser.parse(fp)
                write_swift(file_path.stem, output, archive, args["print_empty"])
            else:
                for nib_file in (
                    file_path.glob("*.nib")
                    if not args["recurse"]
                    else file_path.rglob("*.nib")
                ):
                    if nib_file.is_dir():
                        continue

                    output = nib_file.parent / f"{nib_file.stem}.swift"
                    with open(str(nib_file), "rb") as fp:
                        archive = parser.parse(fp)
                    write_swift(nib_file.stem, output, archive, args["print_empty"])


def dump_json(args: dict):
    files = args["path"]
    parser = NIBArchiveParser(verify=True)

    if len(files) == 1 and not os.path.isdir(files[0]):
        output = pathlib.Path(args.get("output") or ".")
        if output.is_dir():
            output = output / f"nibarchive-{datetime.datetime.now()}.swift"

        with open(files[0], "rb") as fp:
            archive = parser.parse(fp)
        with open(str(output), "w", encoding="utf-8") as ofp:
            json.dump(dataclasses.asdict(archive), ofp, indent=2, cls=JSONBytesEncoder)

    else:
        for file_path in map(pathlib.Path, files):
            if not file_path.is_dir():
                with open(str(file_path), "rb") as fp:
                    archive = parser.parse(fp)
                output = str(file_path.parent / f"{file_path.stem}.swift")
                with open(output, "w", encoding="utf-8") as ofp:
                    json.dump(
                        dataclasses.asdict(archive), ofp, indent=2, cls=JSONBytesEncoder
                    )
            else:
                for nib_file in (
                    file_path.glob("*.nib")
                    if not args["recurse"]
                    else file_path.rglob("*.nib")
                ):
                    if nib_file.is_dir():
                        continue

                    output = nib_file.parent / f"{nib_file.stem}.swift"
                    with open(str(nib_file), "rb") as fp:
                        archive = parser.parse(fp)
                    # Using dataclasses we can simply convert our NIBArchive into a dict
                    with open(output, "w", encoding="utf-8") as ofp:
                        json.dump(
                            dataclasses.asdict(archive),
                            ofp,
                            indent=2,
                            cls=JSONBytesEncoder,
                        )


def main(cmd=None):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    p_dump_swift = subparsers.add_parser(
        "dump-swift", help="NIB => Swift"
    )
    p_dump_swift.add_argument(
        "path", help="File path(s) or directories where NIB files are located.", nargs="*"
    )
    p_dump_swift.add_argument(
        "-o", "--output", help="Output path (only applicable to single file input)"
    )
    p_dump_swift.add_argument("-pE", "--print-empty", help="Prints empty variables.", action="store_true")
    p_dump_swift.add_argument(
        "-d", "--max-depth", default=3, help="Specifies the maximum recursion depth."
    )
    p_dump_swift.add_argument(
        "-r",
        "--recurse",
        action="store_true",
        help="Converts all NIB files recursively.",
    )
    p_dump_swift.set_defaults(fn=dump_swift)

    p_dump_json = subparsers.add_parser(
        "dump-json", help="NIB => JSON"
    )
    p_dump_json.add_argument(
        "path", help="File path(s) or directories where NIB files are located.", nargs="*"
    )
    p_dump_json.add_argument(
        "-o", "--output", help="Output path (only applicable to single file input)"
    )
    p_dump_json.add_argument(
        "-r",
        "--recurse",
        action="store_true",
        help="Converts all NIB files recursively.",
    )
    p_dump_json.set_defaults(fn=dump_json)

    args = parser.parse_args(cmd)
    func = args.fn
    if func is not None:
        func(args.__dict__)


if __name__ == "__main__":
    main()
