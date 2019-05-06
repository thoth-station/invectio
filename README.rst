Invectio
--------

A simple tool to gather library calls and attribute usage based on static
analysis of sources of Python applications.


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

  invectio project-dir/   # To scan all Python files recursively.
  invectio app.py         # To perform usage gathering just on app.py file.


.. code-block:: python

  from invectio import gather_library_calls

  # To scan all Python files recursively.
  result: dict = gather_library_usage("project-dir")

  # To perform usage gathering just on app.py file.
  result: dict = gather_library_usage("app.py")


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
