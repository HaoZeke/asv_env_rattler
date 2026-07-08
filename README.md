# asv_env_rattler

Drop-in ASV backend for `environment_type = "rattler"`.

Creates conda-style prefixes with a **maturin** wheel over the **rattler**
Rust crate stack (`rattler`, `rattler_solve` / resolvo, repodata gateway).

## Drop-in setup

```bash
pip install asv
pip install maturin
maturin build --release
pip install target/wheels/asv_env_rattler-*.whl
```

```json
{
  "environment_type": "rattler",
  "conda_channels": ["conda-forge"],
  "pythons": ["3.12"],
  "matrix": {
    "req": {
      "numpy": ["1.26"]
    }
  },
  "install_command": [
    "in-dir={env_dir} python -mpip install --no-deps {wheel_file}"
  ]
}
```

No conf `plugins` list is required when the entry point is installed.

## Capabilities / matrix meaning

| Flag | Value |
|------|-------|
| `matrix_install_mode` | `create` (single rattler solve of python + matrix conda specs) |
| `supports_joint_pypi_conda_solve` | `False` (blocked on [rattler#1044](https://github.com/conda/rattler/issues/1044)) |
| `project_install_prefers_no_deps` | `True` |
| `requires_host_tool` | none |

`pip+` matrix keys are installed after the conda solve (second mutation).
Prefer pure conda specs when pins must hold. For joint conda+PyPI, use
`asv_env_pixi` until rattler gains unified solve.

## Discovery

```toml
[project.entry-points."asv.environment_backends"]
rattler = "asv_env_rattler:Rattler"
```

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
