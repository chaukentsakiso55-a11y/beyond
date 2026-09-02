$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Main = Join-Path $Root 'main.py'
$Pythonw = Join-Path $Root '.venv\Scripts\pythonw.exe'
$Python = Join-Path $Root '.venv\Scripts\python.exe'
$Launcher = Join-Path $Root 'RUN-INFINITY.bat'
$Icon = Join-Path $Root 'assets\infinity.ico'

$Shell = New-Object -ComObject WScript.Shell
$Desktop = $Shell.SpecialFolders.Item('Desktop')
if ([string]::IsNullOrWhiteSpace($Desktop)) { $Desktop = [Environment]::GetFolderPath('Desktop') }
$ShortcutPath = Join-Path $Desktop 'Infinity OS V7 REBORN.lnk'

if (-not (Test-Path $Main)) { throw "Infinity main.py was not found: $Main" }
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
if (Test-Path $Pythonw) {
    $Shortcut.TargetPath = $Pythonw
    $Shortcut.Arguments = '"' + $Main + '"'
} elseif (Test-Path $Python) {
    $Shortcut.TargetPath = $Python
    $Shortcut.Arguments = '"' + $Main + '"'
} else {
    $Shortcut.TargetPath = $Launcher
}
$Shortcut.WorkingDirectory = $Root
$Shortcut.Description = 'Infinity OS V7 REBORN — Ultimate'
if (Test-Path $Icon) { $Shortcut.IconLocation = "$Icon,0" }
$Shortcut.Save()
if (-not (Test-Path $ShortcutPath)) { throw 'Windows did not create the Desktop shortcut.' }
Write-Host "Desktop shortcut created: $ShortcutPath"
