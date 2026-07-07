# asv_env_rattler

ASV environment backend for `environment_type = "rattler"` using **py-rattler**
(`solve` / `install` APIs), not the conda CLI.

## Stage-1 discovery

```toml
[project.entry-points."asv.environment_backends"]
rattler = "asv_env_rattler:Rattler"
```

```bash
pip install "git+https://github.com/HaoZeke/asv_env_rattler.git"
```

```json
{ "environment_type": "rattler" }
```

## Conflict with in-tree ASV

Stage-1 ASV may also ship `asv.plugins.rattler` with `tool_name = "rattler"`.
**In-tree registration wins** when both are present. This package is the
extract / fallback implementation when optional in-tree backends are omitted.
Do not register two different third-party providers for the same EP name.

## Requirements

- `py-rattler` and `PyYAML` (declared dependencies)
- Host ASV with `asv.envmgmt.discover` (Stage-1) or conf `plugins`

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
