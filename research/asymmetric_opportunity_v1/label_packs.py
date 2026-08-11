"""OK-SBI-0 dual label packs — seal hashes only, never join outcomes.

Sealing ≠ opening.  Packs bind structural fields; any BLOCKED_UNSET field
prevents a complete seal and keeps runnable_evaluation false.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields
from typing import Any, Mapping


Q_CLOCK_LABEL_PACK = "Q_CLOCK_LABEL_PACK"
M_CLOCK_LABEL_PACK = "M_CLOCK_LABEL_PACK"

REQUIRED_PACK_FIELDS = (
    "pack_id",
    "clock_id",
    "horizons",
    "target_functional",
    "right_tail_cut",
    "catastrophe_cut",
    "maturity_cutoff",
    "eligible_decision_date_list",
    "row_key_set",
    "label_source_receipt",
)

_BLOCKED = frozenset(
    {
        "",
        "BLOCKED_UNSET",
        "TBD",
        "NULL",
        "PLACEHOLDER",
        "UNHASHED",
        "UNLANDED",
        "NONE",
    }
)


@dataclass
class LabelPackV1:
    pack_id: str
    clock_id: str
    horizons: str
    target_functional: str
    right_tail_cut: str
    catastrophe_cut: str
    maturity_cutoff: str
    eligible_decision_date_list: str
    row_key_set: str
    label_source_receipt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def blocked_fields(self) -> list[str]:
        out: list[str] = []
        for f in fields(self):
            value = str(getattr(self, f.name)).strip()
            if value.upper() in _BLOCKED or "BLOCKED_UNSET" in value.upper():
                out.append(f.name)
        return out

    def is_sealable(self) -> bool:
        return not self.blocked_fields()


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def default_q_clock_pack() -> LabelPackV1:
    """Q clock structure frozen; numeric cuts remain owner-gated."""

    return LabelPackV1(
        pack_id=Q_CLOCK_LABEL_PACK,
        clock_id="Q_CLOCK",
        horizons="9_to_15_months",
        target_functional="forward_net_payoff_distribution",
        right_tail_cut="BLOCKED_UNSET",
        catastrophe_cut="BLOCKED_UNSET",
        maturity_cutoff="BLOCKED_UNSET",
        eligible_decision_date_list="BLOCKED_UNSET",
        row_key_set="BLOCKED_UNSET",
        label_source_receipt="BLOCKED_UNSET",
    )


def default_m_clock_pack() -> LabelPackV1:
    """M clock structure frozen; numeric cuts remain owner-gated."""

    return LabelPackV1(
        pack_id=M_CLOCK_LABEL_PACK,
        clock_id="M_CLOCK",
        horizons="20_to_60_trading_days",
        target_functional="forward_net_payoff_distribution",
        right_tail_cut="BLOCKED_UNSET",
        catastrophe_cut="BLOCKED_UNSET",
        maturity_cutoff="BLOCKED_UNSET",
        eligible_decision_date_list="BLOCKED_UNSET",
        row_key_set="BLOCKED_UNSET",
        label_source_receipt="BLOCKED_UNSET",
    )


def seal_label_pack(pack: LabelPackV1) -> dict[str, Any]:
    """Hash a pack.  Complete seal only if no blocked fields.  Never joins labels."""

    payload = pack.to_dict()
    blocked = pack.blocked_fields()
    structural_hash = _canonical_sha256(payload)
    if blocked:
        return {
            "pack_id": pack.pack_id,
            "clock_id": pack.clock_id,
            "seal_status": "PACK_BLOCKED_UNSET",
            "sha256": None,
            "structural_fingerprint_sha256": structural_hash,
            "blocked_fields": blocked,
            "joined": False,
            "outcome_inspected": False,
            "seal_means_open": False,
        }
    return {
        "pack_id": pack.pack_id,
        "clock_id": pack.clock_id,
        "seal_status": "SEALED_UNJOINED",
        "sha256": structural_hash,
        "structural_fingerprint_sha256": structural_hash,
        "blocked_fields": [],
        "joined": False,
        "outcome_inspected": False,
        "seal_means_open": False,
    }


def seal_dual_label_packs(
    q_pack: LabelPackV1 | None = None,
    m_pack: LabelPackV1 | None = None,
) -> dict[str, Any]:
    q = seal_label_pack(q_pack or default_q_clock_pack())
    m = seal_label_pack(m_pack or default_m_clock_pack())
    return {
        "step": 5,
        "step_name": "seal_dual_label_packs",
        "Q_CLOCK_LABEL_PACK": q,
        "M_CLOCK_LABEL_PACK": m,
        "join_forbidden": True,
        "both_fully_sealed": q["seal_status"] == "SEALED_UNJOINED"
        and m["seal_status"] == "SEALED_UNJOINED",
    }


def refuse_outcome_join() -> None:
    raise ValueError("ok_sbi_0_outcome_join_forbidden:no_dev_open_carveout")
