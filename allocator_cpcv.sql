-- Phase 53 CPCV reader template
-- Tokens for script formatting:
--   {splits_root} -> root directory for CPCV shards
--   {max_date}    -> max allowed snapshot date (YYYY-MM-DD)

WITH cpcv_source AS (
    SELECT *
    FROM read_parquet(
        '{splits_root}/fold=*/year=*/month=*/*.parquet',
        hive_partitioning = true
    )
    WHERE CAST(snapshot_date AS DATE) <= DATE '{max_date}'
)
SELECT *
FROM cpcv_source;
