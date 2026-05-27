# Terminal Zero Boot

Boot-core v0 is the first executable control-plane slice. It proves the boot
status contract, basic Git/dirty inspection, CLI wiring, and status artifact
shape. The current governance slice also runs `scripts.governance_preflight`;
data-readiness remains deferred from this boot proof.

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

Deferred from boot-core v0:

- data-readiness gates
- context packet rebuild/validation
- Portfolio AppTest smoke
- focused replay/dashboard contract
- optimizer, Rule100, replay, and data-repair work

`BOOT.md` is intentionally static. The living verdict is the generated JSON
status. Governance preflight is in the current boot slice; safe boot still
requires later data-readiness, context, smoke, replay/dashboard, optimizer,
Rule100, and data-repair slices.
