param(
    [Parameter(Mandatory=$true)][int]$ChunkIndex,
    [Parameter(Mandatory=$true)][datetime]$AsOfDate,
    [Parameter(Mandatory=$true)][string]$PartsDir,
    [string]$MasterPath = '',
    [int]$EntitiesPerChunk = 10,
    [int]$BootSeconds = 8
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $MasterPath) { $MasterPath = Join-Path $repoRoot 'data\aov0\raw\ciq_primary_security_master_20260808T162322Z.csv' }
if (-not (Test-Path -LiteralPath $MasterPath)) { throw "historical_pit_master_missing:$MasterPath" }
if ($EntitiesPerChunk -lt 1 -or $EntitiesPerChunk -gt 20) { throw 'historical_pit_entities_per_chunk_out_of_range' }

Add-Type -AssemblyName office
if (-not ('AovHistoricalPitChunkRcStub' -as [type])) {
    $source = @'
using System; using Microsoft.Office.Core;
public sealed class AovHistoricalPitChunkRcStub : IRibbonControl {
    public string Id { get; private set; }
    public string Tag { get; private set; }
    public object Context { get; private set; }
    public AovHistoricalPitChunkRcStub(string id, object context) { Id=id; Tag=""; Context=context; }
}
'@
    Add-Type -TypeDefinition $source -ReferencedAssemblies ([Microsoft.Office.Core.IRibbonControl].Assembly.Location)
}

function Is-Missing([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return $true }
    $normalized = $Text.Trim().ToUpperInvariant()
    return $normalized -in @('NA','N/A','NAN','NULL','NONE') -or $normalized.StartsWith('#')
}

function Read-NumericCell([object]$Cell) {
    $text = [string]$Cell.Text
    if (Is-Missing $text) { return 'NA' }
    try {
        $value = [double]$Cell.Value2
        if ([double]::IsNaN($value) -or [double]::IsInfinity($value)) { return 'NA' }
        return [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:R}', $value)
    }
    catch { return 'NA' }
}

function Read-DateCell([object]$Cell) {
    $text = [string]$Cell.Text
    if (Is-Missing $text) { return 'NA' }
    try {
        $raw = $Cell.Value2
        if ($raw -is [double] -or $raw -is [single] -or $raw -is [decimal] -or $raw -is [int] -or $raw -is [long]) {
            return [datetime]::FromOADate([double]$raw).ToString('yyyy-MM-dd')
        }
    }
    catch {}
    $parsed = [datetime]::MinValue
    if ([datetime]::TryParse($text, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AllowWhiteSpaces, [ref]$parsed)) {
        return $parsed.ToString('yyyy-MM-dd')
    }
    return 'NA'
}

$masterRows = @(Import-Csv -LiteralPath $MasterPath)
if ($masterRows.Count -ne 109) { throw "historical_pit_master_count_invalid:$($masterRows.Count)" }
if (@($masterRows.SP_ENTITY_ID | Sort-Object -Unique).Count -ne 109) { throw 'historical_pit_master_entity_collision' }
if (@($masterRows.SP_CIQ_ID | Sort-Object -Unique).Count -ne 109) { throw 'historical_pit_master_security_collision' }
if (@($masterRows.SPT_INSTRUMENT_ITEM_ID | Sort-Object -Unique).Count -ne 109) { throw 'historical_pit_master_trading_collision' }

$chunkCount = [int][Math]::Ceiling($masterRows.Count / [double]$EntitiesPerChunk)
if ($ChunkIndex -lt 0 -or $ChunkIndex -ge $chunkCount) { throw "historical_pit_chunk_index_invalid:$ChunkIndex/$chunkCount" }
$offset = $ChunkIndex * $EntitiesPerChunk
$take = [Math]::Min($EntitiesPerChunk, $masterRows.Count - $offset)
$batch = @($masterRows[$offset..($offset + $take - 1)])
$periods = @('FQ0','FQ-1','FQ-2','FQ-3','FQ-4','FQ-5','FQ-6','FQ-7')
$metrics = @(
    'IQ_PERIOD_END',
    'IQ_TOTAL_REV',
    'IQ_TOTAL_ASSETS',
    'IQ_INVENTORY',
    'IQ_DA_SUPPL_CF',
    'IQ_TOTAL_EQUITY',
    'IQ_TOTAL_DEBT',
    'IQ_CASH_ST_INVEST',
    'IQ_OPER_INC',
    'IQ_CAPEX_BNK'
)
$options = 'Options:Curr=USD,Mag=Thousands,ConvMethod=R,FilingVer=Original'
$asOfText = $AsOfDate.ToString('MM/dd/yyyy', [Globalization.CultureInfo]::InvariantCulture)
$asOfIso = $AsOfDate.ToString('yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
$availabilityBoundary = [datetime]::SpecifyKind($AsOfDate.Date.AddDays(1).AddHours(12), [DateTimeKind]::Utc)
$masterHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $MasterPath).Hash.ToLowerInvariant()

[IO.Directory]::CreateDirectory($PartsDir) | Out-Null
$firstEntity = [string]$batch[0].SP_ENTITY_ID
$lastEntity = [string]$batch[-1].SP_ENTITY_ID
$out = Join-Path $PartsDir ("part_{0:D3}_{1}_{2}_{3}.csv" -f $ChunkIndex, $firstEntity, $lastEntity, $AsOfDate.ToString('yyyyMMdd'))
$receiptOut = [IO.Path]::ChangeExtension($out, '.receipt.json')
if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $receiptOut)) {
    if (-not ((Test-Path -LiteralPath $out) -and (Test-Path -LiteralPath $receiptOut))) { throw "historical_pit_partial_existing_part:$out" }
    $receipt = Get-Content -LiteralPath $receiptOut -Raw | ConvertFrom-Json
    $rawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash.ToLowerInvariant()
    if ($receipt.raw_object_sha256 -ne $rawHash -or $receipt.master_sha256 -ne $masterHash -or $receipt.historical_as_of_date -ne $asOfIso) {
        throw "historical_pit_existing_part_binding_invalid:$out"
    }
    $existing = @(Import-Csv -LiteralPath $out)
    if ($existing.Count -ne $take * $periods.Count) { throw "historical_pit_existing_part_row_count_invalid:$out" }
    Write-Output("HISTORICAL_PIT_PART_EXISTS`tINDEX=$ChunkIndex`tENTITIES=$take`tROWS=$($existing.Count)`tSHA256=$rawHash`tPATH=$out")
    exit 0
}

$excel = $null
$workbook = $null
try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    foreach ($key in @('MI Office Excel Functions','MI Office Excel Compatibility Add-in')) {
        try {
            $addin = $excel.AddIns2.Item($key)
            $addin.Installed = $false
            Start-Sleep -Milliseconds 300
            $addin.Installed = $true
        }
        catch {}
    }
    Start-Sleep -Seconds $BootSeconds
    $workbook = $excel.Workbooks.Add()
    $sheet = $workbook.Worksheets.Item(1)
    $sheet.Name = 'HistoricalPIT'
    $rowCursor = 2
    foreach ($securityRow in $batch) {
        $entityId = [string]$securityRow.SP_ENTITY_ID
        $ciqId = [string]$securityRow.SP_CIQ_ID
        $tradingItemId = [string]$securityRow.SPT_INSTRUMENT_ITEM_ID
        if ([string]::IsNullOrWhiteSpace($entityId) -or [string]::IsNullOrWhiteSpace($ciqId) -or [string]::IsNullOrWhiteSpace($tradingItemId)) {
            throw "historical_pit_chunk_identity_blank:$ChunkIndex"
        }
        foreach ($period in $periods) {
            $sheet.Cells.Item($rowCursor, 1).NumberFormat = '@'
            $sheet.Cells.Item($rowCursor, 1).Value2 = $entityId
            $sheet.Cells.Item($rowCursor, 2).NumberFormat = '@'
            $sheet.Cells.Item($rowCursor, 2).Value2 = $ciqId
            $sheet.Cells.Item($rowCursor, 3).NumberFormat = '@'
            $sheet.Cells.Item($rowCursor, 3).Value2 = $tradingItemId
            $sheet.Cells.Item($rowCursor, 4).Value2 = $period
            for ($metricIndex=0; $metricIndex -lt $metrics.Count; $metricIndex++) {
                $metric = $metrics[$metricIndex]
                $formula = '=SPG(' + $entityId + ',"' + $metric + '","' + $period + '","' + $asOfText + '","' + $options + '")'
                $sheet.Cells.Item($rowCursor, 5 + $metricIndex).Formula = $formula
            }
            $rowCursor++
        }
    }
    $lastRow = $rowCursor - 1
    $lastColumn = 4 + $metrics.Count
    $addinObject = $excel.COMAddIns.Item('SNL.Clients.Office.Excel.ExcelAddIn').Object
    if ($null -eq $addinObject) { throw 'historical_pit_ciq_addin_object_missing' }
    $addinObject.OnRibbonAction2([AovHistoricalPitChunkRcStub]::new('allowDataRefresh', $excel), $true)
    $addinObject.OnRibbonAction([AovHistoricalPitChunkRcStub]::new('refreshDataAllSheets', $excel))
    Start-Sleep -Seconds 2

    $stable = 0
    for ($poll=0; $poll -lt 120; $poll++) {
        $pending = $false
        for ($row=2; $row -le $lastRow -and -not $pending; $row++) {
            for ($column=5; $column -le $lastColumn; $column++) {
                $text = [string]$sheet.Cells.Item($row, $column).Text
                if ($text -eq '#PEND' -or $text -eq '#REFRESH') { $pending = $true; break }
            }
        }
        if ($pending) { $stable = 0 } else { $stable++ }
        if ($stable -ge 2) { break }
        if ($poll % 15 -eq 0) { Write-Output("POLL`tINDEX=$ChunkIndex`tN=$poll`tPENDING=$pending") }
        Start-Sleep -Seconds 1
    }
    if ($stable -lt 2) { throw "historical_pit_chunk_timeout:$ChunkIndex" }

    $retrievedAt = [DateTime]::UtcNow
    $rows = New-Object System.Collections.Generic.List[object]
    $rowCursor = 2
    foreach ($securityRow in $batch) {
        $entityId = [string]$securityRow.SP_ENTITY_ID
        $ciqId = [string]$securityRow.SP_CIQ_ID
        $tradingItemId = [string]$securityRow.SPT_INSTRUMENT_ITEM_ID
        foreach ($period in $periods) {
            $values = @{}
            for ($metricIndex=0; $metricIndex -lt $metrics.Count; $metricIndex++) {
                $metric = $metrics[$metricIndex]
                $cell = $sheet.Cells.Item($rowCursor, 5 + $metricIndex)
                if ($metric -eq 'IQ_PERIOD_END') { $values[$metric] = Read-DateCell $cell }
                else { $values[$metric] = Read-NumericCell $cell }
            }
            $rows.Add([pscustomobject]@{
                SP_ENTITY_ID = $entityId
                SP_CIQ_ID = $ciqId
                SPT_INSTRUMENT_ITEM_ID = $tradingItemId
                relative_period = $period
                IQ_PERIOD_END = $values['IQ_PERIOD_END']
                IQ_TOTAL_REV = $values['IQ_TOTAL_REV']
                IQ_TOTAL_ASSETS = $values['IQ_TOTAL_ASSETS']
                IQ_INVENTORY = $values['IQ_INVENTORY']
                IQ_DA_SUPPL_CF = $values['IQ_DA_SUPPL_CF']
                IQ_TOTAL_EQUITY = $values['IQ_TOTAL_EQUITY']
                IQ_TOTAL_DEBT = $values['IQ_TOTAL_DEBT']
                IQ_CASH_ST_INVEST = $values['IQ_CASH_ST_INVEST']
                IQ_OPER_INC = $values['IQ_OPER_INC']
                IQ_CAPEX_BNK = $values['IQ_CAPEX_BNK']
                as_of_date = $asOfIso
                pit_available_at_utc = $availabilityBoundary.ToString('o')
                retrieved_at_utc = $retrievedAt.ToString('o')
                source_id = 'SPCIQPRO:HISTORICAL_ASOF_QUARTERLY_FUNDAMENTALS'
                filing_version = 'Original'
            })
            $rowCursor++
        }
    }
    if ($rows.Count -ne $take * $periods.Count) { throw "historical_pit_chunk_row_count_invalid:$($rows.Count)" }
    $blankIdentityRows = @($rows | Where-Object { [string]::IsNullOrWhiteSpace($_.SP_ENTITY_ID) -or [string]::IsNullOrWhiteSpace($_.SP_CIQ_ID) -or [string]::IsNullOrWhiteSpace($_.SPT_INSTRUMENT_ITEM_ID) })
    if ($blankIdentityRows.Count -ne 0) { throw "historical_pit_chunk_output_identity_blank:$($blankIdentityRows.Count)" }
    $validPeriodEnds = @($rows | Where-Object { $_.IQ_PERIOD_END -ne 'NA' })
    if ($validPeriodEnds.Count -eq 0) { throw "historical_pit_chunk_no_valid_period_end:$ChunkIndex" }
    $validRevenue = @($rows | Where-Object { $_.IQ_TOTAL_REV -ne 'NA' })
    if ($validRevenue.Count -eq 0) { throw "historical_pit_chunk_no_valid_revenue:$ChunkIndex" }

    $temp = $out + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    $rows | Export-Csv -LiteralPath $temp -NoTypeInformation -Encoding UTF8
    [IO.File]::Move($temp, $out)
    $rawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash.ToLowerInvariant()
    $receipt = [ordered]@{
        schema_version = 'aov0_ciq_historical_pit_fundamental_part_receipt_v1'
        source_id = 'SPCIQPRO:HISTORICAL_ASOF_QUARTERLY_FUNDAMENTALS'
        provider = 'S&P Capital IQ Pro Office SPG'
        historical_as_of_date = $asOfIso
        pit_available_at_utc = $availabilityBoundary.ToString('o')
        availability_semantics = 'CONSERVATIVE_END_OF_ASOF_DATE_ANY_TIMEZONE'
        retrieved_at_utc = $retrievedAt.ToString('o')
        master_path = $MasterPath
        master_sha256 = $masterHash
        chunk_index = $ChunkIndex
        chunk_count = $chunkCount
        entity_offset = $offset
        entity_count = $take
        first_entity_id = $firstEntity
        last_entity_id = $lastEntity
        relative_periods = $periods
        metrics = $metrics
        options = $options
        raw_object_path = $out
        raw_object_sha256 = $rawHash
        raw_grid_rows = $rows.Count
        financial_alpha_evidence = 0
        evidence_authority = 'HISTORICAL_PIT_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY'
        prospective_clock_authority = 'NONE'
        parent_child_mutation_authority = 'NONE'
    }
    $receiptTemp = $receiptOut + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptTemp -Encoding UTF8
    [IO.File]::Move($receiptTemp, $receiptOut)
    $receiptHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $receiptOut).Hash.ToLowerInvariant()
    Write-Output("HISTORICAL_PIT_PART_OK`tINDEX=$ChunkIndex`tENTITIES=$take`tROWS=$($rows.Count)`tRETRIEVED_AT=$($retrievedAt.ToString('o'))`tSHA256=$rawHash`tRECEIPT_SHA256=$receiptHash`tPATH=$out")
}
finally {
    if ($workbook) { try { $workbook.Close($false) } catch {} }
    if ($excel) {
        try { $excel.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
    }
}
