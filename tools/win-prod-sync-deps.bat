@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1

echo Running: uv sync
uv sync
if errorlevel 1 (
    echo uv sync failed
    pause
    exit /b 1
)

echo Done
pause
