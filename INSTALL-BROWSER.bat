@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 echo Run INSTALL-INFINITY.bat first.
 pause
 exit /b 1
)
.venv\Scripts\python.exe -m playwright install chromium
pause
