@echo off
setlocal
echo Installing uv (Astral)...
echo.
powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
if errorlevel 1 (
    echo Install failed
    pause
    exit /b 1
)
echo.
echo Done. Restart the terminal or add %%USERPROFILE%%\.local\bin to PATH if uv is not found.
uv --version 2>nul && echo uv is available.
if exist "%~dp0..\locale.py" (
    cd /d "%~dp0.." || exit /b 1
    call tools\win-build-locale.bat --no-pause
)
pause
