"""Broker-free Alpha AppTest — no Alpaca, no broker env, network socket-denied."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from core.gv_v2_alpha0_case_close import (
    FUNCTIONAL_STAGE_OPERABLE,
    FUNCTIONAL_STAGE_PRE_ADJUDICATION,
    OPERATOR_CONFIRMATION_PHRASE,
    seal_pre_adjudication_case,
)

ROOT = Path(__file__).resolve().parents[2]

BROKER_ENV_KEYS = (
    "APCA_API_KEY_ID",
    "APCA_API_SECRET_KEY",
    "APCA_API_BASE_URL",
    "ALPACA_API_KEY",
    "ALPACA_API_SECRET",
    "ALPACA_BASE_URL",
)


@pytest.fixture
def broker_env_cleared(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in BROKER_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    # Do NOT set NO_PROXY=* (that bypasses dead proxies). Hard-deny sockets.
    monkeypatch.delenv("NO_PROXY", raising=False)
    monkeypatch.delenv("no_proxy", raising=False)


@pytest.fixture
def network_socket_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail closed on outbound TCP — stronger than proxy env tricks."""

    def _denied(*_a: object, **_k: object) -> None:
        raise OSError("ALPHA0_NETWORK_DENIED")

    monkeypatch.setattr(socket, "create_connection", _denied)
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda self, address: (_ for _ in ()).throw(OSError("ALPHA0_NETWORK_DENIED")),
    )
    monkeypatch.setattr(
        socket.socket,
        "connect_ex",
        lambda self, address: (_ for _ in ()).throw(OSError("ALPHA0_NETWORK_DENIED")),
    )


def test_alpha_app_module_has_no_broker_imports() -> None:
    import ast

    for path in (ROOT / "alpha_app.py", ROOT / "launch_alpha.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name.split(".")[0]
                    assert name not in {"alpaca", "dashboard", "broker_api"}
            elif isinstance(node, ast.ImportFrom) and node.module:
                name = node.module.split(".")[0]
                assert name not in {"alpaca", "dashboard", "broker_api", "execution"}
    src = (ROOT / "alpha_app.py").read_text(encoding="utf-8")
    assert "streamlit" in src
    assert "render_case_workspace" in src
    assert "verify=True" in src


def test_requirements_alpha_has_no_alpaca() -> None:
    lines = [
        ln.strip().lower()
        for ln in (ROOT / "requirements-alpha.txt").read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    joined = "\n".join(lines)
    assert "alpaca" not in joined
    assert any(ln.startswith("streamlit") for ln in lines)
    assert any(ln.startswith("pytest") for ln in lines)


def test_alpha_app_apptest_pre_adj_then_confirm(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    broker_env_cleared: None,
    network_socket_denied: None,
) -> None:
    """Full AppTest on alpha_app.py: sealed bank, verify load, UI confirm → OPERABLE."""

    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    case_dir = tmp_path / "case"
    seal_pre_adjudication_case(root=ROOT, case_dir=case_dir)
    assert not (case_dir / "result.json").exists()

    monkeypatch.chdir(ROOT)
    import views.gv_alpha0_case_workspace as ws

    monkeypatch.setattr(ws, "resolve_case_dir", lambda *, root=None: case_dir)

    def _load(*, root=None, verify=True):
        # Product path always verifies; refuse verify=False.
        if not verify:
            raise ws.GvAlpha0CaseWorkspaceError(
                "ALPHA0_CLOSE_VERIFY_REQUIRED_BEFORE_CONFIRM"
            )
        return __import__(
            "core.gv_v2_alpha0_case_close", fromlist=["load_banked_case_workspace"]
        ).load_banked_case_workspace(
            root=ROOT, case_dir=case_dir, verify=True, allow_pre_adjudication=True
        )

    monkeypatch.setattr(ws, "load_workspace_model", _load)

    import sys

    sys.modules.pop("alpaca", None)
    sys.modules.pop("alpaca.trading", None)

    app = AppTest.from_file(str(ROOT / "alpha_app.py"))
    app = app.run(timeout=90)
    assert not app.exception, app.exception

    headers = [el.value for el in app.header]
    assert "Case Workspace" in headers
    table_blob = "\n".join(str(getattr(t, "value", t)) for t in app.table)
    caption_blob = "\n".join(el.value for el in app.caption)
    body = table_blob + "\n" + caption_blob
    assert "PARTIAL" in body or "PARTIAL" in table_blob
    assert FUNCTIONAL_STAGE_PRE_ADJUDICATION in body or any(
        FUNCTIONAL_STAGE_PRE_ADJUDICATION in str(getattr(t, "value", t))
        for t in list(app.table) + list(app.caption) + list(app.subheader)
    )
    assert "SealVerifiedOnLoad" in table_blob or "True" in table_blob

    for inp in app.text_input:
        if getattr(inp, "key", None) == "alpha0_confirm_phrase" or "phrase" in str(
            getattr(inp, "label", "")
        ).lower():
            inp.set_value(OPERATOR_CONFIRMATION_PHRASE)
        if getattr(inp, "key", None) == "alpha0_operator_label":
            inp.set_value("SELF_LABELLED_OPERATOR")

    clicked = False
    for btn in app.button:
        label = str(getattr(btn, "label", "") or getattr(btn, "value", "") or "")
        if "Confirm" in label or getattr(btn, "key", None) == "alpha0_confirm_btn":
            btn.click()
            clicked = True
            break
    assert clicked, "confirm button not found"
    app = app.run(timeout=120)
    assert not app.exception, app.exception
    # RC1.2: confirm forces verified rerun → single certified paint.
    # Drain residual sealed paint (AppTest may need one extra run after st.rerun).
    for _ in range(3):
        sub_blob = "\n".join(str(getattr(s, "value", s)) for s in app.subheader)
        table_blob = "\n".join(str(getattr(t, "value", t)) for t in app.table)
        sealed_still = "sealed pre-adjudication" in sub_blob.lower() or (
            FUNCTIONAL_STAGE_PRE_ADJUDICATION in table_blob
        )
        if not sealed_still:
            break
        app = app.run(timeout=120)
        assert not app.exception, app.exception

    assert (case_dir / "operator_confirmation.json").is_file()
    assert (case_dir / "result.json").is_file()
    result = (case_dir / "result.json").read_text(encoding="utf-8")
    assert FUNCTIONAL_STAGE_OPERABLE in result
    assert "CASE_WORKSPACE_UI" in (case_dir / "operator_confirmation.json").read_text(
        encoding="utf-8"
    )

    # Fresh session load of the same bank must paint certified-only (no dual state).
    app2 = AppTest.from_file(str(ROOT / "alpha_app.py"))
    app2 = app2.run(timeout=90)
    assert not app2.exception, app2.exception
    subheaders = [str(getattr(s, "value", s)) for s in app2.subheader]
    table_after = "\n".join(str(getattr(t, "value", t)) for t in app2.table)
    success_after = "\n".join(str(getattr(s, "value", s)) for s in app2.success)
    captions = [str(getattr(c, "value", c)) for c in app2.caption]
    page_blob = "\n".join(subheaders + [table_after, success_after] + captions)
    assert any("certified multi-source case" in s.lower() for s in subheaders), subheaders
    assert not any("sealed pre-adjudication" in s.lower() for s in subheaders), subheaders
    assert not any("sealed pre-adjudication only" in c.lower() for c in captions)
    assert FUNCTIONAL_STAGE_OPERABLE in page_blob or FUNCTIONAL_STAGE_OPERABLE in table_after
    assert FUNCTIONAL_STAGE_PRE_ADJUDICATION not in table_after
    assert "NOT_YET" not in table_after
    # Confirm form is sealed-path only; certified reload must not offer it.
    assert not any(
        "Confirm NO_POSITION and certify" in str(getattr(b, "label", "") or "")
        for b in app2.button
    ), [getattr(b, "label", None) for b in app2.button]


def test_workspace_no_autobuild_on_missing_bank(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from views.gv_alpha0_case_workspace import (
        GvAlpha0CaseWorkspaceError,
        load_workspace_model,
    )
    import views.gv_alpha0_case_workspace as ws

    empty = tmp_path / "empty_case"
    empty.mkdir()
    monkeypatch.setattr(ws, "resolve_case_dir", lambda *, root=None: empty)
    with pytest.raises(GvAlpha0CaseWorkspaceError, match="CASE_BANK_MISSING|MISSING"):
        load_workspace_model(root=ROOT, verify=True)


def test_render_refuses_verify_false() -> None:
    from views.gv_alpha0_case_workspace import (
        GvAlpha0CaseWorkspaceError,
        render_case_workspace,
    )

    class _Fake:
        def header(self, body: str) -> None:
            return None

        def caption(self, body: str) -> None:
            return None

        def error(self, body: str) -> None:
            return None

        def subheader(self, body: str) -> None:
            return None

        def table(self, data: object) -> None:
            return None

        def info(self, body: str) -> None:
            return None

        def warning(self, body: str) -> None:
            return None

        def success(self, body: str) -> None:
            return None

        def markdown(self, body: str) -> None:
            return None

        def text_input(self, label: str, value: str = "", key: str | None = None) -> str:
            return value

        def button(self, label: str, key: str | None = None) -> bool:
            return False

    with pytest.raises(GvAlpha0CaseWorkspaceError, match="VERIFY_REQUIRED"):
        render_case_workspace(_Fake(), verify=False)


def test_render_certified_has_no_sealed_subheader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """RC1.2: certified paint must not include sealed pre-adjudication chrome."""

    from core.gv_v2_alpha0_case_close import (
        CAPTURE_SURFACE_UI,
        confirm_operator_and_certify,
        seal_pre_adjudication_case,
    )
    from views.gv_alpha0_case_workspace import render_case_workspace
    import views.gv_alpha0_case_workspace as ws

    case_dir = tmp_path / "case"
    seal_pre_adjudication_case(root=ROOT, case_dir=case_dir)
    confirm_operator_and_certify(
        root=ROOT,
        case_dir=case_dir,
        adjudicator_label="UNIT_TEST_OPERATOR",
        confirmed_at="2026-07-24T15:00:00.000000Z",
        confirmation_phrase=OPERATOR_CONFIRMATION_PHRASE,
        capture_surface=CAPTURE_SURFACE_UI,
    )
    monkeypatch.setattr(ws, "resolve_case_dir", lambda *, root=None: case_dir)

    class _Fake:
        def __init__(self) -> None:
            self.subheaders: list[str] = []
            self.tables: list[object] = []
            self.successes: list[str] = []
            self.captions: list[str] = []

        def header(self, body: str) -> None:
            return None

        def caption(self, body: str) -> None:
            self.captions.append(body)

        def error(self, body: str) -> None:
            return None

        def subheader(self, body: str) -> None:
            self.subheaders.append(body)

        def table(self, data: object) -> None:
            self.tables.append(data)

        def info(self, body: str) -> None:
            return None

        def warning(self, body: str) -> None:
            return None

        def success(self, body: str) -> None:
            self.successes.append(body)

        def markdown(self, body: str) -> None:
            return None

        def text_input(self, label: str, value: str = "", key: str | None = None) -> str:
            return value

        def button(self, label: str, key: str | None = None) -> bool:
            return False

    fake = _Fake()
    model = render_case_workspace(fake, root=ROOT, verify=True)
    assert model.get("functional_stage") == FUNCTIONAL_STAGE_OPERABLE
    assert any("certified multi-source case" in s.lower() for s in fake.subheaders)
    assert not any("sealed pre-adjudication" in s.lower() for s in fake.subheaders)
    assert fake.successes
    table_blob = "\n".join(str(t) for t in fake.tables)
    assert FUNCTIONAL_STAGE_PRE_ADJUDICATION not in table_blob
    assert "NOT_YET" not in table_blob
    assert not any("sealed pre-adjudication only" in c.lower() for c in fake.captions)


def test_launch_alpha_strips_broker_env_keys() -> None:
    launch = (ROOT / "launch_alpha.py").read_text(encoding="utf-8")
    for key in BROKER_ENV_KEYS:
        assert key in launch
    assert "BROKER_ENV_KEYS" in launch


def test_network_denied_blocks_socket(network_socket_denied: None) -> None:
    with pytest.raises(OSError, match="ALPHA0_NETWORK_DENIED"):
        socket.create_connection(("example.com", 443), timeout=1)
