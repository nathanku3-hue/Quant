# Low Confidence And Boundaries

## Low Confidence Items For Expert Resolution

1. Expert authority model
Options: expert decides, board vote, or orchestrator reconciliation.
Preferred draft: orchestrator reconciliation with CEO/CTO/COO/Quant lenses.
Question: should any expert role have veto power, and when?

2. Strict boot as baseline gate
Options: require PASS every feature branch, or carry known inherited data-artifact BLOCK unless boot/data is touched.
Preferred draft: carry known inherited BLOCK for research/dashboard slices.
Question: when must strict boot be a hard blocker?

3. Multi-stream sequencing
Options: parallel branches, one sequential integration branch, or hybrid.
Preferred draft: master plan plus stream briefs; parallel only for disjoint write sets.
Question: should Research always stabilize schema/artifact before Frontend/UI?

4. Harness self-update frequency
Options: every SAW, repeated friction only, or manual-only.
Preferred draft: repeated friction or explicit user approval.
Question: what threshold should trigger AGENTS.md or skill updates?

5. File budget enforcement
Options: warning threshold, hard max changed files, or per-stream write allowlist.
Preferred draft: per-stream allowlist plus warning threshold.
Question: what max file churn is acceptable for small/medium/big rounds?

## Out Of Boundary / Need Explicit Human Approval

- live trading
- broker/order execution
- action alerts
- ranking/scoring/recommendations
- BUY/SELL/HOLD or ENTER/EXIT as instructions
- replay-output certification
- provider ingestion during boot
- runtime/boot_status_current.json generation in ordinary feature branches
- large data artifact commit
- backend/data repair outside chosen scope
- broad dashboard copy rewrite
- full repo cleanup
- auto-modifying AGENTS.md after every SAW
- letting expert output override repo truth without orchestrator reconciliation
