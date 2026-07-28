@echo off
setlocal
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv. Create it and install requirements-release.txt first.
  exit /b 2
)
".venv\Scripts\python.exe" launch_alpha.py %*
