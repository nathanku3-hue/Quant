# PIT-SOURCE-AUTHORITY-1 Brief

Date: 2026-08-06
Branch: `codex/pit-source-authority-1`
Base: published main / terminal `9af5259d49969ba00db1fb3f4b3323ffb1d49205`
Tag: `pit-alpha-authority-cut-1-terminal` → exact `9af5259`
Status: `AUTHORIZED; IMPLEMENTATION ACTIVE; ALPHA CUT PUBLISHED; LIVE CLOSED`
Canonical score: `70/100` (product operability, custody, and replay only)
Limited Live: `CLOSED; NOT AUTHORIZED`

## Score boundary

`70/100` measures product operability, custody, and replay after the authority cut published to main:

- one Command Center product;
- bounded paper BUY entry;
- proposal/book/certification-bound SELL+BUY rotation;
- explicit confirm/reject;
- atomic persistence;
- certification lineage;
- exact fresh-process reopen;
- residual `0`;
- fresh-clone `123/123`;
- independent reviews;
- preservation `F_PASS`;
- hosted Windows/Ubuntu proof;
- main fast-forward and terminal tag at exact `9af5259`.

This is **not** an alpha, source-quality, realized-value, broker, or live-readiness score. No investment advice, provider programme, or live capital follows from `70/100`.

## Prior gate closed

`PIT-ALPHA-AUTHORITY-CUT-1` is published and closed:

| Item | Value |
|---|---|
| Cleanup C | `a92745118aab1a857a0251ce747cab247ba94605` |
| Product P | `9af5259d49969ba00db1fb3f4b3323ffb1d49205` |
| Pre-cut main | `e4cf949a895a5f987502328631ebac28af7d154f` |
| Remote main | equals `9af5259` (fast-forward only) |
| Terminal tag | `pit-alpha-authority-cut-1-terminal` → `9af5259` |

Roadmap deviation banked as explicit and beneficial: automatic Scale→Universe→Challenger progression abandoned; seventeen-commit replay replaced by two-commit final-state transplant; duplicate operator product deleted without compatibility.

## Active product slice

Replace manually entered `operator://` market authority with one independently traceable immutable bitemporal market packet that travels through the existing loop:

```text
immutable packet
→ existing PIT proposal
→ calculation-only preview
→ explicit confirm or reject-all
→ atomic persistence
→ certification lineage
→ exact fresh-process reopen
```

Required packet fields:

- source/permission identity;
- raw bytes or receipt;
- valid/effective time;
- retrieval/knowledge time;
- permanent instrument identity;
- value / unit / currency;
- schema version;
- SHA-256 content identity.

## Sole-product boundary

`dashboard.py` remains the only launchable operator product. Domain modules own accounting, persistence, certification, and replay. The dashboard owns request composition and display only.

## Closed scope

No new engine, provider programme, optimizer, broker, historical repair, compatibility layer, alpha claim, advice path, or Limited Live.

## Acceptance target

- [x] Immutable market packet schema and SHA-256 identity are fail-closed.
- [x] Entry and rotation accept the packet in place of free-text `operator://` market authority.
- [x] Preview → confirm → persist → certify → reopen preserves packet identity exactly.
- [x] Tamper/stale/missing fields fail closed.
- [x] Focused dashboard/PIT tests pass; no second application path.

## What Was Done

- Fast-forwarded `main` from `e4cf949` to exact `9af5259` (C+P only).
- Verified remote `main == 9af5259`.
- Tagged `pit-alpha-authority-cut-1-terminal` at that exact SHA.
- Opened `codex/pit-source-authority-1` from `9af5259`.
- Reassessed canonical maturity to `70/100` for operability/custody/replay only.

## What Is Locked

- `dashboard.py` sole product.
- Published tip `9af5259` and terminal tag must not be rewritten.
- Score claim boundary: operability/custody/replay only.
- Limited Live closed.
- No provider, optimizer, broker, historical repair, or compatibility work.

## What Is Next

- Ship one narrow functional slice: immutable market packet through the existing operated loop.
- Keep all other programmes closed.

## First Command

`python -m pytest -q tests/test_gv_pit_transaction.py tests/test_gv_pit_operated_capital.py tests/test_gv_pit_operated_rotation.py tests/test_dash_1_page_registry_shell.py`
