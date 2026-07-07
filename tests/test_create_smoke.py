# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import tempfile
from pathlib import Path

import pytest

from asv.config import Config
from asv_env_rattler import Rattler, _HAS_RATTLER


@pytest.fixture
def conf(tmp_path):
    c = Config()
    c.env_dir = str(tmp_path / "env")
    c.project = "smoke"
    c.repo = str(tmp_path / "repo")
    c.repo_subdir = ""
    c.install_timeout = 900.0
    c.default_benchmark_timeout = 60.0
    c.conda_channels = ["conda-forge"]
    c.conda_environment_file = "IGNORE"
    c.matrix = {}
    return c


def test_create_rattler_has_python(conf):
    if not _HAS_RATTLER:
        pytest.skip("py-rattler not installed")
    os.chdir(tempfile.mkdtemp())
    import sys

    py = f"{sys.version_info.major}.{sys.version_info.minor}"
    env = Rattler(conf, py, {}, {})
    Path(env._path).mkdir(parents=True, exist_ok=True)
    env._setup()
    py_path = Path(env.find_executable("python"))
    assert py_path.exists()
    out = env.run_executable("python", ["-c", "print(3+3)"])
    assert "6" in out
