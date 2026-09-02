@echo off
cd /d "%~dp0"
call "%~dp0RUN-INFINITY.bat"
exit /b %errorlevel%
