# -*- coding: utf-8 -*-
"""F3 R7. ¿El defecto S150 (fila OCR con distancia/clase de otra pasada) es solo de Suomi NPP? Donde la MISMA
pasada (volcan, sensor, minuto) tiene fila de la tabla y fila del OCR, la tabla es la medida de MIROVA para
esa pasada: comparar distancia, VRP y tipo. Desde 2026-06-13 (A119 deja decidir al OCR).
P1: si el OCR describiera siempre su pasada, distancia y tipo coincidirian salvo redondeo. P2: control: el VRP
de VIIRS 375 debe coincidir (S139: 0 de las compartidas difieren > 0,05 MW en V375); si no coincide, la clave
pareo mal y el resto no vale.
Referencia: snapshot OCR del repo (al dia) y latest_consolidado.csv (copia horaria del remoto), 2026-10-09."""
import sys, collections
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
from referencia_mirova_unificada import leer_pasadas, SNAP_OCR
cons = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]): f for f in leer_pasadas(RAIZ / "latest_consolidado.csv", "CONS", "v")}
ocr = [f for f in leer_pasadas(SNAP_OCR, "OCR", "s") if f["fecha_utc"][:10] >= "2026-06-13"]
par = [(o, cons[(o["volcano"], o["sensor_bucket"], o["fecha_utc"][:16])]) for o in ocr if (o["volcano"], o["sensor_bucket"], o["fecha_utc"][:16]) in cons]
print("filas OCR desde 2026-06-13: %d | con fila de la tabla para la misma pasada: %d" % (len(ocr), len(par)))
for b in ("VIIRS375", "VIIRS750", "MODIS"):
    s = [(o, c) for o, c in par if o["sensor_bucket"] == b]
    if not s: continue
    dv = sum(1 for o, c in s if o["vrp_mw"] is not None and c["vrp_mw"] is not None and abs(o["vrp_mw"] - c["vrp_mw"]) > 0.05)
    dd = [(o, c) for o, c in s if o["dist_km"] is not None and c["dist_km"] is not None and abs(o["dist_km"] - c["dist_km"]) > 0.5]
    sin_d = sum(1 for o, c in s if o["dist_km"] is None)
    tipo = collections.Counter((o["tipo"], c["tipo"]) for o, c in s)
    print("\n%s pares %d | VRP difiere > 0,05 MW: %d | OCR sin distancia legible: %d | distancia difiere > 0,5 km: %d" % (b, len(s), dv, sin_d, len(dd)))
    print("   (tipo OCR, tipo tabla):", dict(tipo))
    for o, c in dd[:8]:
        print("   ", o["fecha_utc"][:16], o["volcano"], "OCR", o["tipo"], o["dist_km"], "| tabla", c["tipo"], c["dist_km"], "| VRP", o["vrp_mw"], c["vrp_mw"])
