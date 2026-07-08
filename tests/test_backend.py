# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ast
from pathlib import Path

import asv_env_rattler
from asv_env_rattler import Rattler, _HAS_RATTLER, rattler_solve_and_install


def test_tool_name():
    assert Rattler.tool_name == "rattler"


def test_has_rattler_or_matches_false():
    if _HAS_RATTLER:
        assert Rattler.matches("3.12") is True
    else:
        assert Rattler.matches("3.12") is False


def test_create_path_imports_rattler():
    tree = ast.parse(Path(asv_env_rattler.__file__).read_text())
    imported = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            imported.append(n.module)
        elif isinstance(n, ast.Import):
            imported.extend(a.name for a in n.names)
    assert any(m == "rattler" or m.startswith("rattler.") for m in imported)
    assert "rattler_solve_and_install" in asv_env_rattler.__all__


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "rattler"}
    assert "rattler" in names
    assert "asv_env_rattler" in names["rattler"]


def test_rattler_api_callable():
    if not _HAS_RATTLER:
        return
    import rattler

    assert callable(rattler.solve)
    assert callable(rattler.install)
    assert callable(rattler_solve_and_install)
