# Terminal Zero Boot

Boot-core v0 is the first executable control-plane slice. It proves the boot
status contract, governance scanner integration, basic Git/dirty inspection,
CLI wiring, and status artifact shape without importing the broader
data-readiness/runtime-smoke graph.

Normal boot-core check:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict
```

Planning-mode check for dirty local work:

```powershell
.\.venv\Scripts\python launch.py --preflight --mode planning
```

Write the generated boot-status JSON only when intentional:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict --write-status
```

Final GitHub-aligned proof after an intentional status commit:

```powershell
.\.venv\Scripts\python launch.py --preflight --strict --require-github
```

Generated boot status:

```text
runtime/boot_status_current.json
```

Schema:

```text
docs/context/boot_status_current.schema.json
```

The runtime JSON file is the only canonical generated boot-status verdict for
v0. `docs/context/boot_status_current.json` is a noncanonical docs/context
snapshot path only; strict preflight must not read, write, mirror, or fall back
to it for safe-boot truth.

Deferred from boot-core v0:

- data-readiness gates
- context packet rebuild/validation
- Portfolio AppTest smoke
- focused replay/dashboard contract
- optimizer, Rule100, replay, and data-repair work

`BOOT.md` is intentionally static. The living verdict is the generated JSON
status, and safe boot still requires a later full safe-boot slice.
