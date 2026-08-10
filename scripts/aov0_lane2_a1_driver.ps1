<#
.SYNOPSIS
  Lane 2 driver: wait for market custody, capture PIT fundamentals, run A1, freeze A2 if earned.

Does not mutate Parent/Child or financial_alpha_evidence.
#>
param(
    [switch]$SkipFundamentals,
    [switch]$SkipA1,
    [string]$SecurityMaster = '',
    [string[]]$MarketPartDir = @(),
    [string]$A1Start = '2025-05-16',
    [string]$A1End = '2026-06-05',
    [string]$A2Start = '2026-06-12',
    [string]$A2End = '2026-08-07',
    [string]$RiskSetMembership = '',
    [string]$RiskSetReceipt = '',
    [string]$HistoricalSecurityMasterReceipt = '',
    [string]$TerminalEvents = '',
    [string]$TerminalEventsReceipt = '',
    [ValidateRange(1,20)][int]$PeriodChunkDates = 1,
    [ValidateRange(1,40)][int]$TransitionChunkSize = 1,
    [ValidateSet('ExcelOffice','ExistingWebProductQuery')][string]$FundamentalTransport = 'ExcelOffice',
    [ValidateRange(1,65535)][int]$CiqCdpPort = 9230
)

$ErrorActionPreference = 'Stop'
$wt = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $wt
$py = Join-Path $wt '.venv\Scripts\python.exe'
$env:PYTHONPATH = $wt
if ([string]::IsNullOrWhiteSpace($SecurityMaster) -or -not (Test-Path -LiteralPath $SecurityMaster)) {
    throw 'historical_risk_set_security_master_required'
}
$master = (Resolve-Path -LiteralPath $SecurityMaster).Path
$masterRowCount = @(Import-Csv -LiteralPath $master).Count
if ($masterRowCount -lt 1) { throw 'historical_security_master_empty' }
if ($MarketPartDir.Count -lt 1) { throw 'historical_market_part_directory_required' }
$marketDirs = @()
foreach ($dir in $MarketPartDir) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "historical_market_part_directory_missing:$dir" }
    $marketDirs += (Resolve-Path -LiteralPath $dir).Path
}
$periodDir = Join-Path $wt 'data\aov0\historical\raw\period_matrix_a1'
$transitionDir = Join-Path $wt 'data\aov0\historical\raw\transitions_a1'
$planDir = Join-Path $wt 'data\aov0\historical\plans'
$evidenceDir = Join-Path $wt 'data\aov0\historical\evidence'
$sofrRaw = Join-Path $wt 'data\aov0\historical\raw\nyfed_sofr_20230101_20260807.json'
New-Item -ItemType Directory -Force -Path $planDir, $periodDir, $transitionDir, $evidenceDir | Out-Null
if ([string]::IsNullOrWhiteSpace($RiskSetMembership) -or [string]::IsNullOrWhiteSpace($RiskSetReceipt)) {
    throw 'historical_risk_set_membership_and_receipt_required_for_admitted_a1'
}
if (-not (Test-Path -LiteralPath $RiskSetMembership) -or -not (Test-Path -LiteralPath $RiskSetReceipt)) {
    throw 'historical_risk_set_artifact_missing'
}
if ([string]::IsNullOrWhiteSpace($HistoricalSecurityMasterReceipt)) {
    throw 'historical_security_master_receipt_required_for_admitted_a1'
}
if (-not (Test-Path -LiteralPath $HistoricalSecurityMasterReceipt)) {
    throw 'historical_security_master_receipt_missing'
}
$historicalSecurityMasterReceipt = (Resolve-Path -LiteralPath $HistoricalSecurityMasterReceipt).Path
if ([string]::IsNullOrWhiteSpace($TerminalEvents) -or [string]::IsNullOrWhiteSpace($TerminalEventsReceipt)) {
    throw 'historical_terminal_events_and_receipt_required_for_admitted_a1'
}
if (-not (Test-Path -LiteralPath $TerminalEvents) -or -not (Test-Path -LiteralPath $TerminalEventsReceipt)) {
    throw 'historical_terminal_event_artifact_missing'
}
$terminalEvents = (Resolve-Path -LiteralPath $TerminalEvents).Path
$terminalEventsReceipt = (Resolve-Path -LiteralPath $TerminalEventsReceipt).Path

function Get-MarketParts {
    $paths = @()
    foreach ($dir in $marketDirs) {
        $paths += Get-ChildItem -LiteralPath $dir -Filter 'part_*.csv' -File | Where-Object { $_.Name -notlike '*.tmp' } | ForEach-Object { $_.FullName }
    }
    $paths = @($paths | Sort-Object -Unique)
    if ($paths.Count -lt 1) { throw 'historical_market_parts_empty' }
    return $paths
}

function Invoke-PlanFundamentals {
    param([string[]]$MarketParts)
    $out = Join-Path $planDir "weekly_asof_a1_${A1Start}_${A1End}.csv".Replace('-','')
    if (Test-Path $out) {
        Write-Host "PLAN_EXISTS $out"
        return $out
    }
    $args = @(
        (Join-Path $wt 'scripts\aov0_historical_pit_replay.py'), 'plan-fundamentals',
        '--security-master', $master,
        '--start', $A1Start, '--end', $A1End,
        '--risk-set-membership', $RiskSetMembership,
        '--risk-set-receipt', $RiskSetReceipt,
        '--historical-security-master-receipt', $historicalSecurityMasterReceipt,
        '--out', $out, '--refuse-existing'
    )
    foreach ($p in $MarketParts) { $args += @('--market-part', $p) }
    & $py @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "plan_fundamentals_failed:$LASTEXITCODE" }
    return $out
}

function Invoke-PeriodMatrix {
    param([string]$PlanPath)
    $planRows = @(Import-Csv -LiteralPath $PlanPath | Sort-Object as_of_date)
    if ($planRows.Count -lt 1) { throw 'period_matrix_plan_empty' }
    if ($FundamentalTransport -eq 'ExistingWebProductQuery') {
        $first = ([datetime]$planRows[0].as_of_date).ToString('yyyyMMdd')
        $last = ([datetime]$planRows[-1].as_of_date).ToString('yyyyMMdd')
        $expected = Join-Path $periodDir ("period_000_{0}_{1}.csv" -f $first, $last)
        if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
            & $py (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_productquery.py') --port $CiqCdpPort --batch-requests 200 period-matrix --plan $PlanPath --master $master --out $expected | Out-Host
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw "period_matrix_web_capture_failed:$LASTEXITCODE" }
        }
        $landed = @(Import-Csv -LiteralPath $expected)
        $expectedRows = $planRows.Count * $masterRowCount
        if ($landed.Count -ne $expectedRows) { throw "period_matrix_web_row_count_invalid:$($landed.Count)/$expectedRows" }
        return @($expected)
    }
    $chunkCount = [int][Math]::Ceiling($planRows.Count / [double]$PeriodChunkDates)
    for ($chunk = 0; $chunk -lt $chunkCount; $chunk++) {
        $offset = $chunk * $PeriodChunkDates
        $take = [Math]::Min($PeriodChunkDates, $planRows.Count - $offset)
        $batch = @($planRows[$offset..($offset + $take - 1)])
        $expected = Join-Path $periodDir ("period_{0:D3}_{1}_{2}.csv" -f $chunk, ([datetime]$batch[0].as_of_date).ToString('yyyyMMdd'), ([datetime]$batch[-1].as_of_date).ToString('yyyyMMdd'))
        Write-Host "PERIOD_CHUNK $chunk/$chunkCount expected=$expected"
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_period_matrix_chunk.ps1') `
            -ChunkIndex $chunk -PlanPath $PlanPath -OutDir $periodDir -Master $master -ChunkDates $PeriodChunkDates -BootSeconds 10 | Out-Host
        $exitCode = $LASTEXITCODE
        if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
            throw "period_matrix_chunk_missing_after_capture:${chunk}:exit=$exitCode"
        }
        $landed = @(Import-Csv -LiteralPath $expected)
        $expectedRows = $take * $masterRowCount
        if ($landed.Count -ne $expectedRows) {
            throw "period_matrix_chunk_row_count_invalid:${chunk}:$($landed.Count)/$expectedRows"
        }
        if ($exitCode -ne 0) {
            Write-Warning "period_matrix_capture_exit_nonzero_but_landed_verified:${chunk}:exit=$exitCode"
        }
    }
    $parts = @(Get-ChildItem -LiteralPath $periodDir -Filter 'period_*.csv' -File | Sort-Object Name)
    if ($parts.Count -ne $chunkCount) { throw "period_matrix_part_count_invalid:$($parts.Count)/$chunkCount" }
    return $parts.FullName
}

function Invoke-PlanTransitions {
    param([string[]]$PeriodParts)
    $out = if ($FundamentalTransport -eq 'ExistingWebProductQuery') {
        Join-Path $planDir ("transition_plan_a1_web_104_{0}_{1}.csv" -f $A1Start.Replace('-',''), $A1End.Replace('-',''))
    } else {
        Join-Path $planDir 'transition_plan_a1.csv'
    }
    if (Test-Path $out) {
        Write-Host "TRANSITION_PLAN_EXISTS $out"
        return $out
    }
    $args = @((Join-Path $wt 'scripts\aov0_historical_pit_replay.py'), 'plan-transitions', '--out', $out, '--refuse-existing')
    foreach ($p in $PeriodParts) { $args += @('--period-part', $p) }
    & $py @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "plan_transitions_failed:$LASTEXITCODE" }
    return $out
}

function Invoke-Transitions {
    param([string]$TransitionPlan)
    $planRows = @(Import-Csv -LiteralPath $TransitionPlan | Sort-Object source_entity_id,as_of_date)
    if ($planRows.Count -lt 1) { throw 'transition_plan_empty' }
    if ($FundamentalTransport -eq 'ExistingWebProductQuery') {
        $first = ([datetime]($planRows | Sort-Object as_of_date | Select-Object -First 1).as_of_date).ToString('yyyyMMdd')
        $last = ([datetime]($planRows | Sort-Object as_of_date | Select-Object -Last 1).as_of_date).ToString('yyyyMMdd')
        $expected = Join-Path $transitionDir ("transition_000_{0}_{1}.csv" -f $first, $last)
        if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
            & $py (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_productquery.py') --port $CiqCdpPort --batch-requests 200 transitions --plan $TransitionPlan --master $master --out $expected | Out-Host
            if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $expected -PathType Leaf)) { throw "transition_web_capture_failed:$LASTEXITCODE" }
        }
        $landed = @(Import-Csv -LiteralPath $expected)
        $expectedRows = $planRows.Count * 5
        if ($landed.Count -ne $expectedRows) { throw "transition_web_row_count_invalid:$($landed.Count)/$expectedRows" }
        return @($expected)
    }
    $chunkCount = [int][Math]::Ceiling($planRows.Count / [double]$TransitionChunkSize)
    for ($chunk = 0; $chunk -lt $chunkCount; $chunk++) {
        $offset = $chunk * $TransitionChunkSize
        $take = [Math]::Min($TransitionChunkSize, $planRows.Count - $offset)
        $batch = @($planRows[$offset..($offset + $take - 1)])
        $expected = Join-Path $transitionDir ("transition_{0:D3}_{1}_{2}.csv" -f $chunk, ([string]$batch[0].as_of_date).Replace('-',''), ([string]$batch[-1].as_of_date).Replace('-',''))
        Write-Host "TRANSITION_CHUNK $chunk/$chunkCount expected=$expected"
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $wt 'scripts\aov0_capture_ciq_historical_pit_transition_batch.ps1') `
            -ChunkIndex $chunk -TransitionPlanPath $TransitionPlan -OutDir $transitionDir -ChunkTransitions $TransitionChunkSize -BootSeconds 10 | Out-Host
        $exitCode = $LASTEXITCODE
        if (-not (Test-Path -LiteralPath $expected -PathType Leaf)) {
            throw "transition_chunk_missing_after_capture:${chunk}:exit=$exitCode"
        }
        $landed = @(Import-Csv -LiteralPath $expected)
        $expectedRows = $take * 5
        if ($landed.Count -ne $expectedRows) {
            throw "transition_chunk_row_count_invalid:${chunk}:$($landed.Count)/$expectedRows"
        }
        if ($exitCode -ne 0) {
            Write-Warning "transition_capture_exit_nonzero_but_landed_verified:${chunk}:exit=$exitCode"
        }
    }
    $parts = @(Get-ChildItem -LiteralPath $transitionDir -Filter 'transition_*.csv' -File | Sort-Object Name)
    if ($parts.Count -ne $chunkCount) { throw "transition_part_count_invalid:$($parts.Count)/$chunkCount" }
    return $parts.FullName
}

function Invoke-A1 {
    param([string[]]$MarketParts, [string[]]$PeriodParts, [string[]]$TransitionParts)
    $out = Join-Path $evidenceDir 'a1_report.json'
    $ev = Join-Path $evidenceDir 'a1_runs'
    if (Test-Path $out) { throw "a1_report_exists:$out" }
    $args = @(
        (Join-Path $wt 'scripts\aov0_historical_pit_replay.py'), 'run',
        '--stage', 'A1',
        '--security-master', $master,
        '--start', $A1Start, '--end', $A1End,
        '--sofr-raw', $sofrRaw,
        '--risk-set-membership', $RiskSetMembership,
        '--risk-set-receipt', $RiskSetReceipt,
        '--historical-security-master-receipt', $historicalSecurityMasterReceipt,
        '--terminal-events', $terminalEvents,
        '--terminal-events-receipt', $terminalEventsReceipt,
        '--out', $out,
        '--evidence-root', $ev,
        '--refuse-existing'
    )
    foreach ($p in $MarketParts) { $args += @('--market-part', $p) }
    foreach ($p in $PeriodParts) { $args += @('--period-part', $p) }
    foreach ($p in $TransitionParts) { $args += @('--transition-part', $p) }
    & $py @args | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "a1_run_failed:$LASTEXITCODE" }
    return $out
}

function Invoke-FreezeA2 {
    param([string]$A1Report)
    $out = Join-Path $evidenceDir 'a2_freeze.json'
    & $py (Join-Path $wt 'scripts\aov0_historical_pit_replay.py') freeze-a2 `
        --a1-report $A1Report --a2-start $A2Start --a2-end $A2End --out $out | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "a2_freeze_failed:$LASTEXITCODE" }
    return $out
}

Write-Host "LANE2_DRIVER_START wt=$wt fundamental_transport=$FundamentalTransport cdp_port=$CiqCdpPort financial_alpha_evidence=0"
$marketParts = Get-MarketParts
Write-Host "MARKET_PARTS=$($marketParts.Count)"

if (-not $SkipFundamentals) {
    $weeklyPlan = Invoke-PlanFundamentals -MarketParts $marketParts
    $periodParts = Invoke-PeriodMatrix -PlanPath $weeklyPlan
    $transitionPlan = Invoke-PlanTransitions -PeriodParts $periodParts
    $transitionParts = Invoke-Transitions -TransitionPlan $transitionPlan
} else {
    $periodParts = @(Get-ChildItem -LiteralPath $periodDir -Filter 'period_*.csv' | ForEach-Object { $_.FullName })
    $transitionParts = @(Get-ChildItem -LiteralPath $transitionDir -Filter 'transition_*.csv' | ForEach-Object { $_.FullName })
}

if (-not $SkipA1) {
    $a1 = Invoke-A1 -MarketParts $marketParts -PeriodParts $periodParts -TransitionParts $transitionParts
    Write-Host "A1_REPORT=$a1"
    $report = Get-Content $a1 -Raw | ConvertFrom-Json
    Write-Host ("A1_GATE_PASS={0} trading_days={1} financial_alpha_evidence={2}" -f $report.a1_minimum_gate.candidate_pass, $report.window.trading_days, $report.financial_alpha_evidence)
    if ($report.a1_minimum_gate.candidate_pass -eq $true) {
        $freeze = Invoke-FreezeA2 -A1Report $a1
        Write-Host "A2_FROZEN=$freeze (held-out capture still required after freeze)"
    } else {
        Write-Host "A1_NOT_ADMITTED — freeze skipped; deepen history or diagnose"
    }
}
Write-Host "LANE2_DRIVER_DONE financial_alpha_evidence=0"
