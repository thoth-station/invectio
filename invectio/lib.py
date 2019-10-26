#!/usr/bin/env python3
# Invectio
# Copyright(C) 2019 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""A library part of Invectio for static analysis of Python sources."""

from pathlib import Path
import ast
import glob
import logging
import os
import sys
import distutils.sysconfig as sysconfig
from typing import Set
from typing import Dict
from typing import List
from typing import Any
from typing import Optional

import attr

from invectio import __version__ as invectio_version


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG if bool(int(os.getenv("INVECTIO_VERBOSE", 0))) else logging.INFO)


@attr.s(slots=True)
class InvectioVisitor(ast.NodeVisitor):
    """Visitor for capturing imports, nodes and relevant parts to be reported by Invectio."""

    imports = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
    imports_from = attr.ib(type=Dict[str, Dict[str, Optional[str]]], default=attr.Factory(dict))
    usage = attr.ib(type=Dict[str, Set[str]], default=attr.Factory(dict))

    def visit_Import(self, import_node: ast.Import) -> None:
        """Visit `import` statements and capture imported modules/names."""
        for alias in import_node.names:
            if alias.asname is not None:
                if alias.asname in self.imports:
                    _LOGGER.warning(
                        "Detected multiple imports with same name %r, results of calls "
                        "will differ based on actual execution",
                        alias.asname,
                    )

                self.imports[alias.asname] = alias.name
            else:
                self.imports[alias.name] = alias.name

    def visit_ImportFrom(self, import_from_node: ast.ImportFrom) -> None:
        """Visit `import from` statements and capture imported modules/names."""
        if import_from_node.level != 0:
            _LOGGER.debug(
                "Not considering local import %r",
                ",".join(i.name for i in import_from_node.names),
            )
            return

        for alias in import_from_node.names:
            if alias.asname:
                if alias.asname in self.imports_from:
                    _LOGGER.warning(
                        "Multiple imports for %r found, detection might give misleading results",
                        alias.asname,
                    )
                self.imports_from[alias.asname] = {
                    "module": import_from_node.module,
                    "name": alias.name,
                }
            else:
                if alias.name in self.imports_from:
                    _LOGGER.warning(
                        "Multiple imports for name %r found, detection might give misleading results",
                        alias.name,
                    )
                self.imports_from[alias.name] = {
                    "module": import_from_node.module,
                    "name": alias.name,
                }

    def visit_Attribute(self, attr_node: ast.Attribute) -> None:
        """Visit a function call in ast."""
        attrs = []
        item = attr_node

        # Dereference actual attributes if multiple where used.
        while not isinstance(item, ast.Name):
            if isinstance(item, ast.Attribute):
                attrs.append(item.attr)
                item = item.value  # type: ignore
            else:
                _LOGGER.debug("Omitting node of type %r", item.__class__.__name__)
                return

        attrs = list(reversed(attrs))
        self._maybe_mark_usage(item.id, attrs)

    def visit_Name(self, name_name: ast.Name) -> None:
        """Visit a name node in ast."""
        self._maybe_mark_usage(name_name.id, [])

    def _maybe_mark_usage(self, item_id: str, attrs: List[str]) -> None:
        """Mark usage of an attribute."""
        all_import_types = [item_id]
        for attr_item in attrs:
            all_import_types.append(f"{all_import_types[-1]}.{attr_item}")

        for import_type in all_import_types:
            if import_type in self.imports_from:
                module = self.imports_from[item_id]["module"].split(".", maxsplit=1)[0]  # type: ignore

                used = self.imports_from[item_id]["module"]
                used += "." + self.imports_from[item_id]["name"]  # type: ignore
                if attrs:
                    used += "." + ".".join(attrs)

                if module not in self.usage:
                    self.usage[module] = set()

                self.usage[module].add(used)
            if import_type in self.imports:
                module = self.imports[import_type].split(".", maxsplit=1)[0]
                if module not in self.usage:
                    self.usage[module] = set()

                used = module + "." + ".".join(attrs)
                self.usage[module].add(used)

    def get_module_report(self) -> Dict[str, List[str]]:
        """Get raw module report after the library scan discovery."""
        # Convert sets to lists to make them serializable.

        result = {}
        for key, value in self.usage.items():
            result[key] = list(sorted(value))

        return result


def get_standard_imports() -> Set[str]:
    """Get Python's standard imports."""
    result = set()

    std_lib = sysconfig.get_python_lib(standard_lib=True)
    for name in os.listdir(std_lib):
        if name in ("site-packages", "__pycache__"):
            continue

        if name.endswith(".py"):
            name = name[:-len(".py")]

        result.add(name)

    return result


def gather_library_usage(
    path: str,
    *,
    ignore_errors: bool = False,
    without_standard_imports: bool = False,
    without_builtin_imports: bool = False
) -> Dict[str, Any]:
    """Find all sources in the given path and statically extract any library call."""
    if os.path.isfile(path):
        files = list((path,))
    else:
        files = glob.glob(f"{path}/**/*.py", recursive=True)

    if not files:
        raise FileNotFoundError(f"No files to process for {str(path)!r}")

    standard_imports: Set[str] = set()
    if without_standard_imports:
        standard_imports = get_standard_imports()

    builtin_imports: Set[str] = set()
    if without_builtin_imports:
        builtin_imports = set(sys.builtin_module_names)

    report = {}
    for python_file in files:
        python_file_path = Path(python_file)
        _LOGGER.debug("Parsing file %r", str(python_file_path.absolute()))
        try:
            file_ast = ast.parse(python_file_path.read_text())
        except Exception:
            if ignore_errors:
                _LOGGER.exception("Failed to parse Python file %r", python_file)
                continue

            raise

        visitor = InvectioVisitor()
        visitor.visit(file_ast)

        file_report = {}
        module_report = visitor.get_module_report()
        for module_import, symbols in module_report.items():
            if without_standard_imports and module_import in standard_imports:
                _LOGGER.debug("Omitting standard library import %r", module_import)
                continue

            if without_builtin_imports and module_import in builtin_imports:
                _LOGGER.debug("Omitting builtin import %r", module_import)
                continue

            file_report[module_import] = symbols

        report[str(python_file)] = file_report

    return {
        "report": report,
        "version": invectio_version,
    }
