@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File tools\build-native.ps1
pause
