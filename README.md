# asv_env_rattler

ASV `environment_type = "rattler"` as a **maturin** wheel whose Rust core
depends on the **rattler** crate stack (`rattler`, `rattler_solve`, …).

```bash
# build (prefer remote builder with cargo+maturin)
maturin build --release
pip install target/wheels/asv_env_rattler-*.whl
```

```json
{ "environment_type": "rattler" }
```
