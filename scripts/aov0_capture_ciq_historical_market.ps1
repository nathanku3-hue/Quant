param(
    [Parameter(Mandatory=$true)][datetime]$StartDate,
    [Parameter(Mandatory=$true)][datetime]$EndDate,
    [Parameter(Mandatory=$true)][datetime]$DecisionTargetDate,
    [string]$Master = '',
    [string]$OutDir = '',
    [int]$ChunkWeekdays = 7
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Master) { $Master = Join-Path $repoRoot 'data\aov0\raw\ciq_primary_security_master_20260808T162322Z.csv' }
if (-not $OutDir) { $OutDir = Join-Path $repoRoot 'data\aov0\raw' }
if ($ChunkWeekdays -ne 7) { throw 'historical_market_chunk_weekdays_must_equal_frozen_7' }
if ($EndDate.Date -lt $StartDate.Date) { throw 'historical_market_date_order_invalid' }
if ($DecisionTargetDate.Date -lt $StartDate.Date -or $DecisionTargetDate.Date -gt $EndDate.Date) { throw 'historical_market_target_outside_range' }

Add-Type -AssemblyName office
if (-not ('AovHistoricalMarketRcStub' -as [type])) {
    $source = @'
using System; using Microsoft.Office.Core;
public sealed class AovHistoricalMarketRcStub : IRibbonControl {
    public string Id { get; private set; }
    public string Tag { get; private set; }
    public object Context { get; private set; }
    public AovHistoricalMarketRcStub(string id, object context) { Id=id; Tag=""; Context=context; }
}
'@
    Add-Type -TypeDefinition $source -ReferencedAssemblies ([Microsoft.Office.Core.IRibbonControl].Assembly.Location)
}

function Complete-Value([object]$Value) {
    if ($null -eq $Value) { return $false }
    $text = [string]$Value
    if ([string]::IsNullOrWhiteSpace($text)) { return $false }
    return $text -notmatch '^(?i:NA|N/A|#N/A|#VALUE!?|#ERROR!?|#PEND|#REFRESH|null|none)$'
}

function Invariant-Value([object]$Value) {
    if (-not (Complete-Value $Value)) { return 'NA' }
    try { return [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:R}', [double]$Value) }
    catch { return [string]$Value }
}

function Invoke-ComRetry([scriptblock]$Action, [string]$Label='COM', [int]$Attempts=60) {
    for ($i=0; $i -lt $Attempts; $i++) {
        try { return & $Action }
        catch [Runtime.InteropServices.COMException] {
            if ($_.Exception.HResult -eq -2147418111) { Start-Sleep -Milliseconds 500; continue }
            throw
        }
    }
    throw "$Label rejected after $Attempts retries"
}

function Column-Name([int]$Number) {
    $name = ''
    while ($Number -gt 0) {
        $Number--
        $name = [char](65 + ($Number % 26)) + $name
        $Number = [math]::Floor($Number / 26)
    }
    return $name
}

$masterRows = @(Import-Csv -LiteralPath $Master)
if ($masterRows.Count -ne 109) { throw "historical_market_master_count_invalid:$($masterRows.Count)" }
foreach ($column in @('SP_ENTITY_ID','SP_SECURITY_ID','SP_CIQ_ID','SPT_INSTRUMENT_ITEM_ID','SP_TRADING_ITEM_ID')) {
    if (-not ($masterRows[0].PSObject.Properties.Name -contains $column)) { throw "historical_market_master_column_missing:$column" }
    if (@($masterRows.$column | Where-Object { $_ } | Sort-Object -Unique).Count -ne 109) { throw "historical_market_master_identity_collision:$column" }
}
$masterHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Master).Hash.ToLowerInvariant()

$dates = New-Object System.Collections.Generic.List[datetime]
for ($date=$StartDate.Date; $date -le $EndDate.Date; $date=$date.AddDays(1)) {
    if ($date.DayOfWeek -ne [DayOfWeek]::Saturday -and $date.DayOfWeek -ne [DayOfWeek]::Sunday) { $dates.Add($date) }
}
if ($dates.Count -lt 1) { throw 'historical_market_no_weekdays' }
$fields = @('SP_TOTAL_RETURN','SP_PRICE_CLOSE','SP_VOLUME')
$rows = New-Object System.Collections.Generic.List[object]
$excel = $null
$workbook = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    foreach ($key in @('MI Office Excel Functions','MI Office Excel Compatibility Add-in')) {
        $addin = $excel.AddIns2.Item($key)
        $addin.Installed = $false
        Start-Sleep -Milliseconds 300
        $addin.Installed = $true
    }
    Start-Sleep -Seconds 10
    $officeAddin = $excel.COMAddIns.Item('SNL.Clients.Office.Excel.ExcelAddIn').Object
    if ($null -eq $officeAddin) { throw 'historical_market_ciq_addin_object_missing' }
    $officeAddin.OnRibbonAction2([AovHistoricalMarketRcStub]::new('allowDataRefresh', $excel), $true)

    $workbook = Invoke-ComRetry { $excel.Workbooks.Add() } 'Workbooks.Add'
    $sheet = $workbook.Worksheets.Item(1)
    $sheet.Name = 'HistoricalMarket'
    $firstDataRow = 8
    $lastDataRow = $firstDataRow + $masterRows.Count - 1
    for ($entityIndex=0; $entityIndex -lt $masterRows.Count; $entityIndex++) {
        $row = $firstDataRow + $entityIndex
        $sheet.Cells.Item($row, 2).NumberFormat = '@'
        $sheet.Cells.Item($row, 2).Value2 = 'IQT' + [string]$masterRows[$entityIndex].SP_TRADING_ITEM_ID
    }

    $chunkNumber = 0
    for ($offset=0; $offset -lt $dates.Count; $offset += $ChunkWeekdays) {
        $chunkNumber++
        $take = [Math]::Min($ChunkWeekdays, $dates.Count - $offset)
        $chunk = @($dates[$offset..($offset+$take-1)])
        $column = 3
        foreach ($date in $chunk) {
            $dateText = $date.ToString('MM/dd/yyyy', [Globalization.CultureInfo]::InvariantCulture)
            foreach ($field in $fields) {
                $sheet.Cells.Item(5, $column).Value2 = $field
                $sheet.Cells.Item(6, $column).Value2 = $dateText
                $column++
            }
        }
        $lastColumn = $column - 1
        $lastColumnName = Column-Name $lastColumn
        $sheet.Range('A3').Formula = ('=SPGTable($B$8:$B${0},$C$5:${1}$5,$C$6:${1}$6,"Options:Curr=USD,ConvMethod=R,FilingVer=Current/Restated")' -f $lastDataRow, $lastColumnName)
        $officeAddin.OnRibbonAction([AovHistoricalMarketRcStub]::new('refreshDataAllSheets', $excel))

        $valueRange = $sheet.Range($sheet.Cells.Item($firstDataRow, 3), $sheet.Cells.Item($lastDataRow, $lastColumn))
        $matrix = $null
        $pending = -1
        $filled = 0
        for ($poll=0; $poll -lt 75; $poll++) {
            Start-Sleep -Seconds 1
            $matrix = Invoke-ComRetry { ,$valueRange.Value2 } 'HistoricalMarket.Value2'
            $pending = 0; $filled = 0
            $rowLow = $matrix.GetLowerBound(0); $rowHigh = $matrix.GetUpperBound(0)
            $colLow = $matrix.GetLowerBound(1); $colHigh = $matrix.GetUpperBound(1)
            for ($ri=$rowLow; $ri -le $rowHigh; $ri++) {
                for ($ci=$colLow; $ci -le $colHigh; $ci++) {
                    $value = [string]$matrix[$ri,$ci]
                    if ($value -eq '#PEND' -or $value -eq '#REFRESH') { $pending++ }
                    elseif (-not [string]::IsNullOrWhiteSpace($value)) { $filled++ }
                }
            }
            if ($pending -eq 0 -and $filled -gt 0) { break }
            if ($poll % 10 -eq 0) { Write-Output("POLL`tCHUNK=$chunkNumber`tN=$poll`tPENDING=$pending`tFILLED=$filled") }
        }
        if ($pending -ne 0 -or $filled -eq 0) { throw "historical_market_chunk_incomplete:chunk=$chunkNumber;pending=$pending;filled=$filled" }
        Start-Sleep -Milliseconds 750
        $matrix = Invoke-ComRetry { ,$valueRange.Value2 } 'HistoricalMarket.FinalValue2'
        $chunkRetrievedAt = [DateTime]::UtcNow
        $rowLow = $matrix.GetLowerBound(0); $colLow = $matrix.GetLowerBound(1)

        for ($entityIndex=0; $entityIndex -lt $masterRows.Count; $entityIndex++) {
            $master = $masterRows[$entityIndex]
            $matrixRow = $rowLow + $entityIndex
            for ($dateIndex=0; $dateIndex -lt $chunk.Count; $dateIndex++) {
                $base = $colLow + ($dateIndex * 3)
                $ret = Invariant-Value $matrix[$matrixRow, $base]
                $close = Invariant-Value $matrix[$matrixRow, $base + 1]
                $volume = Invariant-Value $matrix[$matrixRow, $base + 2]
                $rows.Add([pscustomobject]@{
                    SPT_DATE = $chunk[$dateIndex].ToString('yyyy-MM-dd')
                    SP_ENTITY_ID = [string]$master.SP_ENTITY_ID
                    SP_SECURITY_ID = [string]$master.SP_SECURITY_ID
                    SP_CIQ_ID = [string]$master.SP_CIQ_ID
                    SPT_INSTRUMENT_ITEM_ID = [string]$master.SPT_INSTRUMENT_ITEM_ID
                    SP_TRADING_ITEM_ID = [string]$master.SP_TRADING_ITEM_ID
                    SPT_TOTAL_RETURN = $ret
                    SP_TOTAL_RETURN = $ret
                    SPT_CLOSE = $close
                    SP_PRICE_CLOSE = $close
                    SPT_VOLUME = $volume
                    SP_VOLUME = $volume
                    chunk_retrieved_at_utc = $chunkRetrievedAt.ToString('o')
                    RETURN_SOURCE_METRIC = 'SP_TOTAL_RETURN'
                    CLOSE_SOURCE_METRIC = 'SP_PRICE_CLOSE'
                    VOLUME_SOURCE_METRIC = 'SP_VOLUME'
                })
            }
        }
        $sheet.Range('A3').ClearContents()
        Write-Output("CHUNK_OK`tN=$chunkNumber`tDATES=$take`tFROM=$($chunk[0].ToString('yyyy-MM-dd'))`tTO=$($chunk[-1].ToString('yyyy-MM-dd'))`tROWS_TOTAL=$($rows.Count)")
    }
}
finally {
    if ($workbook) { try { $workbook.Close($false) } catch {} }
    if ($excel) {
        try { $excel.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
    }
}

$expectedRows = 109 * $dates.Count
if ($rows.Count -ne $expectedRows) { throw "historical_market_output_grid_invalid:$($rows.Count)/$expectedRows" }
$retrievedAt = [DateTime]::UtcNow
[IO.Directory]::CreateDirectory($OutDir) | Out-Null
$stamp = $retrievedAt.ToString('yyyyMMddTHHmmssZ')
$out = Join-Path $OutDir ("ciq_historical_market_{0}_{1}_{2}.csv" -f $StartDate.ToString('yyyyMMdd'), $EndDate.ToString('yyyyMMdd'), $stamp)
$temp = $out + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
$rows | Export-Csv -LiteralPath $temp -NoTypeInformation -Encoding UTF8
[IO.File]::Move($temp, $out)
$rawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash.ToLowerInvariant()

$targetText = $DecisionTargetDate.ToString('yyyy-MM-dd')
$counts = @($rows | Group-Object SP_CIQ_ID | ForEach-Object {
    $group = @($_.Group)
    $pre = @($group | Where-Object { $_.SPT_DATE -le $targetText -and $_.SPT_CLOSE -ne 'NA' -and $_.SPT_TOTAL_RETURN -ne 'NA' -and $_.SPT_VOLUME -ne 'NA' })
    $post = @($group | Where-Object { $_.SPT_DATE -gt $targetText -and $_.SPT_CLOSE -ne 'NA' -and $_.SPT_TOTAL_RETURN -ne 'NA' -and $_.SPT_VOLUME -ne 'NA' })
    [pscustomobject]@{
        SP_CIQ_ID = $_.Name
        SP_ENTITY_ID = $group[0].SP_ENTITY_ID
        SPT_INSTRUMENT_ITEM_ID = $group[0].SPT_INSTRUMENT_ITEM_ID
        completed_pre_target = $pre.Count
        target_date_present = [bool](@($pre | Where-Object { $_.SPT_DATE -eq $targetText }).Count)
        completed_post_target = $post.Count
    }
} | Sort-Object SP_CIQ_ID)
$countsOut = [IO.Path]::ChangeExtension($out, '.counts.csv')
$countsTemp = $countsOut + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
$counts | Export-Csv -LiteralPath $countsTemp -NoTypeInformation -Encoding UTF8
[IO.File]::Move($countsTemp, $countsOut)
$countsHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $countsOut).Hash.ToLowerInvariant()
$ge200 = @($counts | Where-Object { [int]$_.completed_pre_target -ge 200 -and $_.target_date_present }).Count

$receipt = [ordered]@{
    schema_version = 'aov0_ciq_historical_market_receipt_v1'
    source_id = 'SPCIQPRO:HISTORICAL_PRIMARY_SECURITY_MARKET_DATA'
    provider = 'S&P Capital IQ Pro Office SPGTable'
    start_date = $StartDate.ToString('yyyy-MM-dd')
    end_date = $EndDate.ToString('yyyy-MM-dd')
    decision_target_date = $targetText
    retrieved_at_utc = $retrievedAt.ToString('o')
    master_path = $Master
    master_sha256 = $masterHash
    frozen_entity_count = 109
    # Compatibility field: this asserts that the query used exactly the SPT
    # supplied by the input master. It is not historical-primary identity proof.
    exact_primary_spt_query = $true
    query_identity_key = 'SPT_INSTRUMENT_ITEM_ID_FROM_INPUT_SECURITY_MASTER'
    identity_columns_source = 'EXTERNAL_INPUT_SECURITY_MASTER'
    historical_primary_identity_reconstructed = $false
    historical_primary_identity_authority = 'NONE_REQUIRES_SEPARATE_HISTORICAL_PRIMARY_RECEIPT'
    alternate_listing_backfill_used = $false
    provider_weekday_chunk_width = 7
    query_fields = $fields
    raw_object_path = $out
    raw_object_sha256 = $rawHash
    raw_grid_rows = $rows.Count
    counts_path = $countsOut
    counts_sha256 = $countsHash
    ge200_with_target = $ge200
    financial_alpha_evidence = 0
    evidence_authority = 'HISTORICAL_MARKET_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY'
    prospective_clock_authority = 'NONE'
    parent_child_mutation_authority = 'NONE'
}
$receiptOut = [IO.Path]::ChangeExtension($out, '.receipt.json')
$receiptTemp = $receiptOut + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptTemp -Encoding UTF8
[IO.File]::Move($receiptTemp, $receiptOut)
$receiptHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $receiptOut).Hash.ToLowerInvariant()
Write-Output("HISTORICAL_MARKET_CAPTURE_OK`tROWS=$($rows.Count)`tDATES=$($dates.Count)`tGE200_WITH_TARGET=$ge200`tSHA256=$rawHash`tPATH=$out`tCOUNTS=$countsOut`tCOUNTS_SHA256=$countsHash`tRECEIPT=$receiptOut`tRECEIPT_SHA256=$receiptHash")
