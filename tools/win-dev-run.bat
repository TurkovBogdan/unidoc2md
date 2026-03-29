@echo off
REM Dev: APP_PROFILE=dev, rebuild locale, then main.py (console stays on errors)
setlocal EnableExtensions

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"
if errorlevel 1 (
    echo ERROR: cannot cd to project root:
    echo   "%ROOT_DIR%"
    pause
    exit /b 1
)

set "APP_PROFILE=dev"
call "%~dp0win-build-locale.bat" --no-pause
if errorlevel 1 (
    echo ERROR: locale build failed. See messages above.
    pause
    exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found in PATH. Install: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

echo Running (dev): "%ROOT_DIR%" APP_PROFILE=%APP_PROFILE%
uv run python main.py %*
if errorlevel 1 (
    echo Run failed.
    pause
    exit /b 1
)
endlocal
exit /b 0
