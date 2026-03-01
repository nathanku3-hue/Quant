# Research Workspace

This folder stores research inputs and synthesis outputs used by planning and review.

## Inputs
- Put source PDFs directly in `docs/research/`.
- Use naming pattern: `YYYY-MM-DD_<domain>_<topic>.pdf`.
- Supported domains: `scientific`, `financial`, `medical`, `law`.

## Required Synthesis Files
- `docs/research/researches.md`: master cross-reference and findings delta log.
- Optional domain notes: `docs/research/researches-<domain>.md`.

## Extraction Contract
For each reviewed PDF, capture:
1. Core methodology (design, assumptions, sample/time horizon).
2. Core findings.
3. Delta vs prior `researches*.md` notes (new, conflicting, or confirming).
4. One-line logic chain.
5. One-line explicit formula (if paper provides one).
