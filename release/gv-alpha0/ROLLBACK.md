# Rollback

1. Stop the running Streamlit process.
2. Copy the entire GV-ALPHA0 user-data directory to a dated backup location.
3. Restore the previously accepted release package.
4. Start that package with its matching backed-up user-data directory.
5. Run `python scripts/smoke_gv_alpha0_release.py` against a separate temporary directory before resuming operator use.

Do not delete or auto-migrate an existing workspace. A seed-version mismatch is intentionally fail-closed. Restore the package and workspace as a matched pair.
