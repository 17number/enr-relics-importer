@echo off
setlocal enabledelayedexpansion
echo === ELDEN RING NIGHTREIGN Relics Analyzer ===

cd /d "%~dp0"

echo Building Docker image...
docker build -t enr-relics-importer .

rem Convert current dir to Linux path
for /f "delims=" %%i in ('powershell -NoProfile -Command "(Get-Location).Path.ToLower()"') do set "PWD_LINUX=%%i"

echo Running analysis...
docker run --rm ^
  -v "!PWD_LINUX!/labeled_chars:/app/labeled_chars" ^
  -v "!PWD_LINUX!/relics.mp4:/app/relics.mp4" ^
  -v "!PWD_LINUX!/output:/app/output" ^
  enr-relics-importer

echo Done!
pause
