# MULTI_EXPERT_RECONCILED_VERDICT_20260602

Final Verdict:
ADVISORY_PASS / PATCH_RESOLVED. Multi-expert review accepts V2-D0 as an offline contract substrate after Backend contract hardening, but it does not authorize a WRDS probe, snapshot generation, dashboard reader, data write, SQLite store, ranking/scoring, recommendations, alerts, broker/order paths, SafeBoot, or BootReady.

Approved Next Stream:
V2-D0.1_WRDS_PERMISSION_TRUTH_AUTHORIZATION. Collect explicit non-secret WRDS entitlement evidence and approval text before any read-only permission probe can be opened.

Rejected/Deferred Streams:
- WRDS read-only permission probe: deferred until exact user/source entitlement evidence exists.
- PIT snapshot builder/generation: deferred until separate storage, manifest, extraction log, validation, and rollback approval.
- Dashboard reader: HOLD; status-only static reader remains a separate approval lane.
- PEAD Variant Factory, Corporate Actions Edge Lab, Meta-labeling, Orbis/BvD, LLM agents, DRL allocator, and live routing: deferred until WRDS/PIT/provenance authority is established.
- SQLite candidate registry/store: blocked without explicit approval.

Expert A Summary:
PASS on Data / WRDS / Provenance boundary. Probe authorization is NEEDS USER EVIDENCE. Required evidence includes WRDS account/license owner, approved account scope, exact library.table permissions, license/access constraints, date/as-of coverage, approval_ref per approved row, and explicit "read-only permission probe only; no snapshot/data output" approval.

Expert B Summary:
PATCH on Backend / Contracts / Tests. The V2-D0 contract was safe as contract-only, but `validate_wrds_permission_probe_contract(...)` needed exact-key drift rejection and `planned_storage_uri` dataclass validation needed schema parity. Patch applied in `v2_discovery/data_lab/wrds_probe.py`, `v2_discovery/data_lab/snapshot_manifest.py`, `tests/test_v2_wrds_permission_matrix.py`, and `tests/test_v2_snapshot_manifest_contract.py`; focused V2-D0 suite now passes with 20 tests.

Expert C Summary:
PASS on Strategy / Product Boundary / Governance. G9 remains context-only, dashboard reader remains HOLD, V2-D0 remains the correct main stream before PEAD variants, and packet/live truth surfaces do not imply ranking, scoring, recommendations, alerts, broker/order paths, dashboard runtime integration, promotion readiness, SafeBoot, or BootReady.

Conflicts:
No expert conflict on dashboard HOLD, G9 context-only status, or blocked provider/snapshot/runtime paths. The only actionable disagreement was Expert B's PATCH finding on contract strictness.

Conflict Resolution:
Expert B's PATCH finding was fixed before closing reconciliation. Expert A's NEEDS USER EVIDENCE blocks probe authorization. Therefore the final next step is entitlement/permission-truth authorization only, not provider access or probe execution.

Allowed Files:
- `docs/handover/MULTI_EXPERT_RECONCILED_VERDICT_20260602.md`
- `docs/saw_reports/saw_v2_d0_multi_expert_reconciliation_20260602.md`
- `v2_discovery/data_lab/wrds_probe.py`
- `v2_discovery/data_lab/snapshot_manifest.py`
- `tests/test_v2_wrds_permission_matrix.py`
- `tests/test_v2_snapshot_manifest_contract.py`
- Current truth surfaces in `docs/context/*_current.md`
- Product/spec/decision/notes/lessons docs needed to record the gate

Forbidden Files:
- `data/**`
- `data/processed/**`
- `data/registry/**`
- `runtime/**`
- `docs/context/boot_status_current.json`
- `v2_discovery/data_lab/snapshots/**`
- `reports/**`
- `promotion_packets/**`
- any credential file such as `.env`, `.pgpass`, WRDS configs, or raw provider logs

Allowed Commands:
- `.venv\Scripts\python -m pytest tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q`
- `.venv\Scripts\python -m compileall v2_discovery\data_lab tests\test_v2_wrds_permission_matrix.py tests\test_v2_snapshot_manifest_contract.py tests\test_v2_data_lab_no_v1_writes.py -q`
- `.venv\Scripts\python scripts\build_context_packet.py`
- `.venv\Scripts\python scripts\build_context_packet.py --validate`
- Closure and SAW validation scripts under `.codex/skills/_shared/scripts/`

Forbidden Commands:
- Any `wrds.Connection`, `import wrds`, provider connection, or credentialed probe.
- Any snapshot extraction or data-write command.
- Any command that writes `data/processed`, `data/registry`, `runtime`, boot-status, SQLite, dashboard runtime outputs, reports, promotion packets, or broker/order artifacts.

Stop Rules:
- Stop before any provider access, credentials, query, table read, snapshot path, data output, runtime write, SQLite store, dashboard reader, ranking/scoring/recommendation/alert/broker path, promotion claim, SafeBoot claim, or BootReady claim.
- Stop if WRDS permission evidence is missing or if an approved permission row lacks `approval_ref`.
- Stop if probe contract validation accepts extra fields, credential-like keys, connection/output fields, changed `next_allowed_action`, changed `denied_actions`, changed `code_ref`, or widened dataset row shape.

Confidence:
8/10. Confidence is high for the offline contract boundary and patch closure, but actual WRDS permission truth remains unknown until user/source entitlement evidence is supplied.
