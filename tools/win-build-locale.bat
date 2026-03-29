@echo off
REM Merge locale/*.json -> assets/locale/<code>.json (build_locale.py)
setlocal EnableExtensions EnableDelayedExpansion

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"
if errorlevel 1 (
    echo ERROR: cannot cd to project root:
    echo   "%ROOT_DIR%"
    pause
    exit /b 1
)

where uv >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv not found in PATH. Install: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

set "PY_ARGS="
set "NO_PAUSE=0"
if /i "%~1"=="--no-pause" set NO_PAUSE=1
if /i "%~1"=="--no-pause" shift

:addargs
if "%~1"=="" goto addargs_done
set "PY_ARGS=!PY_ARGS! %~1"
shift
goto addargs

:addargs_done
echo Running: uv run python build_locale.py!PY_ARGS!
uv run python build_locale.py!PY_ARGS!
if errorlevel 1 (
    echo Locale build failed (build_locale.py^)
    if !NO_PAUSE! equ 0 pause
    exit /b 1
)

echo Locale build done
if !NO_PAUSE! equ 0 pause
exit /b 0
