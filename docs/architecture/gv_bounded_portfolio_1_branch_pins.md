# GV-BOUNDED-PORTFOLIO-1 implementation branch pins

| Pin | Exact SHA | Role |
|---|---|---|
| Implementation branch base / promotion tip | `5fc2e4c01aa98ffe6ad9fcce4d1f9299c4aee6e4` | docs-only open of Bounded Portfolio; ACTIVE_BRIEF |
| **Immutable Replay code pin** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | tag `gv-replay-0-terminal`; **not** the branch point |
| Replay custody base | `03a5c922d250d615380bbd0d60e8fd636e4ec1c6` | tag `gv-replay-0-base` |
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | tag `gv-slice-0-terminal` |

Branch: `codex/gv-bounded-portfolio-1`

Law:

1. Branch from promotion tip `5fc2e4c`, never bare `0e4b93f` (would drop authority-opening docs).
2. Treat Replay modules banked at `0e4b93f` as frozen unless paying explicit Medium debt (R0-D1/D2).
3. Every bounded cycle must re-verify exact reconstruction via Replay 0 machinery.
4. Stop immediately on Replay byte/hash/certification drift.
