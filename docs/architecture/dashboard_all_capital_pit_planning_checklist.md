# GodView All-Capital PIT Planning-Round Checklist

Status: `ACTIVE PLANNING RECONCILIATION`
Date: 2026-08-03
Active gate: `GV-DASHBOARD-ALL-CAPITAL-PIT-1`
Canonical contract: `docs/architecture/dashboard_all_capital_pit_contract.md`

## Status legend

- `[x] DOC-LOCKED` — adopted by active documentation and mandatory for implementation.
- `[ ] EXECUTION` — not implemented or verified yet.
- `[~] DEFERRED` — intentionally outside the immediate slice.
- `[!] VERIFY` — repository or runtime fact must be proven before implementation relies on it.

This checklist reconciles every material correction raised during the planning round. A later implementation brief may narrow file ownership, but it may not silently weaken these decisions.

## A. Product unit and endgame

- [x] DOC-LOCKED — GodView is one portfolio-wide point-in-time capital decision loop, not a collection of independent approval pages.
- [x] DOC-LOCKED — MU is the first real evidence case; it is not the pipeline data model or workflow unit.
- [x] DOC-LOCKED — The episode ingests `CapitalProposal[0..N]` under one certified PIT identity.
- [x] DOC-LOCKED — Zero proposals and reject-all/no-action are first-class outcomes.
- [x] DOC-LOCKED — The real operator question is: given the certified book and every eligible proposal at this PIT, what capital transition, if any, should be staged?
- [x] DOC-LOCKED — Accepted score remains `62/100`; architecture, documentation, and refactoring do not earn uplift.
- [x] DOC-LOCKED — Architecture protects and exposes portfolio alpha by reducing structural leakage; architecture is not itself an empirically proven alpha signal.
- [x] DOC-LOCKED — Limited Live, client assets, advice activity, broker execution, and autonomous submission remain closed.

## B. Visible product surface

- [x] DOC-LOCKED — `dashboard.py` remains the sole future GodView application.
- [x] DOC-LOCKED — Six visible pages are frozen in this order:
  1. Command Center
  2. Discovery & Analysis
  3. Decisions & Thesis
  4. Portfolio & Rotation
  5. Strategy Modules
  6. Operations & Replay
- [x] DOC-LOCKED — Command Center is the default route.
- [x] DOC-LOCKED — Pages are read projections over one decision loop; page boundaries are not business-authority boundaries.
- [x] DOC-LOCKED — Discovery & Analysis remains a first-class functional surface.
- [x] DOC-LOCKED — Full operational diagnostics move to Operations & Replay; Command Center shows compact health only.
- [x] DOC-LOCKED — Existing strategy/replay/optimizer outputs are visibly non-authoritative until adapted into the proposal boundary.
- [x] DOC-LOCKED — The stale single `NO_POSITION` ticket becomes decision history, not the default product action.

## C. Authority separation

- [x] DOC-LOCKED — Strategy modules emit immutable evidence-bound proposals only.
- [x] DOC-LOCKED — Strategy modules do not own lifecycle state, cross-proposal comparison, portfolio preview, confirmation, book mutation, or certification.
- [x] DOC-LOCKED — Decision consensus owns proposal admission, eligibility, identity rejection, disagreement, and later selection semantics.
- [x] DOC-LOCKED — Decision consensus owns no cost, margin, liquidity, covariance, sizing, execution, or certification math.
- [x] DOC-LOCKED — Portfolio authority owns target resolution, cost/risk/limit calculation, preview, stale validation, authorization, application, certification, and replay.
- [x] DOC-LOCKED — The dashboard consumes read models and emits typed commands; it does not calculate strategy signals or mutate canonical authority.
- [x] DOC-LOCKED — UI session state may hold ephemeral widget state only; it cannot be portfolio, proposal, episode, preview, authorization, or certification authority.

## D. Canonical PIT identity

- [x] DOC-LOCKED — Use one immutable `PointInTimeIdentity` embedded unchanged in proposals and episodes.
- [x] DOC-LOCKED — It contains exactly:
  - `certified_book_id`
  - `certified_book_head_event_id`
  - `evidence_set_id`
  - `market_snapshot_id`
  - `as_of_utc`
- [x] DOC-LOCKED — `certified_book_head_event_id` is the final authoritative event in the exact prefix certified by the active certification; it is not merely `events[-1]`.
- [x] DOC-LOCKED — `as_of_utc` is that certified head event's timestamp; wall-clock `now()` and later observation/rejection/UI/certification markers do not open authoritative episodes.
- [x] DOC-LOCKED — Identity comparison is one exact equality assertion; partial warning-based compatibility is forbidden.
- [x] DOC-LOCKED — Mismatch is ineligible and represented by an immutable rejection event.
- [x] DOC-LOCKED — The current cash-only episode uses a typed proof-carrying `NoMarketDependencyCashOnlyV1`, not a fabricated conventional market snapshot.
- [x] DOC-LOCKED — The proof object binds kind, certified book ID, certified head event ID, certified book hash, and validation digest.
- [x] DOC-LOCKED — Admission requires empty positions/orders/fills, zero unexplained residual, zero proposal target quantities, and no notional/weight conversion, price consumption, yield, or market-derived return claim.
- [x] DOC-LOCKED — Existing `reference_price = "1"` is not an admitted market observation and cannot be consumed by Slice 1 adapters.
- [ ] EXECUTION — Map the certified prefix head and construct the no-market proof from the verified active workspace; reject it if any predicate fails.

## E. Immutable proposal and evidence contract

- [x] DOC-LOCKED — `CapitalProposal` is immutable strategy evidence with no lifecycle fields.
- [x] DOC-LOCKED — Use a typed `ProposalOutcome` rather than an unrestricted string.
- [x] DOC-LOCKED — Supporting and contradicting evidence use `EvidenceReference` objects with evidence ID, SHA-256 digest, and source identity.
- [x] DOC-LOCKED — Proposal evidence preserves principal claim, missing discriminator, falsifiers/boundaries, and reason not to act.
- [x] DOC-LOCKED — Evidence artifact digest, extension schema digest, and extension canonical-payload digest are three distinct identities.
- [x] DOC-LOCKED — `schema_digest` hashes the canonical schema definition, not source payload bytes.
- [x] DOC-LOCKED — `canonical_payload_digest` hashes canonical serialized extension payload bytes.
- [x] DOC-LOCKED — `EvidenceReference.sha256_digest` hashes the referenced upstream evidence artifact.
- [ ] EXECUTION — Define the canonical serialization and domain-separated digest rules before any proposal is persisted or replayed.

## F. Strict extension typing

- [x] DOC-LOCKED — `Mapping[str, object]`, `Mapping[str, Any]`, key-presence validation, and untyped module detail dictionaries are forbidden in the canonical contract layer.
- [x] DOC-LOCKED — Use a discriminated union of complete envelope types; schema ID and payload type cannot be paired independently.
- [x] DOC-LOCKED — Initial schemas may include `EQUITY_FUNDAMENTAL_V1` and `CASH_BASELINE_V1`; CTA schema is a future seam, not Slice 1 CTA implementation.
- [x] DOC-LOCKED — Every envelope binds `schema_id`, `schema_version`, `schema_digest`, `canonical_payload_digest`, and its typed payload.
- [x] DOC-LOCKED — Unknown schemas, unexpected fields, mismatched payload type, schema drift, and post-open mutation fail closed.
- [~] DEFERRED — A registry/plugin mechanism may replace a closed union when independent modules require it; the registry must be frozen per episode/process and cannot mutate through import side effects.

## G. Target intent, unit, and normalization

- [x] DOC-LOCKED — Target intent is distinct from unit type.
- [x] DOC-LOCKED — Intent vocabulary is `TARGET_FINAL`, `DELTA`, and `OVERLAY`.
- [x] DOC-LOCKED — Instrument unit vocabulary is initially `QUANTITY`, `NOTIONAL`, and `WEIGHT` only.
- [x] DOC-LOCKED — `RISK_BPS` is not an instrument unit and is not generically converted to notional.
- [x] DOC-LOCKED — `RiskTarget` separates measure from unit:
  - measure: `VAR`, `VOL`, `GROSS`, `MARGIN`, `DELTA`
  - unit: `BPS`, `PERCENT`, `USD`, `NOTIONAL`
- [x] DOC-LOCKED — Canonical prices, quantities, notionals, and target values use `Decimal` or exact integer minor units; authoritative bps fields use integers.
- [x] DOC-LOCKED — Analytics-only z-scores and ratios may remain floats when excluded from canonical economic hashing/authority.
- [x] DOC-LOCKED — Every instrument target has an explicit `NumericNormalizationPolicy`.
- [x] DOC-LOCKED — The policy binds unit quantum, rounding mode, currency, price identity, contract multiplier, and lot-size policy.
- [x] DOC-LOCKED — No blanket defaults silently assume USD, multiplier 1, canonical close, or fractional lots across every asset class.
- [x] DOC-LOCKED — Contract multiplier has one canonical home in target normalization, not both normalization and CTA diagnostics.
- [ ] EXECUTION — Define valid conditional omissions: for example, a pure weight target may not require the same price identity at proposal-ingestion time, but authority must require all conversion inputs before preview.

## H. Composition semantics

- [x] DOC-LOCKED — Never sum absolute final targets by subtracting the current book once per selected proposal.
- [x] DOC-LOCKED — Initial transition grammar permits zero or one base `TARGET_FINAL` proposal plus zero or more compatible `DELTA`/`OVERLAY` legs.
- [x] DOC-LOCKED — Multiple selected base targets are a conflict until explicit arbitration chooses one or creates a new operator-owned target.
- [x] DOC-LOCKED — Valid outcomes include reject all, select one base, base plus compatible overlays, and partial acceptance of explicit target legs.
- [x] DOC-LOCKED — Selection is not necessarily winner-take-all.
- [~] DEFERRED — Target selection and composition belong to Slice 2, not the read-only Slice 1 transaction.
- [~] DEFERRED — Joint optimization scalars are challenger research until calibrated and explicitly authorized; they are not canonical selection truth.

## I. Governance command authority

- [x] DOC-LOCKED — Adapters do not decide which authoritative event to emit.
- [x] DOC-LOCKED — The dashboard does not decide event acceptance or identity rejection.
- [x] DOC-LOCKED — A typed command such as `SubmitProposalCommand` enters a governance command handler.
- [x] DOC-LOCKED — The handler validates the exact five-field PIT identity before proposal acceptance.
- [x] DOC-LOCKED — The handler emits accepted or rejected facts; the projector performs no validation or decision-making.
- [x] DOC-LOCKED — Natural event sequence is submission containing the full proposal, followed by accepted or identity-rejected disposition.
- [x] DOC-LOCKED — A rejection must retain enough immutable proposal information to project a rejected row without fabricating `None`.
- [ ] EXECUTION — Freeze the exact command/event naming after inspecting the existing event conventions in `gv_portfolio_v0`; names may change, authority semantics may not.

## J. Ordered append-only event authority

- [x] DOC-LOCKED — Event classes alone are insufficient; use an ordered event envelope and append/read protocol.
- [x] DOC-LOCKED — Minimum event-envelope identity:
  - `stream_id`
  - `sequence_number`
  - `event_id`
  - `event_schema_version`
  - `timestamp_utc`
  - `correlation_id`
  - `causation_id`
  - `previous_event_digest`
  - `event_digest`
- [x] DOC-LOCKED — Event digest uses canonical bytes and domain separation.
- [x] DOC-LOCKED — Append rejects duplicate event IDs, duplicate sequence positions, sequence gaps, previous-digest mismatch, and conflicting replay.
- [x] DOC-LOCKED — Read returns canonical sequence order.
- [x] DOC-LOCKED — Slice 1 uses a bounded deterministic digest-chained in-memory stream sourced from existing immutable artifacts.
- [x] DOC-LOCKED — Slice 1 creates no durable governance persistence and no second authority path.
- [x] DOC-LOCKED — Durable governance storage is deferred until Slice 2 operator selections must survive restart.

## K. Event-derived read projections

- [x] DOC-LOCKED — `ProposalRecordReadModel` and `DecisionEpisodeReadModel` are projections, not supreme mutable records.
- [x] DOC-LOCKED — Slice 1 status vocabulary is restricted to states backed by Slice 1 events: `ELIGIBLE` and `REJECTED_IDENTITY_MISMATCH`.
- [x] DOC-LOCKED — Slice 1 episode status is `OPEN` or `ABORTED` only.
- [x] DOC-LOCKED — Slice 1 contains no staged state, no selected record IDs beyond the required empty tuple, and no authorization semantics.
- [x] DOC-LOCKED — The projector is a pure deterministic fold over valid events.
- [x] DOC-LOCKED — Proposal rows use a declared canonical ordering, initially event sequence then record ID.
- [x] DOC-LOCKED — Equivalent event streams must produce byte-identical read models.
- [x] DOC-LOCKED — The projector cannot synthesize a missing proposal, consult wall-clock time, call providers, mutate storage, or emit events.

## L. Verified production adapters

- [x] DOC-LOCKED — Production Command Center rows must come from real active objects/artifacts; static dummy dictionaries are forbidden.
- [x] DOC-LOCKED — Test fixtures remain allowed in unit tests and isolated boundary tests.
- [x] DOC-LOCKED — Repository inspection confirms `views/command_center.py` does not yet exist and is a new file.
- [x] DOC-LOCKED — Repository inspection confirms the current operated source is the prospective workspace/object path in `gv_portfolio_v0/prospective.py` and `views/gv_prospective_paper_workspace.py`.
- [x] DOC-LOCKED — Repository inspection confirms the independent shadow source is `core/gv_v2_mu_nvda_shadow_decision.py`.
- [x] DOC-LOCKED — No new JSON/Parquet serialization path may be invented merely to satisfy the adapter contract.
- [x] DOC-LOCKED — Cash baseline is derived from the certified workspace/book cash balance, not assumed to be an external standalone artifact.
- [x] DOC-LOCKED — Cash yield/collateral rate must come from an identified admitted source; absent that source, yield is explicitly unavailable rather than fabricated.
- [ ] EXECUTION — Inspect and freeze exact source-field mappings, hash identities, and missing-value behavior before writing adapter code.
- [ ] EXECUTION — Confirm whether MU operated should adapt the current review/proposal, current authoritative decision snapshot, or a distinct immutable historical artifact; do not silently mix lifecycle layers.

## M. Dashboard and session-state boundary

- [x] DOC-LOCKED — Command Center receives a projected `DecisionEpisodeReadModel` through an explicit composition root.
- [x] DOC-LOCKED — Production UI contains zero fabricated proposal rows.
- [x] DOC-LOCKED — Streamlit session state remains available for ephemeral controls such as selected tab, pagination, expansion, or sort state.
- [x] DOC-LOCKED — Raw session-state reads of certified book, active proposals, episode, preview, authorization, or certification authority are violations.
- [x] DOC-LOCKED — AST verification targets authority-key access, not every `st.session_state` use globally.
- [x] DOC-LOCKED — The AppTest may isolate storage, clock, and Streamlit boundaries while still using real production adapters; “unmocked” does not mean uncontrolled production state.

## N. Preview, authorization, application, and certification

- [x] DOC-LOCKED — `TransitionPreview` is calculation-only and has zero execution authority.
- [x] DOC-LOCKED — Preview binds candidate, episode, certified book/head, as-of, expiry, risk/cost results, and digest.
- [x] DOC-LOCKED — Authorization binds exact preview ID/digest, episode, current book/head, operator, and expiry.
- [x] DOC-LOCKED — Changed, expired, blocked, or stale previews cannot authorize.
- [x] DOC-LOCKED — Operator authorization emits an authorization event.
- [x] DOC-LOCKED — Applying a transition and certifying the resulting book are distinct events unless a separately approved product definition treats certified book state as an authorized target rather than executed holdings.
- [~] DEFERRED — Preview, authorization, application, certification, and exact authority replay belong to Slice 3.

## O. Risk engine

- [x] DOC-LOCKED — No VaR or Sortino implementation is required to ship Slice 1.
- [x] DOC-LOCKED — Risk math cannot delay the identity/event/read-model product slice.
- [x] DOC-LOCKED — Future risk output is multi-model and visibly disagrees when models differ.
- [~] DEFERRED — Historical simulation may be the primary estimate, delta-normal a diagnostic control, with deterministic stress scenarios, concentration, liquidity, and model-disagreement outputs.
- [~] DEFERRED — No single VaR estimator becomes allocation truth.
- [~] DEFERRED — Joint portfolio optimization remains a research challenger until return calibration, downside/covariance policy, constraints, and prospective evidence are explicit.

## P. Deletion and migration

- [x] DOC-LOCKED — No physical deletion occurs in Slice 1.
- [x] DOC-LOCKED — Refactoring success is measured by one authority path and lower ambiguity, not arbitrary line-count reduction.
- [x] DOC-LOCKED — `operated_portfolio_app.py` is the verified standalone application path; the previously named `operated_app.py` was incorrect.
- [x] DOC-LOCKED — Legacy view filenames are not deletion authority until repository existence and dependencies are verified.
- [x] DOC-LOCKED — Deletion requires AST/import reference proof, behavior parity, and regression evidence.
- [x] DOC-LOCKED — Session-state authority cleanup targets canonical authority reads, not ephemeral UI state.
- [~] DEFERRED — Standalone entrypoint and displaced-view deletion occurs after the dashboard path owns the complete operated behavior.

## Q. Sequencing and velocity

- [x] DOC-LOCKED — The original all-in-one Slice 1 was rejected as a coupled failure surface.
- [x] DOC-LOCKED — Work is layer-first but remains one functional product transaction; layers are acceptance dependencies, not independent architecture milestones.
- [x] DOC-LOCKED — Slice 0 is one focused baseline commit, not a release or tag ceremony.
- [x] DOC-LOCKED — No Git tag is created for the temporary pre-refactor baseline.
- [x] DOC-LOCKED — Slice 1 stops at real adapters, command/identity authority, ordered events, pure projections, six-page shell, and read-only Command Center.
- [x] DOC-LOCKED — Slice 2 adds selection and intent-aware target resolution, not risk/preview mutation.
- [x] DOC-LOCKED — Slice 3 adds risk/cost preview, stale-bound confirmation, application, certification, and replay.
- [x] DOC-LOCKED — CTA/macro/provider/live work cannot enter the critical path.
- [x] DOC-LOCKED — No further broad architecture round precedes execution; only repository-grounded field and file reconciliation is allowed.

## R. Slice 0 exact baseline scope

- [x] EXECUTION — Focused same-evidence and real-MU tests passed under Python 3.12.10 / pytest 9.1.0.
- [x] EXECUTION — Committed exactly:
  - `gv_portfolio_v0/prospective.py`
  - `views/gv_prospective_paper_workspace.py`
  - `tests/gv_portfolio_v0/test_real_evidence_mu.py`
  - `core/gv_v2_mu_nvda_shadow_decision.py`
  - `tests/gv_portfolio_v0/test_same_evidence_shadow.py`
- [x] EXECUTION — Excluded all documentation changes and unrelated paths from baseline commit `a520f475bfa4fca42a68a22165ab3ad8960c0bc9`.
- [x] EXECUTION — No tag and no push were created.
- [ ] EXECUTION — Regenerate context and bank this planning authority as a separate docs-only commit.
- [ ] EXECUTION — Require a fully clean worktree before Slice 1 implementation begins; do not carry uncommitted planning docs into the code slice.

## S. Slice 1 expected bill of materials

The exact compact ten-file scope is locked:

### Core transaction

- [ ] EXECUTION — `core/gv_pit/__init__.py`
- [ ] EXECUTION — `core/gv_pit/contracts.py`
- [ ] EXECUTION — `core/gv_pit/adapters.py`
- [ ] EXECUTION — `core/gv_pit/governance.py`
- [ ] EXECUTION — `core/gv_pit/read_models.py`

### Product surface

- [ ] EXECUTION — add `views/command_center.py`
- [ ] EXECUTION — modify `views/page_registry.py`
- [ ] EXECUTION — modify `dashboard.py`

### Verification

- [ ] EXECUTION — modify `tests/test_dash_1_page_registry_shell.py`
- [ ] EXECUTION — add `tests/test_gv_pit_transaction.py`

- [ ] EXECUTION — focused contract/digest/normalization tests
- [ ] EXECUTION — command-handler five-field identity tests
- [ ] EXECUTION — event ordering, duplicate/gap, and digest-chain tests
- [ ] EXECUTION — projector replay and canonical-ordering tests
- [ ] EXECUTION — real-adapter mapping tests
- [ ] EXECUTION — six-page registry tests
- [ ] EXECUTION — Command Center Streamlit AppTest using real adapters and isolated boundaries
- [ ] EXECUTION — AST authority-session-state test
- [ ] EXECUTION — mutation/optimization/deletion absence assertions

Do not treat every listed file as an independently bankable framework. Slice 1 is accepted only when the complete real read-only PIT episode renders through `dashboard.py`.

## T. Immediate next-round stop rules

- [x] RESOLVED — Approved executable proven as `C:\Users\Lenovo\AppData\Local\Programs\Python\Python312\python.exe`; Python 3.12.10 and pytest 9.1.0.
- [x] RESOLVED — Focused baseline tests passed and the exact five files were isolated in commit `a520f475bfa4fca42a68a22165ab3ad8960c0bc9`.
- [x] DOC-LOCKED — Stop and report the exact mismatch if the real MU operated/shadow sources cannot bind one five-field identity without inventing data.
- [x] DOC-LOCKED — Stop if cash yield or market identity would need to be fabricated.
- [x] DOC-LOCKED — Stop if event ordering requires a competing persistence authority rather than an adapter to existing custody.
- [x] DOC-LOCKED — Stop Slice 1 before selection, optimization, preview, book mutation, risk math, certification, or deletion.
