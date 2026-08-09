param(
    [Parameter(Mandatory=$true)][int]$ChunkIndex,
    [Parameter(Mandatory=$true)][string]$TransitionPlanPath,
    [Parameter(Mandatory=$true)][string]$OutDir,
    [int]$ChunkTransitions=40,
    [int]$BootSeconds=10
)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName office
if(-not ('CiqPitTransitionRcStub' -as [type])){$src=@'
using System; using Microsoft.Office.Core;
public sealed class CiqPitTransitionRcStub : IRibbonControl { public string Id{get;private set;} public string Tag{get;private set;} public object Context{get;private set;} public CiqPitTransitionRcStub(string id, object ctx){Id=id;Tag="";Context=ctx;} }
'@;Add-Type -TypeDefinition $src -ReferencedAssemblies ([Microsoft.Office.Core.IRibbonControl].Assembly.Location)}
function Csv([object]$value){$text=[string]$value;return '"'+($text-replace'"','""')+'"'}
function Missing([string]$text){return (!$text -or $text-eq'NA' -or $text-match'^#')}

$plan=@(Import-Csv -LiteralPath $TransitionPlanPath | Sort-Object source_entity_id,as_of_date)
if($plan.Count-eq0){throw 'pit_transition_plan_empty'}
$chunkCount=[int][Math]::Ceiling($plan.Count/[double]$ChunkTransitions)
if($ChunkIndex-lt0-or$ChunkIndex-ge$chunkCount){throw "chunk_index_invalid:$ChunkIndex/$chunkCount"}
$offset=$ChunkIndex*$ChunkTransitions;$take=[Math]::Min($ChunkTransitions,$plan.Count-$offset);$batch=@($plan[$offset..($offset+$take-1)])
[IO.Directory]::CreateDirectory($OutDir)|Out-Null
$out=Join-Path $OutDir ("transition_{0:D3}_{1}_{2}.csv" -f $ChunkIndex,$batch[0].as_of_date.Replace('-',''),$batch[-1].as_of_date.Replace('-',''))
if(Test-Path -LiteralPath $out){$existing=Import-Csv -LiteralPath $out;if($existing.Count-gt0){Write-Output("TRANSITION_EXISTS`tINDEX=$ChunkIndex`tROWS=$($existing.Count)`tPATH=$out");exit 0}else{throw "existing_transition_empty:$out"}}

$periods=@('FQ0','FQ-1','FQ-2','FQ-3','FQ-4')
$metrics=@('IQ_PERIOD_END','IQ_TOTAL_REV','IQ_TOTAL_ASSETS','IQ_INVENTORY','IQ_DA_SUPPL_CF','IQ_TOTAL_EQUITY','IQ_TOTAL_DEBT','IQ_CASH_ST_INVEST','IQ_OPER_INC','IQ_CAPEX_BNK')
$excel=$null;$wb=$null
try{
    $excel=New-Object -ComObject Excel.Application;$excel.Visible=$false;$excel.DisplayAlerts=$false
    foreach($key in @('MI Office Excel Functions','MI Office Excel Compatibility Add-in')){try{$addin=$excel.AddIns2.Item($key);$addin.Installed=$false;Start-Sleep -Milliseconds 300;$addin.Installed=$true}catch{}}
    Start-Sleep -Seconds $BootSeconds;$wb=$excel.Workbooks.Add();$ws=$wb.Worksheets.Item(1);$opts='Options:Curr=USD,Mag=Thousands,ConvMethod=R,FilingVer=Original'
    $row=1;$slots=New-Object System.Collections.Generic.List[object]
    foreach($item in $batch){$entity=[string]$item.source_entity_id;$date=[datetime]$item.as_of_date;$asof=$date.ToString('MM/dd/yyyy',[Globalization.CultureInfo]::InvariantCulture);foreach($period in $periods){$col=1;foreach($metric in $metrics){$formula="=SPG($entity,`"$metric`",`"$period`",`"$asof`",`"$opts`")";$ws.Cells.Item($row,$col).Formula=$formula;$col++};$slots.Add([pscustomobject]@{Row=$row;Date=$date;Entity=$entity;Period=$period});$row++}}
    $addinObject=$excel.COMAddIns.Item('SNL.Clients.Office.Excel.ExcelAddIn').Object;if(!$addinObject){throw'ciq_addin_object_missing'};$addinObject.OnRibbonAction2([CiqPitTransitionRcStub]::new('allowDataRefresh',$excel),$true);$addinObject.OnRibbonAction([CiqPitTransitionRcStub]::new('refreshDataAllSheets',$excel))
    $stable=0;for($poll=0;$poll-lt240;$poll++){Start-Sleep -Seconds 1;$pending=$false;foreach($slot in $slots){for($c=1;$c-le$metrics.Count;$c++){$text=[string]$ws.Cells.Item($slot.Row,$c).Text;if($text-eq'#PEND'-or$text-eq'#REFRESH'){$pending=$true;break}};if($pending){break}};if(!$pending){$stable++}else{$stable=0};if($stable-ge2){break}};if($stable-lt2){throw "pit_transition_timeout:$ChunkIndex"}
    $retrieved=[DateTime]::UtcNow;$headers=@('as_of_date','source_entity_id','relative_period','period_end')+$metrics[1..($metrics.Count-1)]+@('retrieved_at_utc','provider_function','filing_version');$lines=New-Object System.Collections.Generic.List[string];$lines.Add(($headers|ForEach-Object{Csv $_})-join',')
    foreach($slot in $slots){$periodCell=$ws.Cells.Item($slot.Row,1);$periodText=[string]$periodCell.Text;$periodEnd='';if(!(Missing $periodText)){try{$periodEnd=[datetime]::FromOADate([double]$periodCell.Value2).ToString('yyyy-MM-dd')}catch{$periodEnd=''}};$vals=New-Object System.Collections.Generic.List[object];$vals.Add($slot.Date.ToString('yyyy-MM-dd'));$vals.Add($slot.Entity);$vals.Add($slot.Period);$vals.Add($periodEnd);for($c=2;$c-le$metrics.Count;$c++){$cell=$ws.Cells.Item($slot.Row,$c);$text=[string]$cell.Text;if(Missing $text){$vals.Add('')}else{try{$vals.Add([string]::Format([Globalization.CultureInfo]::InvariantCulture,'{0:R}',[double]$cell.Value2))}catch{$vals.Add('')}}};$vals.Add($retrieved.ToString('o'));$vals.Add('SPG');$vals.Add('Original');$lines.Add(($vals|ForEach-Object{Csv $_})-join',')}
    $tmp=$out+'.'+[Guid]::NewGuid().ToString('N')+'.tmp';[IO.File]::WriteAllLines($tmp,$lines,[Text.UTF8Encoding]::new($false));[IO.File]::Move($tmp,$out);$hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $out).Hash.ToLowerInvariant();Write-Output("TRANSITION_OK`tINDEX=$ChunkIndex`tTRANSITIONS=$($batch.Count)`tROWS=$($slots.Count)`tRETRIEVED_AT=$($retrieved.ToString('o'))`tSHA256=$hash`tPATH=$out")
}finally{if($wb){try{$wb.Close($false)}catch{}};if($excel){try{$excel.Quit()}catch{};try{[void][Runtime.InteropServices.Marshal]::ReleaseComObject($excel)}catch{}}}
