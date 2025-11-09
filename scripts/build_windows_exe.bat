@echo off
setlocal enabledelayedexpansion

set "OUTPUT_ROOT=%~1"
if "%OUTPUT_ROOT%"=="" set "OUTPUT_ROOT=dist\windows"
set "APP_ID=embedded-tracker"

for /f "usebackq tokens=1" %%i in (`poetry version -s`) do set "VERSION=%%i"

if not exist "%OUTPUT_ROOT%" mkdir "%OUTPUT_ROOT%"

poetry run pyinstaller ^
  --noconsole ^
  --name "%APP_ID%" ^
  --onefile ^
  --collect-all embedded_tracker ^
  --add-data "embedded_tracker.db;." ^
  main.py

if errorlevel 1 goto :error

if not exist "%OUTPUT_ROOT%" mkdir "%OUTPUT_ROOT%"
copy /Y "dist\%APP_ID%.exe" "%OUTPUT_ROOT%\%APP_ID%_%VERSION%.exe" >nul

echo.
echo Created Windows build at %OUTPUT_ROOT%\%APP_ID%_%VERSION%.exe
goto :eof

:error
echo Build failed.
exit /b 1
