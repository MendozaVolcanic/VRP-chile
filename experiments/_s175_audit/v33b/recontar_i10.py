# -*- coding: utf-8 -*-
"""V33B (verificador): recuento independiente de la afirmacion 308 de F5 («el criterio ninguna protegida perdida no tiene
casos en 5 de 11 volcanes»). Otro camino que el de f5_medir.py: no usa su pkl, lee la referencia del arbol de la base
con referencia_mirova_unificada y cuenta, por volcan, las alertas protegidas (clase_mirova.alerta_protegida, lectura A)
nocturnas (auto_audit_weekly.es_pasada_diurna_descartada) en dos ventanas: la de I9/I10 del auditor (2026-09-01 a
2026-11-07) y la ventana del audit semanal de hoy (ultimos 60 dias hasta la fecha de la base, 2026-11-07).
P1: si la referencia no tuviera protegidas, todos los volcanes saldrian 0 (control positivo: Chillan tiene que salir
con decenas). P2: se imprime el total de filas leidas y el total de protegidas; un cero con total 0 es SIN DATO.
Uso: python recontar_i10.py <arbol_base>
"""
import collections
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import auto_audit_weekly as aw  # noqa: E402
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402

for mod in (aw, bp, cm):
    assert Path(mod.__file__).resolve().is_relative_to(ARBOL), mod.__file__
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
coords = bp._coords_por_volcan()
print(f"filas de referencia leidas: {len(filas)} | cons {SNAP_CONS} | ocr {SNAP_OCR}")
print(f"WINDOW_DAYS del audit semanal: {aw.WINDOW_DAYS} | VOLS {len(aw.VOLS)} | SENSORS {aw.SENSORS}")

VENTANAS = {"I9_I10_auditor": ("2026-09-01", "2026-11-07"),
            "audit_60d_hasta_base": ((datetime(2026, 11, 7) - __import__("datetime").timedelta(days=aw.WINDOW_DAYS)).strftime("%Y-%m-%d"), "2026-11-07"),
            "banco_f2": ("2026-03-01", "2026-11-07")}
for nombre, (ini, fin) in VENTANAS.items():
    prot = {}
    for f in filas:
        if f["volcano"] not in aw.VOLS or f["sensor_bucket"] not in aw.SENSORS:
            continue
        if not (ini <= f["fecha_utc"][:10] <= fin):
            continue
        if not cm.alerta_protegida(f):
            continue
        d = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = coords[f["volcano"]]
        diurna = aw.es_pasada_diurna_descartada(f["sensor_bucket"], lat, lon, d)
        k = cm.clave_pasada(f)
        prot[k] = (f["volcano"], f["sensor_bucket"], diurna)
    noct = collections.Counter(v for v, b, diurna in prot.values() if not diurna)
    noct_v375 = collections.Counter(v for v, b, diurna in prot.values() if not diurna and b == "VIIRS375")
    todas = collections.Counter(v for v, b, diurna in prot.values())
    ceros = [v for v in aw.VOLS if noct.get(v, 0) == 0]
    print(f"\n== ventana {nombre} {ini}..{fin}: pasadas protegidas unicas {len(prot)} (nocturnas {sum(noct.values())})")
    for v in aw.VOLS:
        print(f"  {v:20s} nocturnas {noct.get(v, 0):4d} (V375 {noct_v375.get(v, 0):4d}) | todas {todas.get(v, 0):4d}")
    print(f"  volcanes con 0 protegidas nocturnas: {len(ceros)} de {len(aw.VOLS)}: {ceros}")
    print(f"  control positivo: NevadosDeChillan nocturnas = {noct.get('NevadosDeChillan', 0)} (tiene que ser >> 0)")
