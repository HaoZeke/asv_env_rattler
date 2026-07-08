# Licensed under a 3-clause BSD style license - see LICENSE.rst
from pathlib import Path

import asv_env_rattler
from asv_env_rattler import Rattler, _HAS_NATIVE


def test_tool_name():
    assert Rattler.tool_name == "rattler"


def test_cargo_depends_on_rattler_crates():
    cargo = Path(__file__).resolve().parents[1] / "Cargo.toml"
    text = cargo.read_text()
    assert "rattler" in text
    assert "rattler_solve" in text
    assert "[lib]" in text


def test_maturin_pyproject():
    pp = Path(__file__).resolve().parents[1] / "pyproject.toml"
    text = pp.read_text()
    assert "maturin" in text
    assert "asv_env_rattler._native" in text


def test_native_extension_or_honest_missing():
    if _HAS_NATIVE:
        from asv_env_rattler import _native

        assert _native.backend_name() == "rattler-crates"
        assert callable(_native.create_prefix)
    else:
        assert Rattler.matches("3.12") is False


def test_entry_point_metadata():
    from importlib.metadata import entry_points

    eps = entry_points()
    try:
        group = list(eps.select(group="asv.environment_backends"))
    except AttributeError:
        group = list(eps.get("asv.environment_backends", []))
    names = {ep.name: ep.value for ep in group if ep.name == "rattler"}
    assert "rattler" in names
