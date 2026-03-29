@echo off
setlocal EnableExtensions
REM Sync dev dependencies (uv sync --extra dev)

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"
if errorlevel 1 (
    echo ERROR: cannot cd to project root:
    echo   "%ROOT_DIR%"
    pause
    exit /b 1
)

call "%~dp0win-build-locale.bat" --no-pause
if errorlevel 1 (
    echo ERROR: locale build failed.
    pause
    exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found in PATH.
    pause
    exit /b 1
)

echo Running: uv sync --extra dev
uv sync --extra dev
if errorlevel 1 (
    echo uv sync --extra dev failed.
    pause
    exit /b 1
)

echo Done.
pause
