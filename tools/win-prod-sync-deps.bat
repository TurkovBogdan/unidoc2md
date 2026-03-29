@echo off
setlocal EnableExtensions
REM Sync production dependencies (uv sync)

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

echo Running: uv sync
uv sync
if errorlevel 1 (
    echo uv sync failed.
    pause
    exit /b 1
)

echo Done.
pause
