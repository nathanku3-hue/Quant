# SAW DevSecOps Track 3 Round 2 (2026-03-01)

SAW Verdict: PASS

## Ownership Check
- Implementer: Codex (primary agent)
- Reviewer A: subagent `Nash` (`019ca86e-803a-7ac0-94a5-86decc2c14d4`)
- Reviewer B: subagent `Faraday` (`019ca86e-80c3-7a52-baff-0df3010edb5c`)
- Reviewer C: subagent `Averroes` (`019ca86e-80d7-7643-adc3-1465e0e1cc83`)
- Ownership result: PASS (implementer and reviewers are different agents)

## Findings
| Severity | Impact | Fix | Owner | Status |
|---|---|---|---|---|
| High | HTTP egress accepted for allowlisted hosts | Enforced HTTPS-only egress by default; added localhost-only HTTP break-glass | Implementer | Resolved |
| High | HMAC rotation could be bypassed by future activation timestamp | Added fail-closed future-skew guard (`TZ_HMAC_MAX_FUTURE_SKEW_SECONDS`) | Implementer | Resolved |
| High | Allowlist env replacement could drop broker-critical defaults | Changed allowlist env semantics to additive by default; explicit override mode | Implementer | Resolved |
| High | Post-submit webhook transport failure aborted completed submit path | Added post-submit degraded notification mode (`_post_submit` marker, warning-only on transport fault) | Implementer | Resolved |
| High | High-frequency egress-deny path used directional defaults | Replaced directional fallback values with neutral degraded metrics (`val=0.0`) | Implementer | Resolved |
| High | Runtime mismatch between dict auto-metrics and scalar formatting in console | Added auto-metric normalization helper and regression test for dict metrics | Implementer | Resolved |
| Medium | FMP malformed payload non-rate-limit class coverage can be expanded | Carried as follow-up test expansion in next DevSecOps/Data QA window | Future owner: QA stream | Open |

## Hierarchy Confirmation
- Approved | Session=2026-03-01 | Trigger=SAW mandatory post-work | Domains=DevSecOps Track 3 only

## Document Changes Showing
- `core/security_policy.py`: HTTPS-only egress, additive allowlist mode, future-skew fail-closed for HMAC. Reviewer status: A PASS.
- `scripts/high_freq_data.py`: neutral degraded metrics for blocked/failed fetches. Reviewer status: B PASS.
- `scripts/execution_bridge.py`: post-submit webhook transport degradation path. Reviewer status: B PASS.
- `main_console.py`: post-submit notify marker + dict metric normalization for auto inputs. Reviewer status: B PASS.
- `tests/test_security_policy.py`: added transport/mode/skew regression tests. Reviewer status: A PASS.
- `tests/test_execution_controls.py`: added TLS and notify mode regression tests. Reviewer status: A PASS.
- `tests/test_high_freq_data.py`: added degraded metric regression tests. Reviewer status: B PASS.
- `tests/test_main_console.py`: added dict auto-metric contract test and post-submit notify expectation update. Reviewer status: B PASS.
- `docs/runbook_ops.md`: updated env contracts and post-submit notify semantics. Reviewer status: B PASS.
- `docs/notes.md`: updated formulas and control notes for skew and transport policy. Reviewer status: A PASS.
- `docs/decision log.md`: added D-146 reconciliation decision entry. Reviewer status: A PASS.
- `docs/lessonss.md`: appended DevSecOps SAW reconciliation lesson. Reviewer status: C PASS.

## Evidence
- `.venv\Scripts\python -m pytest -q tests/test_security_policy.py tests/test_high_freq_data.py tests/test_execution_controls.py tests/test_main_console.py tests/test_ingest_fmp_estimates.py`
- `.venv\Scripts\python -m py_compile core/security_policy.py scripts/high_freq_data.py scripts/execution_bridge.py main_console.py tests/test_security_policy.py tests/test_high_freq_data.py tests/test_execution_controls.py tests/test_main_console.py`
- Secret/egress scans:
  - `rg -n "load_dotenv|dotenv" execution scripts core tests data logs -g '!*.pyc'` (no matches)
  - `rg -n "apikey=" data/raw/fmp_cache -g "*.json"` (no matches)

## Open Risks
- Medium: FMP malformed payload negative-path matrix can be expanded beyond current coverage.

## Next action
- Add explicit dict/scalar/invalid-JSON malformed payload regression cases to `tests/test_ingest_fmp_estimates.py` in next review window.
