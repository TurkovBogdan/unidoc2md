@echo off
setlocal EnableExtensions
REM Production build: uv sync --extra build, then PyInstaller

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"
cd /d "%ROOT_DIR%"
if errorlevel 1 (
    echo ERROR: cannot cd to project root:
    echo   "%ROOT_DIR%"
    pause
    exit /b 1
)

set "APP_PROFILE=prod"
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

echo Running: uv sync --extra build
uv sync --extra build
if errorlevel 1 (
    echo Sync failed.
    pause
    exit /b 1
)

echo Running: uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

echo Build done: dist\release\
pause
