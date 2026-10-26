@echo off
REM ============================================================
REM VRP Chile NRT local cron — S72
REM ============================================================
REM Corre VIIRS pipeline localmente (Chile IP, NASA <1s).
REM Workaround para throttling NASA-Azure que afecta GH Actions.
REM
REM Setup Task Scheduler:
REM   schtasks /Create /TN "VRP_Chile_NRT" /TR "C:\path\to\nrt_local.bat" ^
REM           /SC HOURLY /MO 2 /F
REM
REM Pre-requisitos:
REM   1. .env con EARTHDATA_TOKEN (ver docs/LOCAL_NRT_SETUP.md)
REM   2. python conda env activado para VRP Chile
REM   3. git configurado con credenciales push al repo
REM
REM Limitaciones:
REM   - Solo VIIRS (pyhdf broken Windows → MODIS skip).
REM   - PC debe estar ON cuando dispara cron.
REM ============================================================

setlocal

REM Ir al repo root (ajustar path si necesario)
cd /d "%~dp0\.."

REM Timestamp para logs
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set ts=%%a
set ts=%ts:~0,8%_%ts:~8,6%

REM Log path
set LOGDIR=logs\nrt_local
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
set LOG=%LOGDIR%\%ts%.log

echo === VRP Chile NRT local cron === > "%LOG%"
echo Started: %ts% >> "%LOG%"

REM Pull last main (evitar conflicts con GH Actions cron paralelo)
echo. >> "%LOG%"
echo --- git pull --- >> "%LOG%"
git fetch origin main >> "%LOG%" 2>&1
git pull --rebase origin main >> "%LOG%" 2>&1

REM Correr NRT pipeline — todos los Tier A
echo. >> "%LOG%"
echo --- pipeline run --- >> "%LOG%"
python scripts/run_pipeline.py --profile mirova_equivalent >> "%LOG%" 2>&1
set EXITCODE=%ERRORLEVEL%

if %EXITCODE% NEQ 0 (
    echo ERROR: pipeline exit code %EXITCODE% >> "%LOG%"
    exit /b %EXITCODE%
)

REM Push solo si hay cambios
echo. >> "%LOG%"
echo --- git push --- >> "%LOG%"
git add data/mirova_equivalent/ >> "%LOG%" 2>&1
git diff --staged --quiet
if %ERRORLEVEL% EQU 0 (
    echo No changes to commit >> "%LOG%"
    exit /b 0
)

git commit -m "NRT local update %ts%" >> "%LOG%" 2>&1

REM Retry push hasta 3 veces (race condition con GH Actions cron)
set ATTEMPTS=0
:RETRY_PUSH
set /a ATTEMPTS+=1
git pull --rebase -X theirs origin main >> "%LOG%" 2>&1
git push origin main >> "%LOG%" 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Push success on attempt %ATTEMPTS% >> "%LOG%"
    exit /b 0
)
if %ATTEMPTS% LSS 3 (
    echo Push attempt %ATTEMPTS% failed, retrying... >> "%LOG%"
    timeout /t 10 /nobreak > nul
    goto RETRY_PUSH
)

echo ERROR: push failed after %ATTEMPTS% attempts >> "%LOG%"
exit /b 1
