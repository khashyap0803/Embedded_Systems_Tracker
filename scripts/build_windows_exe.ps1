# Windows PowerShell build script for Embedded Tracker
# Creates: dist\windows\embedded-tracker_VERSION.exe

Param(
    [string]$OutputDir = "dist\windows"
)

$ErrorActionPreference = "Stop"

# Get version from pyproject.toml
$Version = (poetry version -s).Trim()
$AppId = "embedded-tracker"

Write-Host "Building Embedded Tracker v$Version for Windows..."
Write-Host ""

# Create output directory if needed
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

try {
    # Build with PyInstaller
    poetry run pyinstaller `
        --noconsole `
        --name $AppId `
        --onefile `
        --collect-all embedded_tracker `
        main.py

    # Copy to output folder with version in filename
    $OutputPath = Join-Path $OutputDir "$AppId`_$Version.exe"
    Copy-Item -Path "dist\$AppId.exe" -Destination $OutputPath -Force

    Write-Host ""
    Write-Host "============================================"
    Write-Host "Build successful!"
    Write-Host "Created: $OutputPath"
    Write-Host "============================================"
}
catch {
    Write-Host ""
    Write-Host "============================================"
    Write-Host "Build failed! Error: $_"
    Write-Host "============================================"
    exit 1
}
