@echo off
setlocal ENABLEEXTENSIONS
cd /d E:\code\quant || exit /b 9009

set "LOG=E:\code\quant\docs\context\e2e_evidence\phase31_full_matrix_final.log"
set "STATUS=E:\code\quant\docs\context\e2e_evidence\phase31_full_matrix_final.status"

set "START_TS=%DATE% %TIME%"
> "%LOG%" echo [phase31_full_matrix] start %START_TS%
if exist "%STATUS%" del /f /q "%STATUS%" >nul 2>&1

call .venv\Scripts\python -m pytest >> "%LOG%" 2>&1
set "EC=%ERRORLEVEL%"

>> "%LOG%" echo [phase31_full_matrix] end exit_code=%EC% %DATE% %TIME%
> "%STATUS%" echo %EC%

exit /b %EC%
