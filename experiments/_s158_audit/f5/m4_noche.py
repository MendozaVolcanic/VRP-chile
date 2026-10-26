# -*- coding: utf-8 -*-
"""F5 medicion 4. Dos definiciones de 'nocturna' en los instrumentos:
  (i) banco_paridad / auto-audit / evaluadores: elevacion solar <= 0 (pipeline/store.py:218, via
      auto_audit_weekly.es_pasada_diurna_descartada);
  (ii) experiments/_s126_lib.cargar_mirova, que usa scripts/libro_de_cuentas.py: hora UTC entre 03 y 09.
Sobre la referencia congelada de V1 (filas de alerta, 2026-01-01 a 2026-10-20): cuantas filas clasifica distinto cada
definicion, y cuantas filas nocturnas por (i) caen en el crepusculo (elevacion -12 a 0), donde el dayflag de MIROVA
(no publicado: es una entrada de MIROVA_VIIRS750_hotspot_detection.m, l. 31-33) podria discrepar.
Instrumento: control positivo = una fila a las 15 UTC tiene que salir diurna por las dos; se imprime."""
import csv, collections, io, os, sys
from datetime import datetime, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import auto_audit_weekly as aa  # noqa
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa
C = RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1"
filas = cargar_referencia_unificada(C / "registro_vrp_consolidado.csv", C / "registro_vrp_ocr.csv",
                                    respaldo_path=C / "respaldo_20260408.csv", historico_path=C / "consolidado_filas_perdidas.csv")
coords = aa._coords_por_volcan()
c = collections.Counter(); crep = collections.Counter(); horas_fuera = collections.Counter()
for f in filas:
    if not f["tipo"].startswith("ALERTA") or not ("2026-01-01" <= f["fecha_utc"][:10] <= "2026-10-20"):
        continue
    dt = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    lat, lon = coords[f["volcano"]]
    elev = aa._solar_elevation(lat, lon, dt)
    noche_i = not aa.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, dt)
    noche_ii = 3 <= dt.hour <= 9
    c[(f["sensor_bucket"], noche_i, noche_ii)] += 1
    if noche_i and -12 <= elev <= 0:
        crep[f["sensor_bucket"]] += 1
    if noche_i and not noche_ii:
        horas_fuera[(f["sensor_bucket"], dt.hour)] += 1
print("filas de alerta 2026-01-01 a 2026-10-20, por (sensor, nocturna por elevacion, nocturna por hora 03-09):")
for k, n in sorted(c.items()):
    print("   ", k, n)
print("nocturnas por elevacion con elevacion entre -12 y 0 (crepusculo):", dict(crep))
print("nocturnas por elevacion fuera de 03-09 UTC, por (sensor, hora):", dict(sorted(horas_fuera.items())))
dt = datetime(2026, 10, 1, 15, 0, tzinfo=timezone.utc); lat, lon = coords["Villarrica"]
print("control: Villarrica 2026-10-01 15:00 UTC diurna por (i):", aa.es_pasada_diurna_descartada("VIIRS375", lat, lon, dt),
      "por (ii):", not (3 <= dt.hour <= 9))
