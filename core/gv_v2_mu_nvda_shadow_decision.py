"""Independent same-evidence shadow decision for the banked MU/NVDA case.

The decision function consumes only decision-free source evidence: the admitted
MU claim evaluation and the independent NVDA fact set. It does not import or
read the existing research decision, portfolio decision, workspace, or book.
It is pure, deterministic, and cannot mutate portfolio authority.
"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from core.gv_fs0_canonical import domain_hash
from core.gv_v2_alpha0_source_family_two import FACT_SET_DOMAIN as NVDA_FACT_SET_DOMAIN
from core.gv_v2_b0b_official_source_intake import CLAIM_DOMAIN as MU_CLAIM_DOMAIN

ROOT = Path(__file__).resolve().parents[1]
MU_CLAIM_PATH = (
    ROOT
    / "data"
    / "gv_v2_b0b"
    / "mu_0000723125-26-000015"
    / "claim_evaluation.json"
)
NVDA_FACT_SET_PATH = (
    ROOT
    / "data"
    / "gv_v2_alpha0"
    / "family_two_nvda_0001045810-26-000052"
    / "fact_set.json"
)

SCHEMA_VERSION = "gv_v2_mu_nvda_shadow_decision_v1"
CASE_ID = "GV_V2_MU_NVDA_SAME_EVIDENCE_SHADOW_1"
DECISION_DOMAIN = "GV-V2:MU-NVDA:SAME-EVIDENCE-SHADOW:V1"
EVIDENCE_DOMAIN = "GV-V2:MU-NVDA:DECISION-FREE-EVIDENCE:V1"
ALLOWED_OUTCOMES = frozenset({"ADMIT", "REJECT", "ABSTAIN"})

_REQUIRED_MU_STATEMENT_IDS = frozenset(
    {
        "B0B_STMT_SUPPLY_ALLOCATION_001",
        "B0B_STMT_CONSTRAINED_SUPPLY_001",
        "B0B_STMT_DEMAND_EXCEEDS_SUPPLY_001",
        "B0B_STMT_SINGAPORE_EXPANSION_001",
    }
)
_REQUIRED_NVDA_FACT_IDS = frozenset(
    {
        "SF2_FACT_MEMORY_PRICES_001",
        "SF2_FACT_FOUNDRY_CAPACITY_001",
        "SF2_FACT_SCARCE_INPUTS_001",
        "SF2_FACT_SUPPLY_SHORTFALL_001",
        "SF2_FACT_NCNR_ORDERS_001",
    }
)


class MuNvdaShadowDecisionError(ValueError):
    """Fail-closed error for invalid decision-free shadow evidence."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MuNvdaShadowDecisionError(f"SHADOW_SOURCE_INVALID:{path}") from exc
    if not isinstance(value, dict):
        raise MuNvdaShadowDecisionError(f"SHADOW_SOURCE_OBJECT_REQUIRED:{path}")
    return value


def _require_domain_hash(
    payload: Mapping[str, Any], *, domain: str, hash_key: str, code: str
) -> None:
    body = {key: deepcopy(value) for key, value in payload.items() if key != hash_key}
    if payload.get(hash_key) != domain_hash(domain, body):
        raise MuNvdaShadowDecisionError(code)


def build_mu_nvda_shadow_decision(
    *,
    mu_claim: Mapping[str, Any],
    nvda_fact_set: Mapping[str, Any],
) -> dict[str, Any]:
    """Return an independent ADMIT/REJECT/ABSTAIN proposal from source evidence only."""

    _require_domain_hash(
        mu_claim,
        domain=MU_CLAIM_DOMAIN,
        hash_key="claim_evaluation_hash",
        code="SHADOW_MU_CLAIM_HASH_MISMATCH",
    )
    _require_domain_hash(
        nvda_fact_set,
        domain=NVDA_FACT_SET_DOMAIN,
        hash_key="fact_set_hash",
        code="SHADOW_NVDA_FACT_SET_HASH_MISMATCH",
    )
    if mu_claim.get("subject") != "MU":
        raise MuNvdaShadowDecisionError("SHADOW_MU_SUBJECT_MISMATCH")
    if nvda_fact_set.get("subject_case") != "MU_G_SUPPLY":
        raise MuNvdaShadowDecisionError("SHADOW_NVDA_CASE_MISMATCH")
    if nvda_fact_set.get("family_one_reference") != mu_claim.get("source_family_id"):
        raise MuNvdaShadowDecisionError("SHADOW_SOURCE_FAMILY_LINK_MISMATCH")

    mu_statement_ids = {
        str(row.get("statement_id")) for row in (mu_claim.get("statements") or [])
    }
    nvda_fact_ids = {
        str(row.get("fact_id")) for row in (nvda_fact_set.get("facts") or [])
    }
    if not _REQUIRED_MU_STATEMENT_IDS.issubset(mu_statement_ids):
        raise MuNvdaShadowDecisionError("SHADOW_MU_REQUIRED_STATEMENTS_MISSING")
    if not _REQUIRED_NVDA_FACT_IDS.issubset(nvda_fact_ids):
        raise MuNvdaShadowDecisionError("SHADOW_NVDA_REQUIRED_FACTS_MISSING")

    evidence_identity = {
        "source_families": [
            mu_claim["source_family_id"],
            nvda_fact_set["source_family_id"],
        ],
        "source_bindings": {
            "mu_claim_evaluation_hash": mu_claim["claim_evaluation_hash"],
            "nvda_fact_set_hash": nvda_fact_set["fact_set_hash"],
        },
        "mu_statement_ids": sorted(_REQUIRED_MU_STATEMENT_IDS),
        "nvda_fact_ids": sorted(_REQUIRED_NVDA_FACT_IDS),
    }
    evidence_hash = domain_hash(EVIDENCE_DOMAIN, evidence_identity)

    physical_supply_status = (
        (mu_claim.get("evidence_dimensions") or {}).get("physical_supply_telemetry")
    )
    direct_mu_physical_evidence = physical_supply_status == "PASS"
    independent_context_only = all(
        row.get("subject_case_relevance") == "MU_G_SUPPLY"
        and row.get("source_family_id") == nvda_fact_set.get("source_family_id")
        for row in (nvda_fact_set.get("facts") or [])
    )

    if direct_mu_physical_evidence:
        outcome = "ADMIT"
        principal_claim = (
            "Decision-free source evidence directly establishes Micron-specific physical "
            "supply persistence across the required observation boundary."
        )
        missing_discriminator = "None at the evidence-admission boundary."
        falsifier = (
            "Point-in-time Micron shipment, inventory, utilization, or channel evidence "
            "showing normalization or non-persistence across successive periods."
        )
    elif not independent_context_only:
        outcome = "REJECT"
        principal_claim = (
            "The independent source family is not coherently bound to the MU supply case, "
            "so the proposed interpretation is rejected."
        )
        missing_discriminator = (
            "A correctly bound independent source family with auditable MU-case relevance."
        )
        falsifier = (
            "A verified source-family linkage showing that every independent fact is "
            "correctly bound to the MU supply case."
        )
    else:
        outcome = "ABSTAIN"
        principal_claim = (
            "The same source evidence supports a broad supply-constrained memory environment "
            "but does not establish Micron-specific physical supply persistence."
        )
        missing_discriminator = (
            "Point-in-time Micron shipment, allocation, inventory, utilization, capacity-ramp, "
            "or channel evidence showing persistence across more than one period."
        )
        falsifier = (
            "Auditable point-in-time Micron-specific physical supply evidence showing "
            "persistence across successive periods would falsify the evidence-insufficiency claim."
        )

    if outcome not in ALLOWED_OUTCOMES:
        raise MuNvdaShadowDecisionError("SHADOW_OUTCOME_INVALID")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": CASE_ID,
        "subject": "MU",
        "outcome": outcome,
        "principal_claim": principal_claim,
        "missing_discriminator": missing_discriminator,
        "falsifier": falsifier,
        "evidence_identity": evidence_identity,
        "evidence_hash": evidence_hash,
        "portfolio_mutation_authorized": False,
        "reads_existing_portfolio_decision": False,
        "claim_boundary": (
            "Independent paper shadow proposal from decision-free banked evidence only. "
            "No score, rank, optimizer, portfolio mutation, broker path, or live-capital claim."
        ),
    }
    body["shadow_decision_hash"] = domain_hash(DECISION_DOMAIN, body)
    return body


def load_mu_nvda_shadow_decision(
    *,
    mu_claim_path: Path = MU_CLAIM_PATH,
    nvda_fact_set_path: Path = NVDA_FACT_SET_PATH,
) -> dict[str, Any]:
    """Load immutable evidence and return the deterministic pure shadow proposal."""

    return build_mu_nvda_shadow_decision(
        mu_claim=_load_json(mu_claim_path),
        nvda_fact_set=_load_json(nvda_fact_set_path),
    )


def verify_mu_nvda_shadow_decision(decision: Mapping[str, Any]) -> None:
    """Verify a returned shadow proposal without consulting portfolio state."""

    body = {
        key: deepcopy(value)
        for key, value in decision.items()
        if key != "shadow_decision_hash"
    }
    if decision.get("shadow_decision_hash") != domain_hash(DECISION_DOMAIN, body):
        raise MuNvdaShadowDecisionError("SHADOW_DECISION_HASH_MISMATCH")
    if decision.get("outcome") not in ALLOWED_OUTCOMES:
        raise MuNvdaShadowDecisionError("SHADOW_OUTCOME_INVALID")
    if decision.get("portfolio_mutation_authorized") is not False:
        raise MuNvdaShadowDecisionError("SHADOW_PORTFOLIO_MUTATION_PROHIBITED")
    if decision.get("reads_existing_portfolio_decision") is not False:
        raise MuNvdaShadowDecisionError("SHADOW_DECISION_INDEPENDENCE_INVALID")
