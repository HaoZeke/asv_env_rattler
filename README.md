# asv_env_rattler

ASV environment backend for `environment_type = "rattler"` (py-rattler APIs).

Core ASV (extract design) ships only **virtualenv** and **existing**.
This package is the **provider** for `rattler` — there is no in-tree
`asv.plugins.rattler`.

## Discovery

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

Install into the host environment that runs ASV. Conf `plugins` is optional
when entry points are registered.

## Tests

```bash
pip install -e ".[test]"
pytest -q
```
