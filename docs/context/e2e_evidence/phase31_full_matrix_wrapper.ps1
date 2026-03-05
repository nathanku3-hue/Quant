$ErrorActionPreference = 'Stop'
Set-Location 'E:\code\quant'

$logPath = 'E:\code\quant\docs\context\e2e_evidence\phase31_full_matrix_final.log'
$statusPath = 'E:\code\quant\docs\context\e2e_evidence\phase31_full_matrix_final.status'
$stdoutPath = 'E:\code\quant\docs\context\e2e_evidence\phase31_full_matrix_final.stdout.tmp'
$stderrPath = 'E:\code\quant\docs\context\e2e_evidence\phase31_full_matrix_final.stderr.tmp'
$baseTemp = 'E:\code\quant\.pytest_tmp_scheduler'

if (Test-Path $statusPath) { Remove-Item -Force $statusPath }
if (Test-Path $stdoutPath) { Remove-Item -Force $stdoutPath }
if (Test-Path $stderrPath) { Remove-Item -Force $stderrPath }

"[phase31_full_matrix] start $(Get-Date -Format o)" | Set-Content -Path $logPath -Encoding ASCII

$exitCode = 1
try {
    $proc = Start-Process `
        -FilePath 'E:\code\quant\.venv\Scripts\python.exe' `
        -ArgumentList "-m pytest --basetemp `"$baseTemp`"" `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru `
        -Wait `
        -NoNewWindow
    $exitCode = $proc.ExitCode
}
catch {
    $exitCode = 1
    "[wrapper_exception] $($_.Exception.ToString())" | Add-Content -Path $stderrPath -Encoding ASCII
}

if (Test-Path $stdoutPath) { Get-Content $stdoutPath | Add-Content -Path $logPath -Encoding ASCII }
if (Test-Path $stderrPath) { Get-Content $stderrPath | Add-Content -Path $logPath -Encoding ASCII }
"[phase31_full_matrix] end exit_code=$exitCode $(Get-Date -Format o)" | Add-Content -Path $logPath -Encoding ASCII
Set-Content -Path $statusPath -Value $exitCode -Encoding ASCII

exit $exitCode
