<#
.SYNOPSIS
  Fast fail-closed Lane-2 unblock controller.

.DESCRIPTION
  Prioritizes the two formal A1 source-authority blockers over the diagnostic
  2023 market backfill.  It never creates financial-alpha authority, never
  opens prospective outcomes, and never launches Excel.

  Automatic priority:
    1. Validate an existing historical high-growth risk-set receipt.
    2. Validate an existing same-date historical primary Security/Trading Item receipt.
    3. If a hash-bound CIQ Securities + Original-revenue partial candidate freeze
       exists, validate it and stop at the historical company-state blocker.
    4. Otherwise, if explicitly requested or still needed, XpressAPI may capture
       an alternate historical market-candidate component (no Excel).
    5. Stop at the exact missing provider component instead of falling back to
       the current 109/current-primary mapping.

  Neither the CIQ partial candidate freeze nor the Xpress market-candidate stage
  claims the final historical high-growth risk set. Historical company type/status
  remains separately required; CIQ Original/as-of annual-revenue evidence is now
  available for the target cut.
#>
param(
    [ValidateSet('Auto','Status','XpressCandidates','ValidateSources')]
    [string]$Mode = 'Auto',
    [string]$AsOfDate = '2025-05-16',

    [string]$CountryCodes = '',
    [string]$CountryColumn = 'countryCode',
    [string]$CountrySourceId = '',
    [string]$PrimaryExchanges = '',
    [string]$ExchangeColumn = 'primaryExchange',
    [string]$ExchangeSourceId = '',
    [int]$XpressCountryChunkSize = 50,
    [string]$XpressTokenEnv = 'SPGLOBAL_XPRESSAPI_TOKEN',

    [string]$RiskSetMembership = '',
    [string]$RiskSetReceipt = '',
    [string]$HistoricalSecurityMaster = '',
    [string]$HistoricalSecurityMasterReceipt = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$py = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py -PathType Leaf)) { throw "repo_python_missing:$py" }
$env:PYTHONPATH = $repoRoot

try {
    $asOf = [datetime]::ParseExact($AsOfDate, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
} catch {
    throw "as_of_date_invalid:$AsOfDate"
}
$asOfIso = $asOf.ToString('yyyy-MM-dd')
$asOfStamp = $asOf.ToString('yyyyMMdd')
$authorityDir = Join-Path $repoRoot ("data\aov0\historical\source_authority\{0}" -f $asOfStamp)
$xpressDir = Join-Path $authorityDir 'xpress_market_candidates'
$ciqProductQueryDir = Join-Path $authorityDir 'ciq_productquery'
$ciqPartialCandidates = Join-Path $ciqProductQueryDir 'market_original_revenue_candidates_20250516.csv'
$ciqPartialReceipt = Join-Path $ciqProductQueryDir 'market_original_revenue_candidates_20250516.receipt.json'

function Write-State([string]$Name, [string]$Value) {
    Write-Output ("LANE2_FAST`t{0}={1}" -f $Name, $Value)
}

function Test-FilePair([string]$Left, [string]$Right) {
    return (-not [string]::IsNullOrWhiteSpace($Left)) -and
           (-not [string]::IsNullOrWhiteSpace($Right)) -and
           (Test-Path -LiteralPath $Left -PathType Leaf) -and
           (Test-Path -LiteralPath $Right -PathType Leaf)
}

function Validate-RiskSet {
    param([string]$Membership, [string]$Receipt)
    $code = @'
import sys
from research.aov0.historical_risk_set import load_historical_start_risk_set
obj = load_historical_start_risk_set(sys.argv[1], sys.argv[2], expected_as_of_date=sys.argv[3])
print(f"RISK_SET_VALID\tASOF={obj.as_of_date.date().isoformat()}\tENTITIES={len(obj.entity_ids)}\tSHA256={obj.metadata['membership_sha256']}")
'@
    & $py -c $code $Membership $Receipt $asOfIso
    if ($LASTEXITCODE -ne 0) { throw "historical_risk_set_validation_failed:$LASTEXITCODE" }
}

function Validate-CiqPartialCandidate {
    param([string]$Candidates, [string]$Receipt)
    $validator = Join-Path $repoRoot 'scripts\aov0_validate_lane2_partial_candidate.py'
    if (-not (Test-Path -LiteralPath $validator -PathType Leaf)) {
        throw "ciq_partial_validator_missing:$validator"
    }
    & $py $validator $Candidates $Receipt --as-of-date $asOfIso
    if ($LASTEXITCODE -ne 0) { throw "ciq_partial_candidate_validation_failed:$LASTEXITCODE" }
}

function Validate-HistoricalIdentity {
    param([string]$Master, [string]$Receipt, [string]$Membership, [string]$RiskReceipt)
    $code = @'
import sys
from research.aov0.historical_risk_set import load_historical_start_risk_set
from research.aov0.historical_security_master import load_historical_start_security_master
risk = load_historical_start_risk_set(sys.argv[1], sys.argv[2], expected_as_of_date=sys.argv[5])
obj = load_historical_start_security_master(sys.argv[3], sys.argv[4], expected_as_of_date=sys.argv[5], expected_entity_ids=risk.entity_ids)
print(f"HISTORICAL_IDENTITY_VALID\tASOF={obj.as_of_date.date().isoformat()}\tENTITIES={len(obj.entity_ids)}\tSHA256={obj.metadata['master_sha256']}")
'@
    & $py -c $code $Membership $RiskReceipt $Master $Receipt $asOfIso
    if ($LASTEXITCODE -ne 0) { throw "historical_identity_validation_failed:$LASTEXITCODE" }
}

function Ensure-CountryReference {
    $referenceDir = Join-Path $authorityDir 'xpress_reference'
    New-Item -ItemType Directory -Force -Path $referenceDir | Out-Null
    $path = Join-Path $referenceDir 'country_codes_windows_geo_iso3.csv'

    if (-not ('Lane2GeoIso3' -as [type])) {
        Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class Lane2GeoIso3 {
    public delegate bool GeoEnumProc(int geoId);
    [DllImport("kernel32.dll")]
    public static extern bool EnumSystemGeoID(int geoClass, int parentGeoId, GeoEnumProc proc);
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode)]
    public static extern int GetGeoInfoW(int geoId, int geoType, StringBuilder data, int dataChars, int languageId);
    public static string[] All() {
        var values = new SortedSet<string>(StringComparer.Ordinal);
        GeoEnumProc callback = id => {
            var buffer = new StringBuilder(16);
            if (GetGeoInfoW(id, 5, buffer, buffer.Capacity, 0) > 0) {
                var value = buffer.ToString().Trim().ToUpperInvariant();
                if (value.Length == 3) values.Add(value);
            }
            return true;
        };
        if (!EnumSystemGeoID(16, 0, callback)) throw new InvalidOperationException("EnumSystemGeoID failed");
        var result = new string[values.Count];
        values.CopyTo(result);
        return result;
    }
}
'@
    }

    $codes = @([Lane2GeoIso3]::All())
    if ($codes.Count -ne 249 -or @($codes | Where-Object { $_ -notmatch '^[A-Z]{3}$' }).Count -gt 0) {
        throw ("windows_geo_iso3_catalog_invalid:count={0}" -f $codes.Count)
    }
    $expected = @('countryCode') + $codes
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $observed = @(Get-Content -LiteralPath $path)
        if (($observed -join "`n") -ne ($expected -join "`n")) {
            throw 'windows_geo_iso3_reference_drift'
        }
    } else {
        [IO.File]::WriteAllLines($path, $expected, [Text.UTF8Encoding]::new($false))
    }
    return [pscustomobject]@{
        Path = $path
        SourceId = 'WINDOWS_NLS:GEO_ISO3_SYSTEM_CATALOG'
        Count = $codes.Count
    }
}

function Invoke-XpressCandidates {
    $token = [Environment]::GetEnvironmentVariable($XpressTokenEnv, 'Process')
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "xpress_token_missing:$XpressTokenEnv"
    }
    if ([string]::IsNullOrWhiteSpace($CountryCodes)) {
        $autoCountries = Ensure-CountryReference
        $script:CountryCodes = [string]$autoCountries.Path
        if ([string]::IsNullOrWhiteSpace($CountrySourceId)) {
            $script:CountrySourceId = [string]$autoCountries.SourceId
        }
        Write-State 'XPRESS_COUNTRY_REFERENCE' ("AUTO:count={0}:path={1}" -f $autoCountries.Count, $CountryCodes)
    }
    foreach ($pair in @(
        @('country_codes', $CountryCodes, $CountrySourceId),
        @('primary_exchanges', $PrimaryExchanges, $ExchangeSourceId)
    )) {
        if ([string]::IsNullOrWhiteSpace([string]$pair[1]) -or -not (Test-Path -LiteralPath ([string]$pair[1]) -PathType Leaf)) {
            throw ("xpress_reference_file_missing:{0}" -f $pair[0])
        }
        if ([string]::IsNullOrWhiteSpace([string]$pair[2])) {
            throw ("xpress_reference_source_id_missing:{0}" -f $pair[0])
        }
    }

    New-Item -ItemType Directory -Force -Path $xpressDir | Out-Null
    $plan = Join-Path $xpressDir ("xpress_screen_market_plan_{0}.json" -f $asOfStamp)
    $runner = Join-Path $repoRoot 'scripts\aov0_xpressapi_historical_screen_candidates.py'

    if (-not (Test-Path -LiteralPath $plan -PathType Leaf)) {
        & $py $runner plan `
            --as-of-date $asOfIso `
            --country-codes $CountryCodes `
            --country-column $CountryColumn `
            --country-source-id $CountrySourceId `
            --primary-exchanges $PrimaryExchanges `
            --exchange-column $ExchangeColumn `
            --exchange-source-id $ExchangeSourceId `
            --chunk-size $XpressCountryChunkSize `
            --out $plan
        if ($LASTEXITCODE -ne 0) { throw "xpress_plan_failed:$LASTEXITCODE" }
    } else {
        Write-State 'XPRESS_PLAN' ('EXISTS:' + $plan)
    }

    $planObject = Get-Content -LiteralPath $plan -Raw | ConvertFrom-Json
    $requestCount = [int]$planObject.request_count
    if ($requestCount -lt 1) { throw 'xpress_plan_request_count_invalid' }
    $receipts = New-Object System.Collections.Generic.List[string]
    for ($chunk = 0; $chunk -lt $requestCount; $chunk++) {
        $stem = "xpress_screen_market_{0:D3}_{1}" -f $chunk, $asOfStamp
        $receipt = Join-Path $xpressDir ($stem + '.receipt.json')
        if (-not (Test-Path -LiteralPath $receipt -PathType Leaf)) {
            $raw = Join-Path $xpressDir ($stem + '.raw.json')
            $csv = Join-Path $xpressDir ($stem + '.csv')
            if ((Test-Path -LiteralPath $raw) -or (Test-Path -LiteralPath $csv)) {
                throw "xpress_partial_chunk_requires_operator_review:$chunk"
            }
            & $py $runner capture --plan $plan --chunk-index $chunk --out-dir $xpressDir --token-env $XpressTokenEnv
            if ($LASTEXITCODE -ne 0) { throw "xpress_capture_failed:chunk=$chunk:exit=$LASTEXITCODE" }
        }
        $receipts.Add($receipt)
    }

    $mergedCsv = Join-Path $xpressDir ("historical_market_candidates_{0}.csv" -f $asOfStamp)
    $mergedReceipt = Join-Path $xpressDir ("historical_market_candidates_{0}.receipt.json" -f $asOfStamp)
    if (-not (Test-Path -LiteralPath $mergedReceipt -PathType Leaf)) {
        $args = @($runner, 'merge', '--plan', $plan)
        foreach ($receipt in $receipts) { $args += @('--part-receipt', $receipt) }
        $args += @('--out-csv', $mergedCsv, '--out-receipt', $mergedReceipt)
        & $py @args
        if ($LASTEXITCODE -ne 0) { throw "xpress_merge_failed:$LASTEXITCODE" }
    }
    if (-not (Test-Path -LiteralPath $mergedCsv -PathType Leaf) -or -not (Test-Path -LiteralPath $mergedReceipt -PathType Leaf)) {
        throw 'xpress_merged_artifact_missing'
    }
    $rows = @(Import-Csv -LiteralPath $mergedCsv).Count
    Write-State 'XPRESS_MARKET_CANDIDATES' ("READY:rows={0}:csv={1}:receipt={2}" -f $rows, $mergedCsv, $mergedReceipt)
    Write-State 'NEXT_REQUIRED' 'HISTORICAL_COMPANY_STATE_AND_ORIGINAL_ANNUAL_REVENUE_FOR_EXACT_CANDIDATE_SET'
    Write-State 'AUTHORITY' 'MARKET_CANDIDATES_ONLY_NOT_A1_RISK_SET'
}

$riskPair = Test-FilePair $RiskSetMembership $RiskSetReceipt
$identityPair = Test-FilePair $HistoricalSecurityMaster $HistoricalSecurityMasterReceipt
$ciqPartialPair = Test-FilePair $ciqPartialCandidates $ciqPartialReceipt

Write-State 'ASOF' $asOfIso
Write-State 'FINANCIAL_ALPHA_EVIDENCE' '0'
Write-State 'EXCEL_REQUIRED_BY_THIS_SCRIPT' 'NO'
Write-State 'RISK_SET_ARTIFACTS_PRESENT' ([string]$riskPair)
Write-State 'HISTORICAL_IDENTITY_ARTIFACTS_PRESENT' ([string]$identityPair)
Write-State 'CIQ_MARKET_ORIGINAL_REVENUE_PARTIAL_PRESENT' ([string]$ciqPartialPair)

if ($Mode -eq 'Status') {
    if (-not $riskPair) {
        if ($ciqPartialPair) {
            Validate-CiqPartialCandidate -Candidates $ciqPartialCandidates -Receipt $ciqPartialReceipt
            Write-State 'CIQ_PARTIAL' 'VALID:104_MARKET_PLUS_ORIGINAL_REVENUE_CANDIDATES_NOT_A1_AUTHORITY'
            Write-State 'FASTEST_NEXT' 'CLOSE_HISTORICAL_COMPANY_TYPE_STATUS_FOR_104_CANDIDATES;DO_NOT_BACKFILL_PART_001_FIRST'
        } else {
            $tokenPresent = -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($XpressTokenEnv, 'Process'))
            Write-State 'XPRESS_TOKEN_PRESENT' ([string]$tokenPresent)
            Write-State 'FASTEST_NEXT' 'CAPTURE_HISTORICAL_MARKET_PLUS_ORIGINAL_REVENUE_COMPONENTS_OR_USE_XPRESS_AS_ALTERNATE;DO_NOT_BACKFILL_PART_001_FIRST'
        }
    } elseif (-not $identityPair) {
        Write-State 'FASTEST_NEXT' 'CLOSE_SAME_DATE_PROVIDER_PRIMARY_SECURITY_TRADING_ITEM_AUTHORITY'
    } else {
        Write-State 'FASTEST_NEXT' 'VALIDATE_BOTH_SOURCE_AUTHORITIES'
    }
    exit 0
}

if ($riskPair) {
    Validate-RiskSet -Membership $RiskSetMembership -Receipt $RiskSetReceipt
    Write-State 'RISK_SET' 'VALID'
} elseif ($Mode -eq 'Auto' -and $ciqPartialPair) {
    Validate-CiqPartialCandidate -Candidates $ciqPartialCandidates -Receipt $ciqPartialReceipt
    Write-State 'CIQ_PARTIAL' 'VALID:104_MARKET_PLUS_ORIGINAL_REVENUE_CANDIDATES_NOT_A1_AUTHORITY'
    Write-State 'BLOCKED' 'HISTORICAL_COMPANY_TYPE_STATUS_AUTHORITY_MISSING_FOR_104_CANDIDATES'
    Write-State 'REJECTED_SHORTCUTS' 'CURRENT_COMPANY_TYPE_STATUS;SPG_PROFILE_FIELDS_WITH_ASOF;CURRENT_109'
    exit 20
} elseif ($Mode -in @('Auto','XpressCandidates')) {
    Invoke-XpressCandidates
    if ($Mode -eq 'XpressCandidates') { exit 0 }
    Write-State 'BLOCKED' 'FINAL_RISK_SET_NOT_YET_AVAILABLE_AFTER_MARKET_CANDIDATE_STAGE'
    exit 20
} elseif ($Mode -eq 'ValidateSources') {
    throw 'risk_set_artifacts_required_for_validate_sources'
}

if (-not $identityPair) {
    Write-State 'BLOCKED' 'HISTORICAL_PRIMARY_SECURITY_TRADING_ITEM_RECEIPT_MISSING'
    Write-State 'REJECTED_SHORTCUTS' 'CURRENT_2026_PRIMARY_MASTER;SCALAR_SPG_ASOF_CURRENT_PRIMARY;TICKER_INFERENCE'
    Write-State 'PREFERRED_PROVIDER_PATH' 'S&P_BASE_SECURITY_GICRS_DAILY_OR_PROVIDER_GENERATED_ASOF_SNAPSHOT'
    exit 21
}

Validate-HistoricalIdentity `
    -Master $HistoricalSecurityMaster `
    -Receipt $HistoricalSecurityMasterReceipt `
    -Membership $RiskSetMembership `
    -RiskReceipt $RiskSetReceipt
Write-State 'HISTORICAL_IDENTITY' 'VALID'
Write-State 'A1_SOURCE_AUTHORITY' 'UNBLOCKED'
Write-State 'NEXT' 'TARGET_MARKET_AND_FUNDAMENTAL_MATERIALIZATION_TO_EXACT_ADMITTED_COHORT_THEN_EXISTING_A1_DRIVER'
exit 0
