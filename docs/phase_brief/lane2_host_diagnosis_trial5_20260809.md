# Lane 2 host diagnosis — Trial 5 series (2026-08-09)

## Custody / non-claims

- Worktree: `.worktrees/devspace-053ca7a4f582fb3e`
- Backfill: **still 1/34** — only `market_backfill_to_20240705/part_000_20230814_20230822.csv` (530 rows / 76 entities)
- Warmup: 33/33 intact
- `financial_alpha_evidence` remains **0**
- No A1/A2 admission; no Parent/Child mutation

## What this session did

1. Confirmed orphan thrash Excel (was pid 23804 earlier; at cleanup time residual was 22272 with `S&P Capital IQ Pro` + workbook).
2. Host cleanup + Quark `LoadBehavior=0` verified.
3. Controlled trials only for **part_001 / index=1** (never full 1–33 fan-out).
4. Fixed a **dismisser footgun**, then stopped after thrash degraded the host further.

## Trial matrix

| Trial | Config | Outcome |
|---|---|---|
| 4 (prior) | EntityBatch=25, quarantine session | Died stuck on first batch `FROM=0 TO=24`; empty `.err` (COM hang / host death) |
| **5a** | EntityBatch=8, visible boot, broad dismisser | `EXCEL_NEWOBJECT_OK` → `excel_process_died` during boot (~35s). **No OWNED_READY**. No Application Error for this death. |
| **5b** | Same + **safe dismisser** (never close CIQ shell) | `OWNED_READY` + **`SMOKE_OK` 1×1** (`TR=[-2.17] CLOSE=[7.20] VOL=[9,641]`) → first `ENTITY_BATCH FROM=0 TO=7 N=8` → **`excel_process_died`** mid-bulk. |
| **5c** | EntityBatch=1 serial | Boot OK → **`ciq_addin_object_missing_after_quarantine`** after ~2 min wait (host degraded by thrash). |

## Root causes (ranked, evidence-based)

### A. Dismisser over-aggression (fixed) — caused Trial 5a

Naive dismiss treated **`S&P Capital IQ Pro`** (main CIQ WinForms shell) as a modal and could `WM_CLOSE` it.

- Fix applied in `tmp/lane2_host_cleanup.ps1` and `tmp/aov0_backfill_trial5_tiny.ps1`:
  - Only sticky prompts: Migrate/PresCenter, Safe Mode, add-in problem dialogs.
  - Never touch `XLMAIN` or title `S&P Capital IQ Pro`.
  - `WM_CLOSE` only for Migrate-family titles.
  - Also avoid reserved PowerShell `$PID` in kill loops.

### B. Bulk SPGTable still kills Excel (primary remaining) — Trial 5b

With healthy 1×1 smoke on the same session:

- Smoke fills instantly (t=0s) with real market cells.
- First multi-name / multi-day batch (even N=8×7) dies the Excel process.
- Matches prior pattern: single-name COM OK; unattended bulk hangs/crashes.

### C. Post-thrash CIQ object null — Trial 5c

After 5b death, next boot never got `COMAddIns['SNL.Clients.Office.Excel.ExcelAddIn'].Object` non-null within ~50×2s.

### D. Persistent host damage factors (unchanged from earlier diagnosis)

| Factor | Evidence |
|---|---|
| Quark Drive crash DLL still on disk | `...\Quark\drive\QuarkDriveOfficeAddin_20260805045915483_7_0_5_931.dll` (earlier Application Error 0xc0000005 / 0xc0000409) |
| Quark registry disabled | HKCU `QuarkDriveExcelAddin.Component` LoadBehavior=**0** |
| SPGMI.ExcelShell user-disabled | HKCU LoadBehavior=**0** (from earlier “disable this add-in?”); HKLM still **3** |
| Main CIQ add-in | HKLM `SNL.Clients.Office.Excel.ExcelAddIn` LoadBehavior=**3** |
| Earlier crash storm | KERNELBASE 0xe0000002 ×5; Safe Mode accepted 15:33; Quark faults 14:41–15:31 |

## What is still healthy

- Warmup market custody 33/33
- Backfill `part_000` quality (530×76)
- SOFR historical custody
- Master 109 identity wiring
- A1/A2 replay code path (not reached; not the blocker)
- After dismisser fix: **1×1 SPGTable still returns real data** when the host is briefly healthy

## Stop rule applied

Two controlled bulk failures on the same gate (`ENTITY_BATCH` start → host death) after one successful smoke:

- **No further unattended bulk restarts this session.**
- Do not count another New-Object loop as progress until interactive host recovery succeeds.

## Ordered recovery before next capture

1. **Interactive Excel only** (human): start Excel once, wait for CIQ login/shell, dismiss any Migrate/Safe Mode/add-in prompts manually.
2. Confirm ribbon CIQ is live; run a manual 1×1 `SPGTable` in the UI (or re-run `tmp/spg_probe_live.ps1` against the live session).
3. Optional hard quarantine of Quark DLL (rename folder after exit) — registry LoadBehavior=0 is not enough if the module still maps.
4. Consider re-enabling **HKCU `SPGMI.ExcelShell` LoadBehavior=3** only if CIQ docs require it; do not thrash Connect=false/true loops.
5. Next automation: **serial EntityBatch=1**, index=1 only, after interactive smoke. If serial dies on multi-day 1-name, further reduce to 1 name × 1 day and assemble part offline.
6. Do **not** resume full 1–33 until one clean `part_001` with ≥40 entities / ≥200 rows lands.

## Scripts / logs

| Path | Role |
|---|---|
| `tmp/lane2_host_cleanup.ps1` | Dismiss sticky prompts + kill orphans + Quark=0 |
| `tmp/aov0_backfill_trial5_tiny.ps1` | Controlled part_001 trial (tiny/serial, smoke gate) |
| `tmp/market_backfill_trial5*.log` | Trial 5a/5b/5c outcomes |
| `tmp/spg_probe_live.out` | Earlier live 1×1 proof with Migrate still open |

## One-sentence diagnosis

Lane 2 remains blocked by a damaged Excel+CIQ desktop host: after thrash, bulk SPGTable kills Excel even when 1×1 works; a dismisser that closed the CIQ shell made boot worse until fixed; unattended backfill must wait for one interactive healthy session and preferably serial capture before claiming `part_001`.
