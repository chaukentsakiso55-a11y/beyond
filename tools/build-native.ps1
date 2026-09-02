$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Bin = Join-Path $Root "native\bin"
New-Item -ItemType Directory -Force -Path $Bin | Out-Null
if (Get-Command cargo -ErrorAction SilentlyContinue) {
  Push-Location (Join-Path $Root "native\rust")
  cargo build --release
  if (Test-Path "target\release\infinity_native.dll") { Copy-Item "target\release\infinity_native.dll" $Bin -Force }
  Pop-Location
} else { Write-Host "Rust unavailable; Python fallback remains active." }
if (Get-Command cmake -ErrorAction SilentlyContinue) {
  $Src = Join-Path $Root "native\cpp"; $Build = Join-Path $Src "build"
  cmake -S $Src -B $Build
  cmake --build $Build --config Release
  $Dll = Get-ChildItem $Build -Recurse -Filter "infinity_telemetry.dll" | Select-Object -First 1
  if ($Dll) { Copy-Item $Dll.FullName $Bin -Force }
} else { Write-Host "CMake unavailable; Python telemetry remains active." }
