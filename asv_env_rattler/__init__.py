# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="rattler"`` via the **py-rattler** Rust stack.

Create path is in-process ``rattler.solve`` + ``rattler.install`` only.
Fails closed if ``py-rattler`` is not installed.

Core ASV does not ship this backend in-tree; this package is the provider.
"""

from __future__ import annotations

import asyncio
import inspect
import os
import re
import sys
from pathlib import Path

from asv import environment, util
from asv.console import log

try:
    from yaml import load

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    from rattler import ChannelPriority, MatchSpec, VirtualPackage, install, solve

    _HAS_RATTLER = True
except ImportError:  # pragma: no cover
    _HAS_RATTLER = False
    load = Loader = ChannelPriority = MatchSpec = VirtualPackage = install = solve = None


def _virtual_packages():
    if hasattr(VirtualPackage, "detect"):
        return VirtualPackage.detect()
    return VirtualPackage.current()


def _expand_channels(channels):
    expanded = []
    for channel in channels:
        if channel == "defaults":
            expanded.extend(
                [
                    "https://repo.anaconda.com/pkgs/main",
                    "https://repo.anaconda.com/pkgs/r",
                ]
            )
            if sys.platform.startswith("win"):
                expanded.append("https://repo.anaconda.com/pkgs/msys2")
        else:
            expanded.append(channel)
    return list(dict.fromkeys(expanded))


async def rattler_solve_and_install(prefix: str, specs: list, channels: list, channel_priority=None):
    """Public create primitive: Rust py-rattler solve + install into *prefix*."""
    if not _HAS_RATTLER:
        raise environment.EnvironmentUnavailable(
            "asv_env_rattler requires py-rattler (pip install py-rattler)"
        )
    if channel_priority is None:
        channel_priority = ChannelPriority.Strict
    match_specs = [MatchSpec(p) for p in specs]
    final_channels = _expand_channels(channels)
    solve_kwargs = {
        "specs": match_specs,
        "virtual_packages": _virtual_packages(),
        "channel_priority": channel_priority,
    }
    # py-rattler >=0.22 uses sources=; older used channels=
    params = inspect.signature(solve).parameters
    if "sources" in params:
        solve_kwargs["sources"] = final_channels
    else:
        solve_kwargs["channels"] = final_channels
    solved_records = await solve(**solve_kwargs)
    Path(prefix).mkdir(parents=True, exist_ok=True)
    await install(records=solved_records, target_prefix=prefix)
    return solved_records


class Rattler(environment.Environment):
    """Manage an environment using in-process py-rattler (Rust)."""

    tool_name = "rattler"

    def __init__(self, conf, python, requirements, tagged_env_vars):
        if not _HAS_RATTLER:
            raise environment.EnvironmentUnavailable(
                "asv_env_rattler requires the py-rattler package "
                "(Rust backend: pip install 'py-rattler>=0.22')"
            )
        self._python = python
        self._requirements = requirements
        self._channels = list(conf.conda_channels or [])
        if "conda-forge" not in self._channels:
            self._channels = list(self._channels) + ["conda-forge"]
        self._environment_file = None

        if conf.conda_environment_file == "IGNORE":
            self._environment_file = None
        elif not conf.conda_environment_file:
            if Path("environment.yml").exists():
                self._environment_file = "environment.yml"
        else:
            if Path(conf.conda_environment_file).exists():
                self._environment_file = conf.conda_environment_file

        super().__init__(conf, python, requirements, tagged_env_vars)
        self._pkg_cache = f"{self._env_dir}/pkgs"
        self._channel_priority = ChannelPriority.Strict

        condarc_path = Path(os.getenv("CONDARC", ""))
        if condarc_path.is_file() and os.getenv("ASV_USE_CONDARC"):
            with condarc_path.open() as f:
                condarc_data = load(f, Loader=Loader) or {}
            if "channels" in condarc_data:
                self._channels = list(condarc_data["channels"]) + list(self._channels)
            if "channel_priority" in condarc_data:
                priority_map = {
                    "strict": ChannelPriority.Strict,
                    "flexible": ChannelPriority.Flexible,
                    "disabled": ChannelPriority.Disabled,
                }
                self._channel_priority = priority_map.get(
                    condarc_data["channel_priority"], ChannelPriority.Strict
                )

    @classmethod
    def matches(cls, python):
        if not _HAS_RATTLER:
            return False
        return bool(re.match(r"^[0-9].*$", python) or re.match(r"^pypy[0-9.]*$", python))

    def _setup(self):
        if not _HAS_RATTLER:
            raise environment.EnvironmentUnavailable("py-rattler is required for create")
        asyncio.run(self._async_setup())

    async def _async_setup(self):
        log.info(f"Creating rattler (py-rattler Rust) environment for {self.name}")
        _args, pip_args = self._get_requirements()
        _pkgs = ["python", "wheel", "pip"]
        if self._environment_file:
            env_data = load(Path(self._environment_file).open(), Loader=Loader)
            _pkgs = [x for x in env_data.get("dependencies", []) if isinstance(x, str)]
            self._channels += [x for x in env_data.get("channels", []) if isinstance(x, str)]
            self._channels = list(dict.fromkeys(self._channels))
            pip_maybe = [x for x in env_data.get("dependencies", []) if isinstance(x, dict)]
            if len(pip_maybe) == 1:
                pip_args += pip_maybe[0].get("pip", [])
        _pkgs += _args
        _pkgs = [util.replace_cpython_version(pkg, self._python) for pkg in _pkgs]
        # Ensure python version pin when only bare "python" present
        normalized = []
        for p in _pkgs:
            if p == "python" or p.startswith("python "):
                normalized.append(f"python={self._python}")
            else:
                normalized.append(p)
        if not any(x.startswith("python") for x in normalized):
            normalized.insert(0, f"python={self._python}")

        await rattler_solve_and_install(
            self._path, normalized, self._channels, self._channel_priority
        )
        for declaration in pip_args:
            parsed = util.ParsedPipDeclaration(declaration)
            util.construct_pip_call(self._run_pip, parsed)()

    def _get_requirements(self):
        _args, pip_args = [], []
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                pip_args.append(f"{key[4:]} {val}" if val else key[4:])
            else:
                _args.append(f"{key}={val}" if val else key)
        return _args, pip_args

    def run(self, args, **kwargs):
        log.debug(f"Running '{' '.join(args)}' in {self.name}")
        return self.run_executable("python", args, **kwargs)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)


__all__ = ["Rattler", "_HAS_RATTLER", "rattler_solve_and_install"]
