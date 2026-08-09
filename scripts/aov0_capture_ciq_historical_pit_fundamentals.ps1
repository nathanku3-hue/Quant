param(
    [Parameter(Mandatory=$true)][datetime]$AsOfDate,
    [string]$Master = '',
    [string]$OutDir = '',
    [int]$BatchEntities = 25
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Master) { $Master = Join-Path $repoRoot 'data\aov0\raw\ciq_primary_security_master_20260808T162322Z.csv' }
if (-not $OutDir) { $OutDir = Join-Path $repoRoot 'data\aov0\raw' }
if ($BatchEntities -lt 1 -or $BatchEntities -gt 40) { throw 'historical_pit_batch_entities_out_of_range' }
if (-not (Test-Path -LiteralPath $Master)) { throw "historical_pit_master_missing:$Master" }

Add-Type -AssemblyName office
if (-not ('AovHistoricalPitRcStub' -as [type])) {
    $source = @'
using System; using Microsoft.Office.Core;
public sealed class AovHistoricalPitRcStub : IRibbonControl {
    public string Id { get; private set; }
    public string Tag { get; private set; }
    public object Context { get; private set; }
    public AovHistoricalPitRcStub(string id, object context) { Id=id; Tag=""; Context=context; }
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
    if ($Value -is [double] -or $Value -is [single] -or $Value -is [decimal] -or $Value -is [int] -or $Value -is [long]) {
        return [string]::Format([Globalization.CultureInfo]::InvariantCulture, '{0:R}', [double]$Value)
    }
    return [string]$Value
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

$masterRows = @(Import-Csv -LiteralPath $Master)
if ($masterRows.Count -ne 109) { throw "historical_pit_master_count_invalid:$($masterRows.Count)" }
if (@($masterRows.SP_ENTITY_ID | Sort-Object -Unique).Count -ne 109) { throw 'historical_pit_master_entity_collision' }
if (@($masterRows.SP_CIQ_ID | Sort-Object -Unique).Count -ne 109) { throw 'historical_pit_master_security_collision' }
if (@($masterRows.SPT_INSTRUMENT_ITEM_ID | Sort-Object -Unique).Count -ne 109) { throw 'historical_pit_master_trading_collision' }

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
$masterHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Master).Hash.ToLowerInvariant()
$rows = New-Object System.Collections.Generic.List[object]

$excel = $null
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
    if ($null -eq $officeAddin) { throw 'historical_pit_ciq_addin_object_missing' }
    $officeAddin.OnRibbonAction2([AovHistoricalPitRcStub]::new('allowDataRefresh', $excel), $true)

    for ($start=0; $start -lt $masterRows.Count; $start += $BatchEntities) {
        $take = [Math]::Min($BatchEntities, $masterRows.Count - $start)
        $batch = @($masterRows[$start..($start+$take-1)])
        $workbook = $null
        try {
            $workbook = Invoke-ComRetry { $excel.Workbooks.Add() } 'Workbooks.Add'
            $sheet = $workbook.Worksheets.Item(1)
            $sheet.Name = 'HistoricalPIT'
            $rowCursor = 2
            foreach ($master in $batch) {
                foreach ($period in $periods) {
                    $sheet.Cells.Item($rowCursor, 1).NumberFormat = '@'
                    $sheet.Cells.Item($rowCursor, 1).Value2 = [string]$master.SP_ENTITY_ID
                    $sheet.Cells.Item($rowCursor, 2).NumberFormat = '@'
                    $sheet.Cells.Item($rowCursor, 2).Value2 = [string]$master.SP_CIQ_ID
                    $sheet.Cells.Item($rowCursor, 3).NumberFormat = '@'
                    $sheet.Cells.Item($rowCursor, 3).Value2 = [string]$master.SPT_INSTRUMENT_ITEM_ID
                    $sheet.Cells.Item($rowCursor, 4).Value2 = $period
                    for ($metricIndex=0; $metricIndex -lt $metrics.Count; $metricIndex++) {
                        $metric = $metrics[$metricIndex]
                        $column = 5 + $metricIndex
                        $formula = '=SPG(' + [string]$master.SP_ENTITY_ID + ',"' + $metric + '","' + $period + '","' + $asOfText + '","' + $options + '")'
                        $sheet.Cells.Item($rowCursor, $column).Formula = $formula
                    }
                    $rowCursor++
                }
            }
            $lastRow = $rowCursor - 1
            $lastColumn = 4 + $metrics.Count
            $officeAddin.OnRibbonAction([AovHistoricalPitRcStub]::new('refreshDataAllSheets', $excel))

            $valueRange = $sheet.Range($sheet.Cells.Item(2, 5), $sheet.Cells.Item($lastRow, $lastColumn))
            $matrix = $null
            $pending = -1
            $filled = 0
            for ($poll=0; $poll -lt 90; $poll++) {
                Start-Sleep -Seconds 1
                $matrix = Invoke-ComRetry { ,$valueRange.Value2 } 'HistoricalPIT.Value2'
                $pending = 0
                $filled = 0
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
                if ($poll % 10 -eq 0) { Write-Output("POLL`tBATCH_START=$start`tN=$poll`tPENDING=$pending`tFILLED=$filled") }
            }
            if ($pending -ne 0 -or $filled -eq 0) { throw "historical_pit_batch_incomplete:start=$start;pending=$pending;filled=$filled" }
            Start-Sleep -Milliseconds 750
            $matrix = Invoke-ComRetry { ,$valueRange.Value2 } 'HistoricalPIT.FinalValue2'

            $rowLow = $matrix.GetLowerBound(0); $colLow = $matrix.GetLowerBound(1)
            for ($entityIndex=0; $entityIndex -lt $take; $entityIndex++) {
                $master = $batch[$entityIndex]
                for ($periodIndex=0; $periodIndex -lt $periods.Count; $periodIndex++) {
                    $matrixRow = $rowLow + ($entityIndex * $periods.Count) + $periodIndex
                    $values = @{}
                    for ($metricIndex=0; $metricIndex -lt $metrics.Count; $metricIndex++) {
                        $metric = $metrics[$metricIndex]
                        $rawValue = $matrix[$matrixRow, $colLow + $metricIndex]
                        if ($metric -eq 'IQ_PERIOD_END' -and (Complete-Value $rawValue)) {
                            try { $values[$metric] = [datetime]::FromOADate([double]$rawValue).ToString('yyyy-MM-dd') }
                            catch { $values[$metric] = 'NA' }
                        } else {
                            $values[$metric] = Invariant-Value $rawValue
                        }
                    }
                    $rows.Add([pscustomobject]@{
                        SP_ENTITY_ID = [string]$master.SP_ENTITY_ID
                        SP_CIQ_ID = [string]$master.SP_CIQ_ID
                        SPT_INSTRUMENT_ITEM_ID = [string]$master.SPT_INSTRUMENT_ITEM_ID
                        relative_period = $periods[$periodIndex]
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
                        source_id = 'SPCIQPRO:HISTORICAL_ASOF_QUARTERLY_FUNDAMENTALS'
                        filing_version = 'Original'
                    })
                }
            }
            Write-Output("BATCH_OK`tSTART=$start`tENTITIES=$take`tROWS=$($take*$periods.Count)`tFILLED=$filled")
        }
        finally {
            if ($workbook) { try { $workbook.Close($false) } catch {} }
        }
    }
}
finally {
    if ($excel) {
        try { $excel.Quit() } catch {}
        try { [void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel) } catch {}
    }
}

if ($rows.Count -ne 109 * $periods.Count) { throw "historical_pit_output_grid_invalid:$($rows.Count)" }
$retrievedAt = [DateTime]::UtcNow
foreach ($row in $rows) { $row | Add-Member -NotePropertyName retrieved_at_utc -NotePropertyValue $retrievedAt.ToString('o') }

[IO.Directory]::CreateDirectory($OutDir) | Out-Null
$stamp = $retrievedAt.ToString('yyyyMMddTHHmmssZ')
$out = Join-Path $OutDir ("ciq_historical_pit_fundamentals_{0}_{1}.csv" -f $AsOfDate.ToString('yyyyMMdd'), $stamp)
$temp = $out + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
$rows | Export-Csv -LiteralPath $temp -NoTypeInformation -Encoding UTF8
[IO.File]::Move($temp, $out)
$rawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash.ToLowerInvariant()
$rawBytes = (Get-Item -LiteralPath $out).Length

$receipt = [ordered]@{
    schema_version = 'aov0_ciq_historical_pit_fundamentals_receipt_v1'
    source_id = 'SPCIQPRO:HISTORICAL_ASOF_QUARTERLY_FUNDAMENTALS'
    provider = 'S&P Capital IQ Pro Office SPG'
    historical_as_of_date = $asOfIso
    pit_available_at_utc = $availabilityBoundary.ToString('o')
    availability_semantics = 'CONSERVATIVE_END_OF_ASOF_DATE_ANY_TIMEZONE'
    retrieved_at_utc = $retrievedAt.ToString('o')
    master_path = $Master
    master_sha256 = $masterHash
    frozen_entity_count = 109
    relative_periods = $periods
    metrics = $metrics
    options = $options
    raw_object_path = $out
    raw_object_sha256 = $rawHash
    raw_object_bytes = $rawBytes
    raw_grid_rows = $rows.Count
    financial_alpha_evidence = 0
    evidence_authority = 'HISTORICAL_PIT_ONLY_NOT_PROSPECTIVE_CLOCK_AUTHORITY'
    prospective_clock_authority = 'NONE'
    parent_child_mutation_authority = 'NONE'
}
$receiptOut = [IO.Path]::ChangeExtension($out, '.receipt.json')
$receiptTemp = $receiptOut + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptTemp -Encoding UTF8
[IO.File]::Move($receiptTemp, $receiptOut)
$receiptHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $receiptOut).Hash.ToLowerInvariant()
Write-Output("HISTORICAL_PIT_CAPTURE_OK`tASOF=$asOfIso`tROWS=$($rows.Count)`tAVAILABLE_AT=$($availabilityBoundary.ToString('o'))`tRETRIEVED_AT=$($retrievedAt.ToString('o'))`tSHA256=$rawHash`tBYTES=$rawBytes`tPATH=$out`tRECEIPT=$receiptOut`tRECEIPT_SHA256=$receiptHash")
