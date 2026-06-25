# V2 PEAD Read-Only Evidence Dashboard

Mode: `EXECUTION_PACKET`
Status: `DONE`
Date: 2026-06-20
RoundID: `ROUND-20260620-V2-PEAD-READ-ONLY-EVIDENCE-DASHBOARD`
ScopeID: `V2_PEAD_READ_ONLY_EVIDENCE_DASHBOARD`
Owner: Frontend/UI + Strategy + Docs/Ops

Hierarchy: L1 Terminal Zero quantitative research console; L2 active streams Frontend/UI, Strategy, and Docs/Ops; L2 Data is locked read-only input; L3 D4 read-only evidence dashboard.

## Objective

Expose the locked PEAD validation JSON in Strategy Research Replay as a compact
read-only evidence dashboard for owner review, with integrity and interpretation
boundaries visible at the point of use.

## Authorized scope

- Read only `docs/context/e2e_evidence/pead_real_data_validation_20260620.json`.
- Require SHA256 `96cdc975d0b4798c6775b12e7bc9dc6af4fb7e9178a4d0ad54feeab8100e980e`.
- Render artifact/hash state, D1/D2B/D3 lineage, approved counts, daily HAC-null
  and quarterly descriptive-only warnings, and the four locked limitations.
- Add the panel to Strategy Research Replay through the existing view composer.
- Fail closed before evidence metrics when the file, hash, schema, or limitations
  contract is invalid.

## Forbidden scope

- No PEAD recomputation, formula change, provider access, Parquet read, or data
  artifact mutation.
- No alpha interpretation or proof, strategy promotion, ranking/scoring, alerts,
  recommendations, broker/order paths, staging, or commit.
- No dashboard architecture refactor.

## Acceptance criteria

- [x] Production loader/renderer exists at `views/pead_validation_evidence.py`.
- [x] Strategy Research Replay exposes `Read-Only Evidence` additively.
- [x] Exact title and review-only warning render.
- [x] Missing JSON, hash mismatch, schema mismatch, and unreadable limitations fail closed.
- [x] Locked counts, lineage, HAC-null warning, quarterly warning, and limitations render.
- [x] Promotional/action language is absent in positive form while the negative disclaimer remains.
- [x] Reader source contains no provider, Parquet, or PEAD recomputation path.
- [x] Streamlit surface execution and focused locked-artifact regression pass.
- [x] Independent Reviewer A/B/C pass with no remaining findings.
- [x] Closure, SE evidence, SAW block, and context validators pass.

## Rollback

Remove the optional evidence renderer argument from `views/strategy_view.py`, its
import/wiring in `dashboard.py`, and `views/pead_validation_evidence.py`. The
existing Strategy Matrix and Backtest Lab paths remain unchanged.
