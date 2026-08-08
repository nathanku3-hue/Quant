# AOV-0 Capital IQ Authority Recut — SAW Receipt

Mode: `IMPLEMENTATION_REVIEW`
Date: 2026-08-07
RoundID: `ROUND-20260807-AOV0-CIQ-AUTHORITY-RECUT`
ScopeID: `AOV0-CIQ-AUTHORITY-V1`
Branch: `codex/pit-source-authority-1`
Base HEAD at round start: `fa20289673944dd1f2c5eabd10950c6546276cda`

SAW Verdict: BLOCK

Hierarchy Confirmation: Approved | Session: current-thread | Trigger: explicit owner Path-B decision | Domains: Product, Architecture, Software Engineering, Data Provenance, Quant Research, Governance | Authority: `docs/context/gv_endgame_authority_current.md` + `docs/phase_brief/alpha-organism-vertical-0-brief.md`

## Intent

Preserve the first-real-seal critical path while removing a false source premise. The available WRDS account lacks CRSP entitlement, so the prior CRSP/PERMNO active contract cannot produce the required bytes. The owner explicitly authorized Path B: one destructive S&P Capital IQ Pro identity/fundamental/market-data family. Direct New York Fed SOFR and every prospective-cut integrity invariant remain unchanged.

## Architecture choice

### COPY / preserve

- one app and one canonical engine;
- one permanent security identity on the active AOV path;
- date-local Rule100 universe and same-cut five-arm experiment;
- immutable input SHA-256 binding, contract hash, universe hash, knowledge cutoff, target date, seal time, first eligible execution bar, and pre/post-run re-hash;
- direct NY Fed SOFR after 15:00 America/New_York;
- frozen insurance `0.05 / 0.0015`;
- `financial_alpha_evidence = 0` until a matured outcome opens.

### MODIFY / chosen Path B

- executable schema: `aov0_ciq_executable_contract_v1`;
- decision-cut schema: `aov0_ciq_decision_cut_v1`;
- permanent active security identity: `CIQSEC:<Capital IQ Security ID>`;
- candidate-screen source: `SPCIQPRO:COMPANIES_SCREENER_RESULT`;
- quarterly Rule100 fundamental source: `SPCIQPRO:QUARTERLY_FUNDAMENTALS`;
- primary-security identity source: `SPCIQPRO:PRIMARY_SECURITY_MASTER`;
- risky-asset total-return authority: `SPCIQPRO:PRIMARY_SECURITY_MARKET_DATA` / `SPCIQPRO_PRIMARY_SECURITY_TOTAL_RETURN_MATRIX_ONLY`;
- first-seal source receipts: CIQ screen result + CIQ quarterly fundamentals + CIQ security master + CIQ market data + direct NY Fed SOFR.

### REJECT

- company `SP_ENTITY_ID` as permanent security identity: company-level identity does not uniquely encode listed share class/security;
- ticker as identity: mutable/non-permanent and exchange-ambiguous;
- restoring legacy PERMNO as a fallback: entitlement cannot produce the active bytes and compatibility would create two authorities;
- dual CIQ/CRSP identity or return paths: violates the zero-compatibility cut and weakens same-cut scientific authority;
- relabeling `run_2.xlsx` as market/return authority: the export has no Capital IQ Security ID or primary-security return history.

## Source capture frozen this round

`run_2.xlsx` is retained as a current candidate-screen receipt only:

- SHA-256: `f610c43b336142b3366136fa71e1fbae82bf4eac301401ac9ef1d0c0ddbe3e0e`;
- bytes: `71320`;
- observed candidates: `109`;
- receipt: `data/aov0/source_receipts/ciq_screen_run_2_20260807.json`;
- identity status: company-level `SP_ENTITY_ID` present; Capital IQ Security ID missing;
- Rule100 status: PIT quarterly fundamental panel for `factor_positive_count` missing;
- return/technical status: primary-security market history needed for `technical_quality`, AOV primitives, and total returns missing;
- seal status: not admitted as security or return authority.

## Implemented paths

- `research/aov0/contracts.py`: CIQ contract family, authority constants, strict `CIQSEC:` canonicalizer, no PERMNO compatibility.
- `research/aov0/cube.py`: `security_id` primary key and CIQ namespace validation.
- `research/aov0/policy.py`: Rule100 matrix columns normalized to canonical CIQ security IDs.
- `research/aov0/experiment.py`: CIQ-security PIT membership proof.
- `scripts/aov0_first_seal.py`: CIQ decision-cut schema/source receipts/universe binding and CIQ security-ID wide matrices.
- `tests/aov0/*`: CIQ fixtures plus explicit legacy-PERMNO/unnamespaced rejection coverage.
- active product/context/spec/decision/lesson surfaces: synchronized to the source-family recut.

## Acceptance checks

| Check | Result |
|---|---|
| CHK-01 False WRDS premise corrected | PASS — entitlement absence is now explicit; login repair is not the path |
| CHK-02 Single CIQ security identity family | PASS — `CIQSEC:<id>` required; active PERMNO/ticker/company-ID compatibility rejected |
| CHK-03 Single CIQ risky-asset return authority | PASS — S&P Capital IQ Pro primary-security market data only |
| CHK-04 Direct NY Fed cash authority unchanged | PASS |
| CHK-05 Insurance V0 unchanged | PASS — `0.05 / 0.0015` |
| CHK-06 AOV tests | PASS — `29/29` |
| CHK-07 AOV + hardened research selected matrix | PASS — `62/62` (`29` AOV + `33` hardened-research selected tests) |
| CHK-08 ZERO-COMPAT | PASS — all seven counters `0` |
| CHK-09 Compile / JSON / whitespace | PASS — selected compile, current-context JSON + screen-receipt JSON, `git diff --check` |
| CHK-10 Context packet validation | PASS — `scripts/build_context_packet.py --validate` |
| CHK-11 First-seal fail-closed state | PASS — `BLOCKED_MISSING_ADMITTED_INPUTS`, owner decisions empty, clock false, financial evidence `0` |
| CHK-12 Real CIQ Rule100/security/market data admitted | FAIL/BLOCKED — current screen export lacks Capital IQ Security ID, PIT quarterly Rule100 factor inputs, and primary-security market/return bytes |
| CHK-13 Independent Reviewer A/B/C on this new code | NOT RUN/BLOCKED — no qualifying independent A/B/C lane is exposed in this execution channel |

ChecksTotal: 13
ChecksPassed: 11
ChecksFailed: 2

## Findings

| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| Blocking | The active CIQ contract cannot create a real seal from `run_2.xlsx` alone because security-level Capital IQ Security ID, canonical Rule100 V1 quarterly factor inputs, and primary-security market/return history are absent. | Export/obtain the primary CIQ security-master identity, PIT quarterly raw fundamentals sufficient to derive `factor_positive_count`, and same-cut market history sufficient to derive `technical_quality`/AOV primitives/total returns; then build the current AOV Parquets. | Data / Operator | Open |
| Blocking for terminal SAW PASS | Code/tests changed but no qualifying independent Reviewer A/B/C lane is exposed in this execution channel. | Run fresh independent strategy/runtime/data reviews against this exact recut candidate before treating the SAW as PASS. | Review | Open external |
| Advisory | Capital IQ cutoff date is user-configured but not embedded in `run_2.xlsx`. | Keep `run_2` as screen evidence only; bind actual retrieval timestamps/raw hashes on the next CIQ security/master/market-data objects. | Data | Open by design |

## Scope split summary

in-scope complete: destructive active identity/source recut, explicit no-compat CIQ namespace, CIQ first-seal receipt contract, 109-company screen receipt freeze, tests/spec/current-truth synchronization, local mechanical validation.

in-scope blocked: real CIQ Security ID/market-data admission and first prospective seal because the required bytes do not yet exist.

inherited out-of-scope: Episode-2 hosted custody/publication, matured outcomes, AI mutation, broker/live capital. Direct NY Fed SOFR remains governed by the existing after-15:00 ET gate and was not redefined.

## Document Changes Showing

| Path | Change summary | Reviewer status |
|---|---|---|
| `research/aov0/contracts.py` | new CIQ executable contract + strict `CIQSEC:` identity | local tests PASS; independent pending |
| `research/aov0/cube.py`, `policy.py`, `experiment.py` | active AOV identity and PIT membership changed from PERMNO to CIQ Security ID | local tests PASS; independent pending |
| `scripts/aov0_first_seal.py` | CIQ decision-cut schema and CIQ fundamentals/security-master/market-data receipts | local tests PASS; independent pending |
| `tests/aov0/*` | CIQ fixtures, explicit legacy-PERMNO/unnamespaced rejection, and mandatory quarterly-fundamental receipt coverage | `29/29` PASS |
| `data/aov0/source_receipts/ciq_screen_run_2_20260807.json` | immutable metadata receipt for current 109-company screen bytes | JSON PASS |
| active PRD/spec/context/decision/notes/lessons | current authority recut, drift explicitly recorded | context validation PASS |

## Remaining critical path

```text
frozen 109-company CIQ screen
→ obtain primary Capital IQ Security ID per candidate
→ obtain PIT quarterly fundamentals for canonical Rule100 V1 factor states
→ obtain same-cut primary-security market/total-return history from Capital IQ Pro
→ derive factor_positive_count + technical_quality
→ build canonical CIQSEC Rule100 targets + vertical primitives + total_returns
→ after 15:00 ET retrieve direct NY Fed SOFR
→ construct aov0_ciq_decision_cut_v1
→ run scripts/aov0_first_seal.py
→ exact reopen
→ prospective_clock_started = true
→ financial_alpha_evidence = 0
```

## Open Risks:

- Capital IQ subscription capability for primary-security Security ID export, PIT quarterly accounting history, and historical market/total-return fields has not yet been demonstrated by bytes; do not assume those fields are available until the next export is observed.
- `run_2.xlsx` cutoff is user-configured but not embedded in the raw export; its receipt therefore remains screen evidence rather than a standalone historical PIT proof.
- No real same-cut CIQ quarterly-fundamental/security-master/market-data artifact, Rule100 target file, vertical primitive file, total-return file, final SOFR artifact, or decision-cut envelope exists yet.
- Independent Reviewer A/B/C has not reviewed the recut code; local tests are not independent review.

## Next Action:

Do not reopen WRDS/CRSP. In Capital IQ Pro, export the frozen candidate set with primary Capital IQ Security ID, PIT quarterly accounting history sufficient to reproduce the canonical Rule100 V1 factor states, and same-cut primary-security market/total-return history sufficient to derive `technical_quality` and AOV primitives. Once those bytes exist, admit the CIQ source receipts, derive canonical Rule100 targets, materialize the three risky-asset Parquets, retrieve NY Fed SOFR after 15:00 ET, construct `aov0_ciq_decision_cut_v1`, and seal immediately.

ClosurePacket: RoundID=ROUND-20260807-AOV0-CIQ-AUTHORITY-RECUT; ScopeID=AOV0-CIQ-AUTHORITY-V1; ChecksTotal=13; ChecksPassed=11; ChecksFailed=2; Verdict=BLOCK; OpenRisks=real CIQ quarterly-fundamental/security-master/market-data bytes missing and independent Reviewer A/B/C unavailable; NextAction=obtain CIQ Security IDs + PIT quarterly Rule100 inputs + same-cut primary-security market data, then materialize five artifacts and seal after NYFed time gate
ClosureValidation: PASS
SAWBlockValidation: PASS
