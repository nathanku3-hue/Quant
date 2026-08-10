param(
    [Parameter(Mandatory=$true)][int]$ChunkIndex,
    [Parameter(Mandatory=$true)][string]$Master,
    [Parameter(Mandatory=$true)][string]$PartsDir,
    [Parameter(Mandatory=$true)][datetime]$TargetDate,
    [Parameter(Mandatory=$true)][int]$Weekdays,
    [ValidateRange(1,20)][int]$ChunkDays=7,
    [int]$BootSeconds=10
)
$ErrorActionPreference='Stop'
if(-not (Test-Path -LiteralPath $Master)){throw "historical_market_master_missing:$Master"}
Add-Type -AssemblyName office
if(-not ('CiqHistoricalMarketRcStub' -as [type])){$src=@'
using System; using Microsoft.Office.Core;
public sealed class CiqHistoricalMarketRcStub : IRibbonControl { public string Id{get;private set;} public string Tag{get;private set;} public object Context{get;private set;} public CiqHistoricalMarketRcStub(string id, object ctx){Id=id;Tag="";Context=ctx;} }
'@;Add-Type -TypeDefinition $src -ReferencedAssemblies ([Microsoft.Office.Core.IRibbonControl].Assembly.Location)}
function File-Sha256([string]$Path){
  $sha = [System.Security.Cryptography.SHA256]::Create()
  try {
    $fs = [System.IO.File]::OpenRead($Path)
    try {
      $hash = $sha.ComputeHash($fs)
      return ([BitConverter]::ToString($hash) -replace '-','').ToLowerInvariant()
    } finally { $fs.Dispose() }
  } finally { $sha.Dispose() }
}
function Csv([object]$value){$text=[string]$value;return '"'+($text-replace'"','""')+'"'}
function ColName([int]$n){$s='';while($n-gt0){$n--; $s=[char](65+($n%26))+$s;$n=[math]::Floor($n/26)};return $s}
function Invoke-ComRetry([scriptblock]$Action,[string]$Label='COM',[int]$Attempts=60){for($i=0;$i-lt$Attempts;$i++){try{return & $Action}catch [Runtime.InteropServices.COMException]{if($_.Exception.HResult-eq-2147418111){Start-Sleep -Milliseconds 500;continue};throw}};throw "$Label rejected after $Attempts retries"}
$ExcelCvErrHresults=@(-2146826288,-2146826281,-2146826273,-2146826265,-2146826259,-2146826252,-2146826246,-2146826245)
function Is-MissingValue([object]$value){if($null-eq$value){return $true};$text=[string]$value;if(!$text-or$text-eq'NA'-or$text-match'^#'){return $true};try{$number=[int64]([double]$value);if($ExcelCvErrHresults-contains$number){return $true}}catch{};return $false}

$masterRows=@(Import-Csv -LiteralPath $Master)
if($masterRows.Count-lt1){throw 'historical_market_master_empty'}
foreach($column in @('SP_ENTITY_ID','SP_SECURITY_ID','SPT_INSTRUMENT_ITEM_ID','SP_TRADING_ITEM_ID')){if(-not ($masterRows[0].PSObject.Properties.Name -contains $column)){throw "historical_market_master_column_missing:$column"}}
if(@($masterRows.SP_ENTITY_ID|ForEach-Object{[string]$_}|Where-Object{$_}|Sort-Object -Unique).Count-ne$masterRows.Count){throw 'historical_market_master_entity_id_invalid_or_duplicate'}
if(@($masterRows.SP_SECURITY_ID|ForEach-Object{[string]$_}|Where-Object{$_}|Sort-Object -Unique).Count-ne$masterRows.Count){throw 'historical_market_master_security_id_invalid_or_duplicate'}
if(@($masterRows.SPT_INSTRUMENT_ITEM_ID|ForEach-Object{[string]$_}|Where-Object{$_}|Sort-Object -Unique).Count-ne$masterRows.Count){throw 'historical_market_master_instrument_id_invalid_or_duplicate'}
if(@($masterRows.SP_TRADING_ITEM_ID|ForEach-Object{[string]$_}|Where-Object{$_}|Sort-Object -Unique).Count-ne$masterRows.Count){throw 'historical_market_master_trading_item_id_invalid_or_duplicate'}
$dates=@();$cursor=$TargetDate.Date
while($dates.Count-lt$Weekdays){if($cursor.DayOfWeek-ne[DayOfWeek]::Saturday-and$cursor.DayOfWeek-ne[DayOfWeek]::Sunday){$dates+=$cursor};$cursor=$cursor.AddDays(-1)}
[array]::Reverse($dates)
$chunkCount=[int][Math]::Ceiling($dates.Count/[double]$ChunkDays)
if($ChunkIndex-lt0-or$ChunkIndex-ge$chunkCount){throw "chunk_index_invalid:$ChunkIndex/$chunkCount"}
$offset=$ChunkIndex*$ChunkDays;$take=[Math]::Min($ChunkDays,$dates.Count-$offset);$chunk=$dates[$offset..($offset+$take-1)]
[IO.Directory]::CreateDirectory($PartsDir)|Out-Null
$out=Join-Path $PartsDir ("part_{0:D3}_{1}_{2}.csv" -f $ChunkIndex,$chunk[0].ToString('yyyyMMdd'),$chunk[-1].ToString('yyyyMMdd'))
if(Test-Path -LiteralPath $out){$existing=Import-Csv -LiteralPath $out;if($existing.Count-gt0){Write-Output("PART_EXISTS`tINDEX=$ChunkIndex`tROWS=$($existing.Count)`tPATH=$out");exit 0}else{throw "existing_part_empty:$out"}}

$excel=$null;$workbook=$null
try{
    $excel=New-Object -ComObject Excel.Application;$excel.Visible=$false;$excel.DisplayAlerts=$false
    foreach($key in @('MI Office Excel Functions','MI Office Excel Compatibility Add-in')){
        try{$addin=$excel.AddIns2.Item($key);$addin.Installed=$false;Start-Sleep -Milliseconds 300;$addin.Installed=$true}catch{}
    }
    Start-Sleep -Seconds $BootSeconds
    $addinObject=$null
    for($attempt=0;$attempt-lt3-and-not$addinObject;$attempt++){
        try{$addinObject=$excel.COMAddIns.Item('SNL.Clients.Office.Excel.ExcelAddIn').Object}catch{}
        if(!$addinObject){Start-Sleep -Seconds 2}
    }
    if(!$addinObject){throw 'ciq_addin_object_missing'}
    $addinObject.OnRibbonAction2([CiqHistoricalMarketRcStub]::new('allowDataRefresh',$excel),$true)
    $workbook=Invoke-ComRetry {$excel.Workbooks.Add()} 'HistoricalMarket.Workbooks.Add';$sheet=$workbook.Worksheets.Item(1);$startRow=8;$lastRow=$startRow+$masterRows.Count-1
    for($i=0;$i-lt$masterRows.Count;$i++){$sheet.Cells.Item($startRow+$i,2).Value2=[string]$masterRows[$i].SPT_INSTRUMENT_ITEM_ID}
    for($d=0;$d-lt$take;$d++){$dateText=$chunk[$d].ToString('MM/dd/yyyy',[Globalization.CultureInfo]::InvariantCulture);$base=3+$d*3;$sheet.Cells.Item(5,$base).Value2='SP_TOTAL_RETURN';$sheet.Cells.Item(6,$base).Value2=$dateText;$sheet.Cells.Item(5,$base+1).Value2='SP_PRICE_CLOSE';$sheet.Cells.Item(6,$base+1).Value2=$dateText;$sheet.Cells.Item(5,$base+2).Value2='SP_VOLUME';$sheet.Cells.Item(6,$base+2).Value2=$dateText}
    $lastCol=2+$take*3;$last=ColName $lastCol;$sheet.Range('A3').Formula=('=SPGTable($B$8:$B${0},$C$5:${1}$5,$C$6:${1}$6,"Options:Curr=USD,ConvMethod=R,FilingVer=Current/Restated")' -f $lastRow,$last)
    $addinObject.OnRibbonAction([CiqHistoricalMarketRcStub]::new('refreshDataAllSheets',$excel));Start-Sleep -Seconds 2
    $valueRange=$sheet.Range($sheet.Cells.Item($startRow,3),$sheet.Cells.Item($lastRow,$lastCol));$matrix=$null;$stable=0
    for($poll=0;$poll-lt120;$poll++){
        $matrix=Invoke-ComRetry {,$valueRange.Value2} 'HistoricalMarket.Value2';$pending=0;$filled=0
        $rowLow=$matrix.GetLowerBound(0);$rowHigh=$matrix.GetUpperBound(0);$colLow=$matrix.GetLowerBound(1);$colHigh=$matrix.GetUpperBound(1)
        for($ri=$rowLow;$ri-le$rowHigh;$ri++){for($ci=$colLow;$ci-le$colHigh;$ci++){$text=[string]$matrix.GetValue($ri,$ci);if($text-eq'#PEND'-or$text-eq'#REFRESH'){$pending++}elseif(-not [string]::IsNullOrWhiteSpace($text)){$filled++}}}
        if($pending-eq0-and$filled-gt0){$stable++}else{$stable=0};if($stable-ge2){break};Start-Sleep -Seconds 1
    }
    if($stable-lt2){throw "chunk_timeout:$ChunkIndex"}
    $matrix=Invoke-ComRetry {,$valueRange.Value2} 'HistoricalMarket.FinalValue2';$retrieved=[DateTime]::UtcNow;$rows=New-Object System.Collections.Generic.List[object]
    $rowLow=$matrix.GetLowerBound(0);$colLow=$matrix.GetLowerBound(1)
    for($i=0;$i-lt$masterRows.Count;$i++){$matrixRow=$rowLow+$i;$m=$masterRows[$i];for($d=0;$d-lt$take;$d++){$base=$colLow+$d*3;$trValue=$matrix.GetValue($matrixRow,$base);$closeValue=$matrix.GetValue($matrixRow,$base+1);$volValue=$matrix.GetValue($matrixRow,$base+2);if((Is-MissingValue $trValue)-or(Is-MissingValue $closeValue)-or(Is-MissingValue $volValue)){continue};try{$tr=[double]$trValue;$close=[double]$closeValue;$vol=[double]$volValue}catch{continue};$rows.Add([pscustomobject]@{date=$chunk[$d].ToString('yyyy-MM-dd');entity=$m.SP_ENTITY_ID;security=$m.SP_SECURITY_ID;spt=$m.SPT_INSTRUMENT_ITEM_ID;trade=$m.SP_TRADING_ITEM_ID;total_return=$tr;close=$close;volume=$vol})}}
    if($rows.Count-eq0){throw "chunk_no_rows:$ChunkIndex"}
    $headers=@('SPT_DATE','SP_ENTITY_ID','SP_SECURITY_ID','SPT_INSTRUMENT_ITEM_ID','SP_TRADING_ITEM_ID','SPT_TOTAL_RETURN','SP_TOTAL_RETURN','SPT_CLOSE','SP_PRICE_CLOSE','SPT_VOLUME','SP_VOLUME','chunk_retrieved_at_utc','RETURN_SOURCE_METRIC','CLOSE_SOURCE_METRIC','VOLUME_SOURCE_METRIC')
    $lines=New-Object System.Collections.Generic.List[string];$lines.Add(($headers|ForEach-Object{Csv $_})-join',')
    foreach($row in $rows){$vals=@($row.date,$row.entity,$row.security,$row.spt,$row.trade,([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',$row.total_return)),([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',$row.total_return)),([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',$row.close)),([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',$row.close)),([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',$row.volume)),([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',$row.volume)),$retrieved.ToString('o'),'SP_TOTAL_RETURN','SP_PRICE_CLOSE','SP_VOLUME');$lines.Add(($vals|ForEach-Object{Csv $_})-join',')}
    $tmp=$out+'.'+[Guid]::NewGuid().ToString('N')+'.tmp';[IO.File]::WriteAllLines($tmp,$lines,[Text.UTF8Encoding]::new($false));
    $landedByThisProcess=$false
    try {
        [IO.File]::Move($tmp,$out)
        $landedByThisProcess=$true
    } catch [System.IO.IOException] {
        if(-not (Test-Path -LiteralPath $out)){throw}
        $existing=Import-Csv -LiteralPath $out
        if($existing.Count-le0){throw "raced_existing_part_empty:$out"}
        Remove-Item -LiteralPath $tmp -Force
    }
    $hash=File-Sha256 $out
    if($landedByThisProcess){Write-Output("PART_OK`tINDEX=$ChunkIndex`tROWS=$($rows.Count)`tFROM=$($chunk[0].ToString('yyyy-MM-dd'))`tTO=$($chunk[-1].ToString('yyyy-MM-dd'))`tRETRIEVED_AT=$($retrieved.ToString('o'))`tSHA256=$hash`tPATH=$out")}
    else{Write-Output("PART_RACE_EXISTING`tINDEX=$ChunkIndex`tROWS=$($existing.Count)`tSHA256=$hash`tPATH=$out")}
}finally{
    if($workbook){try{$workbook.Worksheets.Item(1).Range('A3').ClearContents()|Out-Null}catch{};try{$workbook.Close($false)}catch{}}
    if($excel){try{$excel.Quit()}catch{};try{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}catch{}}
}
