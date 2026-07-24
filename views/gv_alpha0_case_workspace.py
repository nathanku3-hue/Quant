"""Case Workspace — default Alpha product surface (adjudication capture).

Shows sealed multi-source pre-adjudication evidence: cutoff, both-family binds,
both-source excerpts + locators + overlap, coverage=PARTIAL (overlap only),
claim=CLAIM_INSUFFICIENT, sole permitted paper NO_POSITION.

Product bank is sealed-only until dogfood confirmation. Page load never
auto-builds. Operator confirmation requires a verified seal load first.
CERTIFIED_MULTI_SOURCE_CASE_OPERABLE is earned only by UI dogfood confirmation,
not offline bank tooling.

RC1.2: after UI confirm, force a verified full-page rerun so the page shows
exactly one canonical state (certified) — never sealed table + success toast.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from core.gv_v2_alpha0_case_close import (
    CASE_DIR,
    CAPTURE_SURFACE_UI,
    FUNCTIONAL_STAGE_OPERABLE,
    FUNCTIONAL_STAGE_PRE_ADJUDICATION,
    OPERATOR_CONFIRMATION_PHRASE,
    PORTFOLIO_ACTION_NO_POSITION,
    GvAlpha0CloseError,
    confirm_operator_and_certify,
    load_banked_case_workspace,
)

ROOT = Path(__file__).resolve().parents[1]


class WorkspaceRenderer(Protocol):
    def header(self, body: str) -> Any: ...

    def subheader(self, body: str) -> Any: ...

    def caption(self, body: str) -> Any: ...

    def markdown(self, body: str) -> Any: ...

    def table(self, data: Any) -> Any: ...

    def info(self, body: str) -> Any: ...

    def warning(self, body: str) -> Any: ...

    def error(self, body: str) -> Any: ...

    def success(self, body: str) -> Any: ...

    def text_input(self, label: str, value: str = "", key: str | None = None) -> str: ...

    def button(self, label: str, key: str | None = None) -> bool: ...


class GvAlpha0CaseWorkspaceError(ValueError):
    """Case Workspace presentation refused."""


def resolve_case_dir(*, root: Path | None = None) -> Path:
    """Banked case path only — never creates authority."""

    base = Path(root) if root is not None else ROOT
    return base / "data" / "gv_v2_alpha0" / "case_mu_g_supply_close_1"


def load_workspace_model(
    *,
    root: Path | None = None,
    verify: bool = True,
) -> dict[str, Any]:
    """Load banked seal/result. Fail closed if bank missing — no auto-build.

    Product path requires verify=True (rebuild-from-raw exact match of seal).
    """

    base = Path(root) if root is not None else ROOT
    case_dir = resolve_case_dir(root=base)
    try:
        return load_banked_case_workspace(
            root=base, case_dir=case_dir, verify=verify, allow_pre_adjudication=True
        )
    except GvAlpha0CloseError as exc:
        raise GvAlpha0CaseWorkspaceError(str(exc)) from exc


def build_workspace_rows(model: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"label": "CaseId", "value": str(model.get("case_id", ""))},
        {"label": "Subject", "value": str(model.get("subject_case", ""))},
        {"label": "Stage", "value": str(model.get("functional_stage", ""))},
        {
            "label": "SealVerifiedOnLoad",
            "value": str(bool(model.get("seal_verified_on_load"))),
        },
        {"label": "Cutoff", "value": str(model.get("cutoff_at", ""))},
        {"label": "FamilyOne", "value": str(model.get("family_one_id", ""))},
        {"label": "FamilyTwo", "value": str(model.get("family_two_id", ""))},
        {
            "label": "Coverage",
            "value": f"{model.get('coverage_status', '')} (overlap only; not claim sufficiency)",
        },
        {"label": "Claim", "value": str(model.get("claim_outcome", ""))},
        {
            "label": "PortfolioInvariant",
            "value": str(model.get("portfolio_action_invariant", "")),
        },
        {
            "label": "OperatorConfirmation",
            "value": (
                f"present={model.get('operator_confirmation_present', False)}; "
                f"surface={model.get('capture_surface', '') or '—'}; "
                f"hash={model.get('operator_confirmation_hash', '') or '—'}"
            ),
        },
        {
            "label": "Adjudication",
            "value": (
                f"kind={model.get('adjudication_kind', '')}; "
                f"present={model.get('adjudication_present', False)}; "
                f"self-labelled only"
            ),
        },
        {
            "label": "Certification",
            "value": str(model.get("certification_status", "") or "NOT_YET"),
        },
        {"label": "ResultHash", "value": str(model.get("result_hash", "") or "")},
        {
            "label": "Score/Observed",
            "value": (
                f"{model.get('shipped_product_score', 39)} / "
                f"{model.get('observed_comparison_count', 0)}"
            ),
        },
        {
            "label": "Publication",
            "value": "NOT_AUTHORIZED_ON_THIS_SURFACE (post dogfood only)",
        },
    ]


def build_evidence_rows(model: Mapping[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for panel in model.get("overlap_panels") or []:
        f1 = panel.get("family_one") or {}
        f2 = panel.get("family_two") or {}
        rows.append(
            {
                "overlap_id": str(panel.get("overlap_id", "")),
                "class": str(panel.get("overlap_class", "")),
                "family_one_id": str(f1.get("statement_id", "")),
                "family_one_locator": str(f1.get("document_locator", "")),
                "family_one_bytes": f"{f1.get('byte_start', '')}-{f1.get('byte_end', '')}",
                "family_one_excerpt": str(f1.get("exact_excerpt", ""))[:160],
                "family_two_id": str(f2.get("fact_id", "")),
                "family_two_locator": str(f2.get("document_locator", "")),
                "family_two_bytes": f"{f2.get('byte_start', '')}-{f2.get('byte_end', '')}",
                "family_two_excerpt": str(f2.get("exact_excerpt", ""))[:160],
            }
        )
    return rows


def apply_operator_confirmation(
    *,
    root: Path | None = None,
    adjudicator_label: str,
    confirmation_phrase: str,
    confirmed_at: str | None = None,
    require_verified_load: bool = True,
) -> dict[str, Any]:
    """Persist confirmation then certify. Requires prior verified seal load."""

    base = Path(root) if root is not None else ROOT
    case_dir = resolve_case_dir(root=base)
    if require_verified_load:
        # Fail closed if seal cannot be rebuilt/matched before writing confirmation.
        load_banked_case_workspace(
            root=base,
            case_dir=case_dir,
            verify=True,
            allow_pre_adjudication=True,
        )
    when = confirmed_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        return confirm_operator_and_certify(
            root=base,
            case_dir=case_dir,
            adjudicator_label=adjudicator_label,
            confirmed_at=when,
            confirmation_phrase=confirmation_phrase,
            capture_surface=CAPTURE_SURFACE_UI,
        )
    except GvAlpha0CloseError as exc:
        raise GvAlpha0CaseWorkspaceError(str(exc)) from exc


def _is_awaiting_confirmation(model: Mapping[str, Any]) -> bool:
    stage = str(model.get("functional_stage", ""))
    if bool(model.get("awaiting_operator_confirmation")):
        return True
    if stage == FUNCTIONAL_STAGE_PRE_ADJUDICATION:
        return True
    if not model.get("adjudication_present"):
        return True
    return False


def _render_evidence(st: WorkspaceRenderer, model: Mapping[str, Any]) -> None:
    st.subheader("Both-source evidence (excerpts · locators · overlap)")
    evidence_rows = build_evidence_rows(model)
    if evidence_rows:
        st.table(evidence_rows)
        for panel in model.get("overlap_panels") or []:
            f1 = panel.get("family_one") or {}
            f2 = panel.get("family_two") or {}
            st.markdown(
                f"**{panel.get('overlap_id', '')}** "
                f"({panel.get('overlap_class', '')})\n\n"
                f"- Family one `{f1.get('statement_id', '')}` @ "
                f"`{f1.get('document_locator', '')}` "
                f"bytes {f1.get('byte_start', '')}-{f1.get('byte_end', '')}\n"
                f"  > {f1.get('exact_excerpt', '')}\n"
                f"- Family two `{f2.get('fact_id', '')}` @ "
                f"`{f2.get('document_locator', '')}` "
                f"bytes {f2.get('byte_start', '')}-{f2.get('byte_end', '')}\n"
                f"  > {f2.get('exact_excerpt', '')}\n"
                f"- Note: {panel.get('note', '')}"
            )
    else:
        st.warning("Evidence panel empty — bank is incomplete.")

    st.info(
        "PARTIAL coverage ≠ claim sufficiency. "
        "Evidence cannot force a position without price-consistent expectations, "
        "business capture, and economics. Alpha remains paper NO_POSITION."
    )


def _render_sealed_pre_adjudication(
    st: WorkspaceRenderer,
    model: Mapping[str, Any],
    *,
    root: Path | None,
) -> dict[str, Any]:
    """Single canonical sealed state + confirm form. Never mixed with certified rows.

    Confirm controls are evaluated *before* sealed tables are painted so a click
    run never leaves sealed/NOT_YET rows on the same page as success chrome.
    """

    st.caption(
        "GV-ALPHA0-CLOSE · sealed pre-adjudication only. "
        "coverage=PARTIAL (overlap only) · claim=CLAIM_INSUFFICIENT · "
        "portfolio=NO_POSITION. Score 39 / observed 0. "
        "Confirm requires verified seal; OPERABLE is UI-dogfood only."
    )

    st.subheader("Operator confirmation (required before certification)")
    st.caption(
        f"Verified seal loaded. Type phrase `{OPERATOR_CONFIRMATION_PHRASE}` "
        f"and a self-labelled operator id, then confirm. Sole permitted action: "
        f"`{PORTFOLIO_ACTION_NO_POSITION}`. "
        f"UI confirm earns `{FUNCTIONAL_STAGE_OPERABLE}` (dogfood); "
        f"offline bank tooling cannot."
    )
    label = st.text_input(
        "Self-labelled operator id",
        value="SELF_LABELLED_OPERATOR",
        key="alpha0_operator_label",
    )
    phrase = st.text_input(
        "Confirmation phrase",
        value="",
        key="alpha0_confirm_phrase",
    )
    if st.button("Confirm NO_POSITION and certify", key="alpha0_confirm_btn"):
        try:
            apply_operator_confirmation(
                root=root,
                adjudicator_label=label.strip(),
                confirmation_phrase=phrase.strip(),
                require_verified_load=True,
            )
            # Full verified re-run → next paint is certified-only.
            rerun = getattr(st, "rerun", None)
            if callable(rerun):
                rerun()
            # AppTest / non-streamlit fallback: do not paint sealed rows this run.
            model = load_workspace_model(root=root, verify=True)
            return _render_certified_canonical(st, model)
        except GvAlpha0CaseWorkspaceError as exc:
            st.error(f"Confirmation refused: {exc}")
            # Fall through to sealed paint so operator can correct input.

    # Sealed evidence tables only when this run is not a successful confirm.
    st.subheader("MU G_supply — sealed pre-adjudication case")
    st.table(build_workspace_rows(model))
    _render_evidence(st, model)

    st.warning(
        "Publication of current decision and truth cutover are not authorized "
        "from this surface yet."
    )
    if model.get("claim_boundary"):
        st.caption(str(model["claim_boundary"]))
    return dict(model)


def _render_certified_canonical(
    st: WorkspaceRenderer,
    model: Mapping[str, Any],
) -> dict[str, Any]:
    """Single canonical certified state — no sealed/NOT_YET/pre-adjudication chrome."""

    stage = str(model.get("functional_stage", ""))
    st.caption(
        "GV-ALPHA0-CLOSE · certified multi-source case (canonical post-confirm). "
        "coverage=PARTIAL (overlap only) · claim=CLAIM_INSUFFICIENT · "
        f"stage=`{stage}` · surface=`{model.get('capture_surface') or '—'}`. "
        "Score 39 / observed 0. Publication not authorized on this surface."
    )
    st.subheader("MU G_supply — certified multi-source case")
    st.success(
        f"Operator confirmation present; certification="
        f"{model.get('certification_status')} · stage={stage} "
        f"· surface={model.get('capture_surface')} "
        f"· result_hash={(model.get('result_hash') or '')[:16]}…"
    )
    st.table(build_workspace_rows(model))
    _render_evidence(st, model)

    # Explicit absence of pre-adjudication / confirm chrome.
    st.warning(
        "Publication of current decision and truth cutover are not authorized "
        "from this surface yet."
    )
    if model.get("claim_boundary"):
        st.caption(str(model["claim_boundary"]))
    return dict(model)


def render_case_workspace(
    st: WorkspaceRenderer,
    *,
    root: Path | None = None,
    verify: bool = True,
) -> dict[str, Any]:
    """Render default Case Workspace for GV-ALPHA0-CLOSE.

    Product path must use verify=True. Confirmation is refused without a
    verified seal load (dogfood interaction, not offline pre-cert).

    Exactly one of sealed-pre-adjudication or certified-canonical is painted
    per run. Post-confirm always forces verified reload/rerun (RC1.2).
    """

    st.header("Case Workspace")
    if not verify:
        st.error("Case Workspace product path requires verify=True")
        st.caption("Authority refused: ALPHA0_CLOSE_VERIFY_REQUIRED_BEFORE_CONFIRM")
        raise GvAlpha0CaseWorkspaceError("ALPHA0_CLOSE_VERIFY_REQUIRED_BEFORE_CONFIRM")

    try:
        model = load_workspace_model(root=root, verify=True)
    except GvAlpha0CaseWorkspaceError as exc:
        st.error("Case Workspace unavailable")
        st.caption(f"Authority refused: {exc}")
        raise

    if not model.get("seal_verified_on_load"):
        st.error("Seal was not verified on load; confirmation blocked")
        raise GvAlpha0CaseWorkspaceError("ALPHA0_CLOSE_SEAL_NOT_VERIFIED_ON_LOAD")

    if _is_awaiting_confirmation(model):
        return _render_sealed_pre_adjudication(st, model, root=root)
    return _render_certified_canonical(st, model)


# Re-export banked path for tests.
DEFAULT_CASE_DIR = CASE_DIR
