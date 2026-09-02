@echo off
setlocal
cd /d "%~dp0"
set "QUIET=0"
if /I "%~1"=="/quiet" set "QUIET=1"

where cscript.exe >nul 2>&1
if not errorlevel 1 (
    cscript.exe //nologo "%~dp0CREATE-DESKTOP-SHORTCUT.vbs"
    set "RC=%errorlevel%"
) else (
    set "RC=1"
)

if "%RC%"=="0" goto :done

rem Fallback to PowerShell if Windows Script Host is unavailable.
where powershell.exe >nul 2>&1
if errorlevel 1 goto :fail
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0CREATE-DESKTOP-SHORTCUT.ps1"
if errorlevel 1 goto :fail
set "RC=0"

goto :done

:fail
if "%QUIET%"=="0" (
    echo.
    echo Could not create the Desktop shortcut.
    echo Infinity can still be opened with RUN-INFINITY.bat.
    pause
)
exit /b 1

:done
if "%QUIET%"=="0" (
    echo.
    echo Infinity OS V7 REBORN is now on your Desktop.
    echo If Windows still shows an old icon, right-click the Desktop and choose Refresh.
    echo.
    pause
)
exit /b 0
