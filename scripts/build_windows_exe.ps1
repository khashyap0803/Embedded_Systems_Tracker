Param(
    [string]$OutputDir = "dist/windows"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

poetry run pyinstaller `
    --noconsole `
    --name EmbeddedTracker `
    --onefile `
    --collect-all embedded_tracker `
    main.py

Copy-Item -Path "dist/EmbeddedTracker.exe" -Destination (Join-Path $OutputDir "EmbeddedTracker.exe") -Force
Write-Host "Executable staged to $OutputDir/EmbeddedTracker.exe"
