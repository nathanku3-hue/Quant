# GV-PORTFOLIO-SCALE-1 implementation branch pins

| Pin | Exact SHA | Role |
|---|---|---|
| Implementation branch base / promotion tip | `eedf853566d009dc6a5af74397c316013b87a853` | docs-only open of Portfolio Scale |
| **Immutable Bounded terminal** | **`abaa814ce99ea78afadc33dd40506f4e13a742ef`** | tag `gv-bounded-portfolio-1-terminal`; **not** the branch point |
| **Immutable Replay terminal** | **`0e4b93fb370f67956502edc02e9c6f56ceb2eba3`** | tag `gv-replay-0-terminal` |
| Slice 0 product terminal | `85e6601742710f03e6cced7377b4be426cd4892f` | tag `gv-slice-0-terminal` |

Branch: `codex/gv-portfolio-scale-1`

Law:

1. Branch from promotion tip `eedf853`, never bare `abaa814` / `0e4b93f` alone.
2. Treat Bounded modules banked at `abaa814` and Replay modules at `0e4b93f` as frozen.
3. Scale is concurrent multi-session operation above Bounded V1 single-universe size (4 securities × N sessions).
4. Every cycle: re-run Bounded multi-cycle semantics and exact Replay gates; stop on any event/cert/reopen/book/ledger/hash drift.
