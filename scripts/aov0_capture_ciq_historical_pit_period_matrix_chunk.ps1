param(
    [Parameter(Mandatory=$true)][int]$ChunkIndex,
    [Parameter(Mandatory=$true)][string]$PlanPath,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [Parameter(Mandatory=$true)][string]$Master,
    [int]$ChunkDates=20,
    [int]$BootSeconds=10
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName office
if(-not ('CiqPitPeriodRcStub' -as [type])){$src=@'
using System; using Microsoft.Office.Core;
public sealed class CiqPitPeriodRcStub : IRibbonControl { public string Id{get;private set;} public string Tag{get;private set;} public object Context{get;private set;} public CiqPitPeriodRcStub(string id, object ctx){Id=id;Tag="";Context=ctx;} }
'@;Add-Type -TypeDefinition $src -ReferencedAssemblies ([Microsoft.Office.Core.IRibbonControl].Assembly.Location)}
function Csv([object]$value){$text=[string]$value;return '"'+($text-replace'"','""')+'"'}
function Missing([string]$text){return (!$text -or $text-eq'NA' -or $text-match'^#')}

if(-not (Test-Path -LiteralPath $Master)){throw "historical_period_master_missing:$Master"}
$masterRows=@(Import-Csv -LiteralPath $Master)
if($masterRows.Count-lt1){throw 'historical_period_master_empty'}
if(@($masterRows.SP_ENTITY_ID|ForEach-Object{[string]$_}|Where-Object{$_}|Sort-Object -Unique).Count-ne$masterRows.Count){throw 'historical_period_master_entity_id_invalid_or_duplicate'}
$plan=@(Import-Csv -LiteralPath $PlanPath | ForEach-Object {[datetime]$_.as_of_date} | Sort-Object -Unique)
if($plan.Count-eq0){throw 'pit_period_plan_empty'}
$chunkCount=[int][Math]::Ceiling($plan.Count/[double]$ChunkDates)
if($ChunkIndex-lt0-or$ChunkIndex-ge$chunkCount){throw "chunk_index_invalid:$ChunkIndex/$chunkCount"}
$offset=$ChunkIndex*$ChunkDates;$take=[Math]::Min($ChunkDates,$plan.Count-$offset);$dates=@($plan[$offset..($offset+$take-1)])
[IO.Directory]::CreateDirectory($OutDir)|Out-Null
$out=Join-Path $OutDir ("period_{0:D3}_{1}_{2}.csv" -f $ChunkIndex,$dates[0].ToString('yyyyMMdd'),$dates[-1].ToString('yyyyMMdd'))
if(Test-Path -LiteralPath $out){$existing=Import-Csv -LiteralPath $out;if($existing.Count-gt0){Write-Output("PERIOD_EXISTS`tINDEX=$ChunkIndex`tROWS=$($existing.Count)`tPATH=$out");exit 0}else{throw "existing_period_empty:$out"}}

$excel=$null;$wb=$null
try{
    $excel=New-Object -ComObject Excel.Application;$excel.Visible=$false;$excel.DisplayAlerts=$false
    foreach($key in @('MI Office Excel Functions','MI Office Excel Compatibility Add-in')){try{$addin=$excel.AddIns2.Item($key);$addin.Installed=$false;Start-Sleep -Milliseconds 300;$addin.Installed=$true}catch{}}
    Start-Sleep -Seconds $BootSeconds;$wb=$excel.Workbooks.Add();$ws=$wb.Worksheets.Item(1)
    $opts='Options:Curr=USD,Mag=Thousands,ConvMethod=R,FilingVer=Original'
    $row=1;$slots=New-Object System.Collections.Generic.List[object]
    foreach($date in $dates){$asof=$date.ToString('MM/dd/yyyy',[Globalization.CultureInfo]::InvariantCulture);foreach($m in $masterRows){$formula="=SPG($($m.SP_ENTITY_ID),`"IQ_PERIOD_END`",`"FQ0`",`"$asof`",`"$opts`")";$ws.Cells.Item($row,1).Formula=$formula;$slots.Add([pscustomobject]@{Row=$row;Date=$date;Entity=[string]$m.SP_ENTITY_ID});$row++}}
    $addinObject=$null
    for($attempt=0;$attempt-lt3-and-not$addinObject;$attempt++){
        try{$addinObject=$excel.COMAddIns.Item('SNL.Clients.Office.Excel.ExcelAddIn').Object}catch{}
        if(!$addinObject){Start-Sleep -Seconds 2}
    }
    if(!$addinObject){throw 'ciq_addin_object_missing'}
    $addinObject.OnRibbonAction2([CiqPitPeriodRcStub]::new('allowDataRefresh',$excel),$true);$addinObject.OnRibbonAction([CiqPitPeriodRcStub]::new('refreshDataAllSheets',$excel))
    $stable=0;for($poll=0;$poll-lt180;$poll++){Start-Sleep -Seconds 1;$pending=$false;foreach($slot in $slots){$text=[string]$ws.Cells.Item($slot.Row,1).Text;if($text-eq'#PEND'-or$text-eq'#REFRESH'){$pending=$true;break}};if(!$pending){$stable++}else{$stable=0};if($stable-ge2){break}};if($stable-lt2){throw "pit_period_timeout:$ChunkIndex"}
    $retrieved=[DateTime]::UtcNow;$lines=New-Object System.Collections.Generic.List[string];$headers=@('as_of_date','source_entity_id','fq0_period_end','retrieved_at_utc','provider_function','provider_metric','relative_period','filing_version');$lines.Add(($headers|ForEach-Object{Csv $_})-join',')
    foreach($slot in $slots){$cell=$ws.Cells.Item($slot.Row,1);$text=[string]$cell.Text;$period='';if(!(Missing $text)){try{$period=[datetime]::FromOADate([double]$cell.Value2).ToString('yyyy-MM-dd')}catch{$period=''}};$vals=@($slot.Date.ToString('yyyy-MM-dd'),$slot.Entity,$period,$retrieved.ToString('o'),'SPG','IQ_PERIOD_END','FQ0','Original');$lines.Add(($vals|ForEach-Object{Csv $_})-join',')}
    $tmp=$out+'.'+[Guid]::NewGuid().ToString('N')+'.tmp';[IO.File]::WriteAllLines($tmp,$lines,[Text.UTF8Encoding]::new($false));[IO.File]::Move($tmp,$out);$hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash.ToLowerInvariant();Write-Output("PERIOD_OK`tINDEX=$ChunkIndex`tDATES=$($dates.Count)`tROWS=$($slots.Count)`tRETRIEVED_AT=$($retrieved.ToString('o'))`tSHA256=$hash`tPATH=$out")
}finally{if($wb){try{$wb.Close($false)}catch{}};if($excel){try{$excel.Quit()}catch{};try{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}catch{}}}
