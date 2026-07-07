# Licensed under a 3-clause BSD style license - see LICENSE.rst
import asv_env_rattler
from asv_env_rattler import Rattler, _HAS_RATTLER


def test_tool_name():
    assert Rattler.tool_name == "rattler"
    assert asv_env_rattler.Rattler is Rattler


def test_matches_respects_import():
    assert Rattler.matches("not-a-version") is False
    result = Rattler.matches("3.12")
    if _HAS_RATTLER:
        assert result is True
    else:
        assert result is False


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
