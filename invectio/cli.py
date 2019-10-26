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

"""A command line interface to Invectio."""

import sys
import logging
import json

import click
import daiquiri

from invectio import __version__
from invectio import __title__
from invectio import gather_library_usage

daiquiri.setup(level=logging.INFO)


_LOGGER = logging.getLogger(__title__)


def _print_version(ctx, _, value):
    """Print Invectio version and exit."""
    if not value or ctx.resilient_parsing:
        return

    click.echo(__version__)
    ctx.exit()


@click.command()
@click.pass_context
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    envvar="INVECTIO_VERBOSE",
    help="Be verbose about what's going on.",
)
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    callback=_print_version,
    expose_value=False,
    help="Print Invectio version and exit.",
)
@click.option(
    "--ignore-errors/--no-ignore-errors",
    is_flag=True,
    help="Ignore syntax or parsing errors for Python files.",
)
@click.option(
    "--without-standard-imports/--with-standard-imports",
    is_flag=True,
    help="Do not report usage of Python's standard library.",
)
@click.option(
    "--without-builtin-imports/--with-builtin-imports",
    is_flag=True,
    help="Do not report usage of Python's builtins.",
)
@click.argument("path")
def cli(
    ctx,
    path: str,
    verbose: bool = False,
    ignore_errors: bool = False,
    without_standard_imports: bool = False,
    without_builtin_imports: bool = False,
):
    """Statically analyze sources and extract information about called library functions in Python applications."""
    if ctx:
        ctx.auto_envvar_prefix = "INVECTIO"

    if verbose:
        _LOGGER.setLevel(logging.DEBUG)

    _LOGGER.debug("Debug mode is on")
    _LOGGER.debug("Version: %s", __version__)

    result = gather_library_usage(
        path,
        ignore_errors=ignore_errors,
        without_standard_imports=without_standard_imports,
        without_builtin_imports=without_builtin_imports,
    )
    click.echo(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    sys.exit(cli())
