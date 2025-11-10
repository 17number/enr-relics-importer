@echo off
setlocal enabledelayedexpansion
echo === ELDEN RING NIGHTREIGN Relics Analyzer ===
echo Building Docker image...
docker build -t enr-relics-importer .

for /f "delims=" %%i in ('wsl wslpath "%cd%"') do set "PWD_LINUX=%%i"

echo Running analysis...
docker run --rm ^
  -v "!PWD_LINUX!/labeled_chars:/app/labeled_chars" ^
  -v "!PWD_LINUX!/relics.mp4:/app/relics.mp4" ^
  -v "!PWD_LINUX!/output:/app/output" ^
  enr-relics-importer

echo Done!
pause
