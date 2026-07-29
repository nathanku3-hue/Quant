# Impact Packet — Current

## Active — R0 roadmap custody repair (2026-07-29)

### Changed authority surfaces

- corrected canonical roadmap and compact top-level roadmap;
- root product surfaces: `README.md`, `PRD.md`, `PRODUCT_SPEC.md`, `PHASE_QUEUE.md`;
- explicit active brief pointer: `docs/context/ACTIVE_BRIEF`;
- new active brief: `docs/phase_brief/phase0-gv-micro-portfolio-vertical-0-brief.md`;
- Phase 66 bridge moved to historical archive;
- context generator and focused tests updated for explicit selection and fail-closed behavior;
- current truth, decision/lesson entries, SAW evidence, and handover reconciled.

### Product impact

- standalone contract-only `GV-CANON-RESET-0` is removed from the product sequence;
- the first product slice is the complete micro-portfolio operator loop;
- deterministic replay remains immediately before any bounded portfolio expansion;
- released FS0 remains immutable and a new portfolio namespace is required.

### Execution impact

- three mergeable packages replace seven automatic independent branches;
- minimum identity/event seams freeze before parallel implementation;
- detailed schema fields freeze only when exercised by the vertical fixture;
- implementation remains stopped pending independent audit of `ROADMAP_FREEZE_COMMIT`.

### Runtime/data impact

No portfolio runtime, provider, data artifact, model, score, broker, or live-capital behavior changed in R0. The only code change is the context-authority selector and its focused tests.

### Open risk

The root source checkout remains unsafe and untouched. Any implementation branch created from raw `93e7a55` or another stale base would omit the corrected authority and is invalid.
