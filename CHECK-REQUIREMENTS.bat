@echo off
setlocal
cd /d "%~dp0"
title Infinity OS - Requirements Check

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

%PY% -c "import importlib.util; mods=['PySide6','psutil','pyautogui','pywinauto','pyperclip','playwright','qrcode','PIL','pypdf','docx','speech_recognition','pyttsx3','sounddevice','numpy','pytest']; missing=[m for m in mods if importlib.util.find_spec(m) is None]; print('All Infinity OS Python requirements are installed.' if not missing else 'Missing: ' + ', '.join(missing)); raise SystemExit(0 if not missing else 1)"
if errorlevel 1 (
  echo.
  echo Run RUN-INFINITY.bat to install or repair the missing requirements.
) else (
  echo.
  echo Python libraries look ready.
  echo Note: Browser Agent also needs Chromium; run INSTALL-BROWSER.bat once.
)
echo.
pause
