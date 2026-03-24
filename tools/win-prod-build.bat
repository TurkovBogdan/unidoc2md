@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1
set APP_PROFILE=prod
call tools\win-build-locale.bat --no-pause
if errorlevel 1 exit /b 1

echo uv sync --extra build
uv sync --extra build
if errorlevel 1 (
    echo Sync failed
    pause
    exit /b 1
)

echo uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
uv run pyinstaller --clean --distpath dist/release --workpath dist/build urb-app.spec
if errorlevel 1 (
    echo Build failed
    pause
    exit /b 1
)

echo Build done: dist\release\
