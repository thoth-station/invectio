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
# type: ignore

import os
import pytest

from invectio import gather_library_usage
from invectio import get_standard_imports
from invectio import __version__ as invectio_version


class TestInvectio:
    @classmethod
    def _get_test_path(cls, test_case_name: str) -> str:
        return str(os.path.join("tests", "data", test_case_name))

    def test_version(self):
        file_path = self._get_test_path("empty.py")
        result = gather_library_usage(file_path)
        assert "version" in result
        assert result["version"] == invectio_version

    def test_empty(self):
        file_path = self._get_test_path("empty.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {}}

    def test_no_files(self):
        file_path = self._get_test_path("somenonexistingfileorfilepath")
        with pytest.raises(FileNotFoundError):
            gather_library_usage(file_path)

    def test_app_1(self):
        file_path = self._get_test_path("app_1.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {"tensorflow": ["tensorflow.layers.conv2d"]}}

    def test_app_2(self):
        file_path = self._get_test_path("app_2.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {"tensorflow": ["tensorflow.layers.conv2d"]}}

    def test_app_3(self):
        file_path = self._get_test_path("app_3.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {"tensorflow": ["tensorflow.layers.conv2d"]}}

    def test_app_4(self):
        file_path = self._get_test_path("app_4.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {"tensorflow": ["tensorflow.layers.conv2d"]}}

    def test_app_5(self):
        file_path = self._get_test_path("app_5.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {"tensorflow": ["tensorflow.layers.conv2d"]}}

    def test_app_6(self):
        file_path = self._get_test_path("app_6.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert result["report"] == {file_path: {"tensorflow": ["tensorflow.layers.conv2d"]}}

    def test_lstm(self):
        file_path = self._get_test_path("lstm.py")
        result = gather_library_usage(file_path)
        assert "report" in result
        assert file_path in result["report"]
        assert len(result["report"].keys()) == 1
        assert result["report"][file_path] == {
            "tensorflow": [
                "tensorflow.Session",
                "tensorflow.Variable",
                "tensorflow.argmax",
                "tensorflow.cast",
                "tensorflow.contrib.rnn.BasicLSTMCell",
                "tensorflow.contrib.rnn.static_rnn",
                "tensorflow.equal",
                "tensorflow.examples.tutorials.mnist.input_data.read_data_sets",
                "tensorflow.float32",
                "tensorflow.global_variables_initializer",
                "tensorflow.matmul",
                "tensorflow.nn.softmax",
                "tensorflow.nn.softmax_cross_entropy_with_logits",
                "tensorflow.placeholder",
                "tensorflow.random_normal",
                "tensorflow.reduce_mean",
                "tensorflow.train.GradientDescentOptimizer",
                "tensorflow.unstack",
            ]
        }

    def test_project_dir(self):
        project_path = self._get_test_path("project_dir")
        result = gather_library_usage(project_path)
        assert "report" in result
        assert result["report"] == {
            "tests/data/project_dir/main.py": {
                "flask": ["flask.Flask"],
                "proj": ["proj.get_model"],
            },
            "tests/data/project_dir/proj/__init__.py": {},
            "tests/data/project_dir/proj/model.py": {
                "numpy": ["numpy.random.random"],
                "tensorflow": [
                    "tensorflow.keras.Sequential",
                    "tensorflow.keras.layers.Dense",
                ],
            },
            "tests/data/project_dir/proj/utils.py": {
                "datetime": ["datetime.datetime.utcnow"]
            },
        }

    def test_get_standard_imports(self):
        standard_imports = get_standard_imports()
        assert isinstance(standard_imports, set)
        assert len(standard_imports) > 0
        assert "json" in standard_imports
        assert "collections" in standard_imports

    def test_standard_imports_detection(self):
        file_path = self._get_test_path("app_7.py")

        result = gather_library_usage(file_path, without_standard_imports=True)
        assert "report" in result
        assert "version" in result
        assert file_path in result["report"]
        assert result["report"][file_path] == {}

        result = gather_library_usage(file_path, without_standard_imports=False)
        assert "report" in result
        assert "version" in result
        assert file_path in result["report"]
        assert result["report"][file_path] == {
            "collections": ["collections.deque"],
            "datetime": ["datetime.datetime.utcnow"]
        }

    def test_without_builtin_and_standard_imports(self):
        file_path = self._get_test_path("app_8.py")

        result = gather_library_usage(file_path, without_standard_imports=True, without_builtin_imports=True)

        assert "version" in result
        assert "report" in result
        assert file_path in result["report"]
        assert result["report"][file_path] == {'tensorflow': ['tensorflow.python.keras.layers.LSTM']}

    def test_without_builtin_imports(self):
        file_path = self._get_test_path("app_8.py")

        result = gather_library_usage(file_path, without_standard_imports=False, without_builtin_imports=True)

        assert "version" in result
        assert "report" in result
        assert file_path in result["report"]
        assert {k: set(v) for k, v in result["report"][file_path].items()} == {
            "collections": {"collections.deque"},
            "signal": {"signal.SIGKILL", "signal.signal"},
            "tensorflow": {"tensorflow.python.keras.layers.LSTM"},
        }
