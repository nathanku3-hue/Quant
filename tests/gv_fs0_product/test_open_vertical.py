from __future__ import annotations

import ast
import copy
from pathlib import Path
import sys
from typing import Any

import pytest

from core.gv_fs0_book import build_open_book, validate_schema
from core.gv_fs0_canonical import canonical_document_bytes, domain_hash
from core.gv_fs0_certify import (
    GvFs0CertificationError,
    _subprocess_environment,
    _supervise_process,
    build_open_certified_result,
    run_isolated_verifier,
)
from views.gv_fs0_portfolio_adapter import (
    GvFs0PresentationError,
    build_portfolio_view_model,
    render_gv_fs0_portfolio,
)

ROOT = Path(__file__).resolve().parents[2]
PERMANENT_BUNDLE = ROOT / "data" / "gv_fs0" / "gv_fs0_certified_bundle.json"


class FakeRenderer:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def subheader(self, body: str) -> None:
        self.calls.append(("subheader", body))

    def table(self, data: Any) -> None:
        self.calls.append(("table", data))

    def caption(self, body: str) -> None:
        self.calls.append(("caption", body))


def test_open_book_exact_economics_and_immutable_identity_chain() -> None:
    build = build_open_book()
    assert build.decision.action == "OPEN"
    assert build.decision.authority_tier == "MANUAL_OWNER_PAPER"
    assert build.decision.requested_quantity == 10
    assert build.book.book_id.startswith("BOOK_")
    assert len(build.book.events) == 13
    assert len(build.book.snapshots) == 5

    assert [
        {
            "session": row["session"],
            "shares": row["shares"],
            "cash": row["cash"],
            "receivables": row["receivables"],
            "market_value": row["market_value"],
            "nav": row["nav"],
            "session_contribution": row["session_contribution"],
            "cumulative_contribution": row["cumulative_contribution"],
        }
        for row in build.book.snapshots
    ] == [
        {
            "session": "2026-07-13",
            "shares": 0,
            "cash": "1000",
            "receivables": "0",
            "market_value": "0",
            "nav": "1000",
            "session_contribution": "0",
            "cumulative_contribution": "0",
        },
        {
            "session": "2026-07-14",
            "shares": 10,
            "cash": "899",
            "receivables": "0",
            "market_value": "110",
            "nav": "1009",
            "session_contribution": "9",
            "cumulative_contribution": "9",
        },
        {
            "session": "2026-07-15",
            "shares": 10,
            "cash": "899",
            "receivables": "5",
            "market_value": "120",
            "nav": "1024",
            "session_contribution": "15",
            "cumulative_contribution": "24",
        },
        {
            "session": "2026-07-16",
            "shares": 10,
            "cash": "904",
            "receivables": "0",
            "market_value": "130",
            "nav": "1034",
            "session_contribution": "10",
            "cumulative_contribution": "34",
        },
        {
            "session": "2026-07-17",
            "shares": 10,
            "cash": "904",
            "receivables": "0",
            "market_value": "140",
            "nav": "1044",
            "session_contribution": "10",
            "cumulative_contribution": "44",
        },
    ]
    assert [event["semantic_sequence"] for event in build.book.events] == list(range(13))
    assert len({event["event_id"] for event in build.book.events}) == 13
    assert build.book.economic_payload_hash == domain_hash(
        "GV-FS0:ECONOMIC_PAYLOAD:V1", build.book.economic_payload
    )


def test_verifier_input_contains_only_original_projected_inputs() -> None:
    verifier_input = build_open_book().verifier_input
    assert set(verifier_input) == {
        "schema_version",
        "protocol",
        "decision",
        "source_prices",
        "source_intents",
    }
    encoded = canonical_document_bytes(verifier_input)
    for prohibited in (
        b'"events"',
        b'"book_id"',
        b'"snapshot_id"',
        b'"certification_id"',
        b'"bundle_id"',
    ):
        assert prohibited not in encoded


def test_open_certification_runs_exactly_two_attempts_and_certifies() -> None:
    calls = 0

    def counted_runner(verifier_input: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return run_isolated_verifier(verifier_input)

    result = build_open_certified_result(counted_runner)
    assert calls == 2
    assert result["role"] == "OPEN"
    assert result["certification"]["certification_status"] == "CERTIFIED"
    assert set(result["certification"]["checks"].values()) == {"TRUE"}
    assert [attempt["ordinal"] for attempt in result["verifier_attempts"]] == [1, 2]
    assert [attempt["outcome"] for attempt in result["verifier_attempts"]] == [
        "RESULT",
        "RESULT",
    ]
    assert len(result["retained_verifier_results"]) == 1
    assert result["events"][-1]["event_type"] == "CERTIFICATION_REFERENCE"
    assert result["events"][-1]["semantic_sequence"] == 13
    assert result["snapshots"][-1]["nav"] == "1044"
    assert result["economic_payload_hash"] == result["certification"][
        "primary_economic_payload_hash"
    ]
    validate_schema(result, "gv_fs0_certified_decision_result_v1.schema.json")


def test_open_complete_runs_are_byte_identical() -> None:
    first = build_open_certified_result()
    second = build_open_certified_result()
    assert canonical_document_bytes(first) == canonical_document_bytes(second)
    assert first["certified_decision_result_hash"] == second[
        "certified_decision_result_hash"
    ]
    assert first["presentation"]["presentation_hash"] == second["presentation"][
        "presentation_hash"
    ]


def test_supervision_stops_at_output_cap(tmp_path: Path) -> None:
    script = tmp_path / "overflow.py"
    script.write_text(
        "import sys\nsys.stdout.buffer.write(b'x' * 65)\nsys.stdout.buffer.flush()\n",
        encoding="utf-8",
    )
    with pytest.raises(
        GvFs0CertificationError, match="VERIFIER_OUTPUT_LIMIT_EXCEEDED"
    ):
        _supervise_process(
            [str(Path(sys.executable).resolve()), "-I", "-X", "utf8", str(script)],
            cwd=str(tmp_path),
            env=_subprocess_environment(str(tmp_path)),
            deadline_seconds=2.0,
            shutdown_seconds=0.5,
            stdout_limit=64,
            stderr_limit=64,
        )


def test_supervision_stops_at_deadline(tmp_path: Path) -> None:
    script = tmp_path / "timeout.py"
    script.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
    with pytest.raises(GvFs0CertificationError, match="VERIFIER_TIMEOUT"):
        _supervise_process(
            [str(Path(sys.executable).resolve()), "-I", "-X", "utf8", str(script)],
            cwd=str(tmp_path),
            env=_subprocess_environment(str(tmp_path)),
            deadline_seconds=0.05,
            shutdown_seconds=0.5,
            stdout_limit=64,
            stderr_limit=64,
        )


def test_infrastructure_failure_still_executes_exactly_two_attempts() -> None:
    calls = 0

    def failing_runner(_verifier_input: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        raise GvFs0CertificationError("VERIFIER_TIMEOUT")

    with pytest.raises(GvFs0CertificationError, match="CERTIFICATION_BLOCKED"):
        build_open_certified_result(failing_runner)
    assert calls == 2


def test_disagreeing_verifier_attempt_blocks_certification() -> None:
    calls = 0

    def disagreeing_runner(verifier_input: dict[str, Any]) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        result = run_isolated_verifier(verifier_input)
        if calls == 1:
            return result
        changed = copy.deepcopy(result)
        changed["economic_payload"]["sessions"][-1]["nav"] = "1045"
        changed["economic_payload"]["final_state"]["nav"] = "1045"
        changed["canonical_payload_hash"] = domain_hash(
            "GV-FS0:ECONOMIC_PAYLOAD:V1", changed["economic_payload"]
        )
        without_hash = {
            key: value for key, value in changed.items() if key != "verifier_result_hash"
        }
        changed["verifier_result_hash"] = domain_hash(
            "GV-FS0:VERIFIER_RESULT:V1", without_hash
        )
        return changed

    with pytest.raises(GvFs0CertificationError, match="CERTIFICATION_BLOCKED"):
        build_open_certified_result(disagreeing_runner)
    assert calls == 2


def test_final_adapter_renders_injected_open_without_owning_truth() -> None:
    result = build_open_certified_result()
    renderer = FakeRenderer()
    model = render_gv_fs0_portfolio(
        renderer,
        presentation=result["presentation"],
        terminal_snapshot=result["snapshots"][-1],
        certification=result["certification"],
    )
    assert model["status"] == "CERTIFIED"
    assert model["title"].endswith("OPEN")
    row_map = {row["label"]: row["value"] for row in model["rows"]}
    assert row_map["Shares"] == "10"
    assert row_map["Cash"] == "904"
    assert row_map["NAV"] == "1044"
    assert row_map["CertificationStatus"] == "CERTIFIED"
    assert [name for name, _ in renderer.calls] == ["subheader", "table", "caption"]


def test_adapter_rejects_uncertified_or_mismatched_injection() -> None:
    result = build_open_certified_result()
    blocked = copy.deepcopy(result["certification"])
    blocked["certification_status"] = "BLOCKED"
    with pytest.raises(GvFs0PresentationError, match="CERTIFIED_INPUT_REQUIRED"):
        build_portfolio_view_model(
            presentation=result["presentation"],
            terminal_snapshot=result["snapshots"][-1],
            certification=blocked,
        )
    wrong_snapshot = copy.deepcopy(result["snapshots"][-1])
    wrong_snapshot["snapshot_id"] = "SNAP_" + "0" * 64
    with pytest.raises(GvFs0PresentationError, match="TERMINAL_SNAPSHOT_BINDING_INVALID"):
        build_portfolio_view_model(
            presentation=result["presentation"],
            terminal_snapshot=wrong_snapshot,
            certification=result["certification"],
        )


def test_f1a_never_publishes_permanent_bundle() -> None:
    before = PERMANENT_BUNDLE.read_bytes() if PERMANENT_BUNDLE.exists() else None
    build_open_certified_result()
    after = PERMANENT_BUNDLE.read_bytes() if PERMANENT_BUNDLE.exists() else None
    assert after == before
    assert before is None


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_static_product_boundaries() -> None:
    adapter_imports = _imports(ROOT / "views" / "gv_fs0_portfolio_adapter.py")
    assert not any(name.startswith("core.") for name in adapter_imports)
    assert not any(name.startswith("validation.") for name in adapter_imports)

    book_imports = _imports(ROOT / "core" / "gv_fs0_book.py")
    assert not any(name.startswith("views.") for name in book_imports)
    assert not any(name.startswith("validation.") for name in book_imports)
    assert not any(name.startswith("strategies.") for name in book_imports)

    certification_imports = _imports(ROOT / "core" / "gv_fs0_certify.py")
    assert not any(name.startswith("views.") for name in certification_imports)
    assert not any(name.startswith("validation.") for name in certification_imports)
    assert not any(name.startswith("strategies.") for name in certification_imports)
