# GV-CHALLENGER-PROMOTION-1 implementation branch pins

| Pin | Exact SHA | Role |
|---|---|---|
| Implementation branch base / promotion tip | `cf771107d726458df6fc956a05337583407c6091` | docs-only open of Challenger (Live closed) |
| **Immutable Universe terminal** | **`dca67e36edc02dddf8c7ba446ac34f22562ee165`** | tag `gv-universe-scale-1-terminal`; **not** the branch point |
| **Immutable Portfolio Scale terminal** | **`c37abf00293937b9b99eb6e560f6b5b77a92ea1f`** | tag `gv-portfolio-scale-1-terminal` |
| **Immutable Bounded terminal** | **`abaa814ce99ea78afadc33dd40506f4e13a742ef`** | tag `gv-bounded-portfolio-1-terminal` |
| **Immutable Replay terminal** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | tag `gv-replay-0-terminal` |
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | tag `gv-slice-0-terminal` |

Branch: `codex/gv-challenger-promotion-1`

Law:

1. Branch from promotion tip `cf77110`, never bare terminals alone.
2. Treat Universe/Scale/Bounded/Replay modules as frozen at their terminals.
3. Shadow-first only: prospective challenger evidence; no production mutation.
4. **`GV-LIMITED-LIVE-1` remains CLOSED** without explicit owner authorization.
5. Every cycle: re-run Universe + Scale + Bounded + exact Replay; stop on drift.
