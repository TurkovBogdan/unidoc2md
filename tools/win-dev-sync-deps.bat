@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1
call tools\win-build-locale.bat --no-pause
if errorlevel 1 exit /b 1

echo Running: uv sync --extra dev
uv sync --extra dev
if errorlevel 1 (
    echo uv sync --extra dev failed
    pause
    exit /b 1
)

echo Done
pause
