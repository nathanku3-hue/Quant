# Recent Lessons Summary

Status: excerpted orientation for the expert packet

## Lessons That Matter For This Decision

- Boot-control commands sourced from artifacts must be argv-bounded, allowlisted, timeout-bounded, and followed by mutation proof before any read-only alignment claim.
- Canonical boot/status path contention must stop implementation work until a single contract is selected.
- Root evidence beats packet artifacts when the live root is changing or dirty.
- Local ignored data is not BootReady truth.
- Boot preflight is not artifact authorization evidence while data readiness remains blocked.
- Harness flow must be recorded without overlapping owners: docs should record workflow contracts and boundaries without editing templates, skills, packet scripts, code, or truth packets owned by other workers.

## Packet Implication

This packet should be used to select a bounded next direction only. It should not be used to justify direct continuation in the dirty root or to treat unmerged harness artifacts as implementation-ready.
