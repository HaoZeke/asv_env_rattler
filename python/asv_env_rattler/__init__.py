# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""ASV ``environment_type="rattler"`` — maturin wheel over **rattler** Rust crates.

Create path calls the compiled extension ``asv_env_rattler._native.create_prefix``,
which links ``rattler`` / ``rattler_solve`` / related crates (not pure Python solve).
"""

from __future__ import annotations

import re
from pathlib import Path

from asv import environment, util
from asv.console import log

try:
    from asv_env_rattler import _native as _native

    _HAS_NATIVE = True
except ImportError:  # pragma: no cover
    _native = None
    _HAS_NATIVE = False


class Rattler(environment.Environment):
    """Manage an environment via the maturin/Rust rattler extension."""

    tool_name = "rattler"
    matrix_install_mode = "create"
    supports_joint_pypi_conda_solve = False  # rattler#1044
    supports_joint_pypi_solve = False
    project_install_prefers_no_deps = True
    requires_host_tool = None

    def __init__(self, conf, python, requirements, tagged_env_vars):
        if not _HAS_NATIVE:
            raise environment.EnvironmentUnavailable(
                "asv_env_rattler requires the maturin-built extension "
                "(install a wheel built with `maturin build` linking rattler crates)"
            )
        self._python = python
        self._requirements = requirements
        self._channels = list(getattr(conf, "conda_channels", None) or [])
        if "conda-forge" not in self._channels:
            self._channels.append("conda-forge")
        super().__init__(conf, python, requirements, tagged_env_vars)

    @classmethod
    def matches(cls, python):
        if not _HAS_NATIVE:
            return False
        return bool(re.match(r"^[0-9].*$", python) or re.match(r"^pypy[0-9.]*$", python))

    def _extra_specs(self):
        specs = []
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if key.startswith("pip+"):
                continue
            specs.append(f"{key}={val}" if val else key)
        return specs

    def _setup(self):
        log.info(
            f"Creating rattler env for {self.name} via maturin/_native "
            f"(backend={_native.backend_name()})"
        )
        Path(self._path).mkdir(parents=True, exist_ok=True)
        _native.create_prefix(
            self._path,
            self._python,
            list(self._channels),
            self._extra_specs(),
        )
        # pip+ requirements with python -m pip inside prefix
        for key, val in {**self._requirements, **self._base_requirements}.items():
            if not key.startswith("pip+"):
                continue
            declaration = f"{key[4:]} {val}" if val else key[4:]
            parsed = util.ParsedPipDeclaration(declaration)
            util.construct_pip_call(self._run_pip, parsed)()

    def run(self, args, **kwargs):
        log.debug(f"Running '{' '.join(args)}' in {self.name}")
        return self.run_executable("python", args, **kwargs)

    def _run_pip(self, args, **kwargs):
        return self.run_executable("python", ["-m", "pip"] + list(args), **kwargs)


__all__ = ["Rattler", "_HAS_NATIVE"]
