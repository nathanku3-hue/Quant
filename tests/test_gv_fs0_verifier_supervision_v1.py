from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/gv_fs0_certification_and_data_authority_contract.md"

RANKS = {
    "VERIFIER_SUPERVISION_INCOMPLETE": 10,
    "VERIFIER_TIMEOUT": 20,
    "VERIFIER_OUTPUT_LIMIT_EXCEEDED": 30,
    "VERIFIER_PROCESS_FAILED": 40,
    "VERIFIER_STDERR_NONEMPTY": 50,
    "VERIFIER_OUTPUT_INVALID_UTF8": 60,
    "VERIFIER_OUTPUT_NOT_CANONICAL": 70,
    "VERIFIER_OUTPUT_SCHEMA_INVALID": 80,
    "VERIFIER_RESULT_BINDING_INVALID": 90,
}


def _select_code(observed: set[str]) -> str | None:
    return min(observed, key=RANKS.__getitem__) if observed else None


def test_exact_process_invocation_and_isolation_flags_are_frozen() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "<absolute sys.executable> -I -X utf8 <absolute verifier script> --input <absolute declared input file>" in contract
    assert "imports only Python standard-library modules" in contract
    assert "emits exactly one canonical JSON document to stdout" in contract


def test_exact_deadlines_and_byte_limits_are_frozen() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    required = [
        "execution deadline             = 30.000 seconds",
        "shutdown observation interval  = 2.000 seconds",
        "stdout validity limit          = 1,048,576 bytes",
        "stderr validity limit          = 65,536 bytes",
        "stdout observation cap         = 1,048,577 bytes",
        "stderr observation cap         = 65,537 bytes",
    ]
    for line in required:
        assert line in contract


def test_stable_controller_rank_is_complete_and_ordered() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for code, rank in RANKS.items():
        assert re.search(rf"{rank}\s+{code}", contract)
    assert sorted(RANKS.values()) == list(range(10, 100, 10))


def test_lowest_rank_wins_independent_of_observation_order() -> None:
    observed = {
        "VERIFIER_PROCESS_FAILED",
        "VERIFIER_STDERR_NONEMPTY",
        "VERIFIER_OUTPUT_INVALID_UTF8",
    }
    assert _select_code(observed) == "VERIFIER_PROCESS_FAILED"
    reversed_observation = set(reversed(tuple(observed)))
    assert _select_code(reversed_observation) == "VERIFIER_PROCESS_FAILED"


def test_supervision_incomplete_precedes_all_other_observed_predicates() -> None:
    assert _select_code(set(RANKS)) == "VERIFIER_SUPERVISION_INCOMPLETE"


def test_simultaneous_timeout_and_output_limit_precedence_is_explicit() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    block = "1. VERIFIER_TIMEOUT\n2. VERIFIER_OUTPUT_LIMIT_EXCEEDED"
    assert block in contract
    assert _select_code({"VERIFIER_TIMEOUT", "VERIFIER_OUTPUT_LIMIT_EXCEEDED"}) == "VERIFIER_TIMEOUT"


def test_decode_pipeline_occurs_only_after_byte_limit_enforcement() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    required = "enforce byte limits\n-> strict UTF-8 decode\n-> canonical-document validation\n-> JSON parse\n-> schema validation\n-> binding validation"
    assert required in contract


def test_timeout_is_not_added_after_output_limit_initiated_termination() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    assert "later crossing the execution deadline during shutdown does not add `VERIFIER_TIMEOUT`" in contract


def test_minimal_environment_allowlists_are_platform_specific() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")
    for variable in ["HOME", "TMPDIR", "TZ", "LC_ALL", "LANG", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP"]:
        assert variable in contract
    assert "PATH may be included only if the selected Python distribution demonstrably requires it" in contract
