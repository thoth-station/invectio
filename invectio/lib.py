#!/usr/bin/env python3
# Invectio
# Copyright(C) 2019, 2020 Fridolin Pokorny
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

import ast
import distutils.sysconfig as sysconfig
import glob
import logging
import os
import sys
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Set
from typing import Tuple

import attr

from invectio import __version__ as invectio_version


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(
    logging.DEBUG if bool(int(os.getenv("INVECTIO_VERBOSE", 0))) else logging.INFO
)


@attr.s(slots=True)
class InvectioLibraryUsageVisitor(ast.NodeVisitor):
    """Visitor for capturing imports, nodes and relevant parts to be reported by Invectio."""

    imports = attr.ib(type=dict, default=attr.Factory(dict))
    imports_from = attr.ib(type=dict, default=attr.Factory(dict))
    usage = attr.ib(type=dict, default=attr.Factory(dict))

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

    def _maybe_mark_usage(self, item_id: str, attrs: list) -> None:
        """Mark usage of an attribute."""
        all_import_types = [item_id]
        for attr_item in attrs:
            all_import_types.append(f"{all_import_types[-1]}.{attr_item}")

        for import_type in all_import_types:
            if import_type in self.imports_from:
                module = self.imports_from[item_id]["module"].split(".", maxsplit=1)[0]

                used = self.imports_from[item_id]["module"]
                used += "." + self.imports_from[item_id]["name"]
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

    def get_module_report(self) -> dict:
        """Get raw module report after the library scan discovery."""
        # Convert sets to lists to make them serializable.

        result = {}
        for key, value in self.usage.items():
            result[key] = list(sorted(value))

        return result


@attr.s(slots=True)
class InvectioSymbolsProvidedVisitor:
    """Visitor for capturing symbols provided.

    The functionality does not retrieve imported symbols.
    """

    file_name = attr.ib(type=str)
    include_private = attr.ib(type=bool, default=True)
    symbols = attr.ib(type=Set[str], factory=set, init=False)

    def visit_FunctionDef(self, function_def: ast.FunctionDef) -> None:
        """Visit a function definition."""
        if not self.include_private and function_def.name.startswith("_"):
            return

        if function_def.name in self.symbols:
            _LOGGER.warning(
                "Function definition overrides already defined symbol in file %r: %r",
                self.file_name,
                function_def.name,
            )

        self.symbols.add(function_def.name)

    def visit_AsyncFunctionDef(self, async_function_def: ast.AsyncFunctionDef) -> None:
        """Visit a async function definition."""
        if not self.include_private and async_function_def.name.startswith("_"):
            return

        if async_function_def.name in self.symbols:
            _LOGGER.warning(
                "Async function definition overrides already defined symbol in file %r: %r",
                self.file_name,
                async_function_def.name,
            )

        self.symbols.add(async_function_def.name)

    def visit_ClassDef(self, class_def: ast.ClassDef) -> None:
        """Visit a class definition."""
        if not self.include_private and class_def.name.startswith("_"):
            return

        if class_def.name in self.symbols:
            _LOGGER.warning(
                "Class definition overrides already defined symbol in file %r: %r",
                self.file_name,
                class_def.name,
            )

        self.symbols.add(class_def.name)

    def visit_Assign(self, assign: ast.Assign) -> None:
        """Visit a global."""

        def _maybe_add_maybe_log(n: str):
            if not self.include_private and n.startswith("_"):
                return

            if n in self.symbols:
                _LOGGER.warning(
                    "Target in assignment overrides already defined symbol in file %r: %r",
                    self.file_name,
                    n,
                )

            self.symbols.add(n)

        def _maybe_add(node: ast.AST):
            if isinstance(node, ast.Name):
                _maybe_add_maybe_log(node.id)
            elif isinstance(node, ast.Starred):
                _maybe_add(node.value)
            elif isinstance(node, ast.Tuple):
                for i in node.elts:
                    _maybe_add(i)
            elif isinstance(node, (ast.Subscript, ast.Attribute)):
                # Should be declared beforehand.
                pass
            else:
                _LOGGER.error(
                    "Unhandled type for target in assignment: %r",
                    node.__class__.__name__,
                )

        for target in assign.targets:
            if isinstance(target, ast.Name):
                _maybe_add_maybe_log(target.id)
            else:
                try:
                    _maybe_add(target)
                except RecursionError:
                    _LOGGER.exception(
                        f"Failed to parse assign statement in {self.file_name}"
                    )

    def visit_AnnAssign(self, ann_assign: ast.AugAssign) -> None:
        """Visit aug assignments."""
        if not isinstance(ann_assign.target, ast.Name):
            # Skip subscription and attributes.
            return

        if not self.include_private and ann_assign.target.id.startswith("_"):
            return

        if ann_assign.target.id in self.symbols:
            _LOGGER.warning(
                "Target in assignment overrides already defined symbol in file %r: %r",
                self.file_name,
                ann_assign.target.id,
            )

        self.symbols.add(ann_assign.target.id)

    def visit(self, module: ast.Module) -> None:
        """Gather symbols provided by the given ast.

        Note we are traversing top level modules exported. We do not visit nested AST trees.
        """
        for item in module.body:
            handler_name = f"visit_{item.__class__.__name__}"
            handler = getattr(self, handler_name, None)
            if handler:
                handler(item)

    def get_module_report(self) -> Set[str]:
        """Get report once the traversal is done."""
        module_name = (
            self.file_name[: -len(".py")]
            if self.file_name.endswith(".py")
            else self.file_name
        ).replace("/", ".")
        return {f"{module_name}.{s}" for s in self.symbols}


def get_standard_imports() -> Set[str]:
    """Get Python's standard imports."""
    result = set()

    std_lib = sysconfig.get_python_lib(standard_lib=True)
    for name in os.listdir(std_lib):
        if name in ("site-packages", "__pycache__"):
            continue

        if name.endswith(".py"):
            name = name[: -len(".py")]

        result.add(name)

    return result


def _get_python_files(path: str) -> List[str]:
    """Get Python files for the given path."""
    if os.path.isfile(path):
        files = [path]
    else:
        files = glob.glob(f"{path}/**/*.py", recursive=True)

    if not files:
        raise FileNotFoundError(f"No files to process for {str(path)!r}")

    return files


def _iter_python_file_ast(
    path: str, *, ignore_errors: bool
) -> Generator[Tuple[Path, object], None, None]:
    """Get AST for all the files given the path."""
    for python_file in _get_python_files(path):
        python_file_path = Path(python_file)
        _LOGGER.debug("Parsing file %r", str(python_file_path.absolute()))
        try:
            yield python_file_path, ast.parse(python_file_path.read_text())
        except Exception:
            if ignore_errors:
                _LOGGER.exception("Failed to parse Python file %r", python_file)
                continue

            raise


def gather_library_usage(
    path: str,
    *,
    ignore_errors: bool = False,
    without_standard_imports: bool = False,
    without_builtin_imports: bool = False,
) -> Dict[str, Any]:
    """Find all sources in the given path and statically extract any library call."""
    standard_imports: Set[str] = set()
    if without_standard_imports:
        standard_imports = get_standard_imports()

    builtin_imports: Set[str] = set()
    if without_builtin_imports:
        builtin_imports = set(sys.builtin_module_names)

    report = {}

    for python_file, file_ast in _iter_python_file_ast(
        path, ignore_errors=ignore_errors
    ):
        visitor = InvectioLibraryUsageVisitor()
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


def gather_symbols_provided(
    path: str, include_private: bool = False, ignore_errors: bool = False
) -> Dict[str, Any]:
    """Gather symbols provided by a library."""
    report = {}

    for python_file, file_ast in _iter_python_file_ast(
        path, ignore_errors=ignore_errors
    ):
        visitor = InvectioSymbolsProvidedVisitor(
            file_name=str(python_file), include_private=include_private
        )
        visitor.visit(file_ast)

        report[str(python_file)] = sorted(visitor.get_module_report())

    return {
        "report": report,
        "version": invectio_version,
    }
