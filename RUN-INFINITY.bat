@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title Infinity OS V7 REBORN - Setup and Launch

if not exist "data\logs" mkdir "data\logs" >nul 2>&1
set "LOG=%~dp0data\logs\launcher.log"
>"%LOG%" echo [%date% %time%] Infinity OS launcher started

echo ============================================
echo        INFINITY OS V7 REBORN
echo          INSTALL + OPEN
echo ============================================
echo.
echo This launcher will prepare Infinity once, create the Desktop icon,
echo and then run main.py automatically.
echo.

rem ------------------------------------------------------------
rem Find a real Python installation. Prefer the normal python command
rem because this matches the command the user can run manually.
rem ------------------------------------------------------------
set "PY_CMD="
python -c "import sys; print(sys.executable)" >nul 2>&1
if not errorlevel 1 set "PY_CMD=python"

if not defined PY_CMD (
    py -3 -c "import sys; print(sys.executable)" >nul 2>&1
    if not errorlevel 1 set "PY_CMD=py -3"
)

if not defined PY_CMD goto :no_python

echo [1/5] Python found: %PY_CMD%
echo Python command: %PY_CMD%>>"%LOG%"

rem ------------------------------------------------------------
rem Create or repair the private environment used by Infinity.
rem ------------------------------------------------------------
set "VENV_PY=.venv\Scripts\python.exe"
set "VENV_PYW=.venv\Scripts\pythonw.exe"

if exist "%VENV_PY%" (
    "%VENV_PY%" -c "import sys" >nul 2>&1
    if errorlevel 1 (
        echo [2/5] Existing environment is damaged. Rebuilding it...
        echo Existing venv failed validation. Rebuilding.>>"%LOG%"
        rmdir /s /q ".venv" >>"%LOG%" 2>&1
    ) else (
        echo [2/5] Infinity Python environment is ready.
    )
)

if not exist "%VENV_PY%" (
    echo [2/5] Creating Infinity Python environment...
    %PY_CMD% -m venv ".venv" >>"%LOG%" 2>&1
    if errorlevel 1 goto :venv_fail
)

rem ------------------------------------------------------------
rem Make sure pip exists, then install only the packages required for
rem the desktop app. The Python Playwright package is included; its Chromium
rem runtime is downloaded separately by INSTALL-BROWSER.bat.
rem ------------------------------------------------------------
echo [3/5] Checking Infinity dependencies...
"%VENV_PY%" -m pip --version >nul 2>&1
if errorlevel 1 (
    "%VENV_PY%" -m ensurepip --upgrade >>"%LOG%" 2>&1
    if errorlevel 1 goto :pip_fail
)

"%VENV_PY%" -c "import PySide6, psutil" >nul 2>&1
if errorlevel 1 (
    echo       Installing the Infinity desktop UI...
    "%VENV_PY%" -m pip install --disable-pip-version-check -r "requirements-core.txt" >>"%LOG%" 2>&1
    if errorlevel 1 goto :install_fail
) else (
    echo       Infinity desktop UI is already installed.
)

"%VENV_PY%" -c "import PySide6, psutil" >nul 2>&1
if errorlevel 1 goto :install_fail

rem Optional feature packages should never stop Infinity from opening.
"%VENV_PY%" -c "import psutil, pyautogui, pyperclip, qrcode, PIL, pypdf, docx, speech_recognition, pyttsx3, sounddevice, numpy, playwright; import pywinauto" >nul 2>&1
if errorlevel 1 (
    echo       Installing automation, clipboard, browser, QR, document and voice features...
    "%VENV_PY%" -m pip install --disable-pip-version-check -r "requirements-extras.txt" >>"%LOG%" 2>&1
    if errorlevel 1 (
        echo       WARNING: Some optional features could not be installed.
        echo       Infinity will still open; details are in data\logs\launcher.log.
        echo Optional extras install returned an error. Continuing.>>"%LOG%"
    )
) else (
    echo       Optional Infinity features are already installed.
)

rem ------------------------------------------------------------
rem Create a real Windows .lnk with the Infinity icon.
rem ------------------------------------------------------------
echo [4/5] Creating Desktop shortcut...
call "%~dp0CREATE-DESKTOP-SHORTCUT.bat" /quiet >>"%LOG%" 2>&1
if errorlevel 1 (
    echo       Shortcut creation failed, but Infinity can still run.
    echo       You can retry CREATE-DESKTOP-SHORTCUT.bat later.
) else (
    echo       Desktop shortcut ready: Infinity OS V7 REBORN
)

rem ------------------------------------------------------------
rem Launch exactly as requested: Python runs main.py from the project root.
rem Keep this window available so a startup error is visible instead of
rem disappearing instantly.
rem ------------------------------------------------------------
echo [5/5] Opening Infinity OS...
echo.
echo Command: .venv\Scripts\python.exe main.py
echo.
echo [%date% %time%] Launching main.py>>"%LOG%"
"%VENV_PY%" "main.py"
set "APP_EXIT=!errorlevel!"

echo [%date% %time%] main.py exit code !APP_EXIT!>>"%LOG%"
if not "!APP_EXIT!"=="0" (
    echo.
    echo ============================================
    echo       INFINITY DID NOT START CORRECTLY
    echo ============================================
    echo.
    echo The error should be visible above.
    echo Launcher log:
    echo   %LOG%
    echo.
    pause
)
exit /b !APP_EXIT!

:no_python
echo.
echo ============================================
echo              PYTHON NOT FOUND
echo ============================================
echo.
echo Infinity needs Python 3.11 or newer.
echo Install Python and make sure "python" or "py" works in Command Prompt.
echo Then double-click RUN-INFINITY.bat again.
echo.
echo A useful test is:
echo     python --version
echo.
pause
exit /b 10

:venv_fail
echo.
echo Failed to create .venv.
echo Open this log and send me the final lines:
echo   %LOG%
echo.
echo You can also test Infinity manually from this folder with:
echo   python main.py
echo.
pause
exit /b 11

:pip_fail
echo.
echo Python was found, but pip could not be prepared.
echo See:
echo   %LOG%
echo.
pause
exit /b 12

:install_fail
echo.
echo ============================================
echo        DEPENDENCY INSTALLATION FAILED
echo ============================================
echo.
echo Infinity was not opened because a required package failed to install.
echo Open this file and send me its final lines:
echo   %LOG%
echo.
echo If PySide6 is already installed globally, you can also try:
echo   python main.py
echo.
pause
exit /b 13
