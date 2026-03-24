@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1

echo Running: uv run python locale.py
uv run python locale.py
if errorlevel 1 (
    echo Locale build failed
    if /i not "%~1"=="--no-pause" pause
    exit /b 1
)

echo Locale build done
if /i not "%~1"=="--no-pause" pause
