# Impact Packet — Current

## Change under review

A terminal repair was applied to the remote-equal GV Micro-Portfolio V0 integration candidate without opening Product or Replay implementation.

### Functional impact

- Certification now binds prior certification identity, pre-observation recomputation, current/prior linkage, ordered certification-record events, and later-observation event source/instrument envelopes.
- Persisted explanation, claim boundary, fixture identity, instrument registry, benchmark registry, review labels/roles, and status-specific later-observation projection fail closed on contradiction.
- Strategy rejects a later observation whose evidence ID is absent from the available evidence set.
- Accounting requires declared event sequences to be unique, ordered, zero-based, and contiguous.
- Certification reduces the full immutable ledger while hashing only the certification subject, preserving both ledger continuity and stable certification identity.

### Test-authority impact

The four legacy product failures were not product regressions. Their tests asserted superseded E0A/FS0 status text after the canonical seven-slice roadmap replaced that authority. The narrow assertion repair produces **263/263 PASS** without changing Product runtime.

### Environment impact

`requirements.lock` already pins `alpaca-py`, `psycopg2-binary`, `PyYAML`, and `schedule`; no dependency change was required. A fresh Python 3.12 environment installs from the lock and passes `pip check`.

Windows `core.autocrlf=true` changed hash-bound CSV/JSON bytes. Repository `.gitattributes` now requires LF for textual data artifacts and binary treatment for parquet/raw artifacts. In a fresh LF-preserving clone, repository failures fall from 111 to 50.

### Verification impact

- Portfolio: **94/94 PASS** after independent Reviewer A repair.
- Context + frozen protocol: **175/175 PASS**.
- Legacy product: **263/263 PASS**.
- Full collection: **2664 tests / 201 files**, PASS.
- Full LF suite: **2598 passed, 16 skipped, 50 failed**.

### Product and score impact

The user flow remains:

review four securities and cash → confirm one portfolio aim → emit one transition → create one deterministic paper order and fill → reconcile and certify → persist and reopen → admit one later WATCH observation with unchanged aim.

The repair makes that flow materially harder to mislabel or forge, but adds no user-facing capability. Canonical shipped score remains **39/100** and observed comparisons remain **0** until full-suite and independent audit gates pass.
