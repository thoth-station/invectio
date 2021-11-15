Invectio
--------

A simple tool to gather symbols provided or library calls and attribute usage
based on static analysis of sources of Python applications.


Installation
============

Invectio can be installed from `PyPI <https://pypi.org/project/invectio>`_ using:

.. code-block:: console

  $ pip3 install invectio
  $ invectio --help


Usage
=====

You can use this library as a CLI tool or as a Python module:

.. code-block:: console

  invectio whatprovides project-dir/   # To scan all Python files recursively for symbols provided.
  invectio whatprovides app.py         # To perform symbols gathering on app.py file.

  invectio whatuses project-dir/       # To scan all Python files recursively for symbols used from libraries.
  invectio whatuses app.py             # To perform gather symbols used from libraries on app.py file.


.. code-block:: python

  from invectio import gather_library_calls
  from invectio import gather_symbols_provided

  result: dict = gather_library_usage("project-dir")
  result: dict = gather_library_usage("app.py")

  result: dict = gather_symbols_provided("project-dir")
  result: dict = gather_symbols_provided("app.py")


Limitations
###########

As Python is a dynamic programming language, it's not possible to obtain all
library functions/attributes usage simply by performing static analysis of
sources. One can still perfom "crazy" things like:


.. code-block:: python

  import tensorflow

  getattr(tensorflow, "const" + "ant")("Hello, Invectio")


This library does its best to detect all function/attributes being used inside
Python sources, but usage like shown above cannot be detected simply by static
analysis of source code.


Development
===========

To create a dev environment, clone the invectio repo and install all the dependencies:

.. code-block:: console

  git clone https:://github.com/thoth-station/invectio && cd invectio
  pipenv install --dev

To perform checks against unit tests present in the `tests/` directory,
issue the following command from the root of the git repo:

.. code-block:: console

  pipenv run python3 setup.py test
