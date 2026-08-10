<#
.SYNOPSIS
  Lane 2 held-out A2 driver. Requires an admitted A1 freeze, captures Original PIT
  fundamentals only after that freeze, and consumes the one-shot A2 query exactly once.

Does not sign in to Capital IQ Pro and does not mutate Parent/Child or
financial_alpha_evidence.
#>
param(
    [Parameter(Mandatory=$true)][string]$Freeze,
    [Parameter(Mandatory=$true)][string]$SecurityMaster,
    [Parameter(Mandatory=$true)][string[]]$MarketPartDir,
    [ValidateRange(1,20)][int]$PeriodChunkDates = 20,
    [ValidateRange(1,40)][int]$TransitionChunkSize = 40,
    [ValidateSet('ExcelOffice','ExistingWebProductQuery')][string]$FundamentalTransport = 'ExcelOffice',
    [ValidateRange(1,65535)][int]$CiqCdpPort = 9230
)

$ErrorActionPreference = 'Stop'
$wt = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $wt
$py = Join-Path $wt '.venv\Scripts\python.exe'
$env:PYTHONPATH = $wt

if (-not (Test-Path -LiteralPath $Freeze -PathType Leaf)) { throw "a2_freeze_missing:$Freeze" }
if (-not (Test-Path -LiteralPath $SecurityMaster -PathType Leaf)) { throw "a2_security_master_missing:$SecurityMaster" }
$freezePath = (Resolve-Path -LiteralPath $Freeze).Path
$master = (Resolve-Path -LiteralPath $SecurityMaster).Path
$freezePayload = Get-Content -LiteralPath $freezePath -Raw | ConvertFrom-Json
if ($freezePayload.schema_version -ne 'aov0_historical_pit_a1_to_a2_freeze_v1') { throw 'a2_freeze_schema_invalid' }
$A2Start = [string]$freezePayload.a2_window.start
$A2End = [string]$freezePayload.a2_window.end
if (-not $A2Start -or -not $A2End) { throw 'a2_freeze_window_missing' }
$freezeTime = [datetimeoffset]$freezePayload.created_at_utc
$resultPath = [string]$freezePayload.a2_paths.result
$evidenceRoot = [string]$freezePayload.a2_paths.evidence_root
$queryLock = [string]$freezePayload.a2_paths.query_lock
$queryReceipt = [string]$freezePayload.a2_paths.query_receipt
foreach ($path in @($resultPath, $evidenceRoot, $queryLock, $queryReceipt)) {
    if ([string]::IsNullOrWhiteSpace($path)) { throw 'a2_freeze_bound_path_missing' }
}
if (Test-Path -LiteralPath $resultPath) { throw "a2_result_already_exists:$resultPath" }
if (Test-Path -LiteralPath $queryLock) { throw "a2_query_already_consumed:$queryLock" }
if (Test-Path -LiteralPath $queryReceipt) { throw "a2_query_receipt_already_exists:$queryReceipt" }
if ((Test-Path -LiteralPath $evidenceRoot -PathType Container) -and @(Get-ChildItem -LiteralPath $evidenceRoot -Force).Count -gt 0) {
    throw "a2_evidence_root_not_empty:$evidenceRoot"
}

$marketDirs = @()
foreach ($dir in $MarketPartDir) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "a2_market_part_directory_missing:$dir" }
    $marketDirs += (Resolve-Path -LiteralPath $dir).Path
}
$marketParts = @()
foreach ($dir in $marketDirs) {
    $marketParts += Get-ChildItem -LiteralPath $dir -Filter 'part_*.csv' -File | Where-Object { $_.Name -notlike '*.tmp' } | ForEach-Object { $_.FullName }
}
$marketParts = @($marketParts | Sort-Object -Unique)
if ($marketParts.Count -lt 1) { throw 'a2_market_parts_empty' }

$planDir = Join-Path $wt 'data\aov0\historical\plans'
$periodDir = Join-Path $wt 'data\aov0\historical\raw\period_matrix_a2'
$transitionDir = Join-Path $wt 'data\aov0\historical\raw\transitions_a2'
$sofrRaw = Join-Path $wt 'data\aov0\historical\raw\nyfed_sofr_20230101_20260807.json'
New-Item -ItemType Directory -Force -Path $planDir, $periodDir, $transitionDir | Out-Null
if (-not (Test-Path -LiteralPath $sofrRaw -PathType Leaf)) { throw "a2_sofr_missing:$sofrRaw" }

function Assert-AfterFreezeCapture([string]$Path) {
    $rows = @(Import-Csv -LiteralPath $Path)
    if ($rows.Count -lt 1) { throw "a2_capture_empty:$Path" }
    if (-not ($rows[0].PSObject.Properties.Name -contains 'retrieved_at_utc')) { throw "a2_capture_timestamp_missing:$Path" }
    foreach ($row in $rows) {
        if ([datetimeoffset]$row.retrieved_at_utc -le $freezeTime) { throw "a2_capture_not_after_freeze:$Path" }
    }
}

function Invoke-A2Plan {
    $out = Join-Path $planDir "weekly_asof_a2_${A2Start}_${A2End}.csv".Replace('-','')
    if (Test-Path -LiteralPath $out) { return $out }
    $args = @(
        (Join-Path $wt 'scripts\aov0_historical_pit_replay.py'), 'plan-fundamentals',
        '--security-master', $master,
        '--start', $A2Start, '--end', $A2End,
        '--freeze', $freezePath,
        '--out', $out, '--refuse-existing'
    )
    foreach ($p in $marketParts) { $args += @('--market-part', $p) }
    & $py @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "a2_plan_fundamentals_failed:$LASTEXITCODE" }
    return $out
}

function Invoke-A2PeriodMatrix([string]$PlanPath) {
    $planRows = @(Import-Csv -LiteralPath $PlanPath | Sort-Object as_of_date)
    if ($planRows.Count -lt 1) { throw 'a2_period_matrix_plan_empty' }
    $masterRows = @(Import-Csv -LiteralPath $master).Count
    if ($FundamentalTransport -eq 'ExistingWebProductQuery') {
        $first = ([datetime]$planRows[0].as_of_date).ToString('yyyyMMdd')
        $last = ([datetime]$planRows[-1].as_of_date).ToString('yyyyMMdd')
        $expected = Join-Path $periodDir ("period_000_{0}_{1}.csv" -f $first, $last)
        if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
            & $py (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_productquery.py') --port $CiqCdpPort --batch-requests 200 period-matrix --plan $PlanPath --master $master --out $expected | Out-Host
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw "a2_period_matrix_web_capture_failed:$LASTEXITCODE" }
        }
        Assert-AfterFreezeCapture $expected
        $landed = @(Import-Csv -LiteralPath $expected)
        $expectedRows = $planRows.Count * $masterRows
        if ($landed.Count -ne $expectedRows) { throw "a2_period_matrix_web_row_count_invalid:$($landed.Count)/$expectedRows" }
        return @($expected)
    }
    $chunkCount = [int][Math]::Ceiling($planRows.Count / [double]$PeriodChunkDates)
    for ($chunk = 0; $chunk -lt $chunkCount; $chunk++) {
        $offset = $chunk * $PeriodChunkDates
        $take = [Math]::Min($PeriodChunkDates, $planRows.Count - $offset)
        $batch = @($planRows[$offset..($offset + $take - 1)])
        $expected = Join-Path $periodDir ("period_{0:D3}_{1}_{2}.csv" -f $chunk, ([datetime]$batch[0].as_of_date).ToString('yyyyMMdd'), ([datetime]$batch[-1].as_of_date).ToString('yyyyMMdd'))
        if (Test-Path -LiteralPath $expected) {
            Assert-AfterFreezeCapture $expected
            $landed = @(Import-Csv -LiteralPath $expected)
            if ($landed.Count -ne ($take * $masterRows)) { throw "a2_period_matrix_existing_row_count_invalid:${chunk}:$($landed.Count)/$($take * $masterRows)" }
            continue
        }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1') `
            -ChunkIndex $chunk -PlanPath $PlanPath -OutDir $periodDir -Master $master -ChunkDates $PeriodChunkDates -BootSeconds 10 | Out-Host
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw "a2_period_matrix_capture_failed:${chunk}:$LASTEXITCODE" }
        Assert-AfterFreezeCapture $expected
        $landed = @(Import-Csv -LiteralPath $expected)
        if ($landed.Count -ne ($take * $masterRows)) { throw "a2_period_matrix_row_count_invalid:${chunk}:$($landed.Count)/$($take * $masterRows)" }
    }
    $parts = @(Get-ChildItem -LiteralPath $periodDir -Filter 'period_*.csv' -File | Sort-Object Name)
    if ($parts.Count -ne $chunkCount) { throw "a2_period_matrix_part_count_invalid:$($parts.Count)/$chunkCount" }
    return $parts.FullName
}

function Invoke-A2TransitionPlan([string[]]$PeriodParts) {
    $out = Join-Path $planDir 'transition_plan_a2.csv'
    if (Test-Path -LiteralPath $out) { return $out }
    $args = @((Join-Path $wt 'scripts\aov0_historical_pit_replay.py'), 'plan-transitions', '--out', $out, '--refuse-existing')
    foreach ($p in $PeriodParts) { $args += @('--period-part', $p) }
    & $py @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "a2_plan_transitions_failed:$LASTEXITCODE" }
    return $out
}

function Invoke-A2Transitions([string]$TransitionPlan) {
    $planRows = @(Import-Csv -LiteralPath $TransitionPlan | Sort-Object source_entity_id,as_of_date)
    if ($planRows.Count -lt 1) { throw 'a2_transition_plan_empty' }
    if ($FundamentalTransport -eq 'ExistingWebProductQuery') {
        $first = ([datetime]($planRows | Sort-Object as_of_date | Select-Object -First 1).as_of_date).ToString('yyyyMMdd')
        $last = ([datetime]($planRows | Sort-Object as_of_date | Select-Object -Last 1).as_of_date).ToString('yyyyMMdd')
        $expected = Join-Path $transitionDir ("transition_000_{0}_{1}.csv" -f $first, $last)
        if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
            & $py (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_productquery.py') --port $CiqCdpPort --batch-requests 200 transitions --plan $TransitionPlan --master $master --out $expected | Out-Host
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw "a2_transition_web_capture_failed:$LASTEXITCODE" }
        }
        Assert-AfterFreezeCapture $expected
        $landed = @(Import-Csv -LiteralPath $expected)
        $expectedRows = $planRows.Count * 5
        if ($landed.Count -ne $expectedRows) { throw "a2_transition_web_row_count_invalid:$($landed.Count)/$expectedRows" }
        return @($expected)
    }
    $chunkCount = [int][Math]::Ceiling($planRows.Count / [double]$TransitionChunkSize)
    for ($chunk = 0; $chunk -lt $chunkCount; $chunk++) {
        $offset = $chunk * $TransitionChunkSize
        $take = [Math]::Min($TransitionChunkSize, $planRows.Count - $offset)
        $batch = @($planRows[$offset..($offset + $take - 1)])
        $expected = Join-Path $transitionDir ("transition_{0:D3}_{1}_{2}.csv" -f $chunk, ([string]$batch[0].as_of_date).Replace('-',''), ([string]$batch[-1].as_of_date).Replace('-',''))
        if (Test-Path -LiteralPath $expected) {
            Assert-AfterFreezeCapture $expected
            $landed = @(Import-Csv -LiteralPath $expected)
            if ($landed.Count -ne ($take * 5)) { throw "a2_transition_existing_row_count_invalid:${chunk}:$($landed.Count)/$($take * 5)" }
            continue
        }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_transition_batch.ps1') `
            -ChunkIndex $chunk -TransitionPlanPath $TransitionPlan -OutDir $transitionDir -ChunkTransitions $TransitionChunkSize -BootSeconds 10 | Out-Host
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw "a2_transition_capture_failed:${chunk}:$LASTEXITCODE" }
        Assert-AfterFreezeCapture $expected
        $landed = @(Import-Csv -LiteralPath $expected)
        if ($landed.Count -ne ($take * 5)) { throw "a2_transition_row_count_invalid:${chunk}:$($landed.Count)/$($take * 5)" }
    }
    $parts = @(Get-ChildItem -LiteralPath $transitionDir -Filter 'transition_*.csv' -File | Sort-Object Name)
    if ($parts.Count -ne $chunkCount) { throw "a2_transition_part_count_invalid:$($parts.Count)/$chunkCount" }
    return $parts.FullName
}

Write-Host "LANE2_A2_DRIVER_START freeze=$freezePath window=$A2Start..$A2End fundamental_transport=$FundamentalTransport cdp_port=$CiqCdpPort financial_alpha_evidence=0"
$weeklyPlan = Invoke-A2Plan
$periodParts = Invoke-A2PeriodMatrix $weeklyPlan
$transitionPlan = Invoke-A2TransitionPlan $periodParts
$transitionParts = Invoke-A2Transitions $transitionPlan

$args = @(
    (Join-Path $wt 'scripts\aov0_historical_pit_replay.py'), 'run',
    '--stage', 'A2',
    '--security-master', $master,
    '--start', $A2Start, '--end', $A2End,
    '--sofr-raw', $sofrRaw,
    '--freeze', $freezePath,
    '--out', $resultPath,
    '--evidence-root', $evidenceRoot,
    '--refuse-existing'
)
foreach ($p in $marketParts) { $args += @('--market-part', $p) }
foreach ($p in $periodParts) { $args += @('--period-part', $p) }
foreach ($p in $transitionParts) { $args += @('--transition-part', $p) }
& $py @args
if ($LASTEXITCODE -ne 0) { throw "a2_one_shot_run_failed:$LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) { throw "a2_result_missing_after_run:$resultPath" }
Write-Host "LANE2_A2_DRIVER_DONE result=$resultPath financial_alpha_evidence=0"
