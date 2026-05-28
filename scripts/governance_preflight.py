from __future__ import annotations

import ast
import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)

from opportunity_engine.candidate_card_schema import validate_candidate_card


ARTIFACT_DRIFT_SENTINELS = (
    "governance_gate_v0.patch",
    "governance_gate_v0_implementation_20260526.zip",
)

EXPECTED_ROOT_FILES = (
    "scripts/governance_preflight.py",
    "scripts/boot_preflight.py",
    "docs/architecture/governance_boundary_policy.md",
    "tests/test_boot_preflight_governance.py",
    "opportunity_engine/candidate_card_schema.py",
)

ALLOWED_EXACT_UI_LABELS = frozenset(
    {
        "Research Portfolio / Replay Allocation",
        "Portfolio & Allocation",
        "Entry/Exit Strategy",
        "Entry/Exit Events",
        "ENTER/EXIT Events",
        "ENTER event",
        "EXIT event",
        "Strategy Research Replay",
        "Historical Replay Lifecycle Events",
        "Replay allocation",
        "Replay Allocation",
        "Replay allocation snapshot",
        "Current allocation",
        "Current allocation snapshot",
        "Replay Weight",
        "Current Weight",
        "Context Role",
        "Target weight",
        "Target Weight",
    }
)

FORBIDDEN_UI_PHRASES = (
    "Strong Buy",
    "STRONG BUY",
    "BUY AGGRESSIVE",
    "ENTER: BUY",
    "ENTER: STRONG BUY",
    "Latest Buys/Sells",
    "Buy/Sell Decision Log",
    "Portfolio & Allocation",
    "Entry/Exit Strategy",
    "Entry/Exit Events",
    "ENTER/EXIT Events",
    "ENTER event",
    "EXIT event",
    "Action Status",
    "Estimated Shares",
    "EXECUTE IF",
    "Qualifying Tickers",
    "Max Alpha",
    "MAX ALPHA",
    "Generate Option Yield",
    "Action Report",
    "Buy Zone",
    "investment recommendation",
    "recommendation",
    "trade alert",
    "broker order",
    "order action",
    "options trade",
    "option yield",
)

ACTION_UI_REGEXES = (
    re.compile(r"(?<![A-Za-z0-9_])broker\s+order(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])trade\s+alert(?![A-Za-z0-9_])", re.IGNORECASE),
    re.compile(r"(?<![A-Za-z0-9_])investment\s+recommendation(?![A-Za-z0-9_])", re.IGNORECASE),
)

FORBIDDEN_DYNAMIC_DISPLAY_VALUES = frozenset(
    {
        "BUY",
        "SELL",
        "HOLD",
        "WATCH",
        "STRONG BUY",
        "BUY AGGRESSIVE",
        "SELL CALL",
        "DO NOT SELL",
    }
)

ACTION_DISPLAY_NAMES = frozenset(
    {
        "action",
        "action_state",
        "action_status",
        "state",
        "rating",
        "recommendation",
        "signal",
    }
)

REQUIRED_CANDIDATE_FLAGS = {
    "not_validated": True,
    "not_actionable": True,
    "no_score": True,
    "no_rank": True,
    "no_buy_sell_signal": True,
    "no_buying_range": True,
    "no_alert": True,
    "no_broker_action": True,
}

REQUIRED_FORBIDDEN_OUTPUT_FLAGS = {
    "no_score": True,
    "no_rank": True,
    "no_buy_sell_signal": True,
    "no_buying_range": True,
    "no_alert": True,
    "no_broker_action": True,
}

ALLOWED_NEGATED_FIELD_KEYS = frozenset(
    REQUIRED_CANDIDATE_FLAGS | REQUIRED_FORBIDDEN_OUTPUT_FLAGS
)

FORBIDDEN_CANDIDATE_KEYS = frozenset(
    {
        "score",
        "alpha_score",
        "signal_score",
        "candidate_score",
        "factor_score",
        "factor_scores",
        "rank",
        "ranking",
        "candidate_rank",
        "upside",
        "upside_pct",
        "price_target",
        "target_price",
        "buy_sell_signal",
        "buy_signal",
        "sell_signal",
        "trade_signal",
        "buy_range",
        "buying_range",
        "entry_price",
        "stop_loss",
        "hold_signal",
        "alert",
        "alert_emitted",
        "broker_action",
        "broker_call",
        "order",
        "order_action",
        "buy_order",
        "sell_order",
    }
)

RUNTIME_FORBIDDEN_TOKENS = (
    "submit_order",
    "broker_call",
    "broker_action",
    "order_action",
    "buy_alert",
    "sell_alert",
    "entry_alert",
    "exit_alert",
    "rebalance_alert",
    "ticker_action_alert",
)

EXECUTION_INVENTORY_PATH = Path("docs/context/execution_module_inventory_current.json")
EXECUTION_INVENTORY_SCHEMA_VERSION = "execution-module-inventory/v0"
EXECUTION_INVENTORY_REVIEW_SCOPE_ID = "ROUND-20260528-EXECUTION-MODULE-INVENTORY"

EXECUTION_INVENTORY_EXACT_PATHS = (
    "execution/broker_api.py",
    "execution/rebalancer.py",
    "main_console.py",
    "main_bot_orchestrator.py",
    "scripts/test_rebalance.py",
    "scripts/test_alpaca_connection.py",
    "scripts/execution_bridge.py",
    "data/providers/alpaca_provider.py",
    "views/drift_monitor_view.py",
)

EXECUTION_INVENTORY_GLOBS = (
    "execution/execution_payload_*.json",
)

EXECUTION_ALLOWED_CLASSIFICATIONS = frozenset(
    {
        "dead_code_historical",
        "test_fixture",
        "ops_health_only",
        "research_only_blocked",
        "unknown_blocker",
    }
)

EXECUTION_BLOCKING_CLASSIFICATIONS = frozenset({"unknown_blocker"})

EXECUTION_SENSITIVE_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "AlpacaBroker": re.compile(r"(?<![A-Za-z0-9_])AlpacaBroker(?![A-Za-z0-9_])"),
    "PortfolioRebalancer": re.compile(r"(?<![A-Za-z0-9_])PortfolioRebalancer(?![A-Za-z0-9_])"),
    "submit_order": re.compile(r"(?<![A-Za-z0-9_])submit_order(?![A-Za-z0-9_])"),
    "close_all_positions": re.compile(r"(?<![A-Za-z0-9_])close_all_positions(?![A-Za-z0-9_])"),
    "execute_orders": re.compile(r"(?<![A-Za-z0-9_])execute_orders(?![A-Za-z0-9_])"),
    "execute_orders_with_idempotent_retry": re.compile(
        r"(?<![A-Za-z0-9_])execute_orders_with_idempotent_retry(?![A-Za-z0-9_])"
    ),
    "generate_execution_payload": re.compile(
        r"(?<![A-Za-z0-9_])generate_execution_payload(?![A-Za-z0-9_])"
    ),
    "notify_pm": re.compile(r"(?<![A-Za-z0-9_])notify_pm(?![A-Za-z0-9_])"),
    "DISCORD_WEBHOOK_URL": re.compile(r"(?<![A-Za-z0-9_])DISCORD_WEBHOOK_URL(?![A-Za-z0-9_])"),
    "requests.post": re.compile(r"(?<![A-Za-z0-9_])requests\.post(?![A-Za-z0-9_])"),
    "webhook": re.compile(r"(?<![A-Za-z0-9_])webhook(?![A-Za-z0-9_])", re.IGNORECASE),
    "tradeapi": re.compile(r"(?<![A-Za-z0-9_])tradeapi(?![A-Za-z0-9_])"),
    "APCA": re.compile(r"(?<![A-Za-z0-9_])APCA_[A-Za-z0-9_]+(?![A-Za-z0-9_])"),
    "ALPACA": re.compile(r"(?<![A-Za-z0-9_])ALPACA[A-Za-z0-9_]*(?![A-Za-z0-9_])"),
    "execution_orders": re.compile(r"(?<![A-Za-z0-9_])execution_orders(?![A-Za-z0-9_])"),
    "BUY_ACTION": re.compile(r'"action"\s*:\s*"BUY"'),
    "MARKET_ORDER_TYPE": re.compile(r'"order_type"\s*:\s*"MARKET"'),
    "DriftAlertManager": re.compile(r"(?<![A-Za-z0-9_])DriftAlertManager(?![A-Za-z0-9_])"),
    "process_drift_result": re.compile(r"(?<![A-Za-z0-9_])process_drift_result(?![A-Za-z0-9_])"),
    "acknowledge_alert": re.compile(r"(?<![A-Za-z0-9_])acknowledge_alert(?![A-Za-z0-9_])"),
    "resolve_alert": re.compile(r"(?<![A-Za-z0-9_])resolve_alert(?![A-Za-z0-9_])"),
}

FALSEY_ENV_VALUES = {"", "0", "false", "no", "off", "disabled"}
TRUTHY_ENV_VALUES = {"1", "true", "yes", "on", "enabled"}


@dataclass(frozen=True)
class GovernanceFinding:
    code: str
    severity: str
    path: str
    message: str
    line: int | None = None

    def format(self) -> str:
        location = self.path
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{self.code} {self.severity} {location} - {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "message": self.message,
        }


@dataclass(frozen=True)
class GovernancePreflightResult:
    passed: bool
    findings: tuple[GovernanceFinding, ...]
    checks: Mapping[str, Any]

    @property
    def status(self) -> str:
        if any(finding.severity == "fail" for finding in self.findings):
            return "FAIL"
        if self.findings:
            return "WARN"
        return "PASS"

    def to_dict(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for finding in self.findings:
            counts[finding.code] = counts.get(finding.code, 0) + 1
        return {
            "status": self.status,
            "passed": self.passed,
            "finding_count": len(self.findings),
            "counts": counts,
            "checks": dict(self.checks),
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass(frozen=True)
class ExecutionSurfaceEntry:
    path: str
    classification: str
    terms: tuple[str, ...]
    evidence_tokens: tuple[str, ...]
    rationale: str


@dataclass(frozen=True)
class ExecutionSurfaceHit:
    path: str
    term: str
    line: int | None


def run_governance_preflight(repo_root: str | Path) -> GovernancePreflightResult:
    root = _resolve_repo_root(repo_root)
    findings: list[GovernanceFinding] = []
    checks: dict[str, Any] = {"repo_root": root.as_posix()}

    _check_artifact_drift(root, findings, checks)
    _check_runtime_defaults(findings, checks)
    _check_ui_strings(root, findings, checks)
    _check_candidate_cards(root, findings, checks)
    _check_runtime_forbidden_tokens(root, findings, checks)
    _check_execution_module_inventory(root, findings, checks)

    return GovernancePreflightResult(
        passed=not any(finding.severity == "fail" for finding in findings),
        findings=tuple(findings),
        checks=checks,
    )


def _resolve_repo_root(repo_root: str | Path) -> Path:
    root = Path(repo_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repo root does not exist or is not a directory: {repo_root}")
    return root


def _check_artifact_drift(
    root: Path,
    findings: list[GovernanceFinding],
    checks: dict[str, Any],
) -> None:
    present_artifacts = [name for name in ARTIFACT_DRIFT_SENTINELS if _inside_existing_path(root, root / name)]
    missing: list[str] = []
    if present_artifacts:
        missing.extend(path for path in EXPECTED_ROOT_FILES if not (root / path).exists())
        missing.extend(_missing_integration_markers(root))
        if missing:
            findings.append(
                GovernanceFinding(
                    code="GOV-000",
                    severity="fail",
                    path=".",
                    message=(
                        "GOVERNANCE_ARTIFACT_NOT_APPLIED: "
                        f"artifacts present ({', '.join(present_artifacts)}) but missing "
                        f"{', '.join(sorted(missing))}"
                    ),
                )
            )
    checks["GOV-000"] = {
        "artifacts_present": present_artifacts,
        "missing_expected_root_items": sorted(missing),
        "expected_root_items": list(EXPECTED_ROOT_FILES),
    }


def _missing_integration_markers(root: Path) -> list[str]:
    missing: list[str] = []
    boot_path = root / "scripts" / "boot_preflight.py"
    if boot_path.exists():
        text = _read_text(boot_path)
        if "run_governance_preflight" not in text:
            missing.append("scripts/boot_preflight.py::run_governance_preflight integration")
        if "\"governance\"" not in text and "'governance'" not in text:
            missing.append("scripts/boot_preflight.py::checks['governance']")

    schema_path = root / "opportunity_engine" / "candidate_card_schema.py"
    if schema_path.exists():
        text = _read_text(schema_path)
        if "no_buying_range" not in text:
            missing.append("candidate_card_schema.py::no_buying_range")
        if "\"governance\"" not in text and "'governance'" not in text:
            missing.append("candidate_card_schema.py::required_governance")
    return missing


def _check_runtime_defaults(
    findings: list[GovernanceFinding],
    checks: dict[str, Any],
) -> None:
    mode = os.environ.get("T0_GOVERNANCE_MODE", "research_only").strip().lower()
    env_snapshot: dict[str, str | None] = {"T0_GOVERNANCE_MODE": mode}
    if mode != "research_only":
        findings.append(
            GovernanceFinding(
                code="GOV-001",
                severity="fail",
                path="environment",
                message="T0_GOVERNANCE_MODE must default to research_only",
            )
        )

    disabled_flags = (
        "T0_ALERTS_ENABLED",
        "T0_BROKER_ENABLED",
        "T0_ORDERS_ENABLED",
        "T0_ESCALATION_ENABLED",
        "T0_NOTIFIER_ENABLED",
    )
    for name in disabled_flags:
        value = os.environ.get(name)
        env_snapshot[name] = value
        if _env_is_truthy(value):
            findings.append(
                GovernanceFinding(
                    code="GOV-001",
                    severity="fail",
                    path="environment",
                    message=f"{name} must be disabled by default",
                )
            )

    ops_health_enabled = os.environ.get("T0_OPS_HEALTH_ALERTS_ENABLED")
    alert_scope = os.environ.get("T0_ALERT_SCOPE", "")
    env_snapshot["T0_OPS_HEALTH_ALERTS_ENABLED"] = ops_health_enabled
    env_snapshot["T0_ALERT_SCOPE"] = alert_scope
    if _env_is_truthy(ops_health_enabled) and alert_scope != "OPS_HEALTH_ONLY":
        findings.append(
            GovernanceFinding(
                code="GOV-001",
                severity="fail",
                path="environment",
                message="T0_OPS_HEALTH_ALERTS_ENABLED requires T0_ALERT_SCOPE=OPS_HEALTH_ONLY",
            )
        )

    checks["GOV-001"] = {"environment": env_snapshot}


def _check_ui_strings(
    root: Path,
    findings: list[GovernanceFinding],
    checks: dict[str, Any],
) -> None:
    files = list(_ui_files(root))
    scanned_literals = 0
    for path in files:
        text = _read_text(path)
        try:
            tree = ast.parse(text, filename=path.as_posix())
        except SyntaxError as exc:
            findings.append(
                GovernanceFinding(
                    code="GOV-002",
                    severity="fail",
                    path=_rel(root, path),
                    line=exc.lineno,
                    message=f"UI file could not be parsed: {exc.msg}",
                )
            )
            continue
        parent_by_node = _parent_by_node(tree)
        docstring_nodes = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if node in docstring_nodes or _is_internal_string_literal(node, parent_by_node):
                    continue
                scanned_literals += 1
                _check_forbidden_ui_phrase(root, path, node.value, getattr(node, "lineno", None), findings)
                _check_dynamic_display_literal(root, path, node, parent_by_node, findings)
    checks["GOV-002"] = {
        "files_scanned": [_rel(root, path) for path in files],
        "string_literals_scanned": scanned_literals,
        "allowed_exact_labels": sorted(ALLOWED_EXACT_UI_LABELS),
        "forbidden_phrases": list(FORBIDDEN_UI_PHRASES),
    }
    checks["GOV-005"] = {
        "status": "covered_by_GOV-002",
        "note": "Replay storage codes are allowed internally; action-shaped display phrases fail.",
    }


def _check_forbidden_ui_phrase(
    root: Path,
    path: Path,
    value: str,
    line: int | None,
    findings: list[GovernanceFinding],
) -> None:
    normalized_value = value.strip()
    if normalized_value in ALLOWED_EXACT_UI_LABELS:
        return

    match_value = _normalize_phrase_for_match(normalized_value)
    rel_path = _rel(root, path)
    for phrase in FORBIDDEN_UI_PHRASES:
        if _normalize_phrase_for_match(phrase) in match_value:
            findings.append(
                GovernanceFinding(
                    code="GOV-002",
                    severity="fail",
                    path=rel_path,
                    line=line,
                    message=f"forbidden UI-visible phrase '{phrase}' found in string literal: {value!r}",
                )
            )
            return
    for pattern in ACTION_UI_REGEXES:
        if pattern.search(match_value):
            findings.append(
                GovernanceFinding(
                    code="GOV-002",
                    severity="fail",
                    path=rel_path,
                    line=line,
                    message=f"forbidden action-shaped UI literal found: {value!r}",
                )
            )
            return


def _check_dynamic_display_literal(
    root: Path,
    path: Path,
    node: ast.Constant,
    parent_by_node: Mapping[ast.AST, ast.AST],
    findings: list[GovernanceFinding],
) -> None:
    value = str(node.value).strip().upper()
    if value not in FORBIDDEN_DYNAMIC_DISPLAY_VALUES:
        return

    parent = parent_by_node.get(node)
    key_name = _display_key_name(parent, node)
    if key_name not in ACTION_DISPLAY_NAMES:
        return

    findings.append(
        GovernanceFinding(
            code="GOV-002",
            severity="fail",
            path=_rel(root, path),
            line=getattr(node, "lineno", None),
            message=(
                f"action-shaped dynamic display value {node.value!r} found under "
                f"{key_name!r}; map it to research-only display copy before rendering"
            ),
        )
    )


def _display_key_name(parent: ast.AST | None, node: ast.Constant) -> str:
    if isinstance(parent, ast.Dict):
        for key, value in zip(parent.keys, parent.values):
            if value is node and isinstance(key, ast.Constant) and isinstance(key.value, str):
                return key.value.strip().lower()
    if isinstance(parent, ast.Assign):
        for target in parent.targets:
            if isinstance(target, ast.Name):
                return target.id.strip().lower()
    if isinstance(parent, ast.AnnAssign) and isinstance(parent.target, ast.Name):
        return parent.target.id.strip().lower()
    return ""


def _parent_by_node(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _docstring_nodes(tree: ast.AST) -> set[ast.AST]:
    nodes: set[ast.AST] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not body or not isinstance(body, list):
            continue
        first = body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            nodes.add(first.value)
    return nodes


def _is_internal_string_literal(node: ast.Constant, parent_by_node: Mapping[ast.AST, ast.AST]) -> bool:
    parent = parent_by_node.get(node)
    if isinstance(parent, ast.Compare):
        return True
    return False


def _normalize_phrase_for_match(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _check_candidate_cards(
    root: Path,
    findings: list[GovernanceFinding],
    checks: dict[str, Any],
) -> None:
    candidate_dir = root / "data" / "candidate_cards"
    card_paths = sorted(_confined_glob(root, candidate_dir, "*_candidate_card_v0.json"))
    for card_path in card_paths:
        card = _load_json(root, card_path, "GOV-003", findings)
        if not isinstance(card, Mapping):
            continue
        _check_required_candidate_flags(root, card_path, card, findings)
        _check_forbidden_candidate_keys(root, card_path, card, findings)
        manifest = _check_candidate_manifest_hash(root, card_path, card, findings)
        _check_canonical_candidate_schema(root, card_path, card, manifest, findings)
    checks["GOV-003"] = {"candidate_cards_scanned": [_rel(root, path) for path in card_paths]}
    checks["GOV-004"] = {"candidate_cards_scanned": [_rel(root, path) for path in card_paths]}
    checks["GOV-008"] = {"candidate_cards_scanned": [_rel(root, path) for path in card_paths]}


def _check_required_candidate_flags(
    root: Path,
    card_path: Path,
    card: Mapping[str, Any],
    findings: list[GovernanceFinding],
) -> None:
    governance = card.get("governance")
    if not isinstance(governance, Mapping):
        findings.append(
            GovernanceFinding(
                code="GOV-003",
                severity="fail",
                path=_rel(root, card_path),
                message="candidate card must include a governance object",
            )
        )
    else:
        for field_name, expected_value in REQUIRED_CANDIDATE_FLAGS.items():
            if governance.get(field_name) is not expected_value:
                findings.append(
                    GovernanceFinding(
                        code="GOV-003",
                        severity="fail",
                        path=_rel(root, card_path),
                        message=f"governance.{field_name} must be true",
                    )
                )

    forbidden_outputs = card.get("forbidden_outputs")
    if not isinstance(forbidden_outputs, Mapping):
        findings.append(
            GovernanceFinding(
                code="GOV-003",
                severity="fail",
                path=_rel(root, card_path),
                message="candidate card must include forbidden_outputs",
            )
        )
        return
    for field_name, expected_value in REQUIRED_FORBIDDEN_OUTPUT_FLAGS.items():
        if forbidden_outputs.get(field_name) is not expected_value:
            findings.append(
                GovernanceFinding(
                    code="GOV-003",
                    severity="fail",
                    path=_rel(root, card_path),
                    message=f"forbidden_outputs.{field_name} must be true",
                )
            )


def _check_forbidden_candidate_keys(
    root: Path,
    card_path: Path,
    card: Mapping[str, Any],
    findings: list[GovernanceFinding],
) -> None:
    for path, key in _walk_mapping_keys(card):
        normalized = _normalize_key(key)
        if normalized in ALLOWED_NEGATED_FIELD_KEYS:
            continue
        if normalized in FORBIDDEN_CANDIDATE_KEYS:
            field_path = ".".join((*path, key))
            findings.append(
                GovernanceFinding(
                    code="GOV-004",
                    severity="fail",
                    path=_rel(root, card_path),
                    message=f"forbidden candidate-card field present: {field_path}",
                )
            )


def _check_candidate_manifest_hash(
    root: Path,
    card_path: Path,
    card: Mapping[str, Any],
    findings: list[GovernanceFinding],
) -> Mapping[str, Any] | None:
    manifest_uri = str(card.get("manifest_uri") or "").strip()
    expected_manifest_path = card_path.with_suffix(".manifest.json")
    expected_manifest_uri = _rel(root, expected_manifest_path)
    expected_artifact_uri = _rel(root, card_path)
    if not manifest_uri:
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, card_path),
                message="candidate card manifest_uri is required for hash binding",
            )
        )
        return None
    if _normalize_path(manifest_uri) != expected_manifest_uri:
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, card_path),
                message=(
                    "candidate card manifest_uri must equal sibling manifest path "
                    f"{expected_manifest_uri}"
                ),
            )
        )
        return None
    manifest_path = root / manifest_uri
    try:
        manifest_path.resolve().relative_to(root.resolve())
    except ValueError:
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, card_path),
                message="candidate card manifest_uri must stay inside repository",
            )
        )
        return None
    if manifest_path.resolve() != expected_manifest_path.resolve():
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, card_path),
                message="candidate card manifest_uri must resolve to sibling manifest path",
            )
        )
        return None
    manifest = _load_json(root, manifest_path, "GOV-008", findings)
    if not isinstance(manifest, Mapping):
        return None

    artifact_uri = str(manifest.get("artifact_uri") or "").strip()
    if not artifact_uri:
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, manifest_path),
                message="manifest artifact_uri is required for candidate card binding",
            )
        )
    elif _normalize_path(artifact_uri) != expected_artifact_uri:
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, manifest_path),
                message="manifest artifact_uri does not match candidate card path",
            )
        )

    expected_sha = str(manifest.get("artifact_sha256") or "").strip().lower()
    actual_sha = hashlib.sha256(card_path.read_bytes()).hexdigest()
    if expected_sha != actual_sha:
        findings.append(
            GovernanceFinding(
                code="GOV-008",
                severity="fail",
                path=_rel(root, manifest_path),
                message="manifest artifact_sha256 does not match candidate card sha256",
            )
        )
    return manifest


def _check_canonical_candidate_schema(
    root: Path,
    card_path: Path,
    card: Mapping[str, Any],
    manifest: Mapping[str, Any] | None,
    findings: list[GovernanceFinding],
) -> None:
    result = validate_candidate_card(card, manifest=manifest)
    for error in result.errors:
        findings.append(
            GovernanceFinding(
                code="GOV-003",
                severity="fail",
                path=_rel(root, card_path),
                message=f"canonical candidate-card schema rejected card: {error}",
            )
        )


def _check_runtime_forbidden_tokens(
    root: Path,
    findings: list[GovernanceFinding],
    checks: dict[str, Any],
) -> None:
    files = list(_runtime_files(root))
    token_patterns = {
        token: re.compile(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])")
        for token in RUNTIME_FORBIDDEN_TOKENS
    }
    for path in files:
        for index, line in enumerate(_read_text(path).splitlines(), start=1):
            for token, pattern in token_patterns.items():
                if pattern.search(line):
                    findings.append(
                        GovernanceFinding(
                            code="GOV-007",
                            severity="fail",
                            path=_rel(root, path),
                            line=index,
                            message=f"forbidden runtime action token '{token}' found",
                        )
                    )
    checks["GOV-007"] = {
        "files_scanned": [_rel(root, path) for path in files],
        "forbidden_tokens": list(RUNTIME_FORBIDDEN_TOKENS),
    }


def _check_execution_module_inventory(
    root: Path,
    findings: list[GovernanceFinding],
    checks: dict[str, Any],
) -> None:
    files = tuple(_execution_inventory_files(root))
    hits = tuple(_execution_surface_hits(root, files))
    unique_hits: dict[tuple[str, str], ExecutionSurfaceHit] = {}
    for hit in hits:
        unique_hits.setdefault((hit.path, hit.term), hit)

    manifest_path = root / EXECUTION_INVENTORY_PATH
    entries = _load_execution_inventory(root, manifest_path, findings) if manifest_path.exists() else ()
    entry_by_path: dict[str, list[ExecutionSurfaceEntry]] = {}
    for entry in entries:
        entry_by_path.setdefault(entry.path, []).append(entry)

    if hits and not manifest_path.exists():
        findings.append(
            GovernanceFinding(
                code="GOV-009",
                severity="fail",
                path=EXECUTION_INVENTORY_PATH.as_posix(),
                message=(
                    "execution inventory manifest is required when broker/order/notifier "
                    "surfaces are present"
                ),
            )
        )

    covered_keys: set[tuple[str, str]] = set()
    for key, hit in unique_hits.items():
        matching_entries = [
            entry
            for entry in entry_by_path.get(hit.path, [])
            if hit.term in entry.terms
        ]
        if not matching_entries:
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=hit.path,
                    line=hit.line,
                    message=(
                        f"unclassified execution-sensitive term {hit.term!r}; "
                        "add an explicit execution inventory classification"
                    ),
                )
            )
            continue
        covered_keys.add(key)
        for entry in matching_entries:
            if entry.classification in EXECUTION_BLOCKING_CLASSIFICATIONS:
                findings.append(
                    GovernanceFinding(
                        code="GOV-009",
                        severity="fail",
                        path=entry.path,
                        line=hit.line,
                        message=(
                            f"execution surface {hit.term!r} is classified as "
                            f"{entry.classification}"
                        ),
                    )
                )
            _check_execution_entry_evidence(root, entry, findings)

    detected_keys = set(unique_hits)
    for entry in entries:
        path = root / entry.path
        if not _inside_existing_path(root, path):
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry.path,
                    message="execution inventory entry points to a missing path",
                )
            )
            continue
        for term in entry.terms:
            if term not in EXECUTION_SENSITIVE_PATTERNS:
                findings.append(
                    GovernanceFinding(
                        code="GOV-009",
                        severity="fail",
                        path=entry.path,
                        message=f"execution inventory term {term!r} is not a known scanner term",
                    )
                )
            elif (entry.path, term) not in detected_keys:
                findings.append(
                    GovernanceFinding(
                        code="GOV-009",
                        severity="fail",
                        path=entry.path,
                        message=f"execution inventory term {term!r} is stale or no longer detected",
                    )
                )

    boot_import_hits = _execution_import_hits_in_boot_surfaces(root)
    for rel_path, line in boot_import_hits:
        findings.append(
            GovernanceFinding(
                code="GOV-009",
                severity="fail",
                path=rel_path,
                line=line,
                message="default research boot surface imports execution modules",
            )
        )

    checks["GOV-009"] = {
        "status": "FAIL"
        if any(finding.code == "GOV-009" and finding.severity == "fail" for finding in findings)
        else "PASS",
        "manifest_path": EXECUTION_INVENTORY_PATH.as_posix(),
        "schema_version": EXECUTION_INVENTORY_SCHEMA_VERSION,
        "files_scanned": [_rel(root, path) for path in files],
        "surface_count": len(unique_hits),
        "covered_surface_count": len(covered_keys),
        "manifest_surface_count": len(entries),
        "classifications": sorted(EXECUTION_ALLOWED_CLASSIFICATIONS),
        "boot_import_hits": [
            {"path": rel_path, "line": line}
            for rel_path, line in boot_import_hits
        ],
        "detected_surfaces": [
            {
                "path": hit.path,
                "term": hit.term,
                "line": hit.line,
            }
            for hit in sorted(unique_hits.values(), key=lambda item: (item.path, item.term, item.line or 0))
        ],
    }


def _load_execution_inventory(
    root: Path,
    manifest_path: Path,
    findings: list[GovernanceFinding],
) -> tuple[ExecutionSurfaceEntry, ...]:
    payload = _load_json(root, manifest_path, "GOV-009", findings)
    rel_manifest = _rel(root, manifest_path)
    if not isinstance(payload, Mapping):
        return ()
    if payload.get("schema_version") != EXECUTION_INVENTORY_SCHEMA_VERSION:
        findings.append(
            GovernanceFinding(
                code="GOV-009",
                severity="fail",
                path=rel_manifest,
                message=f"execution inventory schema_version must be {EXECUTION_INVENTORY_SCHEMA_VERSION}",
            )
        )
    if payload.get("review_scope_id") != EXECUTION_INVENTORY_REVIEW_SCOPE_ID:
        findings.append(
            GovernanceFinding(
                code="GOV-009",
                severity="fail",
                path=rel_manifest,
                message=f"execution inventory review_scope_id must be {EXECUTION_INVENTORY_REVIEW_SCOPE_ID}",
            )
        )
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, list):
        findings.append(
            GovernanceFinding(
                code="GOV-009",
                severity="fail",
                path=rel_manifest,
                message="execution inventory surfaces must be a list",
            )
        )
        return ()

    entries: list[ExecutionSurfaceEntry] = []
    for index, raw_entry in enumerate(surfaces):
        entry_path = f"{rel_manifest}#/surfaces/{index}"
        if not isinstance(raw_entry, Mapping):
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry_path,
                    message="execution inventory surface entry must be an object",
                )
            )
            continue
        path = _normalize_path(str(raw_entry.get("path") or ""))
        classification = str(raw_entry.get("classification") or "").strip()
        terms = _string_tuple(raw_entry.get("terms"))
        evidence_tokens = _string_tuple(raw_entry.get("evidence_tokens"))
        rationale = str(raw_entry.get("rationale") or "").strip()
        if not path or path.startswith("../") or path.startswith("/"):
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry_path,
                    message="execution inventory path must be repo-relative",
                )
            )
            continue
        if classification not in EXECUTION_ALLOWED_CLASSIFICATIONS:
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry_path,
                    message=f"invalid execution inventory classification {classification!r}",
                )
            )
        if not terms:
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry_path,
                    message="execution inventory entry must list detected terms",
                )
            )
        if not evidence_tokens:
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry_path,
                    message="execution inventory entry must list evidence tokens",
                )
            )
        if not rationale:
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry_path,
                    message="execution inventory entry must include rationale",
                )
            )
        entries.append(
            ExecutionSurfaceEntry(
                path=path,
                classification=classification,
                terms=terms,
                evidence_tokens=evidence_tokens,
                rationale=rationale,
            )
        )
    return tuple(entries)


def _check_execution_entry_evidence(
    root: Path,
    entry: ExecutionSurfaceEntry,
    findings: list[GovernanceFinding],
) -> None:
    path = root / entry.path
    if not _inside_existing_path(root, path):
        return
    text = _read_text(path)
    for token in entry.evidence_tokens:
        if token not in text:
            findings.append(
                GovernanceFinding(
                    code="GOV-009",
                    severity="fail",
                    path=entry.path,
                    message=(
                        f"execution inventory evidence token {token!r} missing for "
                        f"classification {entry.classification}"
                    ),
                )
            )


def _execution_inventory_files(root: Path) -> Iterable[Path]:
    files: list[Path] = []
    for rel_path in EXECUTION_INVENTORY_EXACT_PATHS:
        path = root / rel_path
        if _inside_existing_path(root, path) and path.is_file():
            files.append(path.resolve())
    for pattern in EXECUTION_INVENTORY_GLOBS:
        for path in sorted(root.glob(pattern)):
            if _inside_existing_path(root, path) and path.is_file():
                files.append(path.resolve())
    return tuple(dict.fromkeys(files))


def _execution_surface_hits(root: Path, files: Iterable[Path]) -> Iterable[ExecutionSurfaceHit]:
    hits: list[ExecutionSurfaceHit] = []
    for path in files:
        rel_path = _rel(root, path)
        for line_number, line in enumerate(_read_text(path).splitlines(), start=1):
            for term, pattern in EXECUTION_SENSITIVE_PATTERNS.items():
                if pattern.search(line):
                    hits.append(ExecutionSurfaceHit(path=rel_path, term=term, line=line_number))
    return tuple(hits)


def _execution_import_hits_in_boot_surfaces(root: Path) -> tuple[tuple[str, int], ...]:
    files: list[Path] = []
    dashboard = root / "dashboard.py"
    if _inside_existing_path(root, dashboard) and dashboard.is_file():
        files.append(dashboard.resolve())
    views = root / "views"
    if _inside_existing_path(root, views) and views.is_dir():
        files.extend(_confined_glob(root, views, "*.py"))

    pattern = re.compile(r"^\s*(from\s+execution(?:\.|\s)|import\s+execution(?:\.|\s|$))")
    hits: list[tuple[str, int]] = []
    for path in files:
        for line_number, line in enumerate(_read_text(path).splitlines(), start=1):
            if pattern.search(line):
                hits.append((_rel(root, path), line_number))
    return tuple(hits)


def _ui_files(root: Path) -> Iterable[Path]:
    dashboard = root / "dashboard.py"
    if _inside_existing_path(root, dashboard):
        yield dashboard.resolve()
    views = root / "views"
    yield from _confined_glob(root, views, "*.py")


def _runtime_files(root: Path) -> Iterable[Path]:
    yield from _ui_files(root)


def _confined_glob(root: Path, directory: Path, pattern: str) -> Iterable[Path]:
    if not _inside_existing_path(root, directory) or not directory.is_dir():
        return ()
    return tuple(path.resolve() for path in sorted(directory.glob(pattern)) if _inside_existing_path(root, path))


def _load_json(
    root: Path,
    path: Path,
    code: str,
    findings: list[GovernanceFinding],
) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(
            GovernanceFinding(
                code=code,
                severity="fail",
                path=_rel(root, path),
                message="required JSON artifact is missing",
            )
        )
    except json.JSONDecodeError as exc:
        findings.append(
            GovernanceFinding(
                code=code,
                severity="fail",
                path=_rel(root, path),
                line=exc.lineno,
                message=f"JSON decode failure: {exc.msg}",
            )
        )
    return None


def _walk_mapping_keys(obj: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], str]]:
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            key_text = str(key)
            yield path, key_text
            yield from _walk_mapping_keys(value, (*path, key_text))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk_mapping_keys(value, (*path, str(index)))


def _env_is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in FALSEY_ENV_VALUES:
        return False
    if normalized in TRUTHY_ENV_VALUES:
        return True
    return bool(normalized)


def _inside_existing_path(root: Path, path: Path) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    return resolved.exists() and _is_relative_to(resolved, root)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace("-", "_").replace(" ", "_")


def _normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for raw_item in value:
        item = str(raw_item).strip()
        if item:
            items.append(item)
    return tuple(items)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Terminal Zero Governance Gate v0 preflight.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Repository root.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    return parser.parse_args(tuple(argv) if argv is not None else None)


def render_human(result: GovernancePreflightResult) -> str:
    payload = result.to_dict()
    lines = [
        f"Governance Gate v0: {payload['status']}",
        f"Findings: {payload['finding_count']}",
    ]
    if result.findings:
        lines.append("")
        lines.append("Findings:")
        lines.extend(f"- {finding.format()}" for finding in result.findings)
    return "\n".join(lines) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        result = run_governance_preflight(args.repo_root)
    except Exception as exc:
        print(f"Governance preflight v0: ERROR\n{exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True, ensure_ascii=True))
    else:
        print(render_human(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
