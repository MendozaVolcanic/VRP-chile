@echo off
REM F31 A5 piloto S76 - reproc local 3 volcanes con perfil experimental_lowT.
REM Wrapper Windows nativo sobre run_pilot_a5_s76.py.
REM
REM Uso:
REM   scripts\run_pilot_a5_s76.bat             rem 30 dias, 3 volcanes
REM   scripts\run_pilot_a5_s76.bat --dry-run   rem ver comandos sin ejecutar
REM   scripts\run_pilot_a5_s76.bat --days 14   rem ventana corta de prueba
REM
REM Sin Unicode (cp1252 default de cmd no soporta tildes/sigma).
REM Refs: scripts\run_pilot_a5_s76.py
REM       docs\F31_AVENI_VRPTIR_PLAN_S74.md
REM       docs\F31_AGUILERA_2021_PETEROA.md

setlocal
cd /d "%~dp0\.."
python scripts\run_pilot_a5_s76.py %*
endlocal
