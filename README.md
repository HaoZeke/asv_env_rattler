# asv_env_rattler

ASV `environment_type = "rattler"` backend using the **py-rattler** Rust
library (`solve` / `install` in-process). Not the conda CLI.

Core ASV (extract design) ships only virtualenv/existing; this package is
the provider for `rattler`.

```bash
pip install "git+https://github.com/HaoZeke/asv_env_rattler.git"
```

```json
{ "environment_type": "rattler" }
```
