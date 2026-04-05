@echo off
setlocal enabledelayedexpansion
title VRP Chile - Monitor de Calibracion

set CONDA_ENV=C:\Users\nmend\miniconda3\envs\vrp
set DATA=C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\PuyehueCordonCaulle.json

:loop
cls
echo ============================================================
echo    VRP Chile - Estado de Calibracion
echo    %date% %time%
echo ============================================================
echo.

REM Contar registros en JSON
"%CONDA_ENV%\python.exe" -c "import json; d=json.load(open(r'%DATA%')); recs=d['records']; vrp=[r for r in recs if r.get('vrp_mw',0)>0 or r.get('vrp_mir_mw',0)>0]; dates=sorted(set(r['datetime_utc'][:10] for r in recs)); print(f'  Total registros:  {len(recs)}'); print(f'  Detecciones VRP>0: {len(vrp)}'); print(f'  Rango fechas:     {dates[0]} a {dates[-1]}'); print(f'  Dias cubiertos:   {len(dates)}'); print(); from collections import Counter; sc=Counter(r.get('sensor','?') for r in recs); [print(f'    {s}: {c}') for s,c in sc.most_common()]; print(); print('  Ultimos 5 registros:'); [print(f'    {r[\"datetime_utc\"]} | {r.get(\"sensor\",\"?\"):20s} | VRP={r.get(\"vrp_mw\",0) or r.get(\"vrp_mir_mw\",0):.3f} MW') for r in recs[-5:]]"

echo.
echo ============================================================
echo    Presiona Ctrl+C para salir. Actualizando en 30 seg...
echo ============================================================

timeout /t 30 /nobreak >nul
goto loop
