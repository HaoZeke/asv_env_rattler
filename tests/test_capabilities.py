# Licensed under a 3-clause BSD style license - see LICENSE.rst
from asv_env_rattler import Rattler


def test_capability_attrs():
    assert Rattler.matrix_install_mode == 'create'
    assert Rattler.supports_joint_pypi_conda_solve is False
    assert Rattler.project_install_prefers_no_deps is True

