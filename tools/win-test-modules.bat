@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1
call tools\win-build-locale.bat --no-pause
if errorlevel 1 exit /b 1

echo Running: uv run pytest tests/modules -v
uv run pytest tests/modules -v
if errorlevel 1 (
    echo Tests failed
    pause
    exit /b 1
)
echo Tests passed
pause
