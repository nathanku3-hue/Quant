# GV-ALPHA0 Paper-Decision Product

Release claim: one usable, broker-free, certified paper-decision workflow. It does not claim decision improvement, alpha, live-capital readiness, or provider coverage.

## Requirements

- Python 3.12+
- No broker credentials
- No provider credentials
- No network access after dependency installation

## Windows

```bat
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-release.txt
run-windows.cmd
```

## Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-release.txt
chmod +x run-linux.sh
./run-linux.sh
```

The first launch creates a deterministic sealed sample workspace in the platform user-data directory. The workflow is:

```text
launch -> review sealed evidence -> confirm paper NO_POSITION -> persist -> reopen certified state
```

Use `python launch_alpha.py --data-dir <path>` to select an explicit data directory. Before initialization, startup validates the complete extracted package against `RELEASE_MANIFEST.json`, canonicalizes package and runtime paths, and rejects missing/tampered files, symlinks or Windows junctions that escape the workspace or route storage into the package, and unmanaged nonempty data roots.

## Fresh-machine smoke

```bash
python scripts/smoke_gv_alpha0_release.py
```

A passing smoke prints one JSON record with `"status":"PASS"`.
