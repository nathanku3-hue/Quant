"""Assemble OK-SBI-0 S0 machine freeze packet (outcome-blind)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from research.asymmetric_opportunity_v1.applicability import law_semantics as applicability_law
from research.asymmetric_opportunity_v1.arms import arm_catalog, arm_formula_hashes, refuse_empirical_ranking
from research.asymmetric_opportunity_v1.claim_schema import schema_document
from research.asymmetric_opportunity_v1.context_c_firewall import (
    firewall_semantics,
    future_reporting_hook_stubs,
)
from research.asymmetric_opportunity_v1.label_packs import seal_dual_label_packs
from research.asymmetric_opportunity_v1.ledgers import ledger_catalog
from research.asymmetric_opportunity_v1.q_source_contract import (
    evaluate_q_source_feasibility,
)
from research.asymmetric_opportunity_v1.release_gates import (
    default_blocked_gates,
    machine_law,
    review_bar,
)
from research.asymmetric_opportunity_v1.status_strata import contract_semantics as status_semantics
from research.asymmetric_opportunity_v1.orthogonalization import (
    ORTHOGONALIZATION_CONTRACT_ID,
    W3_DENOMINATOR_ID,
    contract_semantics as k0a_semantics,
)


SLICE_ID = "OK-SBI-0"
ALIAS = "AO-K0B-D"
SPEC_VERSION = "v1.2"
FREEZE_SCHEMA = "ok_sbi_0_machine_freeze_v1_2"

CONSTITUTION = (
    "Science is locked. Release is not. "
    "Build pre-open machinery only. "
    "Q may be amended at most once outcome-blind. "
    "Every future claim must bind clock + ledger + population + denominator. "
    "While any release blocker remains, runnable_evaluation=false and outcome open is forbidden. "
    "This is not a Q/M⊥/Q+M⊥ trophy slice. It is sparse basis identification infrastructure."
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_machine_freeze(
    *,
    repo_root: Path | None = None,
    extra_gates: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = (repo_root or Path.cwd()).resolve()
    q_feas = evaluate_q_source_feasibility(repo_root=root, include_custody_audit=True)
    labels = seal_dual_label_packs()
    gates = default_blocked_gates()

    # Bind known upstream hashes when present (still leave numeric science gates blocked).
    k0a_contract = root / "docs" / "architecture" / "orthogonalization_contract_v1.md"
    k0a_receipt = (
        root
        / "docs"
        / "context"
        / "e2e_evidence"
        / "ao_k0a_orthogonal_basis_preflight_20260811.json"
    )
    if k0a_contract.is_file():
        gates["contract_hash"] = _sha256_file(k0a_contract)
    if k0a_receipt.is_file():
        gates["source_hash"] = _sha256_file(k0a_receipt)
    gates["denominator_hash"] = _canonical_sha256(
        {"denominator": W3_DENOMINATOR_ID, "contract": ORTHOGONALIZATION_CONTRACT_ID}
    )

    # q_source_binding_hash remains BLOCKED_UNSET until Q_GF_BOUND / Q_AMENDED_BOUND.
    binding_hash = q_feas.get("q_source_binding_hash", "BLOCKED_UNSET")
    if binding_hash and binding_hash != "BLOCKED_UNSET":
        gates["q_source_binding_hash"] = binding_hash
    else:
        gates["q_source_binding_hash"] = "BLOCKED_UNSET"

    # Label pack seals — only set sha when fully sealed.
    q_seal = labels["Q_CLOCK_LABEL_PACK"]
    m_seal = labels["M_CLOCK_LABEL_PACK"]
    if q_seal.get("sha256"):
        gates["Q_CLOCK_LABEL_PACK_sha256"] = q_seal["sha256"]
    if m_seal.get("sha256"):
        gates["M_CLOCK_LABEL_PACK_sha256"] = m_seal["sha256"]

    if extra_gates:
        gates.update(extra_gates)

    law = machine_law(gates)
    freeze: dict[str, Any] = {
        "schema_version": FREEZE_SCHEMA,
        "slice_id": SLICE_ID,
        "alias": ALIAS,
        "spec_version": SPEC_VERSION,
        "date": "2026-08-12",
        "constitution": CONSTITUTION,
        "authorization": {
            "S0_IMPLEMENTATION_WORK": True,
            "OUTCOME_OPEN_NOW": False,
            "RELEASE_NOW": False,
            "ALPHA_CAPITAL_PRODUCTION": "NONE",
            "financial_alpha_evidence": 0,
            "OK_SBI_0_DEV_OPEN_1": "NOT_ISSUED",
        },
        "inherited_k0a": {
            "contract_id": ORTHOGONALIZATION_CONTRACT_ID,
            "denominator": W3_DENOMINATOR_ID,
            "semantics": k0a_semantics(),
            "contract_path": "docs/architecture/orthogonalization_contract_v1.md",
            "evidence_path": (
                "docs/context/e2e_evidence/ao_k0a_orthogonal_basis_preflight_20260811.json"
            ),
        },
        "step1_q_source": q_feas,
        "step2_applicability": applicability_law(),
        "step3_status_strata": status_semantics(),
        "step4_numeric_gates": gates,
        "step5_label_packs": labels,
        "step6_contracts": {
            "arms": arm_catalog(),
            "arm_formula_hashes": arm_formula_hashes(),
            "ledgers": ledger_catalog(),
            "claim_schema": schema_document(),
            "context_c_firewall": firewall_semantics(),
            "c_future_hooks": future_reporting_hook_stubs(),
            "empirical_ranking": refuse_empirical_ranking(),
        },
        "review_bar": review_bar(),
        "machine_law": law,
        "STATE": law["STATE"],
        "runnable_evaluation": law["runnable_evaluation"],
        "blocked_field_count": law["blocked_field_count"],
        "blocked_fields": law["blocked_fields"],
        "Q_feasibility": q_feas["Q_feasibility"],
        "q_amendment_cycles_used": q_feas["q_amendment_cycles_used"],
        "outcome_open_authorized": False,
        "forbidden_this_turn": [
            "outcome_join",
            "empirical_q_mperp_qplusmperp_result",
            "cross_horizon_leaderboard",
            "composite_trophy",
            "w6",
            "providers",
            "capital",
            "second_q_redesign",
            "silent_field_bridges",
            "a5_presumed_winner",
        ],
    }
    freeze["freeze_body_sha256"] = _canonical_sha256(
        {k: v for k, v in freeze.items() if k != "freeze_body_sha256"}
    )
    return freeze


def write_machine_freeze(
    path: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    freeze = build_machine_freeze(repo_root=repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(freeze, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return freeze
