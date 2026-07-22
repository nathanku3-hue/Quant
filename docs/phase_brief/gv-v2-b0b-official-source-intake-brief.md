# GV-V2-B0B-OFFICIAL-SOURCE-INTAKE — Controlling Brief (GV-ALPHA0 train)

**Status:** REVISE_AND_GO — fold B0B into **GV-ALPHA0** release train (not phase-stop → B0C)  
**Base:** main `2cd3e858…` · tip on PR #8 · score/stage/observed locked: `39` / `CERTIFIED_SINGLE_DECISION_OPERABLE` / `0`  
**Deadline intent:** Alpha product by **2026-07-30** — optimize end-to-end operability, not sequential phase closure  
**Audit:** R2.1 technical direction PASS; merge→truth-cutover→stop→B0C **revoked** as sole next sequence

---

## Strategic recut (binding)

```text
WRONG:  B0B merge → bank → STOP → open B0C as separate phase
RIGHT:  Fold B0B into one GV-ALPHA0 release train
```

B0B is **source family one** inside Alpha — not a terminal product milestone.

### GV-ALPHA0 release train (end-to-end)

```text
1. Authority repairs (strict JSON, true byte locators, atomic case promote)
2. Bank B0B as source family one (SEC accession custody + claim HOLD)
3. Independent source reconciliation (second family; still paper)
4. Operator decision capture (visible NO_POSITION path)
5. Certified NO_POSITION + one atomic result surface
6. Export / replay
7. Fresh-clone proof
8. Non-author dogfood
9. Formal human comparison DEFERRED until after Alpha
```

**Revoked for Alpha:** formal comparison / G08-style independent human observation as a release gate.  
**Preserved:** score 39, observed 0, ADMITTED never auto-ADVANCE, B0A immutable, no live capital.

---

## Alpha-critical authority gaps (B0B module)

| Gap | Repair |
|---|---|
| Duplicate-key JSON acceptance (`json.loads` last-wins) | Authority loads via `parse_json_text` → `V2B0B_JSON_AUTHORITY_INVALID` |
| Character offsets labelled as `byte_start` / `byte_end` | True byte windows on raw document bytes; mid-codepoint cut fails closed |
| Non-transactional multi-file publication | Stage under `.b0b_tx/`, promote in order, **`result.json` last** as commit marker |

R1 / R2 / R2.1 retained: rebuild-from-raw exact compare, HOLD-only outcomes, auth object set ≡ `PACKAGE_OBJECTS`, parity pins `731a…` / `21e4…` / `48cab…`.

---

## Product vertical (B0B role inside ALPHA0)

```text
pre-read access_authorization
 → exact three SEC objects (custody redundancy, independent_source_count=1)
 → package_manifest (receipt)
 → source_manifest (SEC-header PIT)
 → admission (+ certificate if earned)
 → claim evaluation (separate)
 → research HOLD only in one-source B0B
 → certified paper NO_POSITION
 → atomic case bundle + optional current-decision publish
```

Authority chain layers remain distinct. B0A remains immutable banked substrate.

---

## Mandatory custody rules (unchanged)

- Pre-read authorization remote before first SEC fetch
- `authorization_recorded_at < retrieved_at`; auth has null receipt time
- Exact three objects only; no equivalents
- `independent_source_count = 1` (index/submission/primary are not three corroborators)
- Claim vocabulary separate from admission
- No score uplift / alpha / live capital claims

---

## Ship posture for Alpha

1. Land authority repairs on the B0B PR tip without treating merge as “phase complete.”
2. Keep product/protocol/parity green on every tip.
3. Extend the **same train** toward second-source reconciliation and operator/export/fresh-clone/dogfood — not a stop-the-world B0C phase.
4. Formal comparison only **after** Alpha if a multi-source case is genuinely contestable.
