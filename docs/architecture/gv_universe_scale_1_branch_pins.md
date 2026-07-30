# GV-UNIVERSE-SCALE-1 implementation branch pins

| Pin | Exact SHA | Role |
|---|---|---|
| Implementation branch base / promotion tip | `133b6326b74af35388730662206a6495125d4474` | docs-only open of Universe Scale |
| **Immutable Portfolio Scale terminal** | **`c37abf00293937b9b99eb6e560f6b5b77a92ea1f`** | tag `gv-portfolio-scale-1-terminal`; **not** the branch point |
| **Immutable Bounded terminal** | **`abaa814ce99ea78afadc33dd40506f4e13a742ef`** | tag `gv-bounded-portfolio-1-terminal` |
| **Immutable Replay terminal** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | tag `gv-replay-0-terminal` |
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | tag `gv-slice-0-terminal` |

Branch: `codex/gv-universe-scale-1`

Law:

1. Branch from promotion tip `133b632`, never bare `c37abf0` / `abaa814` / `0e4b93f` alone.
2. Treat Scale modules banked at `c37abf0`, Bounded at `abaa814`, and Replay at `0e4b93f` as frozen.
3. Universe declared security slots must exceed Scale multi-session fixture slots (3 × 4 = 12).
4. Every cycle: re-run Scale multi-session control, Bounded multi-cycle semantics, and exact Replay; stop on any event/cert/reopen/book/ledger/hash drift.
