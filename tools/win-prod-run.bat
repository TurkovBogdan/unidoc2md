@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1
set APP_PROFILE=prod

echo Running (prod): runtime\prod
uv run python main.py %*
if errorlevel 1 (
    echo Run failed
    pause
    exit /b 1
)
