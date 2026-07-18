# GV-FS0-PF1L-R3.3 — Lineage-Correct Protocol Re-Freeze (Self-Contained Approval Gate)

`	ext
Mode:                 APPROVAL_GATE
GateID:               GV-FS0-PF1L-R3.3
RoundID:              ROUND-PF1L-R3-3-APPROVAL
ScopeID:              GV_FS0_PROTOCOL_LINEAGE_REFREEZE_R3_3
Execution of freeze:  FORBIDDEN until separate EXECUTION_PACKET cites this payload's
                      raw SHA-256 and the detached identity envelope for payload commit N
Scores:               product 39/100 | protocol capability 92/100 | freeze authority 65/100
`

## 0. Document identity (raw whole-file)

1. This payload **must not** embed its own final SHA-256.
2. **Authoritative packet identity** = SHA-256(exact UTF-8 file bytes as stored).
3. No substitution, no marker replacement, no “replace all occurrences” step.
4. Publish the hash only in a detached identity envelope and/or external approval block.

### Historical (non-targets)

| Object | SHA-256 |
|---|---|
| R3 base | 34ad77f21b478d92ada86470947ff3060741dadc180acd6d21cb3080b680b04f |
| R3.1 raw | 99208bf42d3b5b0968486f9009bec30aa911a5034fe79db57c936c169d4aef16 |
| R3.2 raw | 5e0998705184c4c9ac3a42feef7741cc50d095f3d905de4ecfed5233950907b7 |

R3.1/R3.2 ignored-tmp text is **not** required for execution. **R3.3 is self-contained.**

### Ship-Fast banking order (mandatory before execution authority)

1. Bank this exact markdown as payload commit **N** (tracked path below).
2. Bank detached identity envelope as commit **N+1** binding N (remote, root, commit, tree, path, SHA-256).
3. Only then may an EXECUTION_PACKET issue freeze-implementation authority citing N’s raw SHA-256 + envelope.

---

## 1. Immutable pins

`	ext
REQUIRED_ANCESTOR = 6a8bb6c9410bc91940d53ca727b561aa86776ec7
TRANSPLANT_TIP    = d5d03ec6e0b0a2bcafd6c0eac34caa23703d03ed
FORBIDDEN_SHA     = c007895606c04d9b6de19be80273534ca6437572
GITATTRIBUTES_SHA256 = 7edc9193207199b7882e1b687dd5ca9619d0d4c39cb15e7c1b3e272ac28b3377
GITATTRIBUTES_BYTES  = 624
`

### 1.1 Phase-0 fixture SHA-256 (must match 6a8bb6c bytes)

| Path | SHA-256 | Bytes |
|---|---|---:|
| data/fixtures/v2_proxy/synthetic_weights.csv | 3804eeff6664ada5c03bace1beaeb136a96e5d85f11ba5faeeafb84da9db3760 | 106 |
| data/fixtures/v2_proxy/synthetic_prices.csv | 732e1898866f2dd777b64650d70c154dc6b6f72cbd23785dee8a865e9bd360a7 | 104 |
| data/fixtures/v2_proxy/expected_ledger.csv | 3d69bdf1fb6a8ce98400d0a5eff3255662fe42b3e573f08f4b6b0b1c9b2707fc | 179 |
| data/fixtures/v2_proxy/expected_positions.csv | 32dd6dfba16826051be6adbfe38530f58429a6b7969ca9a6ce6e756dae969d8a | 191 |
| data/fixtures/v2_proxy/expected_result.json | 4029a68df991b5a73eb7a6401e4562fa32f6dcd91f346fcb3151aa98804281eb | 986 |

Cross-OS parity alone is insufficient.

### 1.2 V2 matrix (exactly 79 collected tests)

`	ext
tests/test_v2_fast_proxy_synthetic.py                 # 25
tests/test_v2_fast_proxy_invariants.py                # 9
tests/test_v2_canonical_replay_fixture.py             # 15
tests/test_v2_proxy_registered_candidate_flow.py      # 19
tests/test_v2_proxy_boundary.py                       # 11
`

---

## 2. Complete C transplant allowlist (37 paths from d5d03ec)

Checkout **only** these paths from TRANSPLANT_TIP onto a branch whose ancestry includes REQUIRED_ANCESTOR. No other path from d5d03ec or any c007895-series commit.

`	ext
.github/workflows/gv-fs0-protocol-freeze.yml
contracts/gv_fs0/v1/gv_fs0_freeze_manifest_v1.json
contracts/gv_fs0/v1/registries/gv_fs0_certification_failure_registry_v1.json
contracts/gv_fs0/v1/registries/gv_fs0_operational_error_registry_v1.json
contracts/gv_fs0/v1/schemas/gv_fs0_blocked_evidence_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_certification_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_certified_bundle_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_certified_decision_result_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_decision_envelope_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_portfolio_event_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_snapshot_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_source_fixture_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_source_intent_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_verifier_attempt_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_verifier_input_v1.schema.json
contracts/gv_fs0/v1/schemas/gv_fs0_verifier_result_v1.schema.json
contracts/gv_fs0/v1/tables/gv_fs0_event_ranks_v1.json
contracts/gv_fs0/v1/tables/gv_fs0_generated_event_slots_v1.json
contracts/gv_fs0/v1/tables/gv_fs0_transition_ownership_v1.json
contracts/gv_fs0/v1/vectors/gv_fs0_canonical_vectors_v1.json
core/gv_fs0_canonical.py
docs/architecture/gv_fs0_certification_and_data_authority_contract.md
scripts/generate_gv_fs0_protocol_v1.py
scripts/verify_gv_fs0_protocol_freeze.py
tests/test_gv_fs0_canonical_protocol_v1.py
tests/test_gv_fs0_certification_registries_v1.py
tests/test_gv_fs0_freeze_immutability_v1.py
tests/test_gv_fs0_identity_ordering_v1.py
tests/test_gv_fs0_publication_protocol_v1.py
tests/test_gv_fs0_reconstruction_isolation.py
tests/test_gv_fs0_schema_contracts_v1.py
tests/test_gv_fs0_transition_ownership_v1.py
tests/test_gv_fs0_verifier_projection_v1.py
tests/test_gv_fs0_verifier_results_v1.py
tests/test_gv_fs0_verifier_supervision_v1.py
validation/gv_fs0_ci_reference_encoder.py
validation/gv_fs0_reconstruction.py
`

**Excluded:** d5d03ec:.gitattributes, dual gv_fs0/ package, invalid-lineage PASS docs/SAW, any path not listed.

**C also adds (not from tip):** exact .gitattributes (§3), ancestry/Git identity (§4), five-hash + V2 79 CI (§5), C-marker and closure-binding machinery as needed for F (§6–7).

---

## 3. Exact .gitattributes (full-file pin)

Working tree and git blob at **C** must satisfy:

`	ext
len(bytes) == 624
sha256(bytes) == 7edc9193207199b7882e1b687dd5ca9619d0d4c39cb15e7c1b3e272ac28b3377
`

UTF-8, LF only, no CR. Normative content:

`
# Preserve the approved Phase 0 V2 canonical-fixture checkout boundary.
data/fixtures/v2_proxy/synthetic_weights.csv text eol=lf
data/fixtures/v2_proxy/synthetic_prices.csv text eol=lf
data/fixtures/v2_proxy/expected_ledger.csv text eol=lf
data/fixtures/v2_proxy/expected_positions.csv text eol=lf
data/fixtures/v2_proxy/expected_result.json text eol=lf

# GV-FS0 reviewed authority and immutable V1 machine surfaces.
docs/architecture/gv_fs0_certification_and_data_authority_contract.md text eol=lf
docs/phase_brief/phase-E0-brief.md text eol=lf
contracts/gv_fs0/v1/**/*.json text eol=lf
contracts/gv_fs0/v1/**/*.bin -text
`

**Enforcement:** raw length + SHA-256 mandatory. Subset-only line checks are forbidden as the sole gate. A superset file with extra/contradictory rules must FAIL even if Phase-0 lines are present.

In scripts/verify_gv_fs0_protocol_freeze.py and 	ests/test_gv_fs0_freeze_immutability_v1.py, assert the full-file pin (and optional superset-fail regression). Line lists may exist only as secondary diagnostics.

---

## 4. Sanitized Git identity and ancestry (fail-closed)

Every freeze-authority Git subprocess must:

### 4.1 Set

`	ext
GIT_NO_REPLACE_OBJECTS=1
`

### 4.2 Clear (pop from child env)

`	ext
GIT_DIR
GIT_WORK_TREE
GIT_COMMON_DIR
GIT_OBJECT_DIRECTORY
GIT_ALTERNATE_OBJECT_DIRECTORIES
GIT_INDEX_FILE
GIT_NAMESPACE
`

and **every** variable whose name starts with GIT_CONFIG_.

### 4.3 Replacement refs

`	ext
git for-each-ref --format=%(refname) refs/replace/
`

Empty required; enum error or any ref → FAIL.

### 4.4 Non-shallow complete ancestry

`	ext
git rev-parse --is-shallow-repository  → false (else FAIL)
Ancestors(HEAD) := set(git rev-list HEAD)  # must succeed; error → FAIL

PASS iff:
  REQUIRED_ANCESTOR ∈ Ancestors(HEAD)
  FORBIDDEN_SHA     ∉ Ancestors(HEAD)
`

Missing FORBIDDEN object store entry is OK if not in Ancestors. Shallow/incomplete proof of REQUIRED → FAIL. Align with or exceed scripts/boot_preflight.py sanitization.

### 4.5 Five fixture pins

Working-tree SHA-256 of each §1.1 path equals the pin; also equal git cat-file -p REQUIRED_ANCESTOR:path under sanitized env.

---

## 5. Exact-SHA CI, generator, probes

| Item | Rule |
|---|---|
| C CI | Checkout **exact C full SHA**; etch-depth: 0; §4; generator --check; independent vectors; freeze verify; all 	ests/test_gv_fs0_*.py; V2 **79**; five-hash pins |
| Deps | pandas==2.2.3 (from d5d03ec workflow) |
| Generator | Derivation only; contract + 18 checked-in artifacts normative; --check only |
| Mutation probes | Branch first-parent = **C**; schema/registry/contract/vector/CRLF/dishonest manifest+artifact each reject; do not merge probes |
| F CI | Checkout **exact F full SHA**; frozen empty-diff vs C; §6–7 marker/binding checks |

Branch-tip green without recorded SHA is not freeze evidence.

---

## 6. Exact machine marker for C (deterministic)

### 6.1 Marker grammar (normative)

On every path listed in §7.2 	ruth_surfaces_requiring_c_marker, the file UTF-8 text must contain **exactly one** line matching this full-line regex (Python):

`	ext
^GV_FS0_PF1L_CANDIDATE_COMMIT_C=[0-9a-f]{40}$
`

- No leading/trailing spaces on that line.
- SHA is lowercase hex, full 40-char object id for this repository’s SHA-1 object format.
- The marker line is the **only** authorized machine binding of C inside truth surfaces.
- Free-text “conflicting C claims” detection is **not** used.

### 6.2 Per-file rules

For each required truth surface path at commit F:

| Condition | Result |
|---|---|
| Zero matches of the marker regex | **FAIL** (missing) |
| Two or more matches | **FAIL** (duplicate) |
| One match, SHA ≠ candidate_commit_c in binding JSON | **FAIL** (unequal) |
| One match, SHA = candidate_commit_c | PASS for that file |

### 6.3 Cross-file rule

The set of SHAs extracted from all required surfaces must have cardinality **1**, and that element must equal candidate_commit_c. Any missing/duplicate/unequal → FAIL.

### 6.4 SAW / SE reports

Each matched closure report under §7 globs must also contain **exactly one** line matching the same marker regex, equal to candidate_commit_c.

---

## 7. Closure-binding JSON (F-owned; no self-SHA for F)

### 7.1 Path

`	ext
docs/context/e2e_evidence/gv_fs0_pf1l_closure_binding_v1.json
`

### 7.2 Required JSON fields (no closure_commit_f)

`json
{
  "binding_id": "gv_fs0_pf1l_closure_binding_v1",
  "binding_version": 1,
  "gate_id": "GV-FS0-PF1L-R3.3",
  "protocol_id": "GV_FS0_PROTOCOL_V1",
  "candidate_commit_c": "<40-lowercase-hex SHA of C>",
  "required_ancestor": "6a8bb6c9410bc91940d53ca727b561aa86776ec7",
  "forbidden_ancestor": "c007895606c04d9b6de19be80273534ca6437572",
  "gitattributes_sha256": "7edc9193207199b7882e1b687dd5ca9619d0d4c39cb15e7c1b3e272ac28b3377",
  "c_marker_regex": "^GV_FS0_PF1L_CANDIDATE_COMMIT_C=[0-9a-f]{40}$",
  "truth_surfaces_requiring_c_marker": [
    "docs/phase_brief/phase-E0-brief.md",
    "docs/context/planner_packet_current.md",
    "docs/context/bridge_contract_current.md",
    "docs/context/impact_packet_current.md",
    "docs/context/done_checklist_current.md",
    "docs/context/multi_stream_contract_current.md",
    "docs/context/post_phase_alignment_current.md",
    "docs/context/observability_pack_current.md",
    "docs/context/current_context.md",
    "docs/context/current_context.json",
    "docs/decision log.md",
    "PRD.md",
    "PRODUCT_SPEC.md",
    "docs/prd.md",
    "docs/spec.md"
  ],
  "saw_report_glob": "docs/saw_reports/saw_gv_fs0_pf1l_r3_closure_*.md",
  "se_report_glob": "docs/saw_reports/se_gv_fs0_pf1l_r3_closure_*.md"
}
`

**Omitted by design:** closure_commit_f (cannot embed F’s own commit SHA inside F).

### 7.3 Binding F via later detached envelope **G**

After F is banked:

1. Create detached identity envelope commit **G** (G ≠ F; G does not need to modify frozen protocol surfaces).
2. Envelope G binds: repository remote/root, **payload commit F**, F’s tree, path+SHA-256 of the closure-binding JSON, path+SHA-256 of F’s primary SAW report if any, and candidate_commit_c echoed from the JSON.
3. Envelope G is the Ship-Fast identity for F; the binding JSON remains the machine authority for **C** only.

### 7.4 Parse rules

- Duplicate-key rejection at every JSON object depth; duplicate key → invalid.
- Exact-F CI implements §6 marker checks against candidate_commit_c.
- git rev-list F must contain candidate_commit_c and 
equired_ancestor, and must not contain orbidden_ancestor.

---

## 8. F path allowlist and CI triggers

### 8.1 F may touch only

`	ext
PRD.md
PRODUCT_SPEC.md
docs/prd.md
docs/spec.md
docs/phase_brief/phase-E0-brief.md
docs/decision log.md
docs/notes.md
docs/lessonss.md
docs/context/planner_packet_current.md
docs/context/bridge_contract_current.md
docs/context/impact_packet_current.md
docs/context/done_checklist_current.md
docs/context/multi_stream_contract_current.md
docs/context/post_phase_alignment_current.md
docs/context/observability_pack_current.md
docs/context/current_context.md
docs/context/current_context.json
docs/context/e2e_evidence/gv_fs0_pf1l_closure_binding_v1.json
docs/saw_reports/saw_gv_fs0_pf1l_r3_closure_*.md
docs/saw_reports/se_gv_fs0_pf1l_r3_closure_*.md
`

### 8.2 Frozen empty-diff

For every §2 path and for .gitattributes: git diff C F -- <path> empty.

### 8.3 Workflow path filters (on C)

Must include every §8.1 path (globs for saw/se) under pull_request.paths and push.paths so each F edit triggers exact-F CI.

---

## 9. C / F / G roles and history

| Commit | Role | Review |
|---|---|---|
| **C** | Freeze-authority code candidate | Full independent A/B/C + full SAW |
| **F** | Docs + binding JSON + markers; no self-SHA field | Thin SAW |
| **G** | Detached identity envelope binding F | Envelope verification only |

Final freeze tip ancestry must contain **C** and **F**. **G** should be reachable from the published freeze-authority ref or explicitly recorded as the F-binding envelope.

**Forbidden:** rebase/squash/amend/cherry-pick that drops C or F from 
ev-list; force-push replacing those SHAs.

---

## 10. Execution outline (after EXECUTION_PACKET only)

1. Isolated worktree from 6a8bb6c (not poisoned root with nested gitlinks).
2. Branch; git checkout d5d03ec -- §2 paths only.
3. Write exact 624-byte .gitattributes (§3).
4. Implement §4–5 proof + CI path filters including F paths.
5. Bank **C**; exact-SHA CI; probes from C; full A/B/C + full SAW on C.
6. Bank **F** with binding JSON (no closure_commit_f) and exactly one C marker per required surface.
7. Bank **G** detached envelope binding F.
8. Thin SAW on F; freeze PASS only if all criteria hold.

---

## 11. Future PASS criteria

1. EXECUTION_PACKET cites this R3.3 raw SHA-256 + envelope for N.
2. §4 identity PASS; ancestry predicate PASS on C.
3. .gitattributes exact 624-byte hash PASS.
4. Tree = §2 + §3 + proof only; single V1 surface.
5. Five pins; V2 79/79; GV-FS0 green; probes from C reject.
6. Full A/B/C + full SAW PASS on C.
7. F: binding JSON duplicate-key-clean; §6 markers pass; frozen empty-diff; Thin SAW PASS.
8. G binds F without requiring closure_commit_f inside F.
9. Final tip: C,F ∈ Ancestors(tip); no rewrite.
10. Clean freeze PASS authorizes minimal FS0 product slice only; no second owner gate; real data/FS1 held.

---

## 12. Forbidden

| Forbidden | Why |
|---|---|
| Depend on ignored R3.1/R3.2 for execution text | Non-self-contained |
| closure_commit_f inside F | Self-referential commit identity |
| Free-text conflict detection for C | Non-deterministic |
| Subset-only .gitattributes gate | Contradictory override |
| Unsanitized Git / shallow / replace refs | False ancestry |
| History rewrite dropping C or F | Authority loss |
| Treat approval as freeze execution | Separate EXECUTION_PACKET required |

---

## 13. Approval / banking block (hash filled outside payload)

`	ext
GATE: GV-FS0-PF1L-R3.3
MODE: APPROVAL_GATE
IDENTITY_ALGORITHM: SHA-256(exact UTF-8 file bytes); no in-payload self-hash
C_MARKER: ^GV_FS0_PF1L_CANDIDATE_COMMIT_C=[0-9a-f]{40}$
CLOSURE_BINDING: docs/context/e2e_evidence/gv_fs0_pf1l_closure_binding_v1.json
  (no closure_commit_f; F bound by later detached envelope G)
GITATTRIBUTES_SHA256: 7edc9193207199b7882e1b687dd5ca9619d0d4c39cb15e7c1b3e272ac28b3377
BANKING: payload commit N = this file; envelope commit N+1 = detached bind of N
EXECUTION: only after N+N+1 and separate EXECUTION_PACKET
SCORES: 39 / 92 / 65
`
