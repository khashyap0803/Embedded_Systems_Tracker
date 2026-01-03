@echo off
setlocal enabledelayedexpansion

REM Windows build script for Embedded Tracker
REM Creates: dist\windows\embedded-tracker_VERSION.exe

set "OUTPUT_ROOT=%~1"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=dist\windows"
set "APP_ID=embedded-tracker"

REM Get version from pyproject.toml
for /f "usebackq tokens=1" %%i in (`poetry version -s`) do set "VERSION=%%i"

echo Building Embedded Tracker v%VERSION% for Windows...
echo.

if not exist "%OUTPUT_ROOT%" mkdir "%OUTPUT_ROOT%"

REM Build with PyInstaller
poetry run pyinstaller ^
  --noconsole ^
  --name "%APP_ID%" ^
  --onefile ^
  --collect-all embedded_tracker ^
  main.py

if errorlevel 1 goto :error

REM Copy to output folder with version in filename
copy /Y "dist\%APP_ID%.exe" "%OUTPUT_ROOT%\%APP_ID%_%VERSION%.exe" >nul

echo.
echo ============================================
echo Build successful!
echo Created: %OUTPUT_ROOT%\%APP_ID%_%VERSION%.exe
echo ============================================
goto :eof

:error
echo.
echo ============================================
echo Build failed! Check errors above.
echo ============================================
exit /b 1
