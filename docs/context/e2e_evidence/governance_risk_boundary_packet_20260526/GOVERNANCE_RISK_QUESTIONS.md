# Governance / Risk Expert Questions

GitHub repo: https://github.com/nathanku3-hue/Quant
GitHub branch: https://github.com/nathanku3-hue/Quant/tree/codex/optimizer-core-structured-diagnostics
Commit: https://github.com/nathanku3-hue/Quant/commit/cec79312e091107e9a4bbd14ba855c59f2ca5a75

Local packet caveat: local HEAD matches the GitHub branch commit above, but this packet includes uncommitted local current-truth context. Please distinguish clean GitHub baseline from local reboot truth.

## Mission

Review Terminal Zero as a local-first quantitative research console and decide what governance/risk boundaries must exist before it can be called boot-ready.

The focus is labels, recommendations, scoring, ranking, alerts, broker/trading boundaries, and UI language. We need practical pass/fail rules that can plug into boot preflight and dashboard tests.

## High-Value Real Questions

1. Which current labels create investment-advice risk?
   - Review terms such as `BUY`, `SELL`, `HOLD`, `ENTER`, `EXIT`, `STRONG BUY`, `WATCH`, `allocation`, `portfolio`, `optimizer`, `latest buys/sells`, and `current holdings`.
   - Which labels are acceptable for internal replay audit only?
   - Which labels must be renamed in UI-facing contexts?

2. What is the permitted state taxonomy?
   - What exact difference should exist between `discovery intake`, `candidate card`, `signal card`, `research-only`, `validated strategy`, `allocation evidence`, and `actionable instruction`?
   - Which state transitions must be impossible without explicit approval?

3. What dashboard language must be forbidden?
   - Which UI text could imply recommendation, ranking, scoring, trade timing, suitability, or personalized advice?
   - Which current dashboard sections need stronger "research-only" or "replay-only" labels?

4. How should replay trade labels be governed?
   - Are `ENTER` / `EXIT` safer than `BUY` / `SELL`, or do both require an audit-only qualifier?
   - Should replay lifecycle events be displayed as "historical simulation events" rather than trade language?
   - What tests should prove replay labels cannot trigger alerts, orders, rankings, or recommendations?

5. How should portfolio and optimizer output be described?
   - Is `Portfolio & Allocation` acceptable, or should it be qualified as `Research Portfolio` / `Replay Allocation` / `Simulation Allocation`?
   - Can optimizer weights be shown without being advice?
   - What labels distinguish optimized output, replay output, cash-closed fallback, and unavailable state?

6. What scoring and ranking boundary is required?
   - Which fields are forbidden in candidate cards and dashboard views until validation exists?
   - Are factor scores, ranks, confidence labels, color bands, or sorted lists inherently risky?
   - What would be the minimum governance gate before any score or rank is allowed?

7. What alert and broker boundaries are required?
   - Which files or modules should be reviewed for latent alert/order pathways?
   - Should boot preflight verify that alert, broker, escalation, and execution paths are disabled by default?
   - What exact condition must be met before any alert-like output is allowed?

8. What disclaimers are necessary but not sufficient?
   - What disclaimer belongs in the app shell, candidate-card view, optimizer/replay view, and exported artifacts?
   - Which risks cannot be solved by disclaimers and instead require hard gates or renamed labels?

9. What audit trail is required for governance readiness?
   - What fields must be present in every research object: origin, source, status, validation state, actionability flag, prohibited uses, owner, timestamp, manifest hash?
   - Which artifacts must be hash-bound before they can appear in a dashboard?

10. What should boot preflight check for governance?
    - Should boot fail on forbidden terms in UI-visible strings?
    - Should boot fail on candidate cards with scores, ranks, action states, alerts, broker flags, or missing governance fields?
    - Should boot fail when local dirty UI files contain unreviewed action-language changes?

11. What is the highest-risk current ambiguity?
    - Candidate cards not actionable but dashboard rows using action-shaped labels?
    - Replay events using BUY/SELL language?
    - Optimizer weights looking like personalized allocation advice?
    - Alerts/escalation modules existing in the codebase?
    - Local uncommitted truth diverging from GitHub?

12. What is the minimum Governance Gate v0?
    - Please define 5-10 machine-checkable rules that must pass before the project can be called boot-ready.
    - Include exact examples of allowed language and forbidden language.

## Desired Expert Output

- One governance taxonomy for object states and UI labels.
- One list of forbidden terms or term/context combinations.
- One required disclaimer and one list of hard gates that disclaimers cannot replace.
- One alert/broker/trading boundary policy.
- One boot-preflight governance checklist.
- One first implementation slice with exact files to touch and tests to add.

## Suggested First Slice To Review

Governance Gate v0 should probably touch only:

- `scripts/boot_preflight.py` or its planned governance subcheck.
- `tests/test_boot_preflight.py` or a new governance-boundary test.
- `opportunity_engine/candidate_card_schema.py`.
- `tests/test_g8_2_system_scouted_candidate_card.py`.
- `views/page_registry.py` / `dashboard.py` only if a shell-level disclaimer or label guard is required.
- `docs/architecture/governance_boundary_policy.md`.

Please do not recommend enabling ranking, scoring, alerts, broker actions, provider ingestion, live trading, autonomous allocation, or dashboard recommendation language as part of this review.
