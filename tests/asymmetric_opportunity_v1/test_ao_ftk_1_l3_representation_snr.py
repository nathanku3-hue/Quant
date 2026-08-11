"""AO-FTK-1 L0–L3 Representation/SNR gate — contract firewall tests."""

from __future__ import annotations

import json
from pathlib import Path

from research.asymmetric_opportunity_v1.ao_ftk_1_l3_contract import (
    DISPOSITION_JSON_REL,
    DISPOSITION_MD_REL,
    KERNEL_ID,
    PARENT_FREEZE_COMMIT,
    PARENT_FREEZE_REL,
    PREFLIGHT_JSON_REL,
    PREFLIGHT_MD_REL,
    SLICE_ID,
    assert_material_trial_counter_unchanged,
    assert_no_outcome_join_helpers_invoked,
    assert_no_qm_tokens_in_ftk1_api_surface,
    assert_valid_l3_disposition,
    load_disposition,
    load_preflight,
    validate_l3_disposition,
)


REPO = Path(__file__).resolve().parents[2]


def test_authority_artifacts_landed() -> None:
    paths = [
        REPO / DISPOSITION_JSON_REL,
        REPO / DISPOSITION_MD_REL,
        REPO / PREFLIGHT_JSON_REL,
        REPO / PREFLIGHT_MD_REL,
        REPO / PARENT_FREEZE_REL,
    ]
    for path in paths:
        assert path.is_file(), path


def test_l3_disposition_schema_validates() -> None:
    doc = load_disposition(REPO)
    errors = validate_l3_disposition(doc)
    assert errors == [], errors
    assert_valid_l3_disposition(doc)

    assert doc["slice_id"] == SLICE_ID
    assert doc["parent_freeze_commit"] == PARENT_FREEZE_COMMIT
    assert doc["kernel_id"] == KERNEL_ID
    assert doc["disposition"] == "PASS"
    assert doc["effective_dof_recommendation"] == 2
    assert doc["first_fail_R_if_any"] is None
    assert doc["next_phase_recommendation"] == "L4_CHARGED_SLICE_FREEZE"
    assert doc["phases_completed"] == ["L0", "L1", "L2", "L3"]


def test_r1_r8_all_pass_for_this_receipt() -> None:
    doc = load_disposition(REPO)
    rblock = doc["r1_r8"]
    for key, entry in rblock.items():
        assert entry["status"] == "PASS", key
        assert entry.get("evidence")
        assert entry.get("notes")


def test_no_qm_tokens_in_ftk1_api_surface() -> None:
    doc = load_disposition(REPO)
    assert_no_qm_tokens_in_ftk1_api_surface(doc)
    pre = load_preflight(REPO)
    assert pre["qm_park_unchanged"]["qm_terms_used"] is False
    assert pre["qm_park_unchanged"]["Q_SOURCE_STATUS"] == "Q_SOURCE_BLOCKED_TERMINAL"


def test_no_outcome_join_helpers_invoked() -> None:
    doc = load_disposition(REPO)
    assert_no_outcome_join_helpers_invoked(doc)
    assert doc["label_join_performed"] is False
    assert doc["outcome_open_authorized"] is False
    assert doc["runnable_evaluation"] is False


def test_material_trial_counter_unchanged() -> None:
    doc = load_disposition(REPO)
    assert_material_trial_counter_unchanged(doc)
    # Parent freeze budget must still read 3 remaining if present on disk.
    freeze = json.loads((REPO / PARENT_FREEZE_REL).read_text(encoding="utf-8"))
    assert freeze["search_budget"]["material_trials_remaining"] == 3
    assert freeze["search_budget"]["material_trials_charged_this_slice"] == 0


def test_l5_not_auto_authorized() -> None:
    doc = load_disposition(REPO)
    assert doc["l5_authorized"] is False
    assert doc["l5_auto_open"] is False
    assert doc["financial_alpha_evidence"] == 0
    assert "L5" not in str(doc["next_phase_recommendation"])


def test_preflight_continuous_preferred_encoding() -> None:
    pre = load_preflight(REPO)
    vectors = pre["L2_observation_contract"]["representation_vectors_under_test"]
    encodings = {v["vector_id"]: v["encoding"] for v in vectors}
    assert encodings["INV_ECONOMIC_LEVEL_LAG1_DELTA_CONTINUOUS"] == "CONTINUOUS"
    assert encodings["MARGIN_M1_CONTINUOUS_STATE"] == "CONTINUOUS"
    assert pre["L2_observation_contract"]["material_trial_debited"] is False
    assert pre["L2_observation_contract"]["labels_joined"] is False
