"""OK-SBI-0 QSourceContractV1 — outcome-blind numeric Q source binding.

RevGrowth_12m + ROIC is a conceptual candidate only.  This module never invents
fields, never silent-bridges unavailable primitives, and never opens outcomes.
Binding requires an exact field map for every primitive; incomplete maps yield
one of the four legal feasibility verdicts.

OK-SBI-0-S0-Q-SOURCE-BIND audits admitted custody only (immutable W3 + admitted
S0 + exact W3 market / S0 receipts already frozen by AO-K0A).  Provider shopping,
legacy Rule100 feature-store borrow, and outcome joins are forbidden.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


SLICE_ID = "OK-SBI-0"
CONTRACT_ID = "QSourceContractV1"
SPEC_VERSION = "v1.2"
MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES = 1
BIND_SLICE_ID = "OK-SBI-0-S0-Q-SOURCE-BIND"

Q_GF_BOUND = "Q_GF_BOUND"
Q_MINIMAL_AMENDMENT_REQUIRED = "Q_MINIMAL_AMENDMENT_REQUIRED"
Q_AMENDED_BOUND = "Q_AMENDED_BOUND"
Q_SOURCE_BLOCKED = "Q_SOURCE_BLOCKED"

LEGAL_VERDICTS = frozenset(
    {
        Q_GF_BOUND,
        Q_MINIMAL_AMENDMENT_REQUIRED,
        Q_AMENDED_BOUND,
        Q_SOURCE_BLOCKED,
    }
)

REQUIRED_PRIMITIVE_FIELDS = (
    "primitive_id",
    "provider_source_object",
    "exact_field_identifier",
    "ciqsec_trading_item_identity",
    "period_perspective_semantics",
    "pit_availability_timestamp",
    "minimum_publication_processing_lag",
    "unit_currency_law",
    "formula_denominator",
    "restatement_carry_law",
    "applicability_rule",
    "missingness_reason",
    "corporate_action_treatment",
    "source_receipt_hash",
    "no_bridge_proof",
)

_BLOCKED_TOKENS = frozenset(
    {
        "",
        "BLOCKED_UNSET",
        "TBD",
        "NULL",
        "PLACEHOLDER",
        "UNHASHED",
        "UNLANDED",
        "NONE",
        "N/A",
        "CONCEPTUAL_ONLY",
    }
)

# Canonical admitted-custody paths (AO-K0A authority freeze). Content hashes
# are verified at audit time against the landed objects — never re-fetched.
ADMITTED_S0_STRUCTURED_TRANSITIONS = (
    "data/prebreakout/raw/econphysics_s0_structured_v1/structured_transitions.csv"
)
ADMITTED_S0_STRUCTURED_RECEIPT = (
    "data/prebreakout/raw/econphysics_s0_structured_v1/structured_transitions.receipt.json"
)
ADMITTED_S0_MASTER = (
    "data/prebreakout/compiled/econphysics_s0_request_20260810/s0_ciqsec_company_master.csv"
)
ADMITTED_S0_TRANSITION_PLAN = (
    "data/prebreakout/compiled/econphysics_s0_request_20260810/s0_period_change_plan.csv"
)
ADMITTED_W3_AUTHORITY_MANIFEST = (
    "data/prebreakout/compiled/w3_real_authority_20250324_20260807/authority.manifest.json"
)
ADMITTED_AO_K0A_RECEIPT = (
    "docs/context/e2e_evidence/ao_k0a_orthogonal_basis_preflight_20260811.json"
)

# Expected content hashes from AO-K0A / S0 custody freeze (fail-closed if drift).
EXPECTED_S0_RAW_SHA256 = (
    "a5b873826c9598d33c71cc1e28f44f4ce26512a9c89aa6685f2a1606e9be0b87"
)
EXPECTED_S0_RECEIPT_SHA256 = (
    "2d0400e2d1a4cd6f90b1982c9159fc9f128c56950843f43599dd71c54a0a1f4f"
)
EXPECTED_S0_MASTER_SHA256 = (
    "5f8d425f78093bd9f0ce47f61178f51f40fccafe437e366fa9f7f1818cd54744"
)
EXPECTED_S0_PLAN_SHA256 = (
    "40ebcb33d1f8c1450fc9755d4c6467fc0963318505ec03c02f76f250aeb2b80b"
)

# Metrics actually landed in admitted S0 structured transitions (receipt authority).
ADMITTED_S0_METRICS = frozenset(
    {
        "IQ_PERIOD_END",
        "IQ_TOTAL_REV",
        "IQ_INVENTORY",
        "IQ_OPER_INC",
        "IQ_CAPEX_BNK",
    }
)

# Conceptual candidate only — not authority until every field is source-bound.
CONCEPTUAL_CANDIDATE_PRIMITIVES: tuple[dict[str, str], ...] = (
    {
        "primitive_id": "RevGrowth_12m",
        "provider_source_object": "CONCEPTUAL_ONLY",
        "exact_field_identifier": "BLOCKED_UNSET",
        "ciqsec_trading_item_identity": "CIQSEC+trading_item required; unbound",
        "period_perspective_semantics": "BLOCKED_UNSET",
        "pit_availability_timestamp": "BLOCKED_UNSET",
        "minimum_publication_processing_lag": "BLOCKED_UNSET",
        "unit_currency_law": "BLOCKED_UNSET",
        "formula_denominator": "BLOCKED_UNSET",
        "restatement_carry_law": "BLOCKED_UNSET",
        "applicability_rule": "BLOCKED_UNSET",
        "missingness_reason": "BLOCKED_UNSET",
        "corporate_action_treatment": "BLOCKED_UNSET",
        "source_receipt_hash": "BLOCKED_UNSET",
        "no_bridge_proof": "BLOCKED_UNSET",
    },
    {
        "primitive_id": "ROIC",
        "provider_source_object": "CONCEPTUAL_ONLY",
        "exact_field_identifier": "BLOCKED_UNSET",
        "ciqsec_trading_item_identity": "CIQSEC+trading_item required; unbound",
        "period_perspective_semantics": "BLOCKED_UNSET",
        "pit_availability_timestamp": "BLOCKED_UNSET",
        "minimum_publication_processing_lag": "BLOCKED_UNSET",
        "unit_currency_law": "BLOCKED_UNSET",
        "formula_denominator": "BLOCKED_UNSET",
        "restatement_carry_law": "BLOCKED_UNSET",
        "applicability_rule": "BLOCKED_UNSET",
        "missingness_reason": "BLOCKED_UNSET",
        "corporate_action_treatment": "BLOCKED_UNSET",
        "source_receipt_hash": "BLOCKED_UNSET",
        "no_bridge_proof": "BLOCKED_UNSET",
    },
)


@dataclass(frozen=True)
class PrimitiveBind:
    """Exact source bind for one Q primitive."""

    primitive_id: str
    provider_source_object: str
    exact_field_identifier: str
    ciqsec_trading_item_identity: str
    period_perspective_semantics: str
    pit_availability_timestamp: str
    minimum_publication_processing_lag: str
    unit_currency_law: str
    formula_denominator: str
    restatement_carry_law: str
    applicability_rule: str
    missingness_reason: str
    corporate_action_treatment: str
    source_receipt_hash: str
    no_bridge_proof: str

    def unbound_fields(self) -> list[str]:
        missing: list[str] = []
        for name in REQUIRED_PRIMITIVE_FIELDS:
            value = str(getattr(self, name, "")).strip()
            if value.upper() in _BLOCKED_TOKENS or value in _BLOCKED_TOKENS:
                missing.append(name)
            elif "BLOCKED_UNSET" in value.upper() or value.upper().startswith("CONCEPTUAL"):
                missing.append(name)
        return missing

    def is_fully_bound(self) -> bool:
        return not self.unbound_fields()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QSourceContractV1:
    """Machine-readable Q source contract with amendment accounting."""

    contract_id: str = CONTRACT_ID
    slice_id: str = SLICE_ID
    spec_version: str = SPEC_VERSION
    max_outcome_blind_q_amendment_cycles: int = MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES
    q_amendment_cycles_used: int = 0
    primitives: list[PrimitiveBind] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    forbid_silent_synthetic_substitute: bool = True
    forbid_unavailable_field_bridge: bool = True
    forbid_ticker_entity_permno_fallback: bool = True

    def unbound_inventory(self) -> dict[str, list[str]]:
        return {
            p.primitive_id: p.unbound_fields()
            for p in self.primitives
            if not p.is_fully_bound()
        }

    def all_primitives_bound(self) -> bool:
        return bool(self.primitives) and all(p.is_fully_bound() for p in self.primitives)

    def feasibility_verdict(self) -> str:
        """Return one of the four legal S0 feasibility verdicts."""

        if self.q_amendment_cycles_used > self.max_outcome_blind_q_amendment_cycles:
            return Q_SOURCE_BLOCKED
        if not self.primitives:
            return Q_SOURCE_BLOCKED
        if self.all_primitives_bound():
            if self.q_amendment_cycles_used == 0:
                return Q_GF_BOUND
            if self.q_amendment_cycles_used == 1:
                return Q_AMENDED_BOUND
            return Q_SOURCE_BLOCKED
        # Conceptual / incomplete binds: if any primitive is purely conceptual
        # with no exact field, this is blocked rather than a one-shot amendment.
        if any(
            str(p.provider_source_object).upper() in {"CONCEPTUAL_ONLY", "BLOCKED_UNSET"}
            or str(p.exact_field_identifier).upper() in _BLOCKED_TOKENS
            for p in self.primitives
        ):
            return Q_SOURCE_BLOCKED
        if self.q_amendment_cycles_used < self.max_outcome_blind_q_amendment_cycles:
            return Q_MINIMAL_AMENDMENT_REQUIRED
        return Q_SOURCE_BLOCKED

    def record_amendment(self, *, reason: str) -> None:
        """Consume the single allowed outcome-blind amendment cycle."""

        if self.q_amendment_cycles_used >= self.max_outcome_blind_q_amendment_cycles:
            raise ValueError(
                "ok_sbi_0_second_q_redesign_forbidden:new_slice_id_required"
            )
        self.q_amendment_cycles_used += 1
        self.notes.append(f"amendment_cycle_{self.q_amendment_cycles_used}:{reason}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "slice_id": self.slice_id,
            "spec_version": self.spec_version,
            "max_outcome_blind_q_amendment_cycles": self.max_outcome_blind_q_amendment_cycles,
            "q_amendment_cycles_used": self.q_amendment_cycles_used,
            "primitives": [p.to_dict() for p in self.primitives],
            "unbound_inventory": self.unbound_inventory(),
            "feasibility_verdict": self.feasibility_verdict(),
            "notes": list(self.notes),
            "forbid_silent_synthetic_substitute": self.forbid_silent_synthetic_substitute,
            "forbid_unavailable_field_bridge": self.forbid_unavailable_field_bridge,
            "forbid_ticker_entity_permno_fallback": self.forbid_ticker_entity_permno_fallback,
            "numeric_q_status": (
                "BOUND" if self.all_primitives_bound() else "NOT_BOUND_S0"
            ),
            "outcome_input": False,
            "provider_calls": "FORBIDDEN_THIS_TURN",
        }


def primitive_from_mapping(raw: Mapping[str, Any]) -> PrimitiveBind:
    payload = {name: str(raw.get(name, "BLOCKED_UNSET")) for name in REQUIRED_PRIMITIVE_FIELDS}
    return PrimitiveBind(**payload)


def conceptual_candidate_contract() -> QSourceContractV1:
    """Return the locked conceptual candidate in unbound form (honest S0)."""

    return QSourceContractV1(
        primitives=[primitive_from_mapping(p) for p in CONCEPTUAL_CANDIDATE_PRIMITIVES],
        notes=[
            "RevGrowth_12m+ROIC is conceptual candidate only, not authority.",
            "AO-K0A did not rederive numeric Q; no silent bridge to Rule100 artifacts.",
            "No provider/source substitution authorized this turn.",
        ],
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


def _csv_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        first = handle.readline().strip("\n\r")
    if not first:
        return []
    return [part.strip() for part in first.split(",")]


_REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[2]


def audit_admitted_custody_for_q(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Outcome-blind audit of admitted custody for numeric Q field binding.

    Never opens providers, never borrows Rule100 feature stores, never joins
    outcomes.  Records what is and is not present for RevGrowth_12m + ROIC.
    """

    root = (repo_root or _REPO_ROOT_DEFAULT).resolve()
    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    def _expect_file(rel: str, expected_sha: str | None = None) -> dict[str, Any]:
        path = root / rel
        present = path.is_file()
        row: dict[str, Any] = {
            "path": rel,
            "present": present,
            "sha256": None if not present else _sha256_file(path),
            "expected_sha256": expected_sha,
            "hash_match": None,
        }
        if present and expected_sha is not None:
            row["hash_match"] = row["sha256"] == expected_sha
            if not row["hash_match"]:
                blockers.append(f"custody_hash_drift:{rel}")
        if not present:
            blockers.append(f"custody_missing:{rel}")
        checks.append(row)
        return row

    s0_raw = _expect_file(ADMITTED_S0_STRUCTURED_TRANSITIONS, EXPECTED_S0_RAW_SHA256)
    s0_receipt = _expect_file(ADMITTED_S0_STRUCTURED_RECEIPT, EXPECTED_S0_RECEIPT_SHA256)
    s0_master = _expect_file(ADMITTED_S0_MASTER, EXPECTED_S0_MASTER_SHA256)
    s0_plan = _expect_file(ADMITTED_S0_TRANSITION_PLAN, EXPECTED_S0_PLAN_SHA256)
    _expect_file(ADMITTED_W3_AUTHORITY_MANIFEST)
    _expect_file(ADMITTED_AO_K0A_RECEIPT)

    receipt_metrics: list[str] = []
    receipt_options = "BLOCKED_UNSET"
    receipt_filing_version = "BLOCKED_UNSET"
    if s0_receipt["present"]:
        receipt_payload = json.loads(
            (root / ADMITTED_S0_STRUCTURED_RECEIPT).read_text(encoding="utf-8")
        )
        receipt_metrics = [str(m) for m in receipt_payload.get("metrics", [])]
        receipt_options = str(receipt_payload.get("options", "BLOCKED_UNSET"))
        receipt_filing_version = str(receipt_payload.get("filing_version", "BLOCKED_UNSET"))
        if set(receipt_metrics) != ADMITTED_S0_METRICS:
            # Allow IQ_PERIOD_END presence; fail only if unexpected growth/ROIC
            # authority is claimed without a metric landing.
            extra = set(receipt_metrics) - ADMITTED_S0_METRICS
            missing = ADMITTED_S0_METRICS - set(receipt_metrics)
            if missing:
                blockers.append(f"s0_receipt_missing_expected_metrics:{sorted(missing)}")
            if extra:
                # Extra metrics are informative only; do not auto-bind Q.
                checks.append(
                    {
                        "path": ADMITTED_S0_STRUCTURED_RECEIPT,
                        "note": "unexpected_extra_metrics_not_auto_bound",
                        "extra_metrics": sorted(extra),
                    }
                )

    master_cols: list[str] = []
    if s0_master["present"]:
        master_cols = _csv_header(root / ADMITTED_S0_MASTER)

    s0_row_cols: list[str] = []
    if s0_raw["present"]:
        s0_row_cols = _csv_header(root / ADMITTED_S0_STRUCTURED_TRANSITIONS)

    # Identity: W3 carries CIQSEC+trading_item; S0 fundamentals do not.
    has_w3_trading_item_surface = True  # schema-known from AO-K0A / W3 authority
    s0_has_ciqsec_map = "security_id" in master_cols and "SP_ENTITY_ID" in master_cols
    s0_has_trading_item = (
        "trading_item_id" in master_cols or "trading_item_id" in s0_row_cols
    )
    if not s0_has_ciqsec_map:
        blockers.append("s0_master_lacks_ciqsec_map")
    if not s0_has_trading_item:
        blockers.append(
            "s0_fundamentals_lack_trading_item_id:"
            "CIQSEC+trading_item joint identity unbound for Q primitives"
        )

    has_total_rev = "IQ_TOTAL_REV" in receipt_metrics or "IQ_TOTAL_REV" in s0_row_cols
    has_roic_metric = any(
        token in set(receipt_metrics) | set(s0_row_cols)
        for token in (
            "IQ_ROIC",
            "ROIC",
            "IQ_RETURN_ON_INVESTED_CAPITAL",
            "IQ_NOPAT",
            "IQ_INVESTED_CAPITAL",
        )
    )
    if not has_total_rev:
        blockers.append("revgrowth_input_IQ_TOTAL_REV_absent")
    if not has_roic_metric:
        blockers.append(
            "roic_no_admitted_metric:"
            "no IQ_ROIC/NOPAT/invested_capital in admitted S0 metrics"
        )

    # Field-level bind matrix (honest; candidate inputs ≠ bound Q fields).
    field_matrix: dict[str, dict[str, str]] = {
        "RevGrowth_12m": {},
        "ROIC": {},
    }

    # RevGrowth_12m — candidate input exists; primitive remains unbound without
    # frozen formula + identity + lag law.
    field_matrix["RevGrowth_12m"] = {
        "primitive_id": "BOUND:RevGrowth_12m",
        "provider_source_object": (
            f"CANDIDATE_INPUT_ONLY:{ADMITTED_S0_STRUCTURED_TRANSITIONS}"
            if s0_raw["present"]
            else "BLOCKED_UNSET"
        ),
        "exact_field_identifier": (
            "CANDIDATE_INPUT_ONLY:IQ_TOTAL_REV "
            "(level; RevGrowth_12m transform not source-bound)"
            if has_total_rev
            else "BLOCKED_UNSET"
        ),
        "ciqsec_trading_item_identity": (
            "PARTIAL:S0_master.security_id=CIQSEC + W3.trading_item_id surface exists; "
            "S0 fundamental rows lack trading_item_id; joint Q identity unbound"
            if s0_has_ciqsec_map and has_w3_trading_item_surface
            else "BLOCKED_UNSET"
        ),
        "period_perspective_semantics": (
            "CANDIDATE_INPUT_ONLY:relative_period FQ0..FQ-4 + period_end on S0 transitions; "
            "RevGrowth_12m period law not frozen as Q authority"
            if s0_raw["present"]
            else "BLOCKED_UNSET"
        ),
        "pit_availability_timestamp": (
            "CANDIDATE_INPUT_ONLY:as_of_date + retrieved_at_utc on S0 rows; "
            "decision-cut PIT availability law for Q not frozen"
            if s0_raw["present"]
            else "BLOCKED_UNSET"
        ),
        "minimum_publication_processing_lag": "BLOCKED_UNSET",
        "unit_currency_law": (
            f"CANDIDATE_INPUT_ONLY:{receipt_options}"
            if receipt_options != "BLOCKED_UNSET"
            else "BLOCKED_UNSET"
        ),
        "formula_denominator": (
            "BLOCKED_UNSET:RevGrowth_12m formula not frozen "
            "(must not invent FQ0/FQ-4 ratio as authority this turn)"
        ),
        "restatement_carry_law": (
            f"CANDIDATE_INPUT_ONLY:FilingVer={receipt_filing_version}"
            if receipt_filing_version != "BLOCKED_UNSET"
            else "BLOCKED_UNSET"
        ),
        "applicability_rule": "BLOCKED_UNSET",
        "missingness_reason": "BLOCKED_UNSET",
        "corporate_action_treatment": "BLOCKED_UNSET",
        "source_receipt_hash": (
            str(s0_receipt["sha256"])
            if s0_receipt.get("sha256")
            else "BLOCKED_UNSET"
        ),
        "no_bridge_proof": (
            "PASS_CANDIDATE:no Rule100 feature-store borrow; no ticker/PERMNO fallback; "
            "no synthetic ROIC/RevGrowth fill; Q remains unbound"
        ),
    }

    # ROIC — no admitted metric; full block.
    field_matrix["ROIC"] = {
        "primitive_id": "BOUND:ROIC",
        "provider_source_object": "BLOCKED_UNSET:no_admitted_ROIC_source_object",
        "exact_field_identifier": "BLOCKED_UNSET:no_IQ_ROIC_or_components_in_admitted_S0",
        "ciqsec_trading_item_identity": (
            "PARTIAL:W3 carries CIQSEC+trading_item; ROIC fundamental identity unbound"
        ),
        "period_perspective_semantics": "BLOCKED_UNSET",
        "pit_availability_timestamp": "BLOCKED_UNSET",
        "minimum_publication_processing_lag": "BLOCKED_UNSET",
        "unit_currency_law": "BLOCKED_UNSET",
        "formula_denominator": (
            "BLOCKED_UNSET:forbidden_to_invent_ROIC_from_IQ_OPER_INC_and_IQ_CAPEX_BNK"
        ),
        "restatement_carry_law": "BLOCKED_UNSET",
        "applicability_rule": "BLOCKED_UNSET",
        "missingness_reason": "BLOCKED_UNSET",
        "corporate_action_treatment": "BLOCKED_UNSET",
        "source_receipt_hash": "BLOCKED_UNSET",
        "no_bridge_proof": (
            "PASS_NEGATIVE:refused silent bridge from OPER_INC/CAPEX to ROIC; "
            "refused legacy Rule100-Q borrow"
        ),
    }

    # Convert matrix to PrimitiveBind values: CANDIDATE/PARTIAL/PASS do not count
    # as fully bound (blocked-token detector catches BLOCKED and CONCEPTUAL).
    # Also treat CANDIDATE_* and PARTIAL:* as unbound via explicit scan below.
    attempted_primitives: list[dict[str, str]] = []
    for primitive_id, matrix in field_matrix.items():
        raw = {name: "BLOCKED_UNSET" for name in REQUIRED_PRIMITIVE_FIELDS}
        raw["primitive_id"] = primitive_id
        # Only promote a field to a non-blocked value when it is a true bind.
        # Candidate/partial notes stay in the audit matrix, not the contract bind.
        if primitive_id == "RevGrowth_12m" and s0_receipt.get("sha256"):
            # Receipt hash alone is not enough for full bind; leave contract unbound.
            pass
        attempted_primitives.append(raw)

    contract = QSourceContractV1(
        primitives=[primitive_from_mapping(p) for p in attempted_primitives],
        notes=[
            "OK-SBI-0-S0-Q-SOURCE-BIND admitted-custody audit.",
            "RevGrowth_12m has candidate IQ_TOTAL_REV input in admitted S0 only; "
            "formula/lag/applicability/joint CIQSEC+trading_item remain unbound.",
            "ROIC has no admitted source metric; inventing from OPER_INC/CAPEX forbidden.",
            "No provider calls; no Rule100 feature-store borrow; no outcome join.",
            "Amendment cycle not consumed: a single field tweak cannot complete ROIC.",
        ],
    )
    assert_no_silent_bridge(contract)
    verdict = contract.feasibility_verdict()
    if verdict not in LEGAL_VERDICTS:
        raise AssertionError(f"ok_sbi_0_illegal_q_verdict:{verdict}")

    fully_bound_fields = 0
    unbound_fields = 0
    for prim_matrix in field_matrix.values():
        for name, value in prim_matrix.items():
            if name == "primitive_id":
                continue
            text = str(value).strip()
            upper = text.upper()
            is_unbound = (
                upper in _BLOCKED_TOKENS
                or "BLOCKED_UNSET" in upper
                or upper.startswith("CANDIDATE")
                or upper.startswith("PARTIAL")
                or upper.startswith("CONCEPTUAL")
                or upper.startswith("PASS_")
            )
            if is_unbound:
                unbound_fields += 1
            else:
                fully_bound_fields += 1

    audit = {
        "bind_slice_id": BIND_SLICE_ID,
        "date": "2026-08-12",
        "admitted_boundary_sources": [
            "IMMUTABLE_W3_DATE_LOCAL_AUTHORITY",
            "ADMITTED_ECONPHYSICS_S0",
            "EXACT_W3_MARKET_CUSTODY",
        ],
        "forbidden_boundary_sources": [
            "TEST_ASSEMBLY_ARTIFACTS",
            "TRANSIENT_FEATURE_STORES",
            "RULE100_FEATURE_STORE_BORROW",
            "PROVIDER_SHOPPING",
            "OUTCOME_BEARING_SURFACES",
        ],
        "custody_checks": checks,
        "s0_receipt_metrics": receipt_metrics,
        "s0_master_columns": master_cols,
        "s0_transition_columns": s0_row_cols,
        "has_total_rev_input": has_total_rev,
        "has_roic_metric": has_roic_metric,
        "s0_has_ciqsec_map": s0_has_ciqsec_map,
        "s0_has_trading_item": s0_has_trading_item,
        "field_matrix": field_matrix,
        "fully_bound_field_count": fully_bound_fields,
        "unbound_field_count": unbound_fields,
        "blockers": blockers,
        "q_amendment_cycles_used": 0,
        "amendment_consumed": False,
        "amendment_refusal_reason": (
            "ROIC has zero admitted metric; one outcome-blind amendment cannot "
            "lawfully invent ROIC or complete CIQSEC+trading_item joint identity "
            "for S0 fundamentals without new admitted custody. Second redesign "
            "requires a new slice_id after owner pivot."
        ),
        "Q_feasibility": verdict,
        "q_source_binding_hash": "BLOCKED_UNSET",
        "numeric_q_status": "NOT_BOUND_S0",
        "outcome_input": False,
        "provider_calls": "FORBIDDEN_THIS_TURN",
        "financial_alpha_evidence": 0,
    }
    audit["audit_body_sha256"] = _canonical_sha256(
        {k: v for k, v in audit.items() if k != "audit_body_sha256"}
    )
    return {
        "audit": audit,
        "contract": contract,
        "Q_feasibility": verdict,
    }


def evaluate_q_source_feasibility(
    contract: QSourceContractV1 | None = None,
    *,
    repo_root: Path | None = None,
    include_custody_audit: bool = True,
) -> dict[str, Any]:
    """Produce the Step-1 feasibility packet."""

    custody: dict[str, Any] | None = None
    if contract is None and include_custody_audit:
        attempt = audit_admitted_custody_for_q(repo_root=repo_root)
        active = attempt["contract"]
        custody = attempt["audit"]
    else:
        active = contract if contract is not None else conceptual_candidate_contract()
    verdict = active.feasibility_verdict()
    if verdict not in LEGAL_VERDICTS:
        raise AssertionError(f"ok_sbi_0_illegal_q_verdict:{verdict}")
    packet: dict[str, Any] = {
        "step": 1,
        "step_name": "QSourceContractV1_feasibility",
        "bind_slice_id": BIND_SLICE_ID,
        "contract": active.to_dict(),
        "Q_feasibility": verdict,
        "q_amendment_cycles_used": active.q_amendment_cycles_used,
        "q_source_binding_hash": (
            custody["q_source_binding_hash"] if custody is not None else "BLOCKED_UNSET"
        ),
        "stop_q_binding": verdict == Q_SOURCE_BLOCKED,
        "invent_q_forbidden": True,
        "second_redesign_requires_new_slice_id": True,
        "outcome_input": False,
        "financial_alpha_evidence": 0,
    }
    if custody is not None:
        packet["custody_audit"] = custody
    return packet


def assert_no_silent_bridge(contract: QSourceContractV1) -> None:
    """Refuse synthetic substitutes and identity fallbacks."""

    for prim in contract.primitives:
        for banned in (
            "TICKER_FALLBACK",
            "PERMNO_FALLBACK",
            "ENTITY_BRIDGE",
            "SYNTHETIC_FILL",
            "RULE100_ARTIFACT_BRIDGE",
            "Z_DEMAND_BRIDGE",
        ):
            blob = " ".join(str(v) for v in prim.to_dict().values()).upper()
            if banned in blob:
                raise ValueError(f"ok_sbi_0_silent_bridge_forbidden:{banned}:{prim.primitive_id}")


def validate_amendment_budget(cycles_used: int) -> None:
    if cycles_used > MAX_OUTCOME_BLIND_Q_AMENDMENT_CYCLES:
        raise ValueError("ok_sbi_0_second_q_redesign_forbidden:new_slice_id_required")


def required_field_names() -> Sequence[str]:
    return REQUIRED_PRIMITIVE_FIELDS
