"""Deterministic MU/NVDA evidence reconciliation for the G_supply case.

This module consumes only already-banked authority artifacts. It performs no
network/provider work, emits no score or ranking, mutates no portfolio, and
makes no alpha or investability claim.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from core.gv_v2_alpha0_source_family_two import (
    FACT_SET_DOMAIN as NVDA_FACT_SET_DOMAIN,
    RESEARCH_DOMAIN as NVDA_RESEARCH_DOMAIN,
)
from core.gv_v2_b0b_official_source_intake import (
    CLAIM_DOMAIN as MU_CLAIM_DOMAIN,
    RESEARCH_DOMAIN as MU_RESEARCH_DOMAIN,
)

ROOT = Path(__file__).resolve().parents[1]
MU_CASE_DIR = ROOT / "data" / "gv_v2_b0b" / "mu_0000723125-26-000015"
NVDA_CASE_DIR = (
    ROOT
    / "data"
    / "gv_v2_alpha0"
    / "family_two_nvda_0001045810-26-000052"
)
DEFAULT_OUTPUT_DIR = ROOT / "data" / "gv_v2_reconciliation" / "mu_nvda_supply_1"

SCHEMA_VERSION = "gv_v2_mu_nvda_reconciliation_v1"
CASE_ID = "GV_V2_MU_NVDA_G_SUPPLY_RECONCILIATION_1"
RECONCILIATION_DOMAIN = "GV-V2:MU-NVDA:G_SUPPLY:RECONCILIATION:V1"
DISPOSITION_HOLD = "HOLD"
RESEARCH_ACTION_HOLD = "HOLD_FOR_EVIDENCE"
PORTFOLIO_ACTION_NO_POSITION = "NO_POSITION"
CONTRADICTION_NONE = "NO_DIRECT_CONTRADICTION_IDENTIFIED"
CORROBORATION_PARTIAL = "PARTIAL_INDIRECT"


class MuNvdaReconciliationError(ValueError):
    """Fail-closed error for invalid or disconnected banked evidence."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MuNvdaReconciliationError(f"RECONCILIATION_SOURCE_INVALID:{path}") from exc
    if not isinstance(value, dict):
        raise MuNvdaReconciliationError(f"RECONCILIATION_SOURCE_OBJECT_REQUIRED:{path}")
    return value


def _require_domain_hash(
    payload: Mapping[str, Any], *, domain: str, hash_key: str, code: str
) -> None:
    body = {key: deepcopy(value) for key, value in payload.items() if key != hash_key}
    if payload.get(hash_key) != domain_hash(domain, body):
        raise MuNvdaReconciliationError(code)


def build_mu_nvda_reconciliation(
    *,
    mu_claim: Mapping[str, Any],
    mu_research: Mapping[str, Any],
    nvda_fact_set: Mapping[str, Any],
    nvda_research: Mapping[str, Any],
) -> dict[str, Any]:
    """Reconcile two banked source families without extending their claims."""

    _require_domain_hash(
        mu_claim,
        domain=MU_CLAIM_DOMAIN,
        hash_key="claim_evaluation_hash",
        code="MU_CLAIM_HASH_MISMATCH",
    )
    _require_domain_hash(
        mu_research,
        domain=MU_RESEARCH_DOMAIN,
        hash_key="research_decision_hash",
        code="MU_RESEARCH_HASH_MISMATCH",
    )
    _require_domain_hash(
        nvda_fact_set,
        domain=NVDA_FACT_SET_DOMAIN,
        hash_key="fact_set_hash",
        code="NVDA_FACT_SET_HASH_MISMATCH",
    )
    _require_domain_hash(
        nvda_research,
        domain=NVDA_RESEARCH_DOMAIN,
        hash_key="research_decision_hash",
        code="NVDA_RESEARCH_HASH_MISMATCH",
    )

    if mu_claim.get("claim_evaluation_hash") != mu_research.get(
        "claim_evaluation_hash"
    ):
        raise MuNvdaReconciliationError("MU_CLAIM_RESEARCH_LINK_MISMATCH")
    if nvda_fact_set.get("fact_set_hash") != nvda_research.get("fact_set_hash"):
        raise MuNvdaReconciliationError("NVDA_FACT_RESEARCH_LINK_MISMATCH")
    if mu_claim.get("subject") != "MU" or mu_research.get("subject") != "MU":
        raise MuNvdaReconciliationError("MU_SUBJECT_MISMATCH")
    if nvda_fact_set.get("subject_case") != "MU_G_SUPPLY":
        raise MuNvdaReconciliationError("NVDA_CASE_MISMATCH")
    if nvda_fact_set.get("family_one_reference") != mu_claim.get(
        "source_family_id"
    ):
        raise MuNvdaReconciliationError("SOURCE_FAMILY_LINK_MISMATCH")
    if mu_claim.get("claim_outcome") != "CLAIM_INSUFFICIENT":
        raise MuNvdaReconciliationError("MU_BASELINE_OUTCOME_UNEXPECTED")
    if mu_research.get("portfolio_action") != PORTFOLIO_ACTION_NO_POSITION:
        raise MuNvdaReconciliationError("MU_BASELINE_POSITION_UNEXPECTED")
    if nvda_research.get("reconciliation_status") != "NOT_RUN":
        raise MuNvdaReconciliationError("NVDA_RECONCILIATION_ALREADY_RUN")

    facts = list(nvda_fact_set.get("facts") or [])
    fact_ids = {str(row.get("fact_id")) for row in facts}
    required_fact_ids = {
        "SF2_FACT_MEMORY_PRICES_001",
        "SF2_FACT_FOUNDRY_CAPACITY_001",
        "SF2_FACT_SCARCE_INPUTS_001",
        "SF2_FACT_SUPPLY_SHORTFALL_001",
        "SF2_FACT_NCNR_ORDERS_001",
    }
    if not required_fact_ids.issubset(fact_ids):
        raise MuNvdaReconciliationError("NVDA_REQUIRED_FACTS_MISSING")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": CASE_ID,
        "subject": "MU",
        "module": "G_supply",
        "source_families": [
            mu_claim["source_family_id"],
            nvda_fact_set["source_family_id"],
        ],
        "independent_source_family_count": 2,
        "source_bindings": {
            "mu_claim_evaluation_hash": mu_claim["claim_evaluation_hash"],
            "mu_research_decision_hash": mu_research["research_decision_hash"],
            "nvda_fact_set_hash": nvda_fact_set["fact_set_hash"],
            "nvda_research_decision_hash": nvda_research[
                "research_decision_hash"
            ],
        },
        "corroboration_status": CORROBORATION_PARTIAL,
        "corroboration": [
            {
                "claim": (
                    "The period contained elevated memory prices and a broader "
                    "supply-constrained operating environment."
                ),
                "support": "INDIRECT",
                "nvda_fact_ids": [
                    "SF2_FACT_MEMORY_PRICES_001",
                    "SF2_FACT_SCARCE_INPUTS_001",
                    "SF2_FACT_SUPPLY_SHORTFALL_001",
                ],
                "mu_statement_ids": [
                    "B0B_STMT_DEMAND_EXCEEDS_SUPPLY_001",
                    "B0B_STMT_CONSTRAINED_SUPPLY_001",
                ],
            },
            {
                "claim": (
                    "Long-lead commitments and constrained production capacity can "
                    "create supply-chain inertia at the industry level."
                ),
                "support": "INDIRECT",
                "nvda_fact_ids": [
                    "SF2_FACT_FOUNDRY_CAPACITY_001",
                    "SF2_FACT_NCNR_ORDERS_001",
                ],
                "mu_statement_ids": [
                    "B0B_STMT_SUPPLY_ALLOCATION_001",
                    "B0B_STMT_SINGAPORE_EXPANSION_001",
                ],
            },
        ],
        "not_established": [
            "Micron-specific physical supply persistence",
            "Micron shipment, inventory, utilization, or allocation durability",
            "Causal translation from NVIDIA constraints to Micron economics",
            "Mispricing, alpha, investability, tradability, or position sizing",
        ],
        "contradiction_status": CONTRADICTION_NONE,
        "contradictions": [],
        "disposition": DISPOSITION_HOLD,
        "research_action": RESEARCH_ACTION_HOLD,
        "portfolio_action": PORTFOLIO_ACTION_NO_POSITION,
        "missing_discriminator": (
            "Independent Micron-specific physical supply evidence with point-in-time "
            "custody—such as auditable shipment/allocation, inventory, utilization, "
            "capacity-ramp, or channel data—showing persistence across more than one period."
        ),
        "rationale": (
            "NVDA independently supports a broad memory-price and supply-constrained "
            "environment, but its disclosures concern NVIDIA's inputs and commitments. "
            "They do not establish Micron-specific physical supply persistence. HOLD and "
            "NO_POSITION remain the only justified bounded outcomes."
        ),
        "alpha_claim": False,
        "investability_claim": False,
        "portfolio_mutation_authorized": False,
        "claim_boundary": (
            "Two-source-family research reconciliation only. No score, rank, alpha, "
            "investability, trade recommendation, provider access, or portfolio mutation."
        ),
    }
    body["reconciliation_hash"] = domain_hash(RECONCILIATION_DOMAIN, body)
    return body


def load_verified_mu_nvda_reconciliation(
    *,
    mu_case_dir: Path = MU_CASE_DIR,
    nvda_case_dir: Path = NVDA_CASE_DIR,
    result_path: Path | None = None,
) -> dict[str, Any]:
    """Rebuild from banked source families and verify the persisted result exactly."""

    expected = build_mu_nvda_reconciliation(
        mu_claim=_load_json(mu_case_dir / "claim_evaluation.json"),
        mu_research=_load_json(mu_case_dir / "research_decision.json"),
        nvda_fact_set=_load_json(nvda_case_dir / "fact_set.json"),
        nvda_research=_load_json(nvda_case_dir / "research_decision.json"),
    )
    selected = result_path or (DEFAULT_OUTPUT_DIR / "reconciliation_result.json")
    stored = _load_json(selected)
    if canonical_document_bytes(stored) != canonical_document_bytes(expected):
        raise MuNvdaReconciliationError("RECONCILIATION_RESULT_MISMATCH")
    return stored


def build_decision_packet_markdown(result: Mapping[str, Any]) -> str:
    corroborated = "\n".join(
        f"- {row['claim']} (`{row['support']}`)"
        for row in result["corroboration"]
    )
    absent = "\n".join(f"- {value}" for value in result["not_established"])
    return (
        "# MU/NVDA G_supply Reconciliation\n\n"
        f"- case_id: `{result['case_id']}`\n"
        f"- disposition: `{result['disposition']}`\n"
        f"- research_action: `{result['research_action']}`\n"
        f"- portfolio_action: `{result['portfolio_action']}`\n"
        f"- corroboration_status: `{result['corroboration_status']}`\n"
        f"- contradiction_status: `{result['contradiction_status']}`\n"
        f"- reconciliation_hash: `{result['reconciliation_hash']}`\n\n"
        "## Indirect corroboration\n"
        f"{corroborated}\n\n"
        "## Not established\n"
        f"{absent}\n\n"
        "## Missing discriminator\n"
        f"{result['missing_discriminator']}\n\n"
        "## Decision\n"
        f"{result['rationale']}\n\n"
        "## Boundary\n"
        f"{result['claim_boundary']}\n"
    )


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data)
    temporary.replace(path)


def run_mu_nvda_reconciliation(
    *,
    mu_case_dir: Path = MU_CASE_DIR,
    nvda_case_dir: Path = NVDA_CASE_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    result = build_mu_nvda_reconciliation(
        mu_claim=_load_json(mu_case_dir / "claim_evaluation.json"),
        mu_research=_load_json(mu_case_dir / "research_decision.json"),
        nvda_fact_set=_load_json(nvda_case_dir / "fact_set.json"),
        nvda_research=_load_json(nvda_case_dir / "research_decision.json"),
    )
    _atomic_write(
        output_dir / "reconciliation_result.json",
        canonical_document_bytes(result) + b"\n",
    )
    _atomic_write(
        output_dir / "decision_packet.md",
        build_decision_packet_markdown(result).encode("utf-8"),
    )
    return result


if __name__ == "__main__":
    print(json.dumps(run_mu_nvda_reconciliation(), sort_keys=True))
