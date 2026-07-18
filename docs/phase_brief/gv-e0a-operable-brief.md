# Phase Brief: GV-E0A-OPERABLE — Single Decision Operable Vertical

Mode: `EXECUTION_PACKET`
Status: `AUTHORIZED_ACTIVE_GATE; CODE_NOT_CLAIMED_COMPLETE`
Date: 2026-07-19
RoundID: `ROUND-20260719-E0A-OPERABLE-DIRECTION`
ScopeID: `GV_E0A_OPERABLE_VERTICAL`
Hierarchy: L1 Terminal Zero; L2 active Backend product accounting + Frontend read-only presentation + Docs/Ops canon; L2 held Data admission / PEAD / FS1 / broker
Authority:
- `docs/architecture/top_level_roadmap.md` (hard-recut; sole active gate)
- `docs/architecture/gv_fs0_certification_and_data_authority_contract.md` (frozen certification contract)
- `docs/architecture/godview_portfolio_first_operating_model.md`
- `docs/architecture/godview_e0/*` (frozen research custody; byte-identical)
- F1C-SHIP closed substrate on product tip lineage `490a234`

## Decision (locked A/A/A/A)

```text
PRODUCT_PIVOT = AUTHORIZED (UOE discretionary cockpit → GodView certified portfolio OS)
F1C_SHIP = CLOSED_SUBSTRATE
ACTIVE_GATE = GV-E0A-OPERABLE
SHIPPED_PRODUCT_SCORE = 39/100 (owner claim ceiling; metric confidence low; no alpha)
FUNCTIONAL_STAGE = CERTIFIED_STATIC_BRANCH_DEMO
  (→ CERTIFIED_SINGLE_DECISION_OPERABLE only with operable evidence)
NEXT = frozen E0 custody → HOLD_FOR_EVIDENCE/NO_POSITION → one DecisionEnvelope
       → book/cert → atomic current publication → one visible decision → Streamlit smoke
FORBIDDEN = providers, real prices, FS1 batch, PEAD, alpha claims, broker,
            compatibility dual-authority UI, historical-suite repair
```

## Objective

Ship one **combined vertical** that turns frozen MU `G_supply` research custody into one operator-visible **current** certified paper decision. This is not dual-fixture F1C demo re-shipment and not broad FS1.

## Vertical definition

```text
frozen MU G_supply evidence (4 files exact hashes)
→ explicit HOLD_FOR_EVIDENCE research decision / portfolio NO_POSITION
→ one active DecisionEnvelope
→ PortfolioBook + independent certification
→ atomic publication of current decision
→ one visible current decision
→ real Streamlit smoke
```

## Frozen E0 custody (must remain byte-identical)

```text
docs/architecture/godview_e0/e0_preregistration.yaml
  sha256 0a6dc18a44d7532610a73f90b92477fc7bd36644c1a052d81a48162097176618
docs/architecture/godview_e0/evidence_authority_matrix.csv
  sha256 3306adbed26d27732a0a53d3819a09044e418e183ecc58ebebf82c6f9fe0dcb0
docs/architecture/godview_e0/e0_model_spec.md
  sha256 28a0ea062777d9364008480266ce933bd6a34348ce0defcac7185398068a38f0
docs/architecture/godview_e0/e0_acceptance_tests.md
  sha256 9d9a7f195bd8db2caea82859d6a73d951c862f229fc9d72e5302c58ba7b8d55c
```

Hash drift → hard BLOCK. E0A does not rewrite research claim authority or invent alpha.

## Acceptance checks

1. Custody: four E0 files match exact hashes above.
2. Research decision: explicit `HOLD_FOR_EVIDENCE` (or equivalent sealed hold) derived from frozen custody without provider/real prices.
3. Portfolio action: paper `NO_POSITION` (or explicit paper hold) via one `DecisionEnvelope`.
4. Book + cert: `PortfolioBook` path + independent certification PASS for that single decision.
5. Publication: atomic publication of **current** decision authority (not dual-fixture F1C bundle as the operator endpoint).
6. Visibility: one visible current decision on the product surface.
7. Smoke: real Streamlit smoke evidence (not headless-only as sole proof).
8. Score/stage: score remains **39/100**; stage may become `CERTIFIED_SINGLE_DECISION_OPERABLE` only if 1–7 pass on branch evidence.
9. Forbidden scope zero: no providers, real prices, FS1 batch, PEAD, alpha claims, broker, dual-authority UI, historical-suite repair.

## Non-goals / forbidden

- Reopening F1C-SHIP or sequential F1C/F1D as active gates
- Broad FS1 (policy/benchmark batch paths)
- Provider reads, real market prices, WRDS/PEAD reopen
- Broker/order/live capital paths
- Compatibility layers that restore dual portfolio authorities in UI
- Historical full-suite repair campaigns
- Score uplift to 40+ without rubric-based owner claim
- Alpha / readiness / tradability promotion

## Substrate dependency (closed)

F1A/F1B/F1C-SHIP on product tip lineage `490a234` supply certified dual-fixture demo machinery, permanent bundle publication patterns, and default Certified Portfolio route. E0A reuses certification contracts; it does not claim those dual fixtures are the operable single-decision product.

## Implementation status discipline

- Docs/Ops may lock direction without claiming code complete.
- Backend/Frontend implementer owns code/tests/smoke.
- Until operable evidence exists on branch: `FUNCTIONAL_STAGE = CERTIFIED_STATIC_BRANCH_DEMO`.
- Do not claim `main` is at product tip if product lineage is branch-based; product tip lineage is `490a234` unless superseded by a later banked product tip.

## Streams

| Stream | Role |
|---|---|
| Backend | DecisionEnvelope → book → cert → atomic current publication |
| Frontend/UI | One visible current decision; Streamlit smoke; no dual-authority fallback |
| Data | Held — no provider/real admission |
| Docs/Ops | Canon, truth surfaces, decision log, lessons; no code modules |

## Done when

- Acceptance checks 1–9 have evidence paths and pass/fail recorded
- Independent Reviewer A/B/C and SAW on the implementation commit (when code ships)
- Truth surfaces state sole active gate closed or remaining blockers only for E0A
- Score still 39/100 unless separate owner rubric decision

## Next after E0A (not in this packet)

Future only: GV-FS1 policy/benchmark paths, then later FS2 / RA0 / P1 per roadmap. Not concurrent with E0A.
