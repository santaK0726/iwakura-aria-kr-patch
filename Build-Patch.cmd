@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build-Patch.ps1"
if errorlevel 1 echo Patch build failed. See the error above.
pause
