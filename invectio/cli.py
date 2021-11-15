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

"""A command line interface to Invectio."""

import sys
import logging
import json

import click
import daiquiri

from invectio import __version__
from invectio import __title__
from invectio import gather_library_usage
from invectio import gather_symbols_provided

daiquiri.setup(level=logging.INFO)


_LOGGER = logging.getLogger(__title__)


def _print_version(ctx, _, value):
    """Print Invectio version and exit."""
    if not value or ctx.resilient_parsing:
        return

    click.echo(__version__)
    ctx.exit()


@click.group()
@click.pass_context
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    show_default=True,
    envvar="INVECTIO_VERBOSE",
    help="Be verbose about what's going on.",
)
@click.option(
    "--version",
    is_flag=True,
    show_default=True,
    is_eager=True,
    callback=_print_version,
    expose_value=False,
    help="Print Invectio version and exit.",
)
def cli(
    ctx=None,
    verbose: bool = False,
) -> None:
    """Statically analyze sources and extract information about called library functions in Python applications."""
    if ctx:
        ctx.auto_envvar_prefix = "INVECTIO"

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")
    _LOGGER.debug("Version: %s", __version__)


@cli.command()
@click.argument("path")
@click.option(
    "--ignore-errors/--no-ignore-errors",
    is_flag=True,
    show_default=True,
    help="Ignore syntax or parsing errors for Python files.",
)
@click.option(
    "--without-standard-imports/--with-standard-imports",
    is_flag=True,
    show_default=True,
    help="Do not report usage of Python's standard library.",
)
@click.option(
    "--without-builtin-imports/--with-builtin-imports",
    is_flag=True,
    show_default=True,
    help="Do not report usage of Python's standard library.",
)
@click.option(
    "--without-builtins/--with-builtins",
    is_flag=True,
    show_default=True,
    help="Do not report usage of Python's builtins.",
)
def whatuses(
    path: str,
    ignore_errors: bool = False,
    without_standard_imports: bool = False,
    without_builtin_imports: bool = False,
    without_builtins: bool = False,
) -> None:
    """Gather information about symbol usage by a module or a source file."""
    result = gather_library_usage(
        path,
        ignore_errors=ignore_errors,
        without_standard_imports=without_standard_imports,
        without_builtin_imports=without_builtin_imports,
        without_builtins=without_builtins,
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True))


@cli.command()
@click.argument("path")
@click.option(
    "--ignore-errors/--no-ignore-errors",
    is_flag=True,
    show_default=True,
    help="Ignore syntax or parsing errors for Python files.",
)
@click.option(
    "--include-private/--no-include-private",
    is_flag=True,
    default=False,
    show_default=True,
    help="Ignore syntax or parsing errors for Python files.",
)
def whatprovides(
    path: str,
    ignore_errors: bool = False,
    include_private: bool = False,
) -> None:
    """Gather information about symbols provided by a module or a source file."""
    result = gather_symbols_provided(
        path,
        ignore_errors=ignore_errors,
        include_private=include_private,
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True))


__name__ == "__main__" and sys.exit(cli())
