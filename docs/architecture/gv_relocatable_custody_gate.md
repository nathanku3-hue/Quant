# Relocatable Manifest Custody Gate

Status: `ACTIVE`
Date: 2026-07-30
Parent base: Slice 0 immutable `85e6601742710f03e6cced7377b4be426cd4892f`
Purpose: accept repository-relative, clean-checkout custody for hash-bound
manifests **without** rewriting banked V2-B0 historical package authority.

## Gate law

1. Candidate must descend from exact Slice 0 `85e6601`.
2. Candidate-only full-suite failures versus `85e6601` must be **zero**.
3. Product and Replay implementation remain closed on this gate.
4. Focused custody suites must name every included node and every **retired**
   assertion. Silent omission is not retirement.

## In scope (must remain)

| Surface | Requirement |
|---|---|
| G4 fixture manifest | `artifact_path` is repository-relative |
| `v2_discovery/readiness/canonical_slice.py` | resolve declared path against `repo_root` before compare |
| MSFT G8.2 card manifest | `artifact_sha256` may match live card bytes (not V2-B0 bound) |
| V2-B0 MU package | retain historical declared `artifact_sha256` `368c4fb3…` ≠ card `f87e7908…` |
| V2-B0 admission | still surfaces `SOURCE_PACKAGE_MANIFEST_BINDING_INVALID` |
| Portfolio vertical | no regression on `tests/gv_portfolio_v0` |

## Explicitly retired from this custody gate

| Retired assertion | Former node | Why retired | Residual truth |
|---|---|---|---|
| G8 MU **same-path hash-match PASS** | `tests/test_g8_supercycle_candidate_card.py::test_g8_candidate_card_bundle_hash_validates_against_manifest` | Conflicts with banked V2-B0 intentional non-binding on the **same** live MU package path | Replaced by `test_g8_mu_live_package_retains_v2b0_intentional_non_binding`, which **requires** the mismatch and fails closed if someone "repairs" the hash |

This is not a silent weaken of G8. G8 hash-green remains required for packages that are **not** the V2-B0 historical MU fixture (for example MSFT G8.2). The MU live path is dual-owned until a future product redesign moves the intentional mismatch to a dedicated V2-B0-only package.

## Focused custody proof set

Run (representative; expand only with explicit gate edit):

- `tests/test_g4_real_canonical_readiness_fixture.py`
- `tests/test_g5_single_canonical_replay_no_alpha.py` (manifest/path subset as collected)
- `tests/test_g6_v1_v2_real_slice_mechanical_comparison.py` (manifest/path subset as collected)
- `tests/test_g8_supercycle_candidate_card.py::test_g8_mu_live_package_retains_v2b0_intentional_non_binding`
- `tests/test_g8_2_system_scouted_candidate_card.py` (MSFT path)
- `tests/gv_fs0_product/test_v2_b0_real_block_only.py`
- `tests/gv_portfolio_v0`

## Forbidden on this gate

- Aligning MU declared `artifact_sha256` to live card bytes to green G8
- Opening `GV-DETERMINISTIC-REPLAY-0` product implementation before Replay 0 base promotion
- Claiming full-repository PASS from a subset gate
- Silent drop of any retired assertion without this document and a replacement truth test
