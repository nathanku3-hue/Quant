"""TRANSITION_RECOGNITION_v0 — shadow research contracts (no trial authority)."""

from research.transition_recognition_v0.l2_observation_contract import (
    L2_CONTRACT_PATH,
    L2_RECEIPT_PATH,
    assert_l2_contract_invariants,
    load_l2_contract,
)

__all__ = [
    "L2_CONTRACT_PATH",
    "L2_RECEIPT_PATH",
    "assert_l2_contract_invariants",
    "load_l2_contract",
]
