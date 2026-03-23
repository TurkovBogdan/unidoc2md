@echo off
setlocal
set "ROOT_DIR=%~dp0.."
cd /d "%ROOT_DIR%" || exit /b 1
set APP_PROFILE=dev

REM python (не pythonw) — консоль видима, закрывается при выходе из приложения
echo Running (dev): runtime\dev
uv run python main.py %*
if errorlevel 1 (
    echo Run failed
    pause
    exit /b 1
)
