import sys
import os
from pathlib import Path
from setuptools import setup
from setuptools import find_packages
from setuptools.command.test import test as TestCommand

HERE = os.path.dirname(os.path.realpath(__file__))


class Test(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass into py.test")]

    def initialize_options(self):
        super().initialize_options()
        self.pytest_args = [
            "tests/",
            "--timeout=2",
            "--cov=./invectio",
            "--capture=no",
            "--verbose",
            "-l",
            "-s",
            "-vv",
        ]

    def finalize_options(self):
        super().finalize_options()
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        sys.exit(pytest.main(self.pytest_args))


def get_version():
    with open(os.path.join("invectio", "__init__.py")) as f:
        content = f.readlines()

    for line in content:
        if line.startswith("__version__ ="):
            # dirty, remove trailing and leading chars
            return line.split(" = ")[1][1:-2]
    raise ValueError("No version identifier found")


setup(
    name="invectio",
    url="https://github.com/thoth-station/invectio",
    description="Statically analyze sources and extract information about called library functions in Python applications",
    long_description=(Path(HERE) / "README.rst").read_text(),
    author="Fridolin Pokorny",
    author_email="fridex.devel@gmail.com",
    maintainer="Fridolin Pokorny",
    maintainer_email="fridex.devel@gmail.com",
    license="GPLv3+",
    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Topic :: Software Development",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    keywords="ast source code analysis thoth library",
    packages=find_packages(),
    entry_points={"console_scripts": ["invectio=invectio.cli:cli"]},
    install_requires=(Path(HERE) / "requirements.txt").read_text(),
    cmdclass={"test": Test},
    version=get_version(),
)
