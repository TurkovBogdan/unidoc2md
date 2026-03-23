@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1

echo Running: uv run pytest -v
uv run pytest -v
if errorlevel 1 (
    echo Tests failed
    pause
    exit /b 1
)
echo Tests passed
pause
