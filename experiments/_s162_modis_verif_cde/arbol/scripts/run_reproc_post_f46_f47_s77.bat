@echo off
REM S77 reproc historico 11 Tier A post-F46+F47 (PRs #175 + #177).
REM Wrapper Windows nativo sobre run_reproc_post_f46_f47_s77.py.
REM
REM Uso:
REM   scripts\run_reproc_post_f46_f47_s77.bat --dry-run       rem ver comandos
REM   scripts\run_reproc_post_f46_f47_s77.bat --days 14       rem ventana corta
REM   scripts\run_reproc_post_f46_f47_s77.bat                 rem 30d default
REM   scripts\run_reproc_post_f46_f47_s77.bat --days 90       rem full historico
REM
REM CAVEAT: sobreescribe data\mirova_equivalent\*.json. Hacer backup:
REM   robocopy data\mirova_equivalent data\mirova_equivalent.pre_s77 /E
REM
REM Sin Unicode (cp1252 default de cmd no soporta tildes/sigma).
REM Refs: scripts\run_reproc_post_f46_f47_s77.py

setlocal
cd /d "%~dp0\.."
python scripts\run_reproc_post_f46_f47_s77.py %*
endlocal
