@echo off
setlocal EnableExtensions
REM Install uv (Astral). Optional locale build if uv is on PATH after install.

for %%I in ("%~dp0..") do set "ROOT_DIR=%%~fI"

echo Installing uv (Astral)...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
if errorlevel 1 (
    echo Install failed.
    pause
    exit /b 1
)
echo.
echo Done. If uv is not found, restart the terminal or add to PATH:
echo   %USERPROFILE%\.local\bin
where uv >nul 2>&1
if errorlevel 1 (
    echo uv is not on PATH yet ^(open a new terminal^).
) else (
    uv --version
)

if exist "%ROOT_DIR%\build_locale.py" (
    cd /d "%ROOT_DIR%"
    if errorlevel 1 (
        echo ERROR: cannot cd to "%ROOT_DIR%"
        pause
        exit /b 1
    )
    where uv >nul 2>&1
    if errorlevel 1 (
        echo Skip locale build: uv not on PATH.
    ) else (
        call "%~dp0win-build-locale.bat" --no-pause
        if errorlevel 1 (
            echo Locale build failed.
            pause
            exit /b 1
        )
    )
)
pause
